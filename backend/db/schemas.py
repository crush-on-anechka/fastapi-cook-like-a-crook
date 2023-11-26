from pydantic import (BaseModel, ValidationError, ValidationInfo,
                      field_validator)

# class CustomModel(BaseModel):
#     model_config = ConfigDict(from_attributes=True)


class UserSchema(BaseModel):
    id: int
    name: str


class TagSchema(BaseModel):
    id: int
    name: str
    slug: str
    color: str


class IngredientSchema(BaseModel):
    id: int
    name: str
    measurement_unit: str


class IngredientWithAmountSchema(IngredientSchema):
    amount: int


class RecipeSchema(BaseModel):
    id: int
    name: str
    text: str
    pub_date: str
    author_id: UserSchema  # rename to author!
    cooking_time: int
    image: str
    tags: list[TagSchema]
    ingredients: list[IngredientWithAmountSchema]
    is_favorited: bool
    is_in_shopping_cart: bool

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value, info: ValidationInfo):
        if not value:
            raise ValueError(f'Required field: {info.field_name}')
        return value


class FavoriteSchema(BaseModel):
    id: int
    name: str
    image: str
    cooking_time: int


# class RecipePaginationSchema(BaseModel):
#     count: int
#     next: str
#     previous: str
#     results: list[RecipeSchema]
