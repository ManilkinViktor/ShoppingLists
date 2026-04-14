import uuid

from fastapi import APIRouter, status

from api.docs.responses import (
    AUTH_REQUIRED_RESPONSE,
    CREATE_CONFLICT_RESPONSE,
    NOT_FOUND_RESPONSE,
    VERSION_CONFLICT_RESPONSE,
)
from api.dependencies import CurrentUser, UoWDep
from api.schemas.shopping_lists import (
    ShoppingListCreateWithItemsDTO,
    ShoppingListDeleteRequestDTO,
    ShoppingListPatchRequestDTO,
)
from schemas.shopping_lists import (
    ShoppingListCreateDTO,
    ShoppingListDTO,
    ShoppingListRelItemDTO,
    ShoppingListPatchFullDTO,
)
from services.shopping_lists import ShoppingListsService

router = APIRouter(prefix='/shopping-lists', tags=['shopping-lists'])


@router.get(
    '',
    response_model=list[ShoppingListDTO],
    summary='List shopping lists',
    description='Returns shopping lists available to the current user, optionally filtered by workspace.',
    responses=AUTH_REQUIRED_RESPONSE,
)
async def list_shopping_lists(
        current_user: CurrentUser,
        uow: UoWDep,
        workspace_id: uuid.UUID | None = None,
) -> list[ShoppingListDTO]:
    shopping_lists_service = ShoppingListsService(uow)
    return await shopping_lists_service.lists_for_user(
        current_user.id,
        workspace_id=workspace_id,
    )


@router.get(
    '/{list_id}',
    response_model=ShoppingListRelItemDTO,
    summary='Get shopping list details',
    description='Returns one shopping list together with all of its items.',
    responses={
        **AUTH_REQUIRED_RESPONSE,
        **NOT_FOUND_RESPONSE,
    },
)
async def get_shopping_list(
        list_id: uuid.UUID,
        current_user: CurrentUser,
        uow: UoWDep,
) -> ShoppingListRelItemDTO:
    shopping_lists_service = ShoppingListsService(uow)
    return await shopping_lists_service.get_with_items(list_id, current_user.id)




@router.post(
    '',
    response_model=ShoppingListDTO,
    status_code=status.HTTP_201_CREATED,
    summary='Create shopping list',
    description='Creates a shopping list and optionally creates its initial items in the same request.',
    responses={
        **AUTH_REQUIRED_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **CREATE_CONFLICT_RESPONSE,
    },
)
async def create_shopping_list(
        payload: ShoppingListCreateWithItemsDTO,
        current_user: CurrentUser,
        uow: UoWDep,
) -> ShoppingListDTO:
    shopping_lists_service = ShoppingListsService(uow)
    list_data = ShoppingListCreateDTO(
        **payload.model_dump(exclude={'items', 'workspace_version'})
    )
    created_list = await shopping_lists_service.create(
        list_data,
        current_user.id,
        expected_workspace_version=payload.workspace_version,
        record_change=True,
        items=payload.items,
    )
    await uow.commit()
    return created_list


@router.patch(
    '/{list_id}',
    response_model=ShoppingListDTO,
    summary='Update shopping list',
    description='Updates shopping list fields together list\'s items.',
    responses={
        **AUTH_REQUIRED_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **VERSION_CONFLICT_RESPONSE,
    },
)
async def patch_shopping_list(
        list_id: uuid.UUID,
        payload: ShoppingListPatchRequestDTO,
        current_user: CurrentUser,
        uow: UoWDep,
) -> ShoppingListDTO:
    shopping_lists_service = ShoppingListsService(uow)
    patch_fields = payload.model_dump(exclude={'workspace_version'}, exclude_unset=True)
    patch_data = ShoppingListPatchFullDTO(id=list_id, **patch_fields)
    await shopping_lists_service.patch(
        patch_data,
        current_user.id,
        expected_workspace_version=payload.workspace_version,
        record_change=True,
    )
    result = await shopping_lists_service.get_with_items(list_id, current_user.id)
    await uow.commit()
    return result


@router.delete(
    '/{list_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Delete shopping list',
    description='Soft-deletes a shopping list.',
    responses={
        **AUTH_REQUIRED_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **VERSION_CONFLICT_RESPONSE,
    },
)
async def delete_shopping_list(
        list_id: uuid.UUID,
        payload: ShoppingListDeleteRequestDTO,
        current_user: CurrentUser,
        uow: UoWDep,
) -> None:
    shopping_lists_service = ShoppingListsService(uow)
    await shopping_lists_service.delete(
        list_id,
        current_user.id,
        expected_workspace_version=payload.workspace_version,
        record_change=True,
    )
    await uow.commit()



