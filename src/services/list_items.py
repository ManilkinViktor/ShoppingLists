from uuid import UUID

from core.enums import Role
from database.uow import UnitOfWork
from schemas.list_items import (
    ListItemCreateDTO,
    ListItemDTO,
    ListItemPatchDTO,
    ListItemsCreateDTO,
    ListItemsDeleteDTO,
    ListItemsPatchDTO,
)
from schemas.shopping_lists import ShoppingListDTO
from schemas.workspace_changes import (
    ListItemsCreateOperation,
    ListItemsDeleteOperation,
    ListItemsPatchOperation,
    UnionOperation,
)
from services.base import BaseService
from services.exceptions import ConflictUUID, EntityNotFound, InvalidListItemQuantity


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
                immediate=True,
            )
            raise EntityNotFound(entity_type)

    async def _ensure_editor_access(self, current_user: UUID, workspace_id: UUID) -> None:
        if self._editable_workspace_ids is not None:
            if workspace_id in self._editable_workspace_ids:
                return
            self._log_warning(
                "User doesn't have access to list item",
                extra={'workspace_id': workspace_id, 'user_id': current_user},
                immediate=True,
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
                immediate=True,
            )
            raise EntityNotFound(ListItemDTO)

    async def _get_workspace_id_for_list(self, list_id: UUID) -> UUID:
        cached_workspace_id = self._workspace_id_by_list_id.get(list_id)
        if cached_workspace_id is not None:
            return cached_workspace_id
        parent_list: ShoppingListDTO | None = await self.uow.shopping_lists.get(list_id)
        if not parent_list:
            self._log_warning("Shopping list not found", extra={'list_id': list_id}, immediate=True)
            raise EntityNotFound(ShoppingListDTO)
        self._workspace_id_by_list_id[list_id] = parent_list.workspace_id
        return parent_list.workspace_id

    @staticmethod
    def _same_items(first_item: ListItemDTO, second_item: ListItemCreateDTO) -> bool:
        return all(
            getattr(first_item, field) == value
            for field, value in second_item
        )

    async def _get_items_by_ids(self, item_ids: list[UUID]) -> dict[UUID, ListItemDTO]:
        if not item_ids:
            return {}
        items = await self.uow.list_items.get_all(id=item_ids)
        return {item.id: item for item in items}

    async def _prepare_create(
            self,
            create_data: ListItemsCreateDTO,
            current_user: UUID,
    ) -> tuple[UUID, list[ListItemCreateDTO], dict[UUID, ListItemDTO], bool]:
        list_id = create_data.list_id
        items = create_data.items
        workspace_id = await self._get_workspace_id_for_list(list_id)
        await self._ensure_editor_access(current_user, workspace_id)

        prepared_items = [item.model_copy(update={'list_id': list_id}) for item in items]
        existing_items_by_id = await self._get_items_by_ids([item.id for item in prepared_items])
        request_items_by_id: dict[UUID, ListItemCreateDTO] = {}
        has_creates = False

        for item_data in prepared_items:
            previous_item = request_items_by_id.get(item_data.id)
            if previous_item is not None and previous_item != item_data:
                self._log_warning("Conflict uuid: list item with same uuid and another data exists", immediate=True)
                raise ConflictUUID
            request_items_by_id[item_data.id] = item_data

            found_item = existing_items_by_id.get(item_data.id)
            if found_item is None:
                has_creates = True
                continue
            if not self._same_items(found_item, item_data):
                self._log_warning("Conflict uuid: list item with same uuid and another data exists", immediate=True)
                raise ConflictUUID

        return workspace_id, prepared_items, existing_items_by_id, has_creates

    async def _perform_create(
            self,
            prepared_items: list[ListItemCreateDTO],
            existing_items_by_id: dict[UUID, ListItemDTO],
            *,
            deferred: bool,
    ) -> tuple[list[ListItemDTO], list[ListItemCreateDTO]]:
        created_items: list[ListItemDTO] = []
        created_item_payloads: list[ListItemCreateDTO] = []

        for item_data in prepared_items:
            found_item = existing_items_by_id.get(item_data.id)
            if found_item is not None:
                self._log_info("List item already exists", extra={'item_id': found_item.id})
                if not deferred:
                    created_items.append(found_item)
                continue

            if deferred:
                await self.uow.list_items.add_deferred(item_data)
                self._log_info("List item was created", extra={'item_id': item_data.id})
            else:
                created = await self.uow.list_items.add(item_data)
                self._log_info("List item was created", extra={'item_id': created.id})
                created_items.append(created)

            created_item_payloads.append(item_data)

        return created_items, created_item_payloads

    async def create(
            self,
            create_data: ListItemsCreateDTO,
            current_user: UUID,
            *,
            expected_workspace_version: int | None = None,
            record_change: bool = False,
    ) -> list[ListItemDTO]:
        list_id = create_data.list_id
        items = create_data.items
        if not items:
            return []
        workspace_id, prepared_items, existing_items_by_id, has_creates = await self._prepare_create(
            create_data,
            current_user,
        )

        if has_creates and expected_workspace_version is not None:
            new_version = await self._bump_workspace_version_or_raise(
                workspace_id,
                expected_workspace_version,
            )
        else:
            new_version = None

        created_items, created_item_payloads = await self._perform_create(
            prepared_items,
            existing_items_by_id,
            deferred=False,
        )

        if record_change and new_version is not None and has_creates:
            await self._add_workspace_change(
                workspace_id,
                new_version,
                [
                    UnionOperation(
                        root=ListItemsCreateOperation(
                            data=ListItemsCreateDTO(
                                list_id=list_id,
                                items=created_item_payloads,
                            ),
                        )
                    )
                ],
            )
        return created_items

    async def create_deferred(
            self,
            create_data: ListItemsCreateDTO,
            current_user: UUID,
    ) -> None:
        if not create_data.items:
            return

        _workspace_id, prepared_items, existing_items_by_id, _has_creates = await self._prepare_create(
            create_data,
            current_user,
        )
        await self._perform_create(
            prepared_items,
            existing_items_by_id,
            deferred=True,
        )

    async def patch(
            self,
            patch_data: ListItemsPatchDTO,
            current_user: UUID,
            *,
            expected_workspace_version: int | None = None,
            record_change: bool = False,
    ) -> list[ListItemDTO]:
        list_id = patch_data.list_id
        items = patch_data.items
        if not items:
            return []

        workspace_id = await self._get_workspace_id_for_list(list_id)
        await self._ensure_editor_access(current_user, workspace_id)

        prepared_items = [item.model_copy(update={'list_id': list_id}) for item in items]
        current_items_by_id = await self._get_items_by_ids([item.id for item in prepared_items])
        for item_data in prepared_items:
            current_item = current_items_by_id.get(item_data.id)
            if not current_item or current_item.list_id != list_id:
                self._log_warning("List item not found", extra={'item_id': item_data.id}, immediate=True)
                raise EntityNotFound(ListItemDTO)

        has_changes = any(
            {
                key: value
                for key, value in item.model_dump(exclude_unset=True).items()
                if key not in {'id', 'list_id'}
            }
            for item in prepared_items
        )

        if not has_changes:
            return [current_items_by_id[item.id] for item in prepared_items]

        new_version: int | None = None
        if expected_workspace_version is not None:
            new_version = await self._bump_workspace_version_or_raise(
                workspace_id,
                expected_workspace_version,
            )

        update_data_by_id: dict[UUID, dict[str, object]] = {}
        changed_items: list[ListItemPatchDTO] = []
        for item_data in prepared_items:
            patch_fields = item_data.model_dump(exclude_unset=True)
            patch_fields.pop('id', None)
            patch_fields.pop('list_id', None)
            current_item = current_items_by_id[item_data.id]
            quantity_delta = patch_fields.pop('delta_quantity', None)
            if quantity_delta is not None:
                patch_fields['quantity'] = (current_item.quantity or 0) + quantity_delta
                if patch_fields['quantity'] <= 0:
                    raise InvalidListItemQuantity
            if not patch_fields:
                continue
            update_data_by_id[item_data.id] = patch_fields
            changed_items.append(
                ListItemPatchDTO(id=item_data.id, list_id=list_id, **patch_fields)
            )

        updated_rows = await self.uow.list_items.update_many(update_data_by_id)
        if updated_rows != len(update_data_by_id):
            self._log_warning("Some list items were not updated", extra={'list_id': list_id}, immediate=True)
            raise EntityNotFound(ListItemDTO)

        updated_items_by_id = await self._get_items_by_ids(list(update_data_by_id))
        if len(updated_items_by_id) != len(update_data_by_id):
            self._log_warning("Some list items were not loaded after update", extra={'list_id': list_id}, immediate=True)
            raise EntityNotFound(ListItemDTO)

        updated_items: list[ListItemDTO] = []
        for item_data in prepared_items:
            current_item = current_items_by_id[item_data.id]
            patch_fields = update_data_by_id.get(item_data.id)
            if not patch_fields:
                updated_items.append(current_item)
                continue
            updated_item = updated_items_by_id.get(item_data.id)
            if updated_item is None:
                self._log_warning("List item not found", extra={'item_id': item_data.id}, immediate=True)
                raise EntityNotFound(ListItemDTO)
            current_items_by_id[item_data.id] = updated_item
            self._log_info("List item was updated", extra={'item_id': updated_item.id})
            updated_items.append(updated_item)

        if record_change and new_version is not None and changed_items:
            await self._add_workspace_change(
                workspace_id,
                new_version,
                [
                    UnionOperation(
                        root=ListItemsPatchOperation(
                            data=ListItemsPatchDTO(
                                list_id=list_id,
                                items=changed_items,
                            ),
                        )
                    )
                ],
            )
        return updated_items

    async def delete(
            self,
            delete_data: ListItemsDeleteDTO,
            current_user: UUID,
            *,
            expected_workspace_version: int | None = None,
            record_change: bool = False,
    ) -> None:
        list_id = delete_data.list_id
        ids = delete_data.ids
        if not ids:
            return

        workspace_id = await self._get_workspace_id_for_list(list_id)
        await self._ensure_editor_access(current_user, workspace_id)

        current_items_by_id = await self._get_items_by_ids(ids)
        for item_id in ids:
            item = current_items_by_id.get(item_id)
            if not item or item.list_id != list_id:
                self._log_warning("List item not found", extra={'item_id': item_id})
                raise EntityNotFound(ListItemDTO)

        new_version: int | None = None
        if expected_workspace_version is not None:
            new_version = await self._bump_workspace_version_or_raise(
                workspace_id,
                expected_workspace_version,
            )

        deleted_rows = await self.uow.list_items.delete_many(ids)
        if deleted_rows != len(ids):
            self._log_warning("Some list items were not deleted", extra={'list_id': list_id}, immediate=True)
            raise EntityNotFound(ListItemDTO)

        for item_id in ids:
            self._log_info("List item was deleted", extra={'item_id': item_id})

        if record_change and new_version is not None:
            await self._add_workspace_change(
                workspace_id,
                new_version,
                [
                    UnionOperation(
                        root=ListItemsDeleteOperation(
                            id=ListItemsDeleteDTO(
                                list_id=list_id,
                                ids=ids,
                            ),
                        )
                    )
                ],
            )

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
            self._log_warning("List item not found", extra={'item_id': item_id}, immediate=True)
            raise EntityNotFound(ListItemDTO)
        workspace_id = await self._get_workspace_id_for_list(item.list_id)
        await self._ensure_member_access(current_user, workspace_id, ListItemDTO)
        return item
