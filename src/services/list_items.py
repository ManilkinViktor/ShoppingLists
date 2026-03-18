from uuid import UUID

from core.enums import Role
from database.uow import UnitOfWork
from services.base import BaseService
from services.exceptions import ConflictUUID, EntityNotFound
from schemas.list_items import ListItemDTO, ListItemPatchDTO, ListItemCreateDTO
from schemas.shopping_lists import ShoppingListDTO


class ListItemsService(BaseService):
    def __init__(self, uow: UnitOfWork) -> None:
        super().__init__(uow)
        self._editable_workspace_ids: set[UUID] | None = None
        self._workspace_id_by_list_id: dict[UUID, UUID] = {}

    def set_editable_workspace_ids(self, editable_workspace_ids: set[UUID] | None) -> None:
        self._editable_workspace_ids = editable_workspace_ids

    async def _ensure_member_access(
        self,
        current_user: UUID,
        workspace_id: UUID,
        entity_type: type,
    ) -> None:
        member = await self.uow.workspace_members.get_by(
            user_id=current_user,
            workspace_id=workspace_id,
        )
        if not member:
            self._log_warning(
                "User doesn't have access to list item",
                extra={'workspace_id': workspace_id, 'user_id': current_user},
            )
            raise EntityNotFound(entity_type)

    async def _ensure_editor_access(self, current_user: UUID, workspace_id: UUID) -> None:
        if self._editable_workspace_ids is not None:
            if workspace_id in self._editable_workspace_ids:
                return
            self._log_warning(
                "User doesn't have access to list item",
                extra={'workspace_id': workspace_id, 'user_id': current_user},
            )
            raise EntityNotFound(ListItemDTO)

        member = await self.uow.workspace_members.get_by(
            user_id=current_user,
            workspace_id=workspace_id,
        )
        if not member or member.role != Role.editor:
            self._log_warning(
                "User doesn't have access to list item",
                extra={'workspace_id': workspace_id, 'user_id': current_user},
            )
            raise EntityNotFound(ListItemDTO)

    async def _get_workspace_id_for_list(self, list_id: UUID) -> UUID:
        cached_workspace_id = self._workspace_id_by_list_id.get(list_id)
        if cached_workspace_id is not None:
            return cached_workspace_id
        parent_list: ShoppingListDTO | None = await self.uow.shopping_lists.get(list_id)
        if not parent_list:
            self._log_warning("Shopping list not found", extra={'list_id': list_id})
            raise EntityNotFound(ShoppingListDTO)
        self._workspace_id_by_list_id[list_id] = parent_list.workspace_id
        return parent_list.workspace_id

    @staticmethod
    def _same_items(first_item: ListItemDTO, second_item: ListItemCreateDTO) -> bool:
        return all(
            getattr(first_item, field) == value
            for field, value in second_item
        )

    async def create(self, create_data: ListItemCreateDTO, current_user: UUID) -> ListItemDTO:
        workspace_id = await self._get_workspace_id_for_list(create_data.list_id)
        await self._ensure_editor_access(current_user, workspace_id)
        found_item: ListItemDTO | None = await self.uow.list_items.get(create_data.id)
        if found_item:
            if self._same_items(found_item, create_data):
                self._log_info("List item already exists", extra={'item_id': found_item.id})
                return found_item
            self._log_warning("Conflict uuid: list item with same uuid and another data exists")
            raise ConflictUUID
        created = await self.uow.list_items.add(create_data)
        self._log_info("List item was created", extra={'item_id': created.id})
        return created

    async def patch(self, patch_data: ListItemPatchDTO, current_user: UUID) -> ListItemDTO:
        item: ListItemDTO | None = await self.uow.list_items.get(patch_data.id)
        if not item:
            self._log_warning("List item not found", extra={'item_id': patch_data.id})
            raise EntityNotFound(ListItemDTO)
        if patch_data.list_id is not None and patch_data.list_id != item.list_id:
            self._log_warning("List item not found", extra={'item_id': patch_data.id})
            raise EntityNotFound(ListItemDTO)
        workspace_id = await self._get_workspace_id_for_list(item.list_id)
        await self._ensure_editor_access(current_user, workspace_id)

        update_data = patch_data.model_dump(exclude_unset=True)
        update_data.pop('id', None)
        quantity_delta = update_data.pop('delta_quantity', None)
        if quantity_delta is not None:
            update_data['quantity'] = (item.quantity or 0) + quantity_delta

        updated: ListItemDTO | None = await self.uow.list_items.update(patch_data.id, **update_data)
        if not updated:
            self._log_warning("List item not found", extra={'item_id': patch_data.id})
            raise EntityNotFound(ListItemDTO)
        self._log_info("List item was updated", extra={'item_id': updated.id})
        return updated

    async def delete(self, item_id: UUID, current_user: UUID) -> None:
        item: ListItemDTO | None = await self.uow.list_items.get(item_id)
        if not item:
            self._log_warning("List item not found", extra={'item_id': item_id})
            raise EntityNotFound(ListItemDTO)
        workspace_id = await self._get_workspace_id_for_list(item.list_id)
        await self._ensure_editor_access(current_user, workspace_id)
        deleted = await self.uow.list_items.delete(item_id)
        if not deleted:
            self._log_warning("List item not found", extra={'item_id': item_id})
            raise EntityNotFound(ListItemDTO)
        self._log_info("List item was deleted", extra={'item_id': item_id})

    async def list_for_user(
        self,
        list_id: UUID,
        current_user: UUID,
    ) -> list[ListItemDTO]:
        workspace_id = await self._get_workspace_id_for_list(list_id)
        await self._ensure_member_access(current_user, workspace_id, ShoppingListDTO)
        return await self.uow.list_items.get_all(list_id=list_id)

    async def get_for_user(
        self,
        list_id: UUID,
        item_id: UUID,
        current_user: UUID,
    ) -> ListItemDTO:
        item = await self.uow.list_items.get(item_id)
        if not item or item.list_id != list_id:
            self._log_warning("List item not found", extra={'item_id': item_id})
            raise EntityNotFound(ListItemDTO)
        workspace_id = await self._get_workspace_id_for_list(item.list_id)
        await self._ensure_member_access(current_user, workspace_id, ListItemDTO)
        return item
