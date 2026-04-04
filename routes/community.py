import warnings

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from database.connection import get_db
from database import models, schemas
from utils.authentication import get_current_user

warnings.filterwarnings("ignore")

router = APIRouter(
    prefix="/Community",
    tags=["Community"]
)


# ── Feed ─────────────────────────────────────────────────────────────────────

@router.get(
    "/feed",
    response_model=list[schemas.CommunityRecipeOut],
    summary="Browse the community recipe feed",
    description="Returns all community recipes, newest first, with likes, comments, and recommendations."
)
async def get_community_feed(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
):
    result = await db.execute(
        select(models.CommunityRecipe)
        .options(
            selectinload(models.CommunityRecipe.liked_by),
            selectinload(models.CommunityRecipe.comments),
            selectinload(models.CommunityRecipe.recommendations),
        )
        .order_by(models.CommunityRecipe.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    recipes = result.scalars().all()
    return recipes


@router.get(
    "/recipe/{community_recipe_id}",
    response_model=schemas.CommunityRecipeOut,
    summary="Get a single community recipe"
)
async def get_community_recipe(
    community_recipe_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = await db.execute(
        select(models.CommunityRecipe)
        .where(models.CommunityRecipe.community_recipe_id == community_recipe_id)
        .options(
            selectinload(models.CommunityRecipe.liked_by),
            selectinload(models.CommunityRecipe.comments),
            selectinload(models.CommunityRecipe.recommendations),
        )
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return recipe


# ── Likes ─────────────────────────────────────────────────────────────────────

@router.post(
    "/recipe/{community_recipe_id}/like",
    response_model=schemas.LikeResponse,
    summary="Like or unlike a community recipe",
    description="Toggles like. First call likes, second call unlikes (like Instagram)."
)
async def toggle_like(
    community_recipe_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Load recipe with its liked_by list
    result = await db.execute(
        select(models.CommunityRecipe)
        .where(models.CommunityRecipe.community_recipe_id == community_recipe_id)
        .options(selectinload(models.CommunityRecipe.liked_by))
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    already_liked = any(u.user_id == current_user.user_id for u in recipe.liked_by)

    if already_liked:
        recipe.liked_by.remove(current_user)
        message = "Recipe unliked"
    else:
        recipe.liked_by.append(current_user)
        message = "Recipe liked"

    await db.commit()
    await db.refresh(recipe)

    # Re-load liked_by to get accurate count after commit
    result = await db.execute(
        select(models.CommunityRecipe)
        .where(models.CommunityRecipe.community_recipe_id == community_recipe_id)
        .options(selectinload(models.CommunityRecipe.liked_by))
    )
    recipe = result.scalar_one()

    return schemas.LikeResponse(message=message, likes_count=recipe.likes_count)


# ── Comments ──────────────────────────────────────────────────────────────────

@router.post(
    "/recipe/{community_recipe_id}/comment",
    response_model=schemas.CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to a community recipe"
)
async def add_comment(
    community_recipe_id: int,
    body: schemas.CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Verify recipe exists
    result = await db.execute(
        select(models.CommunityRecipe)
        .where(models.CommunityRecipe.community_recipe_id == community_recipe_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Recipe not found")

    comment = models.RecipeComment(
        community_recipe_id=community_recipe_id,
        user_id=current_user.user_id,
        user_name=current_user.name,
        comment=body.comment,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return schemas.CommentResponse(
        message="Comment added",
        comment=schemas.CommentOut.model_validate(comment)
    )


@router.delete(
    "/comment/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete your own comment"
)
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = await db.execute(
        select(models.RecipeComment).where(models.RecipeComment.comment_id == comment_id)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")

    await db.delete(comment)
    await db.commit()


# ── Recommendations ───────────────────────────────────────────────────────────

@router.post(
    "/recipe/{community_recipe_id}/recommendation",
    response_model=schemas.RecommendationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a recommendation / chef tip to a community recipe"
)
async def add_recommendation(
    community_recipe_id: int,
    body: schemas.RecommendationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = await db.execute(
        select(models.CommunityRecipe)
        .where(models.CommunityRecipe.community_recipe_id == community_recipe_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Recipe not found")

    rec = models.RecipeRecommendation(
        community_recipe_id=community_recipe_id,
        user_id=current_user.user_id,
        user_name=current_user.name,
        recommendation=body.recommendation,
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)

    return schemas.RecommendationResponse(
        message="Recommendation added",
        recommendation=schemas.RecommendationOut.model_validate(rec)
    )


@router.delete(
    "/recommendation/{recommendation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete your own recommendation"
)
async def delete_recommendation(
    recommendation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = await db.execute(
        select(models.RecipeRecommendation)
        .where(models.RecipeRecommendation.recommendation_id == recommendation_id)
    )
    rec = result.scalar_one_or_none()

    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    if rec.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own recommendations")

    await db.delete(rec)
    await db.commit()