from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime


# ── User Authentication ───────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6)
    email: EmailStr

class LoginUser(BaseModel):
    name: str
    password: str

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# ── AI Recipe Generator ───────────────────────────────────────────────────────

class RecipeInput(BaseModel):
    ingredients: List[str] = Field(..., min_length=1)
    cuisine: str = Field(..., min_length=1, max_length=100)
    is_for_community: bool = Field(default=False)

class RecipeResponse(BaseModel):
    recipe_id: int
    recipe_image_url: Optional[str]
    ingredients: List[dict]
    recipe_title: str
    recipe: dict
    cuisine: str
    recipe_nutrition: Optional[dict]
    is_for_community: bool
    created_at: Optional[datetime]
    community_recipe_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


# ── User Own Recipe ───────────────────────────────────────────────────────────

class RecipeTime(BaseModel):
    """Cooking time breakdown — mirrors the AI recipe JSON format."""
    prep:  str = Field(..., example="10 min")
    cook:  str = Field(..., example="20 min")
    total: str = Field(..., example="30 min")


class UserOwnRecipeInput(BaseModel):
    """
    Schema for a user submitting their own hand-written recipe.

    Ingredients are raw strings (e.g. '200g salmon fillet').
    They are automatically:
      1. Parsed by IngredientParser  →  [{"name": "salmon fillet", "grams": 200}, ...]
      2. Sent to NutritionService    →  full nutrition breakdown
      3. Used to fetch a recipe image via ImageSearchService

    The recipe is stored in the same UserRecipes table as AI-generated recipes,
    so the structure mirrors the AI output format exactly.
    """
    title:      str = Field(..., min_length=1, max_length=255, example="Mediterranean Baked Salmon")
    cuisine:    str = Field(..., min_length=1, max_length=100, example="Mediterranean")
    time:       RecipeTime
    servings:   int = Field(..., gt=0, example=2)
    difficulty: str = Field(..., example="Easy")
    why:        Optional[str] = Field(None, example="Lemon complements salmon perfectly")
    ingredients: List[str] = Field(
        ...,
        min_length=1,
        example=["200g salmon fillet", "200g broccoli, cut into florets", "1 lemon, sliced"],
        description="Raw ingredient strings — parsed automatically for nutrition analysis"
    )
    steps:       List[str]      = Field(..., min_length=1, example=["Step 1: Preheat oven to 200°C"])
    health_note: Optional[str]  = None
    chef_tip:    Optional[str]  = None
    message:     Optional[str]  = None
    is_for_community: bool      = Field(default=False)


class UserOwnRecipeResponse(BaseModel):
    """Response returned after a user's own recipe is saved."""
    recipe_id:        int
    recipe_title:     str
    cuisine:          str
    recipe_image_url: Optional[str]
    ingredients:      List[dict]    # structured [{name, grams}] after parsing
    recipe:           dict          # full recipe body as stored in DB
    recipe_nutrition: Optional[dict]
    is_for_community: bool
    created_at:       Optional[datetime]
    community_recipe_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


# ── Community Feed ────────────────────────────────────────────────────────────

class CommentOut(BaseModel):
    comment_id: int
    user_id:    int
    user_name:  str
    comment:    str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RecommendationOut(BaseModel):
    recommendation_id: int
    user_id:           int
    user_name:         str
    recommendation:    str
    created_at:        datetime
    model_config = ConfigDict(from_attributes=True)

class CommunityRecipeOut(BaseModel):
    community_recipe_id: int
    user_id:             int
    user_name:           str
    ingredients:         list
    cuisine:             str
    recipe:              dict
    recipe_image_url:    Optional[str]
    recipe_nutrition:    Optional[dict]
    created_at:          datetime
    likes_count:         int
    comments:            List[CommentOut]        = []
    recommendations:     List[RecommendationOut] = []
    model_config = ConfigDict(from_attributes=True)


# ── Social Actions ────────────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=1000)

class RecommendationCreate(BaseModel):
    recommendation: str = Field(..., min_length=1, max_length=1000)

class LikeResponse(BaseModel):
    message:     str
    likes_count: int

class CommentResponse(BaseModel):
    message: str
    comment: CommentOut

class RecommendationResponse(BaseModel):
    message:        str
    recommendation: RecommendationOut