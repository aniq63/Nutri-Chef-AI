import io
import warnings

from PIL import Image
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database import models, schemas
from services.ingredients_extractor import FoodAnalyzer
from services.recipe_generator import NutriChefAI
from services.nutrition_analysis import NutritionService
from services.recipe_image_service import ImageSearchService
from utils.authentication import get_current_user
from utils.ingredients_parser import IngredientParser

warnings.filterwarnings("ignore")

router = APIRouter(
    prefix="/Fridge-Mode",
    tags=["Fridge Mode"]
)

# Allowed image MIME types for the upload
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}

MAX_IMAGE_SIZE = 1_048_576  # 1 MB — LogMeal API hard limit


def compress_image_bytes(raw_bytes: bytes, max_size: int = MAX_IMAGE_SIZE) -> bytes:
    """Compress an image to fit under `max_size` bytes (default 1 MB).

    Strategy:
    1. Re-encode as JPEG, starting at quality 90.
    2. Reduce quality in steps of 5 down to 20.
    3. If still too large, halve the image dimensions and repeat.
    """
    img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")

    for _ in range(4):                       # max 4 resize rounds
        for quality in range(90, 15, -5):
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)
            if buf.tell() <= max_size:
                return buf.getvalue()
        # still too large → halve both dimensions
        img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)

    # absolute fallback (tiny image at lowest quality)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=20, optimize=True)
    return buf.getvalue()


@router.post(
    "/scan-and-cook",
    response_model=schemas.FridgeModeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Scan your fridge and get a recipe",
    description=(
        "Upload a photo of your fridge or ingredients. "
        "The image is analysed to detect what ingredients are present, "
        "then the full AI recipe pipeline runs automatically: "
        "recipe generation → nutrition analysis → recipe image fetch → save to DB. "
        "Optionally share the result to the community feed."
    )
)
async def fridge_mode(
    # Image upload — sent as multipart/form-data
    image: UploadFile = File(..., description="Photo of your fridge or ingredients"),

    # Extra fields sent alongside the image in the same multipart form
    cuisine: str = Form(..., description="Preferred cuisine style e.g. 'Italian'"),
    is_for_community: bool = Form(False, description="Share to community feed?"),

    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # ── 0. Validate image type ───────────────────────────────────────────────
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{image.content_type}'. Use JPEG, PNG or WEBP."
        )

    # ── 1. Read image bytes, compress, & extract ingredients via LogMeal API ─
    raw_bytes = await image.read()
    image_bytes = compress_image_bytes(raw_bytes)

    analyzer = FoodAnalyzer()
    detected_ingredients = analyzer.get_ingredients(image_content=image_bytes)

    if not detected_ingredients:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "No ingredients could be detected in the image. "
                "Try a clearer photo with better lighting."
            )
        )

    # ── 2. Generate recipe with AI ───────────────────────────────────────────
    # detected_ingredients is already List[str] e.g. ["salmon", "broccoli", "lemon"]
    ai_assistant = NutriChefAI()
    result = ai_assistant.run(ingredients=detected_ingredients, cuisine=cuisine)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI recipe generation failed: {result['error']}"
        )

    recipe_data: dict = result["data"]

    # ── 3. Parse AI ingredients → structured dicts ───────────────────────────
    raw_ingredients: list = recipe_data.get("ingredients", [])

    if not raw_ingredients:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI response is missing the 'ingredients' field."
        )

    parser = IngredientParser()
    structured_ingredients = parser.parse(raw_ingredients)

    # ── 4. Nutrition analysis ────────────────────────────────────────────────
    nutrition_service = NutritionService()
    nutrition_data = nutrition_service.get_total_nutrition(ingredients=structured_ingredients)

    # ── 5. Fetch recipe image ────────────────────────────────────────────────
    image_service = ImageSearchService()
    recipe_title = recipe_data.get("title", f"{cuisine} recipe")
    image_url = image_service.get_first_image_url(query=recipe_title)

    # ── 6. Save to UserRecipes ───────────────────────────────────────────────
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
    await db.flush()

    # ── 7. Publish to community feed if requested ────────────────────────────
    community_recipe_id = None

    if is_for_community:
        community_recipe = models.CommunityRecipe(
            user_id=current_user.user_id,
            user_name=current_user.name,
            ingredients=structured_ingredients,
            cuisine=cuisine,
            recipe=recipe_data,
            recipe_image_url=image_url,
            recipe_nutrition=nutrition_data,
        )
        db.add(community_recipe)
        await db.flush()
        community_recipe_id = community_recipe.community_recipe_id

    # ── 8. Commit everything in one transaction ──────────────────────────────
    await db.commit()
    await db.refresh(user_recipe)

    return schemas.FridgeModeResponse(
        detected_ingredients=detected_ingredients,
        recipe_id=user_recipe.recipe_id,
        recipe_image_url=image_url,
        ingredients=structured_ingredients,
        recipe_title=recipe_title,
        recipe=recipe_data,
        cuisine=cuisine,
        recipe_nutrition=nutrition_data,
        is_for_community=is_for_community,
        created_at=user_recipe.created_at,
        community_recipe_id=community_recipe_id,
    )