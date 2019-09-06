import os

from openapi_server.models import FlowGraph, Module, RequestNode, UrlSegment, Port, PortDirection, PortType, \
    AbstractNode
from generated.openapi import OpenApi
from generated.openapi import OperationObject, ParameterObject
from server_impl.errors.custom_errors import ENotFound
from server_impl.projects_fs.fs_internals import read_yaml


class GraphBuilder:
    def __init__(self, raw_spec: dict, op: OperationObject):
        self.port_count = 0
        self.node_count = 0
        self.port_map = {}
        self.node_map = {}
        self.raw_spec = raw_spec
        self.op = op
        self.request: RequestNode = self._buildRequestNode()

    def _lookup_param(self, name) -> ParameterObject:
        for p in self.op.parameters:
            if p.name == name:
                return p
        raise 500

    def _param_to_port(self, param: ParameterObject) -> Port:
        return Port(id=self.next_port_id(), type=PortType.TEXT, direction=PortDirection.OUT)

    def _buildRequestNode(self) -> RequestNode:
        node = RequestNode(id=self.next_node_id(), method=self.op.method.upper())

        segments = []
        for seg in self.op.url.split('/'):
            if len(seg) == 0:
                continue
            port = None
            if seg.startswith('{'):
                param_name = seg[1:-1]
                p = self._lookup_param(param_name)
                port = self._param_to_port(p)
                port.node = self.get_node_ref(node)
            segments.append(UrlSegment(label=seg, port=port))
# TODO Need a better way to deal with these refs....
        node.segments = segments
        return node

    def get_node_ref(self, node: AbstractNode):
        return '#/nodes/' + node.id

    def next_node_id(self):
        self.node_count += 1
        return 'n%d' % self.node_count

    def next_port_id(self):
        self.port_count += 1
        return 'n%d' % self.port_count


def _build_empty_graph():
    return None

def build_request(op: OperationObject):
    ret = RequestNode()

def build_graph(specfile: str, module: Module) -> FlowGraph:
    print('TRACE')
    raw: dict = read_yaml(specfile)
    paths_object = raw['paths']

    path_object = paths_object.get(module.url, None)
    if path_object is None:
        raise ENotFound("JHCT TOOSODF JCT TODO")

    op_object = path_object.get(module.method.lower(), None)
    if op_object is None:
        raise ENotFound("JHCT TOOSODF JCT TODO")

    return op_object

class GraphWrapper:
    def __init__(self, modlist_filename, mod_dir, mod_tag):
        self.dirname = mod_dir
        self.tag = mod_tag
        self.filename = os.path.join(mod_dir, mod_tag + '.yaml')
        if not os.path.exists(self.filename):
            self.graph: FlowGraph = _build_empty_graph()
        else:
            raw = read_yaml(self.filename)
            self.graph: FlowGraph = FlowGraph.from_dict(raw)