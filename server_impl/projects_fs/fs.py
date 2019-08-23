from typing import List, Optional, Tuple
from glob import glob

from werkzeug.datastructures import FileStorage

from openapi_server.models import ProjectBrief, ProjectDetails, NewProject, StringConstants

import os
import yaml

from server_impl.errors import EBadRequest
from server_impl.errors.custom_errors import ENotFound
from server_impl.projects_fs.caches import GlobCache, CacheMap
import datetime
import shutil

from server_impl.projects_fs.file_names import FileNames, PROJ_DIR
from server_impl.projects_fs.fs_internals import CacheRegistry, save_project, read_yaml


def list_projects() -> List[ProjectBrief]:
    return CacheRegistry.project_list.data


def lookup_tag(tag: str) -> Optional[Tuple[ProjectDetails, str]]:
    project_dir = FileNames.project_dir(tag)
    if not os.path.exists(project_dir):
        return None
    return CacheRegistry.project_details.of(tag).data, project_dir


def project_details(tag: str) -> Optional[ProjectDetails]:
    project_dir = FileNames.project_dir(tag)
    if not os.path.exists(project_dir):
        return None
    return CacheRegistry.project_details.of(tag).data


def project_tag_available(tag: str) -> bool:
    return tag.lower() not in [x.lower() for x in os.listdir(PROJ_DIR)]


def make_project(proj: NewProject):
    dirname = FileNames.project_dir(proj.tag)
    os.makedirs(dirname)

    project = ProjectDetails(tag=proj.tag, name=proj.name, last_modified=datetime.datetime.now(),
                             description=proj.description, api_version=StringConstants.NOT_SET)
    save_project(project)
    return project


def delete_project(tag: str):
    dirname = FileNames.project_dir(tag)
    if os.path.exists(dirname):
        shutil.rmtree(dirname)
        CacheRegistry.project_details.remove(tag)
        CacheRegistry.project_list.filter(lambda proj: proj.tag == tag)
        return
    else:
        raise ENotFound("No project exists with tag '%s'" % tag)


def update_project(project: ProjectDetails):
    project.last_modified = datetime.datetime.now()
    save_project(project)


def add_api(tag: str, api: FileStorage):
    match = lookup_tag(tag)
    if match is not None:
        project, dirname = match

        api.save(dirname)
        print('API File Saved: %s' % api.filename)
        update_project(project)
    else:
        return True, 404
