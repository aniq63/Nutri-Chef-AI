from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Any
from datetime import datetime


# ---------- User Authentication -------------

class UserCreate(BaseModel):
    """Schema for user registration."""
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6)
    email: EmailStr


class LoginUser(BaseModel):
    """Schema for user login."""
    name: str
    password: str


class UserResponse(BaseModel):
    """Response model for user data."""
    user_id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Response model for login token."""
    access_token: str
    token_type: str


# ---------- AI Recipe Generator -------------

class RecipeInput(BaseModel):
    """
    Input schema for the AI recipe generator.
    Ingredients are plain strings exactly as the user types them,
    e.g. ["200g salmon", "1 lemon", "2 cups broccoli"].
    The IngredientParser utility converts them to structured dicts
    before nutrition analysis.
    """
    ingredients: List[str] = Field(
        ...,
        min_length=1,
        description="Raw ingredient strings, e.g. ['200g salmon', '1 lemon']"
    )
    cuisine: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Cuisine style, e.g. 'Italian', 'Pakistani', 'Mediterranean'"
    )
    is_for_community: bool = Field(
        default=False,
        description="Whether this recipe should be shared with the community"
    )


# ---------- Recipe Response -------------

class RecipeResponse(BaseModel):
    """Response model returned after a recipe is generated and saved."""
    recipe_id: int
    recipe_image_url: Optional[str]
    # Structured ingredients after parsing, e.g. [{"name": "salmon", "grams": 200}]
    ingredients: List[dict]
    recipe_title: str
    recipe: dict
    cuisine: str
    recipe_nutrition: Optional[dict]
    is_for_community: bool
    created_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)