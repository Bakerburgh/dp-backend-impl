from typing import List
from werkzeug.datastructures import FileStorage

from openapi_server.models import TagStatus, NewProject, ProjectDetails, Module
from server_impl.projects_fs import ProjectWrapper
from server_impl import projects_fs as fs


def get_module_list(proj_id: str) -> List[Module]:
    wrapper = ProjectWrapper(proj_id)
    if wrapper is None:
        return 404
    return wrapper.get_modules()