from database.models import WorkspaceChangesOrm
from database.repositories.base import BaseRepository


class WorkspaceChangesRepository(
    BaseRepository[
        WorkspaceChangesOrm,

    ]):

