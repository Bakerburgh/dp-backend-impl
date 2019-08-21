import yaml
import os

from openapi_server.models import ProjectBrief, ProjectDetails
from server_impl.projects_fs.caches import GlobCache, CacheMap
from .file_names import FileNames, PROJ_DIR
from glob import glob


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


def debug_dict(data: dict, msg = None):
    if msg:
        print(msg)
    for key in data.keys():
        print('%s: %s' % (key, str(data[key])))


def construct_project_details(tag: str):
    brief = read_yaml(FileNames.project_brief(tag))
    details = read_yaml(FileNames.project_details(tag))
    combined = {**brief, **details}

    debug_dict(ProjectDetails.from_dict(combined).to_dict(), 'BUILT')
    return ProjectDetails.from_dict(combined)


class CacheRegistry:
    project_list = GlobCache(Patterns.project_list, construct_project_list)
    project_details = CacheMap(Patterns.project_details, construct_project_details)


def save_project(details: ProjectDetails):
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
