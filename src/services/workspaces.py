from uuid import UUID

from schemas.workspaces import WorkspaceCreateDTO, WorkspaceDTO
from schemas.workspace_changes import UnionOperation, WorkspaceChangeCreateDTO, WorkspaceSyncResultDTO
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

    def _get_requested_workspace_ids(
        self,
        current_user: UUID,
        workspace_changes: list[WorkspaceChangeCreateDTO],
    ) -> set[UUID]:
        workspace_ids: list[UUID] = [change.workspace_id for change in workspace_changes]
        requested_workspace_ids: set[UUID] = set(workspace_ids)
        if len(requested_workspace_ids) != len(workspace_ids):
            self._log_warning(
                'Sync payload has duplicate workspace_id values',
                extra={'user_id': current_user},
            )
            raise DuplicateWorkspaceSyncPayload
        return requested_workspace_ids

    async def _get_accessible_workspace_ids(
        self,
        current_user: UUID,
        requested_workspace_ids: set[UUID],
    ) -> set[UUID]:
        members = await self.uow.workspace_members.get_all(
            user_id=current_user,
            workspace_id=requested_workspace_ids,
        )
        accessible_workspace_ids: set[UUID] = {member.workspace_id for member in members}
        return accessible_workspace_ids

    async def _validate_accessible_workspace_ids(
        self,
        current_user: UUID,
        requested_workspace_ids: set[UUID],
    ) -> None:
        accessible_workspace_ids: set[UUID] = await self._get_accessible_workspace_ids(
            current_user, requested_workspace_ids
        )
        inaccessible_workspace_ids: set[UUID] = requested_workspace_ids - accessible_workspace_ids
        if inaccessible_workspace_ids:
            workspace_id: UUID = next(iter(inaccessible_workspace_ids))
            self._log_warning(
                "User doesn't have access to workspace sync",
                extra={'workspace_id': workspace_id, 'user_id': current_user},
            )
            raise EntityNotFound(WorkspaceDTO)

    async def _ensure_workspace_access(
        self,
        current_user: UUID,
        workspace_changes: list[WorkspaceChangeCreateDTO],
    ) -> set[UUID]:
        requested_workspace_ids: set[UUID] = self._get_requested_workspace_ids(
            current_user, workspace_changes
        )
        await self._validate_accessible_workspace_ids(current_user, requested_workspace_ids)
        return requested_workspace_ids

    async def _get_workspaces_by_id(self, requested_workspace_ids: set[UUID]) -> list[WorkspaceDTO]:
        workspaces: list[WorkspaceDTO] = await self.uow.workspaces.get_all(id=requested_workspace_ids)
        found_workspace_ids: set[UUID] = {workspace.id for workspace in workspaces}
        missing_workspace_ids: set[UUID] = requested_workspace_ids - found_workspace_ids
        if missing_workspace_ids:
            raise EntityNotFound(WorkspaceDTO)
        return workspaces

    async def _primary_version_check(
        self,
        requested_workspace_ids: set[UUID],
        workspace_changes: list[WorkspaceChangeCreateDTO],
    ) -> tuple[set[UUID], set[UUID], dict[UUID, int]]:
        workspaces: list[WorkspaceDTO] = await self._get_workspaces_by_id(requested_workspace_ids)
        request_versions: dict[UUID, int] = {
            change.workspace_id: change.workspace_version for change in workspace_changes
        }
        outdated_workspace_ids: set[UUID] = set()
        for workspace in workspaces:
            workspace_id: UUID = workspace.id
            request_version: int = request_versions[workspace_id]
            if workspace.version > request_version:
                outdated_workspace_ids.add(workspace_id)
        eligible_workspace_ids: set[UUID] = requested_workspace_ids - outdated_workspace_ids
        return outdated_workspace_ids, eligible_workspace_ids, request_versions

    async def _apply_changes(
        self,
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
            new_changes.append(
                WorkspaceChangeCreateDTO(
                    workspace_id=change.workspace_id,
                    workspace_version=bumped_version,
                    changes=change.changes,
                )
            )
        if new_changes:
            await self.uow.workspace_changes.add_many(new_changes)
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

    @staticmethod
    def _build_sync_result(
        workspace_changes: list[WorkspaceChangeCreateDTO],
        outdated_workspace_ids: set[UUID],
        required_operations_by_workspace: dict[UUID, list[UnionOperation]],
    ) -> list[WorkspaceSyncResultDTO]:
        sync_result: list[WorkspaceSyncResultDTO] = []
        for workspace_change in workspace_changes:
            workspace_id = workspace_change.workspace_id
            accepted = workspace_id not in outdated_workspace_ids
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
        requested_workspace_ids: set[UUID] = await self._ensure_workspace_access(
            current_user, workspace_changes
        )
        outdated_workspace_ids, eligible_workspace_ids, request_versions = self._primary_version_check(
            requested_workspace_ids, workspace_changes
        )
        new_changes, expected_bump_versions, bumped_workspace_versions = await self._apply_changes(
            workspace_changes, eligible_workspace_ids
        )
        outdated_workspace_ids = self._finalize_bump_versions(
            outdated_workspace_ids,
            expected_bump_versions,
            bumped_workspace_versions,
        )
        required_operations_by_workspace: dict[UUID, list[UnionOperation]] = (
            await self._get_required_sync_changes(outdated_workspace_ids, request_versions)
        )

        self._log_info(
            'Workspace changes were synced',
            extra={
                'changes_count': len(new_changes),
                'outdated_workspaces_count': len(outdated_workspace_ids),
                'user_id': current_user,
            },
        )

        return self._build_sync_result(
            workspace_changes,
            outdated_workspace_ids,
            required_operations_by_workspace,
        )
