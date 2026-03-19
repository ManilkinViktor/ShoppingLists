from uuid import UUID

from core.enums import Role
from database.uow import UnitOfWork
from schemas.list_items import ListItemCreateDTO, ListItemsCreateDTO
from schemas.shopping_lists import (
    ShoppingListCreateDTO,
    ShoppingListPatchDTO,
    ShoppingListDTO,
    ShoppingListRelItemDTO,
)
from schemas.workspace_changes import (
    ListItemsCreateOperation,
    ShoppingListCreateOperation,
    ShoppingListDeleteOperation,
    ShoppingListPatchOperation,
    UnionOperation,
)
from services.base import BaseService
from services.exceptions import ConflictUUID, EntityNotFound
from services.list_items import ListItemsService


class ShoppingListsService(BaseService):
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
                "User doesn't have access to shopping list",
                extra={'workspace_id': workspace_id, 'user_id': current_user},
            )
            raise EntityNotFound(entity_type)

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

    async def _create_core(
            self,
            create_data: ShoppingListCreateDTO,
            current_user: UUID,
            *,
            deferred: bool,
    ) -> ShoppingListDTO | None:
        create_data = create_data.model_copy(update={'created_by': current_user})
        await self._ensure_editor_access(current_user, create_data.workspace_id)

        found_list: ShoppingListDTO | None = await self.uow.shopping_lists.get(create_data.id)
        if found_list:
            if self._same_lists(found_list, create_data):
                self._log_info("Shopping list already exists", extra={'list_id': found_list.id})
                return None if deferred else found_list
            self._log_warning("Conflict uuid: shopping list with same uuid and another data exists")
            raise ConflictUUID

        if deferred:
            await self.uow.shopping_lists.add_deferred(create_data)
            self._log_info("Shopping list was created", extra={'list_id': create_data.id})
            return None

        created = await self.uow.shopping_lists.add(create_data)
        self._log_info("Shopping list was created", extra={'list_id': created.id})
        return created

    async def create(
            self,
            create_data: ShoppingListCreateDTO,
            current_user: UUID,
            *,
            expected_workspace_version: int | None = None,
            record_change: bool = False,
            items: list[ListItemCreateDTO] | None = None,
    ) -> ShoppingListDTO:
        normalized_create_data = create_data.model_copy(update={'created_by': current_user})
        await self._ensure_editor_access(current_user, normalized_create_data.workspace_id)
        found_list = await self.uow.shopping_lists.get(create_data.id)
        has_create = found_list is None

        new_version: int | None = None
        if has_create and expected_workspace_version is not None:
            new_version = await self._bump_workspace_version_or_raise(
                normalized_create_data.workspace_id,
                expected_workspace_version,
            )

        created = await self._create_core(create_data, current_user, deferred=False)
        assert created is not None

        changes: list[UnionOperation] = []
        if record_change and new_version is not None and has_create:
            changes.append(
                UnionOperation(
                    root=ShoppingListCreateOperation(
                        data=ShoppingListCreateDTO(
                            id=normalized_create_data.id,
                            workspace_id=normalized_create_data.workspace_id,
                            name=normalized_create_data.name,
                            description=normalized_create_data.description,
                            created_by=normalized_create_data.created_by,
                        ),
                    )
                )
            )

        if items:
            list_items_service = ListItemsService(self.uow)
            prepared_items = [item.model_copy(update={'list_id': created.id}) for item in items]
            await list_items_service.create(
                ListItemsCreateDTO(
                    list_id=created.id,
                    items=prepared_items,
                ),
                current_user,
            )
            if record_change and new_version is not None:
                changes.append(
                    UnionOperation(
                        root=ListItemsCreateOperation(
                            data=ListItemsCreateDTO(
                                list_id=created.id,
                                items=prepared_items,
                            ),
                        )
                    )
                )

        if changes and new_version is not None:
            await self._add_workspace_change(create_data.workspace_id, new_version, changes)

        return created

    async def create_deferred(
            self,
            create_data: ShoppingListCreateDTO,
            current_user: UUID,
    ) -> None:
        await self._create_core(create_data, current_user, deferred=True)

    async def patch(
            self,
            patch_data: ShoppingListPatchDTO,
            current_user: UUID,
            *,
            expected_workspace_version: int | None = None,
            record_change: bool = False,
    ) -> ShoppingListDTO:
        workspace_id = await self._get_workspace_id_for_list(patch_data.id)
        await self._ensure_editor_access(current_user, workspace_id)

        patch_fields = patch_data.model_dump(exclude_unset=True)
        patch_fields.pop('id', None)
        patch_fields.pop('workspace_id', None)
        patch_fields.pop('created_by', None)

        current_list = await self.uow.shopping_lists.get(patch_data.id)
        if current_list is None:
            self._log_warning("Shopping list not found", extra={'list_id': patch_data.id})
            raise EntityNotFound(ShoppingListDTO)

        if not patch_fields:
            return current_list

        new_version: int | None = None
        if expected_workspace_version is not None:
            new_version = await self._bump_workspace_version_or_raise(
                workspace_id,
                expected_workspace_version,
            )

        updated: ShoppingListDTO | None = await self.uow.shopping_lists.update(
            patch_data.id,
            **patch_fields,
        )
        if not updated:
            self._log_warning("Shopping list not found", extra={'list_id': patch_data.id})
            raise EntityNotFound(ShoppingListDTO)

        if record_change and new_version is not None:
            await self._add_workspace_change(
                workspace_id,
                new_version,
                [
                    UnionOperation(
                        root=ShoppingListPatchOperation(
                            data=ShoppingListPatchDTO(id=patch_data.id, **patch_fields),
                        )
                    )
                ],
            )

        self._log_info("Shopping list was updated", extra={'list_id': updated.id})
        return updated

    async def delete(
            self,
            list_id: UUID,
            current_user: UUID,
            *,
            expected_workspace_version: int | None = None,
            record_change: bool = False,
    ) -> None:
        workspace_id = await self._get_workspace_id_for_list(list_id)
        await self._ensure_editor_access(current_user, workspace_id)

        new_version: int | None = None
        if expected_workspace_version is not None:
            new_version = await self._bump_workspace_version_or_raise(
                workspace_id,
                expected_workspace_version,
            )

        deleted = await self.uow.shopping_lists.delete(list_id)
        if not deleted:
            self._log_warning("Shopping list not found", extra={'list_id': list_id})
            raise EntityNotFound(ShoppingListDTO)

        if record_change and new_version is not None:
            await self._add_workspace_change(
                workspace_id,
                new_version,
                [
                    UnionOperation(
                        root=ShoppingListDeleteOperation(id=list_id)
                    )
                ],
            )

        self._log_info("Shopping list was deleted", extra={'list_id': list_id})

    async def list_for_user(
            self,
            current_user: UUID,
            workspace_id: UUID | None = None,
    ) -> list[ShoppingListDTO]:
        if workspace_id is not None:
            await self._ensure_member_access(current_user, workspace_id, ShoppingListDTO)
            return await self.uow.shopping_lists.get_all(workspace_id=workspace_id)
        members = await self.uow.workspace_members.get_all(user_id=current_user)
        workspace_ids = {member.workspace_id for member in members}
        if not workspace_ids:
            return []
        return await self.uow.shopping_lists.get_all(workspace_id=workspace_ids)

    async def get_with_items(
            self,
            list_id: UUID,
            current_user: UUID,
    ) -> ShoppingListRelItemDTO:
        shopping_list = await self.uow.shopping_lists.get_list_with_items(list_id)
        if not shopping_list:
            self._log_warning("Shopping list not found", extra={'list_id': list_id})
            raise EntityNotFound(ShoppingListDTO)
        await self._ensure_member_access(
            current_user,
            shopping_list.workspace_id,
            ShoppingListDTO,
        )
        return shopping_list
