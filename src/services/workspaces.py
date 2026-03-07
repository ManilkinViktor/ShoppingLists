from uuid import UUID

from schemas.workspaces import WorkspaceCreateDTO, WorkspaceDTO
from schemas.workspace_changes import Operation, WorkspaceChangeCreateDTO, WorkspaceSyncResultDTO
from database.models.workspace_members import Role
from services.base import BaseService
from services.exceptions import ConflictUUID, DuplicateWorkspaceSyncPayload, EntityNotFound


class WorkspacesService(BaseService):

    async def create(self, current_user: UUID, workspace_data: WorkspaceCreateDTO) -> WorkspaceDTO:
        found_workspace: WorkspaceDTO = await self.uow.workspaces.get(workspace_data.id)
        if found_workspace:
            if self._same_workspaces(found_workspace, workspace_data):
                self._log_info("Workspace already exists", extra={'workspace_id': found_workspace.id})
                workspace: WorkspaceDTO = found_workspace
            else:
                self._log_warning("Conflict uuid: workspace with same uuid and another data exists")
                raise ConflictUUID
        else:
            workspace_data.owner_id = current_user
            workspace: WorkspaceDTO = await self.uow.workspaces.add(workspace_data)
            await self.uow.workspace_members.add(workspace_id=workspace.id, user_id=current_user, role=Role.editor)
            self._log_info("Workspace was created", extra={'workspace_id': workspace.id})
        return workspace

    @staticmethod
    def _same_workspaces(first_workspace: WorkspaceDTO, second_workspace: WorkspaceCreateDTO) -> bool:
        return all(
            getattr(first_workspace, field) == value
            for field, value in second_workspace
        )

    def _collect_unique_workspace_ids(
        self,
        current_user: UUID,
        workspace_changes: list[WorkspaceChangeCreateDTO],
    ) -> set[UUID]:
        workspace_ids = [change.workspace_id for change in workspace_changes]
        unique_workspace_ids = set(workspace_ids)
        if len(unique_workspace_ids) != len(workspace_ids):
            self._log_warning(
                'Sync payload has duplicate workspace_id values',
                extra={'user_id': current_user},
            )
            raise DuplicateWorkspaceSyncPayload
        return unique_workspace_ids

    async def _validate_workspace_access(
        self,
        current_user: UUID,
        unique_workspace_ids: set[UUID],
    ) -> None:
        members = await self.uow.workspace_members.get_all(
            user_id=current_user,
            workspace_id=unique_workspace_ids,
        )
        accessible_workspace_ids = {member.workspace_id for member in members}
        inaccessible_workspace_ids = unique_workspace_ids - accessible_workspace_ids
        if inaccessible_workspace_ids:
            workspace_id = next(iter(inaccessible_workspace_ids))
            self._log_warning(
                "User doesn't have access to workspace sync",
                extra={'workspace_id': workspace_id, 'user_id': current_user},
            )
            raise EntityNotFound(WorkspaceDTO)

    async def _get_workspace_versions(self, unique_workspace_ids: set[UUID]) -> dict[UUID, int]:
        workspaces = await self.uow.workspaces.get_all(id=unique_workspace_ids)
        workspace_versions: dict[UUID, int] = {}
        for workspace in workspaces:
            workspace_versions[workspace.id] = workspace.version
        missing_workspace_ids = unique_workspace_ids - set(workspace_versions)
        if missing_workspace_ids:
            raise EntityNotFound(WorkspaceDTO)
        return workspace_versions

    @staticmethod
    def _group_required_operations(
        required_changes: list[WorkspaceChangeCreateDTO],
    ) -> dict[UUID, list[Operation]]:
        required_operations_by_workspace: dict[UUID, list[Operation]] = {}
        for required_change in required_changes:
            operations = required_operations_by_workspace.setdefault(required_change.workspace_id, [])
            operations.extend(required_change.changes)
        return required_operations_by_workspace

    @staticmethod
    def _build_sync_result(
        workspace_changes: list[WorkspaceChangeCreateDTO],
        outdated_workspace_versions: dict[UUID, int],
        required_operations_by_workspace: dict[UUID, list[Operation]],
    ) -> list[WorkspaceSyncResultDTO]:
        sync_result: list[WorkspaceSyncResultDTO] = []
        for workspace_change in workspace_changes:
            workspace_id = workspace_change.workspace_id
            accepted = workspace_id not in outdated_workspace_versions
            changes = required_operations_by_workspace.get(workspace_id, [])
            sync_result.append(
                WorkspaceSyncResultDTO(
                    workspace_id=workspace_id,
                    accepted=accepted,
                    changes=changes,
                )
            )
        return sync_result

    async def sync(
        self,
        current_user: UUID,
        workspace_changes: list[WorkspaceChangeCreateDTO],
    ) -> list[WorkspaceSyncResultDTO]:
        unique_workspace_ids = self._collect_unique_workspace_ids(current_user, workspace_changes)
        await self._validate_workspace_access(current_user, unique_workspace_ids)

        workspace_versions = await self._get_workspace_versions(unique_workspace_ids)
        request_versions: dict[UUID, int] = {}
        for workspace_change in workspace_changes:
            request_versions[workspace_change.workspace_id] = workspace_change.workspace_version

        outdated_workspace_versions: dict[UUID, int] = {}
        for workspace_id, actual_version in workspace_versions.items():
            request_version = request_versions[workspace_id]
            if actual_version > request_version:
                outdated_workspace_versions[workspace_id] = request_version

        expected_bump_versions: dict[UUID, int] = {}
        for workspace_change in workspace_changes:
            has_changes = bool(workspace_change.changes)
            is_outdated = workspace_change.workspace_id in outdated_workspace_versions
            if has_changes and not is_outdated:
                expected_bump_versions[workspace_change.workspace_id] = workspace_change.workspace_version

        bumped_workspace_versions = await self.uow.workspaces.compare_and_bump_versions(expected_bump_versions)
        for workspace_id, expected_version in expected_bump_versions.items():
            if workspace_id not in bumped_workspace_versions:
                outdated_workspace_versions[workspace_id] = expected_version

        new_changes: list[WorkspaceChangeCreateDTO] = []
        for workspace_change in workspace_changes:
            if not workspace_change.changes:
                continue

            bumped_version = bumped_workspace_versions.get(workspace_change.workspace_id)
            if bumped_version is None:
                continue

            new_changes.append(
                WorkspaceChangeCreateDTO(
                    workspace_id=workspace_change.workspace_id,
                    workspace_version=bumped_version,
                    changes=workspace_change.changes,
                )
            )

        if new_changes:
            await self.uow.workspace_changes.add_many(new_changes)

        required_changes = await self.uow.workspace_changes.get_since_versions(outdated_workspace_versions)
        required_operations_by_workspace = self._group_required_operations(required_changes)

        self._log_info(
            'Workspace changes were synced',
            extra={
                'changes_count': len(new_changes),
                'outdated_workspaces_count': len(outdated_workspace_versions),
                'user_id': current_user,
            },
        )

        return self._build_sync_result(
            workspace_changes,
            outdated_workspace_versions,
            required_operations_by_workspace,
        )
