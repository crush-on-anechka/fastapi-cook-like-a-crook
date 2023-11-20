from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from db.models import IngredientModel, RecipeModel, TagModel, AmountModel, IngredientModel
from db.schemas import IngredientSchema, RecipeSchema, TagSchema
from db.session import get_async_session
from settings import PAGE_LIMIT

from .dals import get_recipes_from_db, get_single_recipe_from_db
from .serializers import (serialize_ingredient, serialize_ingredients_list,
                          serialize_recipe, serialize_recipes_list,
                          serialize_tag, serialize_tags_list)
from .utils import BoolOptions, get_current_user_id

router = APIRouter()


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

    return JSONResponse(
        content=recipes_data, status_code=status.HTTP_200_OK)


@router.post('/recipes', response_model=RecipeSchema)
async def create_recipe(
    recipe_data: dict,
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session)
        ) -> JSONResponse:

    new_recipe = RecipeModel(   
        name=recipe_data.get('name'),
        text=recipe_data.get('text'),
        cooking_time=recipe_data.get('cooking_time'),
        image=recipe_data.get('image'),
        author_id=current_user_id,
        pub_date=datetime.utcnow(),
    )

    ingredients_data = recipe_data.get('ingredients', [])

    ingredient_ids = [i['id'] for i in ingredients_data]
    ingredients = await session.execute(
        select(IngredientModel).where(IngredientModel.id.in_(ingredient_ids)))
    ingredient_dict = {i.id: i for i in ingredients.scalars()}

    for ingredient_data in ingredients_data:
        ingredient_id = ingredient_data['id']
        amount = ingredient_data['amount']

        ingredient = ingredient_dict.get(ingredient_id)
        if not ingredient:
            raise HTTPException(
                status_code=404,
                detail=f'Ingredient with ID {ingredient_id} not found')

        new_recipe.ingredients.append(
            AmountModel(amount=amount, ingredient=ingredient))

    tags_data = recipe_data.get('tags', [])
    tags = await session.execute(
        select(TagModel).where(TagModel.id.in_(tags_data)))
    tag_dict = {tag.id: tag for tag in tags.scalars()}

    for tag_id in tags_data:
        tag = tag_dict.get(tag_id)
        if not tag:
            raise HTTPException(
                status_code=404, detail=f'Tag with ID {tag_id} not found')

        new_recipe.tags.append(tag)

    session.add(new_recipe)
    await session.flush()

    created_recipe = await get_single_recipe_from_db(
        new_recipe.id, session, current_user_id)

    recipe_data: dict = await serialize_recipe(*created_recipe)

    await session.commit()

    return JSONResponse(
        content=recipe_data, status_code=status.HTTP_201_CREATED)


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

    return JSONResponse(
        content=recipe_data, status_code=status.HTTP_200_OK)



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
