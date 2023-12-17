from pydantic import ValidationError

from db.schemas import (BriefRecipeSchema, BriefUserSchema,
                        DetailedRecipeSchema, DetailedUserSchema,
                        IngredientSchema, TagSchema)

from .utils import handle_validation_error


def serialize_users_list(users) -> list[dict]:
    try:
        users_data = [
            BriefUserSchema(**user.__dict__).dict() for user in users]
    except ValidationError as err:
        handle_validation_error(
            err, 'Validation error while processing the user data')

    return users_data


def serialize_user(user) -> dict:
    try:
        user_data = BriefUserSchema(**user.__dict__).dict()
    except ValidationError as err:
        handle_validation_error(
            err, 'Validation error while processing the user data')

    return user_data


def serialize_user_with_recipes(user, recipes, recipes_count) -> dict:
    try:
        user_data = DetailedUserSchema(
                **{
                    **user.__dict__,
                    'recipes': [r.__dict__ for r in recipes],
                    'recipes_count': recipes_count
                }
            ).dict()

    except ValidationError as err:
        handle_validation_error(
            err, 'Validation error while processing the user data')

    return user_data


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
        recipe_data = BriefRecipeSchema(**recipe.__dict__).dict()
    except ValidationError as err:
        handle_validation_error(
            err, 'Validation error while processing the favorited recipe data')

    return recipe_data


def serialize_shopping_cart(recipe) -> dict:
    try:
        recipe_data = BriefRecipeSchema(**recipe.__dict__).dict()
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
            DetailedRecipeSchema(
                **{
                    **recipe.__dict__,
                    'pub_date': recipe.pub_date.isoformat(),
                    'author': user.__dict__,
                    'tags': [tag.__dict__ for tag in recipe.tags],
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
        recipes_data = DetailedRecipeSchema(
                **{
                    **recipe.__dict__,
                    'pub_date': recipe.pub_date.isoformat(),
                    'author': user.__dict__,
                    'tags': [tag.__dict__ for tag in recipe.tags],
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
