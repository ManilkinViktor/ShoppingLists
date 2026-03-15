import uuid

from fastapi import APIRouter, status
from sqlalchemy.exc import IntegrityError

from api.dependencies import CurrentUser, UoWDep
from api.http_exceptions import domain_to_http_exception, integrity_error_to_http_exception
from api.schemas.shopping_lists import ShoppingListCreateWithItemsDTO
from schemas.list_items import ListItemCreateDTO, ListItemPatchDTO, ListItemDTO
from schemas.shopping_lists import ShoppingListCreateDTO, ShoppingListPatchDTO, ShoppingListDTO
from services.exceptions import DomainException
from services.list_items import ListItemsService
from services.shopping_lists import ShoppingListsService


router = APIRouter(prefix='/shopping-lists', tags=['shopping-lists'])


@router.post('', response_model=ShoppingListDTO, status_code=status.HTTP_201_CREATED)
async def create_shopping_list(
    payload: ShoppingListCreateWithItemsDTO,
    current_user: CurrentUser,
    uow: UoWDep,
) -> ShoppingListDTO:
    shopping_lists_service = ShoppingListsService(uow)
    list_items_service = ListItemsService(uow)
    list_data = ShoppingListCreateDTO(**payload.model_dump(exclude={'items'}))
    list_data.created_by = current_user.id
    try:
        created_list = await shopping_lists_service.create(list_data, current_user.id)
        for item in payload.items:
            item_data = ListItemCreateDTO(list_id=created_list.id, **item.model_dump())
            await list_items_service.create(item_data, current_user.id)
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None
    return created_list


@router.patch('/{list_id}', response_model=ShoppingListDTO)
async def patch_shopping_list(
    list_id: uuid.UUID,
    payload: ShoppingListPatchDTO,
    current_user: CurrentUser,
    uow: UoWDep,
) -> ShoppingListDTO:
    shopping_lists_service = ShoppingListsService(uow)
    update_data = payload.model_dump(exclude_unset=True)
    update_data.pop('id', None)
    update_data.pop('workspace_id', None)
    update_data.pop('created_by', None)
    patch_data = ShoppingListPatchDTO(id=list_id, **update_data)
    try:
        updated_list = await shopping_lists_service.patch(patch_data, current_user.id)
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None
    return updated_list


@router.delete('/{list_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_shopping_list(
    list_id: uuid.UUID,
    current_user: CurrentUser,
    uow: UoWDep,
) -> None:
    shopping_lists_service = ShoppingListsService(uow)
    try:
        await shopping_lists_service.delete(list_id, current_user.id)
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None


@router.post('/{list_id}/items', response_model=list[ListItemDTO], status_code=status.HTTP_201_CREATED)
async def create_list_items(
    list_id: uuid.UUID,
    items: list[ListItemCreateDTO],
    current_user: CurrentUser,
    uow: UoWDep,
) -> list[ListItemDTO]:
    list_items_service = ListItemsService(uow)
    created_items: list[ListItemDTO] = []
    try:
        for item in items:
            item_data = item.model_copy(update={'list_id': list_id})
            created_items.append(await list_items_service.create(item_data, current_user.id))
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None
    return created_items


@router.patch('/{list_id}/items', response_model=list[ListItemDTO])
async def patch_list_items(
    list_id: uuid.UUID,
    items: list[ListItemPatchDTO],
    current_user: CurrentUser,
    uow: UoWDep,
) -> list[ListItemDTO]:
    list_items_service = ListItemsService(uow)
    updated_items: list[ListItemDTO] = []
    try:
        for item in items:
            item_data = item.model_copy(update={'list_id': list_id})
            updated_items.append(await list_items_service.patch(item_data, current_user.id))
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None
    return updated_items


@router.delete('/{list_id}/items', status_code=status.HTTP_204_NO_CONTENT)
async def delete_list_items(
    list_id: uuid.UUID,
    ids: list[uuid.UUID],
    current_user: CurrentUser,
    uow: UoWDep,
) -> None:
    list_items_service = ListItemsService(uow)
    try:
        for item_id in ids:
            await list_items_service.delete(item_id, current_user.id)
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None


