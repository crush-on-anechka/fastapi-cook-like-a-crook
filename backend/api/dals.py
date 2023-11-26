from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, case, delete, exists, literal, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import (AmountModel, RecipeModel, TagModel, UserModel, favorite,
                       recipe_tag_association, shopping_cart)

from .utils import BoolOptions


async def get_amount(
        session, recipe_id, ingredient_id) -> Optional[AmountModel]:
    query = select(AmountModel).where(and_(
        AmountModel.recipe_id == recipe_id,
        AmountModel.ingredient_id == ingredient_id
    ))
    result = await session.execute(query)
    amount_instance = result.scalar()

    return amount_instance


async def recipe_tag_association_exists(session, tag_id, recipe_id) -> bool:
    query = select(recipe_tag_association).where(and_(
        recipe_tag_association.c.tag_id == tag_id,
        recipe_tag_association.c.recipe_id == recipe_id
    ))
    result = await session.execute(query)
    tag_instance = result.scalar()

    return tag_instance is not None


async def is_recipe_in_favorite(session, user_id, recipe_id) -> bool:
    query = select(favorite).where(and_(
        favorite.c.user_id == user_id,
        favorite.c.recipe_id == recipe_id
    ))
    result = await session.execute(query)
    favorite_instance = result.scalar()

    return favorite_instance is not None


async def get_recipe_or_404(
        recipe_id: int, session: AsyncSession) -> RecipeModel:
    existing_recipe = await session.execute(
        select(RecipeModel).where(RecipeModel.id == recipe_id))

    existing_recipe = existing_recipe.scalar()

    if not existing_recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Recipe with id {recipe_id} not found'
        )

    return existing_recipe


async def delete_amounts(
    cur_recipe: RecipeModel,
    ingredient_ids: list[str],
    session: AsyncSession,
        orphan: bool = False) -> None:
    ingredient_condition = AmountModel.ingredient_id.in_(ingredient_ids)
    if orphan:
        ingredient_condition = ~AmountModel.ingredient_id.in_(
            ingredient_ids)

    await session.execute(
        delete(AmountModel)
        .where(and_(ingredient_condition,
                    AmountModel.recipe_id == cur_recipe.id))
    )


async def delete_tags(
    cur_recipe: RecipeModel,
    tag_ids: list[str],
    session: AsyncSession,
        orphan: bool = False) -> None:
    tag_condition = recipe_tag_association.c.tag_id.in_(tag_ids)
    if orphan:
        tag_condition = ~recipe_tag_association.c.tag_id.in_(tag_ids)

    await session.execute(
        delete(recipe_tag_association)
        .where(and_(tag_condition,
                    recipe_tag_association.c.recipe_id == cur_recipe.id))
    )


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
