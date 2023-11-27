from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette.responses import Response

from db.models import (AmountModel, IngredientModel, RecipeModel, TagModel,
                       favorite)
from db.schemas import (FavoriteSchema, IngredientSchema, RecipeSchema,
                        TagSchema)
from db.session import get_async_session
from settings import PAGE_LIMIT

from .dals import (delete_amounts, delete_tags, get_amount, get_recipe_or_404,
                   get_recipes_from_db, get_single_recipe_from_db,
                   is_recipe_in_favorite, recipe_tag_association_exists)
from .serializers import (serialize_favorite, serialize_ingredient,
                          serialize_ingredients_list, serialize_recipe,
                          serialize_recipes_list, serialize_tag,
                          serialize_tags_list)
from .utils import BoolOptions, get_current_user_id

router = APIRouter()


class RecipeUtility:
    @staticmethod
    async def _add_or_update_ingredients(
        ingredients_data,
        ingredient_ids: list[str],
        cur_recipe: RecipeModel,
        recipe_data: RecipeSchema,
            session: AsyncSession):
        ingredients = await session.execute(
            select(IngredientModel)
            .where(IngredientModel.id.in_(ingredient_ids))
        )

        ingredient_dict = {i.id: i for i in ingredients.scalars()}

        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['id']
            new_amount = ingredient_data['amount']

            current_amount = await get_amount(
                session, cur_recipe.id, ingredient_id)
            if current_amount:
                current_amount.amount = new_amount
                continue

            ingredient = ingredient_dict.get(ingredient_id)
            if not ingredient:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f'Ingredient with ID {ingredient_id} not found')

            cur_recipe.ingredients.append(
                AmountModel(amount=new_amount, ingredient=ingredient))

    @staticmethod
    async def _add_or_update_tags(
        tag_ids: list[str],
        cur_recipe: RecipeModel,
        recipe_data: RecipeSchema,
            session: AsyncSession):
        tags = await session.execute(
            select(TagModel).where(TagModel.id.in_(tag_ids)))
        tag_dict = {tag.id: tag for tag in tags.scalars()}

        for tag_id in tag_ids:

            if await recipe_tag_association_exists(
                    session, tag_id, cur_recipe.id):
                continue

            tag = tag_dict.get(tag_id)
            if not tag:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f'Tag with ID {tag_id} not found'
                )
            cur_recipe.tags.append(tag)

    @staticmethod
    async def _update_recipe_fields(
        cur_recipe: RecipeModel,
        recipe_data: RecipeSchema,
        ingredients_data,
        ingredient_ids,
        tag_ids,
            session: AsyncSession):
        cur_recipe.name = recipe_data.get('name')
        cur_recipe.text = recipe_data.get('text')
        cur_recipe.cooking_time = recipe_data.get('cooking_time')
        cur_recipe.image = recipe_data.get('image')

        await RecipeUtility._add_or_update_ingredients(
            ingredients_data, ingredient_ids, cur_recipe, recipe_data, session)

        await RecipeUtility._add_or_update_tags(
            tag_ids, cur_recipe, recipe_data, session)

    @staticmethod
    async def perform_create_recipe(
        cur_recipe: RecipeModel,
        recipe_data: RecipeSchema,
            session: AsyncSession):
        ingredients_data = recipe_data.get('ingredients', [])
        ingredient_ids = [i['id'] for i in ingredients_data]
        tag_ids = recipe_data.get('tags', [])

        await RecipeUtility._update_recipe_fields(
            cur_recipe, recipe_data, ingredients_data,
            ingredient_ids, tag_ids, session
        )

    @staticmethod
    async def perform_update_recipe(
        cur_recipe: RecipeModel,
        recipe_data: RecipeSchema,
            session: AsyncSession):
        ingredients_data = recipe_data.get('ingredients', [])
        ingredient_ids = [i['id'] for i in ingredients_data]
        tag_ids = recipe_data.get('tags', [])

        await RecipeUtility._update_recipe_fields(
            cur_recipe, recipe_data, ingredients_data,
            ingredient_ids, tag_ids, session
        )
        await session.flush()

        await delete_amounts(cur_recipe, ingredient_ids, session, orphan=True)
        await delete_tags(cur_recipe, tag_ids, session, orphan=True)

        await session.commit()


