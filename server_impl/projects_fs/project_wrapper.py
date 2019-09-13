from jsonschema import ValidationError
from typing import List
from werkzeug.datastructures import FileStorage
import datetime

from generated.openapi import OpenApi
from openapi_server.models import ProjectDetails, Module, FlowGraph
from server_impl import TagBuilder
from server_impl.errors.custom_errors import ENotFound, EConflict
from server_impl.projects_fs.file_names import FileNames
from server_impl.projects_fs.fs_internals import read_yaml, save_yaml
from server_impl.projects_fs.graph_wrapper import GraphWrapper, build_graph, load_graph
from server_impl.spec_utils import valid_or_raise

from .fs import lookup_tag, update_project
import os
from server_impl.errors import EBadRequest
import yaml
import re


pattern_v3_major = re.compile(r'^3\.\d+\.\d+$')


def _preprocess_spec_file(file: FileStorage):
    """
    Validate that the file is a useable OpenAPI specification.
    :param file: The incoming file.
    :type file: FileStorage
    :return: The parsed content of the specification file.
    :rtype: TODO
    """
    if file.filename.endswith('.json'):
        content_type = 'text/json'
    elif file.filename.endswith('.yaml') or file.filename.endswith('.yml'):
        content_type = 'text/yaml'
    else:
        raise EBadRequest('File must have a .json, .yaml, or .yml extension')

    file.stream.seek(0)
    try:
        content = yaml.safe_load(file.stream)
    except Exception:
        raise EBadRequest("Failed to parse file. The file must be valid YAML or JSON")

    valid_or_raise(content)

    return content

def _save_api_file(spec_dir: str, api_file: FileStorage):
    os.makedirs(spec_dir)
    dest = os.path.join(spec_dir, api_file.filename)
    print("Saving API file to '%s'" % dest)
    api_file.stream.seek(0)
    api_file.save(dest)

#
# def _parse_and_save_module_list(api: OpenApi, filename: str) -> List[OperationObject]:
#     # Build the module list for: <mod_dir>/index.yaml
#     # Module method=None, url=None, operation_id=None, tag=None, summary=None, description=None, status=None
#
#     tbuilder = TagBuilder('m')
#
#     module_dict_map = {}
#     op_list = []
#     for op in api.operations:
#         op.tag = tbuilder.normalize(op.operationId)
#         if not op.operationId:
#             op.operationId = op.tag
#
#         m = Module(method=op.method, url=op.url, operation_id=op.operationId, tag=op.tag,
#                    summary=op.summary, description=op.description)
#         if not m.status:
#             m.status = 'TODO'
#
#         op_list.append(op)
#         module_dict_map[m.tag] = m.to_dict()
#
#     save_yaml(filename, module_dict_map)
#     return op_list
#
#
# def _save_raw_module(mod_dir: str, op: OperationObject):
#     """
#     Construct an empty graph for a given module and save it.
#     :param mod_dir: The base directory for the module.
#     :type mod_dir: str
#     :param mod: The module (operation) to create a graph for.
#     :type mod: Module
#     :return: None
#     :rtype:
#     """
#     op_dir = os.path.join(mod_dir, op.tag)
#     if os.path.exists(op_dir):
#         raise EConflict('The raw operation has already been saved for module %s' % op.tag)
#     os.makedirs(op_dir)
#     destfile = os.path.join(op_dir, 'raw.yaml')
#     save_yaml(destfile, op.to_dict())
#     return


class ProjectWrapper:
    def __init__(self, tag: str):
        match = lookup_tag(tag)
        if match:
            self.target, self.dirname = match
        else:
            raise ENotFound('No project exists with tag %s' % tag)
        self.dirty = False

    def set_api(self, file: FileStorage):

        if file.filename.endswith('.json'):
            content_type = 'text/json'
        elif file.filename.endswith('.yaml') or file.filename.endswith('.yml'):
            content_type = 'text/yaml'
        else:
            raise EBadRequest('File must have a .json, .yaml, or .yml extension')
        #
        spec_dir = self.spec_dir()
        # if os.path.exists(spec_dir):
        #     raise EConflict("An API was already uploaded to this project.")
        #
        content = _preprocess_spec_file(file)
        api = OpenApi.from_data(content)
        #
        _save_api_file(spec_dir, file)
        #
        mod_dir = self.mod_dir()
        os.makedirs(mod_dir)
        # modules = _parse_and_save_module_list(api, self.modmap_filename())
        # for mod in modules:
        #     _save_raw_module(mod_dir, mod)
        #
        # self.target.api_version = content['info']['version']
        # self.target.api_filename = file.filename
        #
        # self.dirty = True
        return self

    def finish(self):
        """
        Finish any pending changes and save the project details yaml file, updating the last_modified field if anything
        was changed.
        :return: The project details with the updated timestamp (if a change was saved)
        :rtype: ProjectDetails
        """
        if self.dirty:
            update_project(self.target)
        return self.target

    def get_modules(self) -> List[Module]:
        filename = self.modmap_filename()
        if not os.path.exists(filename):
            if os.path.exists(self.dirname):
                raise ENotFound('Project exists, but no module list file...')
            else:
                raise ENotFound('Project does not exist')
        # noinspection PyTypeChecker
        mod_map: dict = read_yaml(filename)
        return [Module.from_dict(m) for m in mod_map.values()]

    def get_module(self, tag: str) -> Module:
        filename = self.modmap_filename()
        if not os.path.exists(filename):
            if os.path.exists(self.dirname):
                raise ENotFound('Project exists, but no module list file...')
            else:
                raise ENotFound('Project does not exist')
        # noinspection PyTypeChecker
        mod_map: dict = read_yaml(filename)
        return Module.from_dict(mod_map[tag])

    def get_graph(self, mod_id: str):
        filename = os.path.join(self.mod_dir(), mod_id, 'graph.yaml')
        if os.path.exists(filename):
            data = read_yaml(filename)
            return FlowGraph.from_dict(data)

        mod = self.get_module(mod_id)
        return build_graph(os.path.join(self.spec_dir(), self.api_filename), mod)

    @property
    def api_filename(self):
        return self.target.api_filename

    def read_api(self):
        if not self.target.api_filename:
            raise ENotFound("No API file has been uploaded")
        filepath = os.path.join(self.spec_dir(), self.target.api_filename)
        if not os.path.exists(filepath):
            print("Failed to find API spec: '%s'" % filepath)
            raise ENotFound("API file not found")
        print("Loading API spec: '%s'" % filepath)
        with open(filepath, 'r') as f:
            content = f.read()
        return content

    def spec_dir(self):
        return os.path.join(self.dirname, 'spec')

    def mod_dir(self):
        return os.path.join(self.dirname, 'modules')

    def modmap_filename(self):
        return os.path.join(self.mod_dir(), 'index.yaml')

    def mock_graph(self) -> FlowGraph:
        # class ObjectView(object):
        #     def __init__(self, data: dict):
        #         self.__dict__ = data
        #
        # class MyFlowGraph:
        #     def __init__(self):
        #         self.request_id = 'foo'
        #         self.response_id = 'bar'
        #         self.nodes = {}  # ObjectView({})
        #
        #     def __str__(self):
        #         return str(self.__dict__)
        #
        #     def __repr__(self):
        #         return str(self.__dict__)

        return FlowGraph()

        # filename = os.path.join(FileNames.mocks_dir(), 'graph-01.yaml')
        # graph = load_graph(filename)
        # return graph
        # return FlowGraph.from_dict(graph)
