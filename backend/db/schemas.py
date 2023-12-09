from pydantic import BaseModel, EmailStr, ValidationInfo, field_validator

# class CustomModel(BaseModel):
#     model_config = ConfigDict(from_attributes=True)


class TokenSchema(BaseModel):
    access_token: str
    token_type: str


class CreateUserSchema(BaseModel):
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    password: str


class BriefUserSchema(BaseModel):
    id: int
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    is_subscribed: bool


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


class AmountSchema(BaseModel):
    id: int
    amount: int


class CreateRecipeSchema(BaseModel):
    name: str
    text: str
    cooking_time: int
    image: str
    tags: list[int]
    ingredients: list[AmountSchema]


class BriefRecipeSchema(BaseModel):
    id: int
    name: str
    image: str
    cooking_time: int


class DetailedRecipeSchema(BriefRecipeSchema):
    text: str
    pub_date: str
    author: BriefUserSchema
    tags: list[TagSchema]
    ingredients: list[IngredientWithAmountSchema]
    is_favorited: bool
    is_in_shopping_cart: bool

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, value, info: ValidationInfo):
        if not value:
            raise ValueError(f'Required field: {info.field_name}')
        return value


class DetailedUserSchema(BriefUserSchema):
    recipes: list[BriefRecipeSchema]
    recipes_count: int


# class RecipePaginationSchema(BaseModel):
#     count: int
#     next: str
#     previous: str
#     results: list[RecipeSchema]
