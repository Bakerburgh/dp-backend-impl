from typing import List, Dict, Optional, Tuple
from glob import glob
from openapi_server.models import ProjectBrief, ProjectDetails, NewProject
import os
import yaml
from server_impl.projects_fs.internal.caches import GlobCache, CacheMap
import datetime
import shutil

# Find the directory storing the projects
PROJ_DIR = os.getenv('PROJECT_DIR')
if PROJ_DIR is None:
    raise Exception('Environmental variable "PROJECT_DIR" must be set')
if not os.path.isdir(PROJ_DIR):
    raise Exception('"PROJECT_DIR" is not set to a valid directory: "%s"' % PROJ_DIR)


def repr_datetime_as_string(dumper, data):
    return dumper.represent_str(data.isoformat())

# When dumping a datetime, convert it to a string. This is needed for the model to import it correctly.
# yaml.SafeDumper.add_representer(datetime.datetime, repr_datetime_as_string)


def read_yaml(filename: str) -> object:
    with open(filename, 'r') as f:
        data = yaml.safe_load(f)
    return data


def save_yaml(filename: str, data: object):
    with open(filename, 'w+') as f:
        yaml.safe_dump(data, f)


class FileNames:
    name_brief = 'brief.yaml'
    name_details = 'details.yaml'

    @classmethod
    def project_dir(cls, tag: str) -> str:
        return os.path.join(PROJ_DIR, tag.lower())

    @classmethod
    def project_brief(cls, tag: str) -> str:
        return os.path.join(PROJ_DIR, tag.lower(), FileNames.name_brief)

    @classmethod
    def project_details(cls, tag: str) -> str:
        return os.path.join(PROJ_DIR, tag.lower(), FileNames.name_details)

    @classmethod
    def project_info(cls, tag: str) -> Tuple[str, str]:
        """
        Return the filenames for the brief and detailed info.
        :param tag: The ID of this project
        :type tag: str
        :return: (brief_filename, details_filename)
        :rtype: Tuple[str, str]
        """
        proj_dir = FileNames.project_dir(tag)
        return os.path.join(proj_dir, FileNames.name_brief), os.path.join(proj_dir, FileNames.name_details)


class Patterns:
    project_list = os.path.join(PROJ_DIR, '*', FileNames.name_brief)

    @classmethod
    def project_details(cls, tag: str):
        return os.path.join(FileNames.project_dir(tag), '*.yaml')


def construct_project_list():
    ret = []
    for f in glob(Patterns.project_list):
        raw = read_yaml(f)
        proj = ProjectBrief.from_dict(raw)
        ret.append(proj)
    return ret


def construct_project_details(tag: str):
    brief = read_yaml(FileNames.project_brief(tag))
    details = read_yaml(FileNames.project_details(tag))
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
    project_dir = FileNames.project_dir(tag)
    if not os.path.exists(project_dir):
        return None
    return CacheRegistry.project_details.of(tag).data


def project_tag_available(tag: str) -> bool:
    return tag.lower() not in [x.lower() for x in os.listdir(PROJ_DIR)]


def make_project(proj: NewProject):
    dirname = FileNames.project_dir(proj.tag)
    os.makedirs(dirname)

    project = ProjectDetails(tag=proj.tag, name=proj.name, last_modified=datetime.datetime.now(), description=proj.description)
    _save_project(project)
    return project


def delete_project(tag: str):
    dirname = FileNames.project_dir(tag)
    if os.path.exists(dirname):
        shutil.rmtree(dirname)
        CacheRegistry.project_details.remove(tag)
        CacheRegistry.project_list.filter(lambda proj: proj.tag == tag)
        return 204
    else:
        return 404


def _save_project(details: ProjectDetails):
    print('_save_project: Description: %s' % details.description)
    data = details.to_dict()
    print(data)

    brief_data = ProjectBrief.from_dict(data).to_dict()
    file_brief, file_detail = FileNames.project_info(details.tag)
    print('Saving to file: %s' % file_brief)
    save_yaml(file_brief, brief_data)

    # Remove brief fields from detail fields
    for key in brief_data:
        del data[key]

    print('Saving to file: %s' % file_detail)
    save_yaml(file_detail, data)

