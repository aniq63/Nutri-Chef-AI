import warnings

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database import models, schemas
from services.nutrition_analysis import NutritionService
from services.recipe_image_service import ImageSearchService
from utils.authentication import get_current_user
from utils.ingredients_parser import IngredientParser

warnings.filterwarnings("ignore")

router = APIRouter(
    prefix="/User-Recipe",
    tags=["User Own Recipe"]
)


@router.post(
    "/save",
    response_model=schemas.UserOwnRecipeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save your own hand-written recipe",
    description=(
        "Submit a recipe you wrote yourself. "
        "Ingredients are parsed from raw strings (e.g. '200g salmon fillet') "
        "into structured data, sent through nutrition analysis, and a recipe "
        "image is fetched automatically. The result is saved to your recipe "
        "library. Set is_for_community=true to also publish it to the community feed."
    )
)
async def save_user_own_recipe(
    input: schemas.UserOwnRecipeInput,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # ── 1. Parse raw ingredient strings ─────────────────────────────────────
    # e.g. "200g broccoli, cut into florets" → {"name": "broccoli", "grams": 200}
    parser = IngredientParser()
    structured_ingredients = parser.parse(input.ingredients)

    # ── 2. Nutrition analysis ────────────────────────────────────────────────
    nutrition_service = NutritionService()
    nutrition_data = nutrition_service.get_total_nutrition(ingredients=structured_ingredients)

    # ── 3. Fetch recipe image ────────────────────────────────────────────────
    image_service = ImageSearchService()
    image_url = image_service.get_first_image_url(query=input.title)

    # ── 4. Build the recipe dict (same shape as AI-generated recipes) ────────
    # Storing it as a unified dict means both recipe types are queried,
    # displayed, and shared to the community in exactly the same way.
    recipe_body = {
        "title":       input.title,
        "cuisine":     input.cuisine,
        "time":        input.time.model_dump(),
        "servings":    input.servings,
        "difficulty":  input.difficulty,
        "why":         input.why,
        "ingredients": input.ingredients,   # original raw strings kept for display
        "steps":       input.steps,
        "health_note": input.health_note,
        "chef_tip":    input.chef_tip,
        "message":     input.message,
    }

    # ── 5. Save to UserRecipes table ─────────────────────────────────────────
    user_recipe = models.UserRecipe(
        user_id=current_user.user_id,
        ingredients=structured_ingredients,     # parsed [{name, grams}] for nutrition queries
        cuisine=input.cuisine,
        recipe=recipe_body,
        recipe_image_url=image_url,
        recipe_nutrition=nutrition_data,
        is_for_community=input.is_for_community,
    )
    db.add(user_recipe)
    await db.flush()    # get recipe_id before optional community insert

    # ── 6. Publish to community feed if requested ────────────────────────────
    community_recipe_id = None

    if input.is_for_community:
        community_recipe = models.CommunityRecipe(
            user_id=current_user.user_id,
            user_name=current_user.name,
            ingredients=structured_ingredients,
            cuisine=input.cuisine,
            recipe=recipe_body,
            recipe_image_url=image_url,
            recipe_nutrition=nutrition_data,
        )
        db.add(community_recipe)
        await db.flush()
        community_recipe_id = community_recipe.community_recipe_id

    # ── 7. Commit both records in one transaction ────────────────────────────
    await db.commit()
    await db.refresh(user_recipe)

    return schemas.UserOwnRecipeResponse(
        recipe_id=user_recipe.recipe_id,
        recipe_title=input.title,
        cuisine=input.cuisine,
        recipe_image_url=image_url,
        ingredients=structured_ingredients,
        recipe=recipe_body,
        recipe_nutrition=nutrition_data,
        is_for_community=input.is_for_community,
        created_at=user_recipe.created_at,
        community_recipe_id=community_recipe_id,
    )