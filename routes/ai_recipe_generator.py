import warnings

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database import models, schemas
from services.recipe_generator import NutriChefAI
from services.nutrition_analysis import NutritionService
from services.recipe_image_service import ImageSearchService
from utils.authentication import get_current_user
from utils.ingredients_parser import IngredientParser

warnings.filterwarnings("ignore")

router = APIRouter(
    prefix="/AI-Recipe-Generator",
    tags=["AI-Recipe-Generator"]
)


@router.post(
    "/recipe_generator",
    response_model=schemas.RecipeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate an AI-powered recipe",
    description=(
        "Accepts a list of ingredients and a cuisine style, then uses an AI model "
        "to generate a full recipe, fetches nutritional data, and retrieves a recipe image. "
        "The result is persisted to the database and linked to the authenticated user."
    )
)
async def ai_recipe_generator(
    input: schemas.RecipeInput,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ingredients: list[str] = input.ingredients
    cuisine = input.cuisine
    is_for_community = input.is_for_community

    # ── 1. Generate recipe with AI ──────────────────────────────────────────
    ai_assistant = NutriChefAI()
    result = ai_assistant.run(ingredients=ingredients, cuisine=cuisine)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI recipe generation failed: {result['error']}"
        )

    recipe_data: dict = result["data"]

    raw_ingredients: list = recipe_data.get("ingredients", [])

    if not raw_ingredients:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI response is missing the 'ingredients' field."
        )

    parser = IngredientParser()
    structured_ingredients = parser.parse(raw_ingredients)

    # ── 3. Fetch nutrition data ──────────────────────────────────────────────
    nutrition_service = NutritionService()
    nutrition_data = nutrition_service.get_total_nutrition(ingredients=structured_ingredients)

    # ── 4. Fetch recipe image ────────────────────────────────────────────────
    image_service = ImageSearchService()
    recipe_title = recipe_data.get("title", f"{cuisine} recipe")
    image_url = image_service.get_first_image_url(query=recipe_title)

    # ── 5. Persist to database ───────────────────────────────────────────────
    user_recipe = models.UserRecipe(
        user_id=current_user.user_id,
        ingredients=structured_ingredients,
        cuisine=cuisine,
        recipe=recipe_data,
        recipe_image_url=image_url,
        recipe_nutrition=nutrition_data,
        is_for_community=is_for_community,
    )

    db.add(user_recipe)
    await db.commit()
    await db.refresh(user_recipe)

    # ── 6. Return structured response ────────────────────────────────────────
    return schemas.RecipeResponse(
        recipe_id=user_recipe.recipe_id,
        recipe_image_url=image_url,
        ingredients=structured_ingredients,
        recipe_title=recipe_title,
        recipe=recipe_data,
        cuisine=cuisine,
        recipe_nutrition=nutrition_data,
        is_for_community=is_for_community,
        created_at=user_recipe.created_at,
    )