from sqlalchemy import and_, case, exists, literal, select
from sqlalchemy.orm import selectinload

from .utils import BoolOptions
from db.models import RecipeModel, UserModel, favorite, shopping_cart, TagModel


async def get_recipes_from_db(
    session,
    current_user_id,
    author_id,
    tags,
    is_favorited_only,
    is_in_shopping_cart_only
        ) -> list[tuple[RecipeModel, UserModel, bool, bool]]:

    favorite_subq = (
        select(RecipeModel.id.label('recipe_id'),
               UserModel.id.label('user_id'))
        .where(favorite.c.recipe_id == RecipeModel.id,
               favorite.c.user_id == current_user_id)
        .alias()
    )

    shopping_cart_subq = (
        select(RecipeModel.id.label('recipe_id'),
               UserModel.id.label('user_id'))
        .where(shopping_cart.c.recipe_id == RecipeModel.id,
               shopping_cart.c.user_id == current_user_id)
        .alias()
    )

    recipes_query = (
        select(RecipeModel,
               UserModel,
               case(
                (exists().where(and_(
                    favorite_subq.c.recipe_id == RecipeModel.id,
                    favorite_subq.c.user_id == current_user_id,)),
                 literal(True)),
                else_=literal(False))
               .label('is_favorited'),
               case(
                (exists().where(and_(
                    shopping_cart_subq.c.recipe_id == RecipeModel.id,
                    shopping_cart_subq.c.user_id == current_user_id,)),
                 literal(True)),
                else_=literal(False))
               .label('is_in_shopping_cart')
               )
        .options(selectinload(RecipeModel.tags),
                 selectinload(RecipeModel.ingredients))
        .outerjoin(UserModel)
    )

    if author_id:
        recipes_query = recipes_query.filter(
            RecipeModel.author_id == author_id)

    if tags:
        recipes_query = recipes_query.filter(
            RecipeModel.tags.any(TagModel.slug.in_(tags)))

    if is_favorited_only == BoolOptions.true:
        recipes_query = recipes_query.join(
            favorite, and_(favorite.c.recipe_id == RecipeModel.id,
                           favorite.c.user_id == current_user_id)
        )

    if is_in_shopping_cart_only == BoolOptions.true:
        recipes_query = recipes_query.join(
            shopping_cart, and_(shopping_cart.c.recipe_id == RecipeModel.id,
                                shopping_cart.c.user_id == current_user_id)
        )

    recipes_result = await session.execute(recipes_query)
    recipes = recipes_result.fetchall()

    return recipes


async def get_single_recipe_from_db(
    id, session, current_user_id
        ) -> tuple[RecipeModel, UserModel, bool, bool]:

    recipe_query = (
        select(RecipeModel, UserModel)
        .options(selectinload(RecipeModel.tags),
                 selectinload(RecipeModel.ingredients))
        .outerjoin(UserModel)
        .filter(RecipeModel.id == id)
    )

    recipe_query = recipe_query.add_columns(
        exists().where(and_(
            favorite.c.recipe_id == id,
            favorite.c.user_id == current_user_id))
        .label('is_favorited')
    )

    recipe_query = recipe_query.add_columns(
        exists().where(and_(
            shopping_cart.c.recipe_id == id,
            shopping_cart.c.user_id == current_user_id))
        .label('is_in_shopping_cart')
    )

    recipe_result = await session.execute(recipe_query)
    recipe_with_user = recipe_result.fetchone()

    return recipe_with_user
