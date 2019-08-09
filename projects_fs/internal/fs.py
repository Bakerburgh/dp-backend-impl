from typing import List, Dict, Optional
from glob import glob
from openapi_server.models import ProjectBrief, ProjectDetails
import os
import yaml
from openapi_server.server_impl.projects_fs.internal.caches import GlobCache, CacheMap


# Find the directory storing the projects


PROJ_DIR = os.getenv('PROJECT_DIR')
if PROJ_DIR is None:
    raise Exception('Environmental variable "PROJECT_DIR" must be set')
if not os.path.isdir(PROJ_DIR):
    raise Exception('"PROJECT_DIR" is not set to a valid directory: "%s"' % PROJ_DIR)


def read_yaml(filename: str) -> object:
    with open(filename, 'r') as f:
        data = yaml.safe_load(f)
    return data


class Patterns:
    project_list = os.path.join(PROJ_DIR, '*', 'brief.yaml')

    @classmethod
    def project_details(cls, tag: str):
        return os.path.join(Patterns.project_dir(tag), '*.yaml')

    @classmethod
    def project_dir(cls, tag: str):
        return os.path.join(PROJ_DIR, tag)


def construct_project_list():
    ret = []
    for f in glob(Patterns.project_list):
        raw = read_yaml(f)
        proj = ProjectBrief.from_dict(raw)
        ret.append(proj)
    return ret


def construct_project_details(tag: str):
    dir = Patterns.project_dir(tag)
    brief = read_yaml(os.path.join(dir, 'brief.yaml'))
    details = read_yaml(os.path.join(dir, 'details.yaml'))
    print(type(brief), type(details))
    combined = {**brief, **details}
    print(combined)
    return ProjectDetails.from_dict(combined)


class CacheRegistry:
    project_list = GlobCache(Patterns.project_list, construct_project_list)
    project_details = CacheMap(Patterns.project_details, construct_project_details)


def list_projects() -> List[ProjectBrief]:
    return CacheRegistry.project_list.data


def project_details(tag: str) -> Optional[ProjectDetails]:
    project_dir = Patterns.project_dir(tag)
    if not os.path.exists(project_dir):
        return None
    return CacheRegistry.project_details.of(tag).data


def project_tag_available(tag: str) -> bool:
    return tag.lower() not in [x.lower() for x in os.listdir(PROJ_DIR)]



#
# class DirCache:
#     """
#     A cache of a directory.
#     """
#
#     def __init__(self):
#         print('foo')