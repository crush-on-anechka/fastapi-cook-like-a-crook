from enum import Enum

from fastapi import HTTPException, status
from pydantic import ValidationError


class BoolOptions(Enum):
    false = '0'
    true = '1'


def get_pagination_links(page: int, limit: int, total_items: int) -> dict:
    last = (total_items - 1) // limit + 1
    nxt = page + 1 if page < last else None
    prev = page - 1 if page > 1 else None

    return {
        'count': total_items,
        'next': f'/items/?page={nxt}&limit={limit}' if nxt else None,
        'previous': f'/items/?page={prev}&limit={limit}' if prev else None,
    }


def handle_validation_error(err: ValidationError, error_message: str) -> None:
    print(err)
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=error_message,
    ) from err


# TODO: IMPLEMENT!!
async def get_current_user_id():
    return 1
