from uuid import UUID
from typing import Protocol, TypeVar

from schemas.workspaces import WorkspaceDTO
from schemas.workspace_changes import (
    UnionOperation,
    WorkspaceChangeCreateDTO,
    WorkspaceVersionDTO,
    WorkspacePushResultDTO,
)
from core.enums import Role
from services.base import BaseService
from services.exceptions import DuplicateWorkspaceSyncPayload, EntityNotFound
from database.uow import UnitOfWork
from services.workspaces import WorkspacesService
from services.shopping_lists import ShoppingListsService
from services.list_items import ListItemsService


CreateDTO = TypeVar('CreateDTO')
PatchDTO = TypeVar('PatchDTO')


class CrudService(Protocol[CreateDTO, PatchDTO]):
    async def create(self, data: CreateDTO, current_user: UUID) -> object: ...
    async def patch(self, data: PatchDTO, current_user: UUID) -> object: ...
    async def delete(self, entity_id: UUID, current_user: UUID) -> None: ...


class WorkspaceSyncService(BaseService):
    def __init__(self, uow: UnitOfWork) -> None:
        super().__init__(uow)
        self._workspaces_service = WorkspacesService(uow)
        self._shopping_lists_service = ShoppingListsService(uow)
        self._list_items_service = ListItemsService(uow)
        self._service_map: dict[str, CrudService] = {
            'workspace': self._workspaces_service,
            'shopping_list': self._shopping_lists_service,
            'list_item': self._list_items_service,
        }

    def _get_requested_workspace_ids(
        self,
        current_user: UUID,
        workspace_changes: list[WorkspaceChangeCreateDTO],
    ) -> tuple[list[UUID], set[UUID]]:
        workspace_ids: list[UUID] = [change.workspace_id for change in workspace_changes]
        requested_workspace_ids: set[UUID] = set(workspace_ids)
        if len(requested_workspace_ids) != len(workspace_ids):
            self._log_warning(
                'Sync payload has duplicate workspace_id values',
                extra={'user_id': current_user},
            )
            raise DuplicateWorkspaceSyncPayload
        return workspace_ids, requested_workspace_ids

    def _get_requested_workspace_versions(
        self,
        current_user: UUID,
        workspace_versions: list[WorkspaceVersionDTO],
    ) -> tuple[list[UUID], set[UUID]]:
        workspace_ids: list[UUID] = [entry.workspace_id for entry in workspace_versions]
        requested_workspace_ids: set[UUID] = set(workspace_ids)
        if len(requested_workspace_ids) != len(workspace_ids):
            self._log_warning(
                'Sync payload has duplicate workspace_id values',
                extra={'user_id': current_user},
            )
            raise DuplicateWorkspaceSyncPayload
        return workspace_ids, requested_workspace_ids

    async def _get_accessible_workspace_ids(
        self,
        current_user: UUID,
    ) -> tuple[set[UUID], set[UUID]]:
        members = await self.uow.workspace_members.get_all(user_id=current_user)
        accessible_workspace_ids: set[UUID] = {member.workspace_id for member in members}
        editable_workspace_ids: set[UUID] = {
            member.workspace_id for member in members if member.role == Role.editor
        }
        return accessible_workspace_ids, editable_workspace_ids

    async def _ensure_workspace_access(
        self,
        current_user: UUID,
        workspace_changes: list[WorkspaceChangeCreateDTO],
    ) -> tuple[list[UUID], set[UUID], set[UUID], set[UUID]]:
        requested_workspace_ids_ordered, requested_workspace_ids = self._get_requested_workspace_ids(
            current_user, workspace_changes
        )
        accessible_workspace_ids, editable_workspace_ids = await self._get_accessible_workspace_ids(
            current_user
        )
        inaccessible_workspace_ids: set[UUID] = requested_workspace_ids - accessible_workspace_ids
        if inaccessible_workspace_ids:
            workspace_id: UUID = next(iter(inaccessible_workspace_ids))
            self._log_warning(
                "User doesn't have access to workspace sync",
                extra={'workspace_id': workspace_id, 'user_id': current_user},
            )
            raise EntityNotFound(WorkspaceDTO)
        return (
            requested_workspace_ids_ordered,
            requested_workspace_ids,
            accessible_workspace_ids,
            editable_workspace_ids,
        )

    async def _get_workspaces_by_id(self, requested_workspace_ids: set[UUID]) -> list[WorkspaceDTO]:
        workspaces: list[WorkspaceDTO] = await self.uow.workspaces.get_all(id=requested_workspace_ids)
        found_workspace_ids: set[UUID] = {workspace.id for workspace in workspaces}
        missing_workspace_ids: set[UUID] = requested_workspace_ids - found_workspace_ids
        if missing_workspace_ids:
            raise EntityNotFound(WorkspaceDTO)
        return workspaces

    async def _primary_version_check(
        self,
        accessible_workspace_ids: set[UUID],
        request_versions: dict[UUID, int],
    ) -> tuple[set[UUID], dict[UUID, int]]:
        workspaces: list[WorkspaceDTO] = await self._get_workspaces_by_id(accessible_workspace_ids)
        request_versions_full: dict[UUID, int] = {
            workspace_id: request_versions.get(workspace_id, 0)
            for workspace_id in accessible_workspace_ids
        }
        outdated_workspace_ids: set[UUID] = set()
        for workspace in workspaces:
            workspace_id: UUID = workspace.id
            request_version: int = request_versions_full[workspace_id]
            if workspace.version > request_version:
                outdated_workspace_ids.add(workspace_id)
        return outdated_workspace_ids, request_versions_full

    async def _apply_operations(
        self,
        current_user: UUID,
        workspace_change: WorkspaceChangeCreateDTO,
    ) -> None:
        for wrapper in workspace_change.changes:
            op_data = wrapper.root
            prefix, action = op_data.op.split('.')
            service = self._service_map.get(prefix)
            if service is None:
                raise ValueError(f'Unknown operation prefix: {prefix}')
            if action == 'create':
                await service.create(op_data.data, current_user)
            elif action == 'patch':
                await service.patch(op_data.data, current_user)
            elif action == 'delete':
                await service.delete(op_data.id, current_user)
            else:
                raise ValueError(f'Unknown operation action: {action}')

    async def _apply_changes(
        self,
        current_user: UUID,
        workspace_changes: list[WorkspaceChangeCreateDTO],
        eligible_workspace_ids: set[UUID],
    ) -> tuple[list[WorkspaceChangeCreateDTO], dict[UUID, int], dict[UUID, int]]:
        bump_candidates: list[WorkspaceChangeCreateDTO] = []
        for change in workspace_changes:
            if change.workspace_id in eligible_workspace_ids and change.changes:
                bump_candidates.append(change)

        expected_bump_versions: dict[UUID, int] = {
            change.workspace_id: change.workspace_version for change in bump_candidates
        }
        bumped_workspace_versions: dict[UUID, int] = await self.uow.workspaces.compare_and_bump_versions(
            expected_bump_versions
        )
        new_changes: list[WorkspaceChangeCreateDTO] = []
        for change in bump_candidates:
            bumped_version: int | None = bumped_workspace_versions.get(change.workspace_id)
            if bumped_version is None:
                continue
            await self._apply_operations(current_user, change)
            new_changes.append(
                WorkspaceChangeCreateDTO(
                    workspace_id=change.workspace_id,
                    workspace_version=bumped_version,
                    changes=change.changes,
                )
            )
        if new_changes:
            await self.uow.workspace_changes.add_all(new_changes)
        return new_changes, expected_bump_versions, bumped_workspace_versions

    @staticmethod
    def _finalize_bump_versions(
        outdated_workspace_ids: set[UUID],
        expected_bump_versions: dict[UUID, int],
        bumped_workspace_versions: dict[UUID, int],
    ) -> set[UUID]:
        race_outdated_ids: set[UUID] = set(expected_bump_versions) - set(bumped_workspace_versions)
        return outdated_workspace_ids | race_outdated_ids

    async def _get_required_sync_changes(
        self,
        outdated_workspace_ids: set[UUID],
        request_versions: dict[UUID, int],
    ) -> dict[UUID, list[UnionOperation]]:
        outdated_workspace_versions: dict[UUID, int] = {
            workspace_id: request_versions[workspace_id]
            for workspace_id in outdated_workspace_ids
        }
        required_changes: list[WorkspaceChangeCreateDTO] = (
            await self.uow.workspace_changes.get_since_versions(outdated_workspace_versions)
        )
        required_operations_by_workspace: dict[UUID, list[UnionOperation]] = {}
        for required_change in required_changes:
            operations: list[UnionOperation] = required_operations_by_workspace.setdefault(
                required_change.workspace_id,
                [],
            )
            operations.extend(required_change.changes)
        return required_operations_by_workspace


    async def pull_changes(
        self,
        current_user: UUID,
        workspace_versions: list[WorkspaceVersionDTO],
    ) -> list[WorkspaceChangeCreateDTO]:
        _requested_ordered, requested_workspace_ids = self._get_requested_workspace_versions(
            current_user,
            workspace_versions,
        )
        accessible_workspace_ids, _editable_workspace_ids = await self._get_accessible_workspace_ids(
            current_user
        )
        inaccessible_workspace_ids = requested_workspace_ids - accessible_workspace_ids
        if inaccessible_workspace_ids:
            workspace_id: UUID = next(iter(inaccessible_workspace_ids))
            self._log_warning(
                "User doesn't have access to workspace sync",
                extra={'workspace_id': workspace_id, 'user_id': current_user},
            )
            raise EntityNotFound(WorkspaceDTO)
        request_versions: dict[UUID, int] = {
            entry.workspace_id: entry.workspace_version for entry in workspace_versions
        }
        request_versions_full: dict[UUID, int] = {
            workspace_id: request_versions.get(workspace_id, 0)
            for workspace_id in accessible_workspace_ids
        }
        return await self.uow.workspace_changes.get_since_versions(request_versions_full)

    async def push_changes(
        self,
        current_user: UUID,
        workspace_changes: list[WorkspaceChangeCreateDTO],
    ) -> list[WorkspacePushResultDTO]:
        (
            requested_workspace_ids_ordered,
            requested_workspace_ids,
            _accessible_workspace_ids,
            editable_workspace_ids,
        ) = await self._ensure_workspace_access(
            current_user, workspace_changes
        )
        self._workspaces_service.set_editable_workspace_ids(editable_workspace_ids)
        self._shopping_lists_service.set_editable_workspace_ids(editable_workspace_ids)
        self._list_items_service.set_editable_workspace_ids(editable_workspace_ids)

        request_versions: dict[UUID, int] = {
            change.workspace_id: change.workspace_version for change in workspace_changes
        }
        requested_workspace_ids_with_changes: set[UUID] = {
            change.workspace_id for change in workspace_changes if change.changes
        }
        outdated_workspace_ids, _request_versions_full = await self._primary_version_check(
            requested_workspace_ids,
            request_versions,
        )
        non_editable_requested_ids: set[UUID] = (
            requested_workspace_ids_with_changes - editable_workspace_ids
        )
        eligible_workspace_ids: set[UUID] = (
            requested_workspace_ids - outdated_workspace_ids - non_editable_requested_ids
        )
        _new_changes, expected_bump_versions, bumped_workspace_versions = await self._apply_changes(
            current_user, workspace_changes, eligible_workspace_ids
        )
        outdated_workspace_ids = self._finalize_bump_versions(
            outdated_workspace_ids,
            expected_bump_versions,
            bumped_workspace_versions,
        )
        accepted_workspace_ids: set[UUID] = (
            requested_workspace_ids - outdated_workspace_ids - non_editable_requested_ids
        )
        return [
            WorkspacePushResultDTO(
                workspace_id=workspace_id,
                accepted=workspace_id in accepted_workspace_ids,
            )
            for workspace_id in requested_workspace_ids_ordered
        ]
