from datetime import datetime

from sqlalchemy import (CheckConstraint, Column, DateTime, ForeignKey, Index,
                        Integer, SmallInteger, String, Table, Text,
                        UniqueConstraint)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


recipe_tag_association = Table(
    'recipe_tag_association',
    Base.metadata,
    Column('recipe_id', Integer, ForeignKey('recipes.id', ondelete='CASCADE')),
    Column(
        'tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE')),
    UniqueConstraint('recipe_id', 'tag_id', name='unique_recipe_tag')
)


favorite = Table(
    'favorite',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('recipe_id', Integer, ForeignKey('recipes.id', ondelete='CASCADE')),
    UniqueConstraint('user_id', 'recipe_id', name='unique_favorite')
)


shopping_cart = Table(
    'shopping_cart',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('recipe_id', Integer, ForeignKey('recipes.id', ondelete='CASCADE')),
    UniqueConstraint('user_id', 'recipe_id', name='unique_shopping_cart')
)


class UserModel(Base):  # TODO: IMPLEMENT!
    __tablename__ = 'users'

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(200), unique=True)


class IngredientModel(Base):
    __tablename__ = 'ingredients'

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(200), unique=True)
    measurement_unit = Column(String(200))
    recipes = relationship('AmountModel', back_populates='ingredient')


class TagModel(Base):
    __tablename__ = 'tags'

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(200), unique=True)  # TODO: validate!!!
    slug = Column(String(200), unique=True)
    color = Column(String(7), unique=True)  # TODO: validate!!!
    recipes = relationship(
        'RecipeModel', secondary=recipe_tag_association, back_populates='tags')


class RecipeModel(Base):
    __tablename__ = 'recipes'

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(200))
    text = Column(Text)
    pub_date = Column(DateTime, default=datetime.utcnow)
    author_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))  # TODO: rename to author!
    ingredients = relationship(
        'AmountModel', back_populates='recipe', lazy='selectin')
    tags = relationship('TagModel',
                        secondary=recipe_tag_association,
                        back_populates='recipes',
                        lazy='selectin')
    cooking_time = Column(SmallInteger, CheckConstraint(
        'cooking_time > 0', name='check_positive_cooking_time'))
    image = Column(String)  # TODO: Store the image path or reference 'recipes/images/')


class AmountModel(Base):
    __tablename__ = 'amounts'

    recipe_id = Column(Integer, ForeignKey(
        'recipes.id', ondelete='CASCADE'), primary_key=True)
    ingredient_id = Column(Integer, ForeignKey(
        'ingredients.id', ondelete='CASCADE'), primary_key=True)
    amount = Column(SmallInteger)

    recipe = relationship(
        'RecipeModel', back_populates='ingredients', lazy='selectin')
    ingredient = relationship(
        'IngredientModel', back_populates='recipes', lazy='selectin')


name_index = Index('name_index', IngredientModel.name)
