from enum import Enum

import yaml
import os

from typing import Union, List

from openapi_server.models import ProjectBrief, ProjectDetails, Module, FlowGraph
from server_impl.projects_fs.caches import GlobCache, CacheMap, CacheDoubleMap
from .file_names import FileNames, PROJ_DIR
from glob import glob


def repr_datetime_as_string(dumper, data):
    return dumper.represent_str(data.isoformat())

# When dumping a datetime, convert it to a string. This is needed for the model to import it correctly.
# yaml.SafeDumper.add_representer(datetime.datetime, repr_datetime_as_string)


def repr_enum(dumper, data: Enum):
    return dumper.represent_str(data.value)


yaml.SafeDumper.add_representer(Enum, repr_enum)


def read_yaml(filename: str) -> Union[dict, list, object]:
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

    @classmethod
    def project_modules(cls, tag: str):
        return os.path.join(FileNames.project_dir(tag), 'modules', '*-modules.yaml')

    @staticmethod
    def project_module_file(tag: str, mod: str):
        return os.path.join(FileNames.project_dir(tag), 'modules', '%s-modules.yaml' % mod)

    @staticmethod
    def project_graph_file(tag: str, mod: str):
        return os.path.join(FileNames.project_dir(tag), 'modules', '%s-graph.yaml' % mod)


def construct_project_list():
    ret = []
    for f in glob(Patterns.project_list):
        raw = read_yaml(f)
        proj = ProjectBrief.inflate(raw)
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

    debug_dict(ProjectDetails.inflate(combined).flatten(), 'BUILT')
    return ProjectDetails.inflate(combined)


def construct_module_list(tag: str) -> List[Module]:
    ret = []
    for f in glob(Patterns.project_modules(tag)):
        raw = read_yaml(f)
        mod = Module.inflate(raw)
        ret.append(mod)
    return ret


def construct_graph(tag: str, mod: str) -> FlowGraph:
    filename = Patterns.project_graph_file(tag, mod)
    data = read_yaml(filename)
    return FlowGraph.inflate(data)


class CacheRegistry:
    project_list = GlobCache(Patterns.project_list, construct_project_list)
    project_details = CacheMap(Patterns.project_details, construct_project_details)
    module_list = CacheMap(Patterns.project_modules, construct_module_list)
    graphs = CacheDoubleMap(Patterns.project_graph_file, construct_graph)


def save_project(details: ProjectDetails):
    print('_save_project: Description: %s' % details.description)
    data = details.flatten()
    print(data)

    brief_data = ProjectBrief.inflate(data).flatten()
    file_brief, file_detail = FileNames.project_info(details.tag)
    print('Saving to file: %s' % file_brief)
    save_yaml(file_brief, brief_data)

    # Remove brief fields from detail fields
    for key in brief_data:
        del data[key]

    print('Saving to file: %s' % file_detail)
    save_yaml(file_detail, data)
