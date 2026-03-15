from uuid import UUID

from database.models.workspace_members import Role
from database.uow import UnitOfWork
from services.base import BaseService
from services.exceptions import ConflictUUID, EntityNotFound
from schemas.shopping_lists import ShoppingListCreateDTO, ShoppingListPatchDTO, ShoppingListDTO


class ShoppingListsService(BaseService):
    def __init__(self, uow: UnitOfWork) -> None:
        super().__init__(uow)
        self._editable_workspace_ids: set[UUID] | None = None
        self._workspace_id_by_list_id: dict[UUID, UUID] = {}

    def set_editable_workspace_ids(self, editable_workspace_ids: set[UUID] | None) -> None:
        self._editable_workspace_ids = editable_workspace_ids

    async def _ensure_editor_access(self, current_user: UUID, workspace_id: UUID) -> None:
        if self._editable_workspace_ids is not None:
            if workspace_id in self._editable_workspace_ids:
                return
            self._log_warning(
                "User doesn't have access to shopping list",
                extra={'workspace_id': workspace_id, 'user_id': current_user},
            )
            raise EntityNotFound(ShoppingListDTO)

        member = await self.uow.workspace_members.get_by(
            user_id=current_user,
            workspace_id=workspace_id,
        )
        if not member or member.role != Role.editor:
            self._log_warning(
                "User doesn't have access to shopping list",
                extra={'workspace_id': workspace_id, 'user_id': current_user},
            )
            raise EntityNotFound(ShoppingListDTO)

    async def _get_workspace_id_for_list(self, list_id: UUID) -> UUID:
        cached_workspace_id = self._workspace_id_by_list_id.get(list_id)
        if cached_workspace_id is not None:
            return cached_workspace_id
        stored_list: ShoppingListDTO | None = await self.uow.shopping_lists.get(list_id)
        if not stored_list:
            self._log_warning("Shopping list not found", extra={'list_id': list_id})
            raise EntityNotFound(ShoppingListDTO)
        self._workspace_id_by_list_id[list_id] = stored_list.workspace_id
        return stored_list.workspace_id

    @staticmethod
    def _same_lists(first_list: ShoppingListDTO, second_list: ShoppingListCreateDTO) -> bool:
        return all(
            getattr(first_list, field) == value
            for field, value in second_list
        )

    async def create(self, create_data: ShoppingListCreateDTO, current_user: UUID) -> ShoppingListDTO:
        await self._ensure_editor_access(current_user, create_data.workspace_id)
        found_list: ShoppingListDTO | None = await self.uow.shopping_lists.get(create_data.id)
        if found_list:
            if self._same_lists(found_list, create_data):
                self._log_info("Shopping list already exists", extra={'list_id': found_list.id})
                return found_list
            self._log_warning("Conflict uuid: shopping list with same uuid and another data exists")
            raise ConflictUUID
        created = await self.uow.shopping_lists.add(create_data)
        self._log_info("Shopping list was created", extra={'list_id': created.id})
        return created

    async def patch(self, patch_data: ShoppingListPatchDTO, current_user: UUID) -> ShoppingListDTO:
        workspace_id = await self._get_workspace_id_for_list(patch_data.id)
        await self._ensure_editor_access(current_user, workspace_id)
        update_data = patch_data.model_dump(exclude_unset=True)
        update_data.pop('id', None)
        updated: ShoppingListDTO | None = await self.uow.shopping_lists.update(
            patch_data.id, **update_data
        )
        if not updated:
            self._log_warning("Shopping list not found", extra={'list_id': patch_data.id})
            raise EntityNotFound(ShoppingListDTO)
        self._log_info("Shopping list was updated", extra={'list_id': updated.id})
        return updated

    async def delete(self, list_id: UUID, current_user: UUID) -> None:
        workspace_id = await self._get_workspace_id_for_list(list_id)
        await self._ensure_editor_access(current_user, workspace_id)
        deleted = await self.uow.shopping_lists.delete(list_id)
        if not deleted:
            self._log_warning("Shopping list not found", extra={'list_id': list_id})
            raise EntityNotFound(ShoppingListDTO)
        self._log_info("Shopping list was deleted", extra={'list_id': list_id})
