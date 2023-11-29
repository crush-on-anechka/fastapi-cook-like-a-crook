from pydantic import ValidationError

from db.schemas import (FavoriteCartSchema, IngredientSchema, RecipeSchema,
                        TagSchema, UserSchema)

from .utils import handle_validation_error


def serialize_tags_list(tags) -> list[dict]:
    try:
        tags_data = [TagSchema(**tag.__dict__).dict() for tag in tags]
    except ValidationError as err:
        handle_validation_error(
            err, 'Validation error while processing the tag data')

    return tags_data


def serialize_tag(tag) -> dict:
    try:
        tag_data = TagSchema(**tag.__dict__).dict()
    except ValidationError as err:
        handle_validation_error(
            err, 'Validation error while processing the tag data')

    return tag_data


def serialize_favorite(recipe) -> dict:
    try:
        recipe_data = FavoriteCartSchema(**recipe.__dict__).dict()
    except ValidationError as err:
        handle_validation_error(
            err, 'Validation error while processing the favorited recipe data')

    return recipe_data


def serialize_shopping_cart(recipe) -> dict:
    try:
        recipe_data = FavoriteCartSchema(**recipe.__dict__).dict()
    except ValidationError as err:
        handle_validation_error(
            err, 'Validation error while processing the recipe in cart data')

    return recipe_data


def serialize_ingredients_list(ingredients) -> list[dict]:
    try:
        ingredients_data = [
            IngredientSchema(**i.__dict__).dict() for i in ingredients]
    except ValidationError as err:
        handle_validation_error(
            err, 'Validation error while processing the ingredient data')

    return ingredients_data


def serialize_ingredient(ingredient) -> dict:
    try:
        ingredient_data = IngredientSchema(**ingredient.__dict__).dict()
    except ValidationError as err:
        handle_validation_error(
            err, 'Validation error while processing the ingredient data')

    return ingredient_data


async def serialize_recipes_list(recipes) -> list[dict]:
    try:
        recipes_data = [
            RecipeSchema(
                **{
                    **recipe.__dict__,
                    'pub_date': recipe.pub_date.isoformat(),
                    'author': UserSchema(**user.__dict__),
                    'tags': [TagSchema(**tag.__dict__) for tag in recipe.tags],
                    'is_favorited': is_favorited,
                    'is_in_shopping_cart': is_in_shopping_cart,
                    'ingredients': [
                        {
                            **i.ingredient.__dict__,
                            'amount': i.amount
                        }
                        for i in recipe.ingredients
                    ]
                }
            ).dict()
            for recipe, user, is_favorited, is_in_shopping_cart in recipes
        ]
    except ValidationError as err:
        handle_validation_error(
            err, 'Validation error while processing the recipe data')

    return recipes_data


async def serialize_recipe(
        recipe, user, is_favorited, is_in_shopping_cart) -> dict:
    try:
        recipes_data = RecipeSchema(
                **{
                    **recipe.__dict__,
                    'pub_date': recipe.pub_date.isoformat(),
                    'author': UserSchema(**user.__dict__),
                    'tags': [TagSchema(**tag.__dict__) for tag in recipe.tags],
                    'is_favorited': is_favorited,
                    'is_in_shopping_cart': is_in_shopping_cart,
                    'ingredients': [
                        {
                            **i.ingredient.__dict__,
                            'amount': i.amount
                        }
                        for i in recipe.ingredients
                    ]
                }
            ).dict()
    except ValidationError as err:
        handle_validation_error(
            err, 'Validation error while processing the recipe data')

    return recipes_data
