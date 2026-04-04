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
    # If shared to community, include the community record id
    community_recipe_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


# ── Community Feed ────────────────────────────────────────────────────────────

class CommentOut(BaseModel):
    """Single comment as returned in the feed."""
    comment_id: int
    user_id: int
    user_name: str
    comment: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RecommendationOut(BaseModel):
    """Single recommendation/tip as returned in the feed."""
    recommendation_id: int
    user_id: int
    user_name: str
    recommendation: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CommunityRecipeOut(BaseModel):
    """Full community recipe card — shown in the feed."""
    community_recipe_id: int
    user_id: int
    user_name: str
    ingredients: list
    cuisine: str
    recipe: dict
    recipe_image_url: Optional[str]
    recipe_nutrition: Optional[dict]
    created_at: datetime
    likes_count: int
    comments: List[CommentOut] = []
    recommendations: List[RecommendationOut] = []
    model_config = ConfigDict(from_attributes=True)


# ── Social Actions ────────────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=1000)

class RecommendationCreate(BaseModel):
    recommendation: str = Field(..., min_length=1, max_length=1000)

class LikeResponse(BaseModel):
    message: str
    likes_count: int

class CommentResponse(BaseModel):
    message: str
    comment: CommentOut

class RecommendationResponse(BaseModel):
    message: str
    recommendation: RecommendationOut