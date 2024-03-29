from jsonschema import ValidationError
from typing import List, Optional, Dict

from openapi_core import create_spec
from openapi_core.schema.infos.models import Info
from werkzeug.datastructures import FileStorage
import datetime

from generated.openapi import OpenApi
from openapi_server.models import ProjectDetails, Module, FlowGraph
from server_impl import TagBuilder
from server_impl.errors.custom_errors import ENotFound, EConflict
from server_impl.projects_fs.file_names import FileNames
from server_impl.projects_fs.fs_internals import read_yaml, save_yaml, Patterns
from server_impl.projects_fs.graph_wrapper import GraphWrapper, build_graph
from server_impl.spec_utils import valid_or_raise
from server_impl.spec_utils.converter import convert

from .fs import lookup_tag, update_project, load_graph
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

# Module Data is saved as:
#
#   <projects>/modules/<mod_id>-module.yaml
#   <projects>/modules/<mod_id>-graph.yaml
#

class ModuleManager:
    def __init__(self, mod_dir: str):
        self.mod_dir = mod_dir
        self.mod_mapping: Optional[dict] = None

    def add_module(self, op_id: str, graph: FlowGraph):
        raise EBadRequest("UNIMPLEMENTED")

    def get_modmap(self) -> dict:
        if self.mod_mapping is None:
            filename = self._modmap_filename()
            if not os.path.exists(filename):
                if os.path.exists(self.mod_dir):
                    raise ENotFound('Project exists, but no module list file...')
                else:
                    raise ENotFound('Project does not exist')
            self.mod_mapping = read_yaml(filename)
        return self.mod_mapping

    def list(self):
        return self.get_modmap().values()

    def _modmap_filename(self):
        return os.path.join(self.mod_dir, 'index.yaml')

    def init_dirs(self):
        if not os.path.exists(self.mod_dir):
            os.makedirs(self.mod_dir)
        self.mod_mapping = {}
        return self.mod_dir

    # def get_graph(self, mod_id):
    #     return
    #     raise EBadRequest("UNIMPLEMENTED")
    #
    #     # mod = self.get_module(mod_id)
    #     # return build_graph(os.path.join(self.spec_dir(), self.api_filename), mod)

    def save(self):
        with open(self._modmap_filename(), 'w+') as f:
            yaml.safe_dump(self.mod_mapping)

    def get_module(self, mod_id):
        raise EBadRequest("UNIMPLEMENTED")


class Graph(object):
    pass


class ProjectWrapper:
    def __init__(self, tag: str):
        match = lookup_tag(tag)
        if match:
            self.target, self.dirname = match
        else:
            raise ENotFound('No project exists with tag %s' % tag)
        self.dirty = False
        self.tag = tag
        self._modules = None

    @property
    def modules(self):
        if self._modules is None:
            self._modules = ModuleManager(self.mod_dir())
        return self._modules

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

        api = create_spec(content)

        modules: Dict[str, Module]
        graphs: Dict[str, FlowGraph]
        modules, graphs = convert(api)

        info: Info = api.info
        print('JCT INFO ====================')
        print('JCT INFO ====================')
        print('JCT INFO ====================')
        print("INFO", info.__dict__)
        print('JCT INFO ====================')
        print('JCT INFO ====================')
        print('JCT INFO ====================')
        self.target.api_filename = file.filename
        self.target.api_version = info.version
        self.target.description = info.title

        #
        mdir = self.modules.init_dirs()

        # modules = _parse_and_save_module_list(api, self.modmap_filename())
        for mod_id in modules.keys():
            mod_file = Patterns.project_module_file(self.tag, mod_id)
            save_yaml(mod_file, modules[mod_id].flatten())
            graph_file = Patterns.project_graph_file(self.tag, mod_id)
            save_yaml(graph_file, graphs[mod_id].flatten())
            # self.modules.add_module(mod_id, graphs[mod_id])
            # _save_raw_module(mod_dir, mod)
        # self.modules.save()
        #
        # self.target.api_version = content['info']['version']
        # self.target.api_filename = file.filename
        #
        self.dirty = True

        # api = OpenApi.from_data(content)
        #
        _save_api_file(spec_dir, file)

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

    #
    # def get_module(self, tag: str) -> Module:
    #     mod_map = self._load_mod_map()
    #     return Module.inflate(mod_map[tag])

    # def get_graph(self, mod_id: str) -> FlowGraph:
    #     return self.modules.get_graph(mod_id)
    #     # filename = os.path.join(self.mod_dir(), mod_id, 'graph.yaml')
    #     # if os.path.exists(filename):
    #     #     data = read_yaml(filename)
    #     #     return FlowGraph.inflate(data)
    #     #
    #     # mod = self.modules.get_graph(mod_id)
    #     # mod = self.get_module(mod_id)
    #     # return build_graph(os.path.join(self.spec_dir(), self.api_filename), mod)

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

    def get_graph(self, mod_id) -> FlowGraph:
        return load_graph(self.tag, mod_id)

    # def mock_graph(self) -> FlowGraph:
    #     pass
    #     # class ObjectView(object):
    #     #     def __init__(self, data: dict):
    #     #         self.__dict__ = data
    #     #
    #     # class MyFlowGraph:
    #     #     def __init__(self):
    #     #         self.request_id = 'foo'
    #     #         self.response_id = 'bar'
    #     #         self.nodes = {}  # ObjectView({})
    #     #
    #     #     def __str__(self):
    #     #         return str(self.__dict__)
    #     #
    #     #     def __repr__(self):
    #     #         return str(self.__dict__)
    #
    #     # return FlowGraph()
    #
    #     filename = os.path.join(FileNames.mocks_dir(), 'graph-01.yaml')
    #     graph = load_graph(filename)
    #     return graph
        # return FlowGraph.from_dict(graph)
