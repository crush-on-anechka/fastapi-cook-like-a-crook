from datetime import datetime

from sqlalchemy import (Boolean, CheckConstraint, Column, DateTime, ForeignKey,
                        Index, Integer, SmallInteger, String, Table, Text,
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


subscription = Table(
    'subscriptions',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('followed_user_id',
           Integer,
           ForeignKey('users.id', ondelete='CASCADE')),
    UniqueConstraint('user_id', 'followed_user_id', name='unique_subscription')
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


class UserModel(Base):
    __tablename__ = 'users'

    id = Column(Integer, autoincrement=True, primary_key=True)
    email = Column(String(), nullable=False)
    password = Column(String(150), nullable=False)
    username = Column(
        String(150),
        # CheckConstraint(
        #     'username ~ "^[\\w.@+-]+$"', name='check_valid_username'),
        unique=True,
        nullable=False)
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    is_subscribed = Column(Boolean(), default=False)
    recipes = relationship(
        'RecipeModel', back_populates='author_relation',
        lazy='selectin', order_by='desc(RecipeModel.pub_date)')


class IngredientModel(Base):
    __tablename__ = 'ingredients'

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(200), unique=True)
    measurement_unit = Column(String(200))
    recipes = relationship('AmountModel', back_populates='ingredient')


class TagModel(Base):
    __tablename__ = 'tags'

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(200), unique=True)
    slug = Column(
        String(200),
        # CheckConstraint(
        #     'slug ~ "^[-a-zA-Z0-9_]+$" COLLATE "C"', name='check_valid_slug'),
        unique=True)
    color = Column(
        String(7),
        # CheckConstraint(
        #     'color ~ "^#([a-f0-9]{6})$"', name='check_valid_hex_color'),
        unique=True)
    recipes = relationship(
        'RecipeModel', secondary=recipe_tag_association, back_populates='tags')


class RecipeModel(Base):
    __tablename__ = 'recipes'

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(200), nullable=False)
    text = Column(Text, nullable=False)
    pub_date = Column(DateTime, default=datetime.utcnow)
    author = Column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    ingredients = relationship('AmountModel',
                               back_populates='recipe',
                               lazy='selectin')
    tags = relationship('TagModel',
                        secondary=recipe_tag_association,
                        back_populates='recipes',
                        lazy='selectin')
    cooking_time = Column(
        SmallInteger,
        CheckConstraint(
            'cooking_time > 0', name='check_positive_cooking_time'),
        nullable=False)
    image = Column(String, nullable=False)  # TODO: Store the image path or reference 'recipes/images/')
    author_relation = relationship(
        'UserModel', back_populates='recipes', lazy='selectin')


class AmountModel(Base):
    __tablename__ = 'amounts'

    recipe_id = Column(Integer, ForeignKey(
        'recipes.id', ondelete='CASCADE'), primary_key=True)
    ingredient_id = Column(Integer, ForeignKey(
        'ingredients.id', ondelete='CASCADE'), primary_key=True)
    amount = Column(SmallInteger, CheckConstraint(
        'amount > 0', name='check_positive_amount'))

    recipe = relationship(
        'RecipeModel', back_populates='ingredients', lazy='selectin')
    ingredient = relationship(
        'IngredientModel', back_populates='recipes', lazy='selectin')


name_index = Index('name_index', IngredientModel.name)