@router.get('/tags', response_model=list[TagSchema])
async def get_tags_list(
        session: AsyncSession = Depends(get_async_session)) -> JSONResponse:
    tags_result = await session.execute(select(TagModel))
    tags = tags_result.scalars().all()
    tags_data: list[dict] = serialize_tags_list(tags)

    return JSONResponse(content=tags_data, status_code=status.HTTP_200_OK)


@router.get('/tags/{id}', response_model=TagSchema)
async def get_tag_by_id(id: int = Path(..., title='Tag ID'),
                        session: AsyncSession = Depends(get_async_session)
                        ) -> JSONResponse:
    tag_result = await session.execute(select(TagModel).filter_by(id=id))
    tag = tag_result.scalar()

    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Tag with ID {id} not found'
        )

    tag_data: dict = serialize_tag(tag)

    return JSONResponse(content=tag_data, status_code=status.HTTP_200_OK)


@router.get('/ingredients', response_model=list[IngredientSchema])
async def get_ingredients_list(
        session: AsyncSession = Depends(get_async_session)) -> JSONResponse:
    ingredients_result = await session.execute(select(IngredientModel))
    ingredients = ingredients_result.scalars().all()
    ingredients_data: list[dict] = serialize_ingredients_list(ingredients)

    return JSONResponse(
        content=ingredients_data, status_code=status.HTTP_200_OK)


@router.get('/ingredients/{id}', response_model=IngredientSchema)
async def get_ingredient_by_id(
    id: int = Path(..., title='Ingredient ID'),
        session: AsyncSession = Depends(get_async_session)) -> JSONResponse:
    ingredient_result = await session.execute(
        select(IngredientModel).filter_by(id=id))
    ingredient = ingredient_result.scalar()

    if ingredient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Ingredient with ID {id} not found'
        )

    ingredient_data: dict = serialize_ingredient(ingredient)

    return JSONResponse(
        content=ingredient_data, status_code=status.HTTP_200_OK)


@router.get('/recipes', response_model=list[RecipeSchema])
async def get_recipes_list(
    current_user_id: int = Depends(get_current_user_id),
    author: int = Query(None, title='Author'),
    tags: list[str] = Query(None, title='Tags'),
    is_favorited: BoolOptions = Query(
        BoolOptions.false, title='Is favorited'),
    is_in_shopping_cart: BoolOptions = Query(
        BoolOptions.false, title='Is in shopping cart'),
    session: AsyncSession = Depends(get_async_session)
        ) -> JSONResponse:
    recipes = await get_recipes_from_db(
        session, current_user_id,
        author, tags,
        is_favorited, is_in_shopping_cart
    )

    recipes_data = await serialize_recipes_list(recipes)

    return JSONResponse(content=recipes_data, status_code=status.HTTP_200_OK)


@router.post('/recipes', response_model=RecipeSchema)
async def create_recipe(
    recipe_data: dict,
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session)
        ) -> JSONResponse:

    new_recipe = RecipeModel(
        author_id=current_user_id,
        pub_date=datetime.utcnow()
    )

    await RecipeUtility.perform_create_recipe(new_recipe, recipe_data, session)

    session.add(new_recipe)
    await session.commit()

    created_recipe = await get_single_recipe_from_db(
        new_recipe.id, session, current_user_id)

    recipe_data: dict = await serialize_recipe(*created_recipe)

    return JSONResponse(
        content=recipe_data, status_code=status.HTTP_201_CREATED)


@router.patch('/recipes/{id}', response_model=RecipeSchema)
async def update_recipe(
    recipe_data: dict,
    id: int = Path(..., title='Recipe ID'),
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session)
        ) -> JSONResponse:

    target_recipe: RecipeModel = await get_recipe_or_404(id, session)

    await RecipeUtility.perform_update_recipe(
        target_recipe, recipe_data, session)

    await session.refresh(target_recipe)

    updated_recipe = await get_single_recipe_from_db(
        target_recipe.id, session, current_user_id)

    recipe_data: dict = await serialize_recipe(*updated_recipe)

    return JSONResponse(content=recipe_data, status_code=status.HTTP_200_OK)


