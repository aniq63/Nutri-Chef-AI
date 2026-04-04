from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database.connection import get_db
from database import models, schemas
from utils.authentication import get_current_user

router = APIRouter(
    prefix="/User-Recipes",
    tags=["User-Recipes"]
)

@router.get(
    "/my_recipes",
    response_model=List[schemas.RecipeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all recipes for the logged-in user",
    description="Returns a list of recipes formatted specifically for UI cards and detail views."
)
async def get_user_recipes(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    stmt = (
        select(models.UserRecipe)
        .where(models.UserRecipe.user_id == current_user.user_id)
        .order_by(models.UserRecipe.created_at.desc())
    )
    
    result = await db.execute(stmt)
    db_recipes = result.scalars().all()

    # 2. Map DB objects to the Schema
    ui_ready_recipes = []
    
    for row in db_recipes:
        raw_recipe = row.recipe or {}
        display_title = raw_recipe.get("title", f"{row.cuisine} Recipe")

        # Create the response object
        recipe_item = schemas.RecipeResponse(
            recipe_id=row.recipe_id,
            recipe_image_url=row.recipe_image_url, # For <img src={...} />
            recipe_title=display_title,           # For Card Title
            ingredients=row.ingredients,           # For 'Ingredients' list
            recipe=row.recipe,                     # For 'Instructions' text
            cuisine=row.cuisine,                   # For 'Cuisine' badge
            recipe_nutrition=row.recipe_nutrition, # For Nutrition facts table
            is_for_community=row.is_for_community,
            created_at=row.created_at              # For 'Created on' label
        )
        ui_ready_recipes.append(recipe_item)

    return ui_ready_recipes