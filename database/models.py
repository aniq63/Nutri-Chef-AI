from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    TIMESTAMP,
    Text,
    Table,
    func,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from database.connection import Base


# ── Many-to-Many association: User ↔ CommunityRecipe (likes) ────────────────
# Composite primary key enforces one-like-per-user-per-recipe at the DB level.
recipe_likes = Table(
    "recipe_likes",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey("user.user_id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "community_recipe_id",
        Integer,
        ForeignKey("community_recipes.community_recipe_id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column("liked_at", TIMESTAMP, server_default=func.now()),
)


# ── User ─────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "user"

    user_id       = Column(Integer, primary_key=True, index=True)
    name          = Column(String(255), nullable=False)
    email         = Column(String(255), nullable=False, unique=True, index=True)
    password      = Column(String(255), nullable=False)
    session_token = Column(String(255), index=True)

    # Private recipes
    recipes = relationship("UserRecipe", back_populates="user", cascade="all, delete")

    # Community recipes this user published
    community_recipes = relationship(
        "CommunityRecipe", back_populates="author", cascade="all, delete"
    )

    # Recipes this user liked (many-to-many)
    liked_recipes = relationship(
        "CommunityRecipe", secondary=recipe_likes, back_populates="liked_by"
    )

    # Comments & recommendations written by this user
    comments        = relationship("RecipeComment",        back_populates="user", cascade="all, delete")
    recommendations = relationship("RecipeRecommendation", back_populates="user", cascade="all, delete")


# ── UserRecipe (private) ──────────────────────────────────────────────────────
class UserRecipe(Base):
    __tablename__ = "user_recipes"

    recipe_id        = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    ingredients      = Column(JSONB, nullable=False)
    cuisine          = Column(String(255), nullable=False)
    recipe           = Column(JSONB, nullable=False)
    recipe_image_url = Column(String(500))
    created_at       = Column(TIMESTAMP, server_default=func.now())
    recipe_nutrition = Column(JSONB)
    is_for_community = Column(Boolean, default=False)

    user = relationship("User", back_populates="recipes")


# ── CommunityRecipe ───────────────────────────────────────────────────────────
class CommunityRecipe(Base):
    """
    A recipe shared to the community feed.
    Auto-populated when is_for_community=True during recipe generation,
    or when a user manually shares a private recipe.

    Social graph:
        likes           → many-to-many with User  (recipe_likes table)
        comments        → one-to-many RecipeComment
        recommendations → one-to-many RecipeRecommendation
    """
    __tablename__ = "community_recipes"

    community_recipe_id = Column(Integer, primary_key=True, index=True)

    # Author info
    user_id   = Column(Integer, ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    user_name = Column(String(255), nullable=False)   # denormalised for fast feed reads

    # Recipe content
    ingredients      = Column(JSONB, nullable=False)
    cuisine          = Column(String(255), nullable=False)
    recipe           = Column(JSONB, nullable=False)
    recipe_image_url = Column(String(500))
    recipe_nutrition = Column(JSONB)
    created_at       = Column(TIMESTAMP, server_default=func.now())

    # ── Relationships ─────────────────────────────────────────────────────────
    author   = relationship("User", back_populates="community_recipes")

    liked_by = relationship(
        "User", secondary=recipe_likes, back_populates="liked_recipes"
    )

    comments = relationship(
        "RecipeComment",
        back_populates="community_recipe",
        cascade="all, delete",
        order_by="RecipeComment.created_at",
    )

    recommendations = relationship(
        "RecipeRecommendation",
        back_populates="community_recipe",
        cascade="all, delete",
        order_by="RecipeRecommendation.created_at",
    )

    @property
    def likes_count(self) -> int:
        """Quick like count without a separate COUNT query when object is loaded."""
        return len(self.liked_by)


# ── RecipeComment ─────────────────────────────────────────────────────────────
class RecipeComment(Base):
    """A comment left by any authenticated user on a community recipe."""
    __tablename__ = "recipe_comments"

    comment_id          = Column(Integer, primary_key=True, index=True)
    community_recipe_id = Column(
        Integer,
        ForeignKey("community_recipes.community_recipe_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id    = Column(Integer, ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    user_name  = Column(String(255), nullable=False)   # denormalised
    comment    = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    community_recipe = relationship("CommunityRecipe", back_populates="comments")
    user             = relationship("User",            back_populates="comments")


# ── RecipeRecommendation ──────────────────────────────────────────────────────
class RecipeRecommendation(Base):
    """
    A recommendation / chef tip left by any user on a community recipe.
    Kept separate from comments so the UI can surface them in a dedicated
    'Tips & Substitutions' section.
    """
    __tablename__ = "recipe_recommendations"

    recommendation_id   = Column(Integer, primary_key=True, index=True)
    community_recipe_id = Column(
        Integer,
        ForeignKey("community_recipes.community_recipe_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id        = Column(Integer, ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    user_name      = Column(String(255), nullable=False)   # denormalised
    recommendation = Column(Text, nullable=False)
    created_at     = Column(TIMESTAMP, server_default=func.now())

    community_recipe = relationship("CommunityRecipe", back_populates="recommendations")
    user             = relationship("User",            back_populates="recommendations")