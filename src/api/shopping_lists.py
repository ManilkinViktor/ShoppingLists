import uuid

from fastapi import APIRouter, status
from sqlalchemy.exc import IntegrityError

from api.dependencies import CurrentUser, UoWDep
from api.http_exceptions import domain_to_http_exception, integrity_error_to_http_exception
from api.schemas.list_items import (
    ListItemsCreateRequestDTO,
    ListItemsDeleteRequestDTO,
    ListItemsPatchRequestDTO,
)
from api.schemas.shopping_lists import (
    ShoppingListCreateWithItemsDTO,
    ShoppingListDeleteRequestDTO,
    ShoppingListPatchRequestDTO,
)
from schemas.list_items import (
    ListItemCreateDTO,
    ListItemDTO,
    ListItemPatchDTO,
    ListItemsCreateDTO,
    ListItemsDeleteDTO,
    ListItemsPatchDTO,
)
from schemas.shopping_lists import (
    ShoppingListCreateDTO,
    ShoppingListPatchDTO,
    ShoppingListDTO,
    ShoppingListRelItemDTO,
)
from services.exceptions import DomainException
from services.list_items import ListItemsService
from services.shopping_lists import ShoppingListsService

router = APIRouter(prefix='/shopping-lists', tags=['shopping-lists'])


@router.get(
    '',
    response_model=list[ShoppingListDTO],
    summary='List shopping lists',
    description='Returns shopping lists available to the current user, optionally filtered by workspace.',
)
async def list_shopping_lists(
        current_user: CurrentUser,
        uow: UoWDep,
        workspace_id: uuid.UUID | None = None,
) -> list[ShoppingListDTO]:
    shopping_lists_service = ShoppingListsService(uow)
    try:
        return await shopping_lists_service.list_for_user(
            current_user.id,
            workspace_id=workspace_id,
        )
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None


@router.get(
    '/{list_id}',
    response_model=ShoppingListRelItemDTO,
    summary='Get shopping list details',
    description='Returns one shopping list together with all of its items.',
)
async def get_shopping_list(
        list_id: uuid.UUID,
        current_user: CurrentUser,
        uow: UoWDep,
) -> ShoppingListRelItemDTO:
    shopping_lists_service = ShoppingListsService(uow)
    try:
        return await shopping_lists_service.get_with_items(list_id, current_user.id)
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None


@router.get(
    '/{list_id}/items',
    response_model=list[ListItemDTO],
    summary='List items in shopping list',
    description='Returns all items from the specified shopping list.',
)
async def get_list_items(
        list_id: uuid.UUID,
        current_user: CurrentUser,
        uow: UoWDep,
) -> list[ListItemDTO]:
    list_items_service = ListItemsService(uow)
    try:
        return await list_items_service.list_for_user(list_id, current_user.id)
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None


@router.get(
    '/{list_id}/items/{item_id}',
    response_model=ListItemDTO,
    summary='Get shopping list item',
    description='Returns a single item from the specified shopping list.',
)
async def get_list_item(
        list_id: uuid.UUID,
        item_id: uuid.UUID,
        current_user: CurrentUser,
        uow: UoWDep,
) -> ListItemDTO:
    list_items_service = ListItemsService(uow)
    try:
        return await list_items_service.get_for_user(list_id, item_id, current_user.id)
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None


@router.post(
    '',
    response_model=ShoppingListDTO,
    status_code=status.HTTP_201_CREATED,
    summary='Create shopping list',
    description='Creates a shopping list and optionally creates its initial items in the same request.',
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
    item_data = [
        ListItemCreateDTO(list_id=list_data.id, **item.model_dump())
        for item in payload.items
    ]
    try:
        created_list = await shopping_lists_service.create(
            list_data,
            current_user.id,
            expected_workspace_version=payload.workspace_version,
            record_change=True,
            items=item_data,
        )
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None
    return created_list


@router.patch(
    '/{list_id}',
    response_model=ShoppingListDTO,
    summary='Update shopping list',
    description='Updates shopping list fields.',
)
async def patch_shopping_list(
        list_id: uuid.UUID,
        payload: ShoppingListPatchRequestDTO,
        current_user: CurrentUser,
        uow: UoWDep,
) -> ShoppingListDTO:
    shopping_lists_service = ShoppingListsService(uow)
    try:
        patch_fields = payload.model_dump(exclude={'workspace_version'}, exclude_unset=True)
        patch_data = ShoppingListPatchDTO(id=list_id, **patch_fields)
        updated_list = await shopping_lists_service.patch(
            patch_data,
            current_user.id,
            expected_workspace_version=payload.workspace_version,
            record_change=True,
        )
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None
    return updated_list


@router.delete(
    '/{list_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Delete shopping list',
    description='Soft-deletes a shopping list.',
)
async def delete_shopping_list(
        list_id: uuid.UUID,
        payload: ShoppingListDeleteRequestDTO,
        current_user: CurrentUser,
        uow: UoWDep,
) -> None:
    shopping_lists_service = ShoppingListsService(uow)
    try:
        await shopping_lists_service.delete(
            list_id,
            current_user.id,
            expected_workspace_version=payload.workspace_version,
            record_change=True,
        )
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None


@router.post(
    '/{list_id}/items',
    response_model=list[ListItemDTO],
    status_code=status.HTTP_201_CREATED,
    summary='Create shopping list items',
    description='Creates one or more items in the specified shopping list.',
)
async def create_list_items(
        list_id: uuid.UUID,
        payload: ListItemsCreateRequestDTO,
        current_user: CurrentUser,
        uow: UoWDep,
) -> list[ListItemDTO]:
    list_items_service = ListItemsService(uow)
    items = [
        ListItemCreateDTO(list_id=list_id, **item.model_dump())
        for item in payload.items
    ]
    try:
        created_items = await list_items_service.create(
            ListItemsCreateDTO(
                list_id=list_id,
                items=items,
            ),
            current_user.id,
            expected_workspace_version=payload.workspace_version,
            record_change=True,
        )
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None
    return created_items


@router.patch(
    '/{list_id}/items',
    response_model=list[ListItemDTO],
    summary='Update shopping list items',
    description='Updates one or more items in the specified shopping list.',
)
async def patch_list_items(
        list_id: uuid.UUID,
        payload: ListItemsPatchRequestDTO,
        current_user: CurrentUser,
        uow: UoWDep,
) -> list[ListItemDTO]:
    list_items_service = ListItemsService(uow)
    items = [ListItemPatchDTO(**item.model_dump()) for item in payload.items]
    try:
        updated_items = await list_items_service.patch(
            ListItemsPatchDTO(
                list_id=list_id,
                items=items,
            ),
            current_user.id,
            expected_workspace_version=payload.workspace_version,
            record_change=True,
        )
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None
    return updated_items


@router.delete(
    '/{list_id}/items',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Delete shopping list items',
    description='Soft-deletes one or more items from the specified shopping list.',
)
async def delete_list_items(
        list_id: uuid.UUID,
        payload: ListItemsDeleteRequestDTO,
        current_user: CurrentUser,
        uow: UoWDep,
) -> None:
    list_items_service = ListItemsService(uow)
    try:
        await list_items_service.delete(
            ListItemsDeleteDTO(
                list_id=list_id,
                ids=payload.ids,
            ),
            current_user.id,
            expected_workspace_version=payload.workspace_version,
            record_change=True,
        )
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None
