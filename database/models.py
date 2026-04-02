from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    TIMESTAMP,
    func,
    Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from database.connection import Base


class User(Base):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)
    session_token = Column(String(255), index=True)

    # One-to-many relationship
    recipes = relationship("UserRecipe", back_populates="user", cascade="all, delete")


class UserRecipe(Base):
    __tablename__ = "user_recipes"

    recipe_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)

    ingredients = Column(JSONB, nullable=False)
    recipe = Column(JSONB, nullable=False)

    recipe_image_url = Column(String(500))

    created_at = Column(TIMESTAMP, server_default=func.now())

    recipe_nutrition = Column(JSONB)

    is_for_community = Column(Boolean, default=False)

    # Relationship
    user = relationship("User", back_populates="recipes")