@router.get('/recipes/{id}', response_model=RecipeSchema)
async def get_recipe_by_id(id: int = Path(..., title='Tag ID'),
                           current_user_id: int = Depends(get_current_user_id),
                           session: AsyncSession = Depends(get_async_session)
                           ) -> JSONResponse:
    recipe_with_user = (
        await get_single_recipe_from_db(id, session, current_user_id))

    if recipe_with_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Recipe with ID {id} not found'
        )

    recipe_data: dict = await serialize_recipe(*recipe_with_user)

    return JSONResponse(content=recipe_data, status_code=status.HTTP_200_OK)


@router.delete('/recipes/{id}')
async def delete_recipe(
    id: int = Path(..., title='Recipe ID'),
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session)
        ) -> Response:

    cur_recipe: RecipeModel = await get_recipe_or_404(id, session)

    for amount in cur_recipe.ingredients:
        await session.delete(amount)

    await session.delete(cur_recipe)
    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post('/recipes/{id}/favorite', response_model=FavoriteSchema)
async def add_to_favorite(
    id: int = Path(..., title='Recipe ID'),
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session)
        ) -> JSONResponse:

    cur_recipe: RecipeModel = await get_recipe_or_404(id, session)

    if await is_recipe_in_favorite(session, current_user_id, id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Recipe with id {id} is already in favorite'
        )

    await session.execute(favorite.insert().values(
        user_id=current_user_id, recipe_id=id))
    await session.commit()

    recipe_data: dict = serialize_favorite(cur_recipe)

    return JSONResponse(content=recipe_data, status_code=status.HTTP_200_OK)


@router.delete('/recipes/{id}/favorite')
async def delete_from_favorite(
    id: int = Path(..., title='Recipe ID'),
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session)
        ) -> Response:

    await get_recipe_or_404(id, session)

    if not await is_recipe_in_favorite(session, current_user_id, id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Recipe with id {id} is not in favorite'
        )

    await session.execute(
        delete(favorite)
        .where(favorite.c.user_id == current_user_id)
        .where(favorite.c.recipe_id == id)
    )
    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)



# class PaginationMixin:

#     def add_pagination(self,
#                        page: int = Query(1, ge=1, title='Page Number'),
#                        limit: int = Query(
#                         PAGE_LIMIT, ge=1, le=100, title='Limit')) -> tuple:
#         return page, limit


# class PaginationHandler(PaginationMixin):

#     @router.get('/recipes', response_model=RecipePaginationSchema)
#     async def get_recipes_list(
#         author: int = Query(None, title='Author'),
#         tags: list[str] = Query(None, title='Tags'),
#         is_favorited: BoolOptions = BoolOptions.FALSE,
#         is_in_shopping_cart: BoolOptions = BoolOptions.FALSE,
#         pagination_params: tuple = Depends(PaginationMixin().add_pagination),
#             session: AsyncSession = Depends(get_async_session)):
#         page, limit = pagination_params

#         query = (
#             select(RecipeModel)
#             .options(joinedload(RecipeModel.tags))
#             .join(recipe_tag_association, isouter=True)
#             .join(TagModel, isouter=True)
#             .filter(TagModel.slug.in_(tags) if tags else True)
#             .filter(RecipeModel.author_id == author
#                     if author is not None else True)
#             .offset((page - 1) * limit)
#             .limit(limit)
#         )
#         recipes_result = await session.execute(query)
#         recipes = recipes_result.scalars().all()
#         total_recipes = len(recipes)
#         content: dict = get_pagination_links(page, limit, total_recipes)

#         try:
#             from pprint import pprint
#             pprint([rec.__dict__ for rec in recipes])
#             recipes_data = [
#                 RecipeSchema(**rec.__dict__).dict() for rec in recipes]
#         except ValidationError as err:
#             raise HTTPException(
#                 status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#                 detail='',
#             ) from err

#         content['results'] = recipes_data

#         return JSONResponse(
#             content=content, status_code=status.HTTP_200_OK)
