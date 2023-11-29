"""init

Revision ID: 9992cb800d49
Revises: 
Create Date: 2023-11-07 19:41:10.533281

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9992cb800d49'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ingredients',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=200), nullable=True),
    sa.Column('measurement_unit', sa.String(length=200), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index('name_index', 'ingredients', ['name'], unique=False)
    op.create_table('tags',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=200), nullable=True),
    sa.Column('slug', sa.String(length=200), nullable=True),
    sa.Column('color', sa.String(length=7), nullable=True),
    sa.CheckConstraint('slug ~ "^[-a-zA-Z0-9_]+$"', name='check_valid_slug'),
    sa.CheckConstraint('color ~ "^#([a-f0-9]{6})$"', name='check_valid_hex_color'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('color'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('slug')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('username', sa.String(length=150), nullable=True),
    sa.Column('first_name', sa.String(length=150), nullable=True),
    sa.Column('last_name', sa.String(length=150), nullable=True),
    sa.Column('is_subscribed', sa.Boolean(), nullable=True, default=False),
    sa.CheckConstraint('username ~ "^[\\w.@+-]+$"', name='check_valid_username'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('recipes',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=200), nullable=True),
    sa.Column('text', sa.Text(), nullable=True),
    sa.Column('pub_date', sa.DateTime(), nullable=True),
    sa.Column('author', sa.Integer(), nullable=True),
    sa.Column('cooking_time', sa.SmallInteger(), nullable=True),
    sa.Column('image', sa.String(), nullable=True),
    sa.CheckConstraint('cooking_time > 0', name='check_positive_cooking_time'),
    sa.ForeignKeyConstraint(['author'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('amounts',
    sa.Column('recipe_id', sa.Integer(), nullable=True),
    sa.Column('ingredient_id', sa.Integer(), nullable=True),
    sa.Column('amount', sa.SmallInteger(), nullable=True),
    sa.CheckConstraint('amount > 0', name='check_positive_amount'),
    sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('recipe_id', 'ingredient_id')
    )
    op.create_table('favorite',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('recipe_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.UniqueConstraint('user_id', 'recipe_id', name='unique_favorite')
    )
    op.create_table('recipe_tag_association',
    sa.Column('recipe_id', sa.Integer(), nullable=True),
    sa.Column('tag_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
    sa.UniqueConstraint('recipe_id', 'tag_id', name='unique_recipe_tag')
    )
    op.create_table('shopping_cart',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('recipe_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.UniqueConstraint('user_id', 'recipe_id', name='unique_shopping_cart')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('shopping_cart')
    op.drop_table('recipe_tag_association')
    op.drop_table('favorite')
    op.drop_table('amount')
    op.drop_table('recipes')
    op.drop_table('users')
    op.drop_table('tags')
    op.drop_index('name_index', table_name='ingredients')
    op.drop_table('ingredients')
    # ### end Alembic commands ###
