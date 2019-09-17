from typing import Generic, TypeVar, Dict, List, Mapping, Optional, Tuple, Callable, cast

from openapi_server.util import Path as ParsePath

from openapi_core.schema.operations.models import Operation
from openapi_core.schema.paths.models import Path
from openapi_core.schema.specs.models import Spec

from openapi_server.models import *

T = TypeVar('T')


class RefPointer(Generic[T]):
    def __init__(self, data: Dict[str, T], rid: str, id_field: str, value: T = None):
        self.rid = rid
        self._value = value
        self._registry = data
        self._id_field = id_field

    @property
    def id(self) -> str:
        return self.rid

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, val: T):
        self._value = val
        self.rid = getattr(val, self._id_field)
        self._registry[self.rid] = self._value


class RefRegistry(Generic[T]):
    def __init__(self, id_prefix: str, id_field: str, registry: Mapping[str, T]):
        self.registry = registry
        self.refs: List[RefPointer] = []
        self.prefix = id_prefix
        self._id_field = id_field

    def _next_id(self):
        return '%s%d' % (self.prefix, len(self.refs))

    def new_ref(self) -> RefPointer[T]:
        p = RefPointer[T](self.registry, rid=self._next_id(), id_field=self._id_field)
        self.refs.append(p)
        return p

    def validate(self):
        for r in self.refs:
            assert r.value is not None, 'A pointer does not have a value set. %s' % r.id
            assert r.id in self.registry


class GraphBuilder:
    def __init__(self):
        self.ports = PortMap()
        self.nodes = NodeMap()
        self.edges = EdgeMap()
        self.plugs = PlugMap()
        self.layouts = LayoutMap()
        self.validators = ValidatorMap()
        self.schemas = SchemaMap()
        self.node_refs: RefRegistry[Node] = RefRegistry('n', 'abstract_node_id', registry=self.nodes)
        self.port_refs: RefRegistry[Port] = RefRegistry('p', 'port_id', registry=self.ports)
        self.request: Optional[RequestNode] = None
        self.response: Optional[ResponseNode] = None

    def add_port(self, node_id: str, port_type: PortType, direction: PortDirection = PortDirection.OUT, is_array = False):
        pntr = self.port_refs.new_ref()
        port = Port(pntr.id, port_type, is_array=is_array, direction=direction, node_id=node_id)
        pntr.value = port
        return port

    def build(self) -> FlowGraph:
        self.node_refs.validate()
        self.port_refs.validate()
        assert self.request is not None
        assert self.response is not None
        return FlowGraph(request_id=self.request.abstract_node_id,
                         response_id=self.response.abstract_node_id,
                         ports=self.ports,
                         nodes=self.nodes,
                         edges=self.edges,
                         plugs=self.plugs,
                         layouts=self.layouts,
                         validators=self.validators,
                         schemas=self.schemas)


def _attach_request_node(path: str, method: str, op: Operation, builder: GraphBuilder, parsePath):
    m = MethodType.inflate(method.upper(), parsePath)
    node_ref = builder.node_refs.new_ref()

    segments = []
    for seg in path.split('/'):
        if seg == '':
            continue
        if seg.startswith('{'):
            print("PARAM! %s" % seg)
        segments.append(UrlSegment(label=seg))

    req = RequestNode(request_node_id=node_ref.id, method=m, segments=segments)

    node_ref.value = req
    builder.request = req


def _attach_constant_node(builder: GraphBuilder, port_type: PortType, val: str):
    node_ptr = builder.node_refs.new_ref()
    port: Port = builder.add_port(node_ptr.id, port_type, direction=PortDirection.OUT)

    node = ConstantNode(constant_node_id=node_ptr.id, port_id=port.port_id, value=val)
    node_ptr.value = node
    return node


def _attach_response_node(op: Operation, builder: GraphBuilder, parsePath: ParsePath):
    node_ref = builder.node_refs.new_ref()

    cn = _attach_constant_node(builder, PortType.NUM, list(op.responses.keys())[0])
    # response_node_id: 'str', code: 'str', layout_id: 'str' = None, body: 'HttpBody' = None):
    resp = ResponseNode(response_node_id = node_ref.id, code=cn.port_id)
    #
    node_ref.value = resp
    builder.response = resp


def operation_to_graph(path: str, method: str, op: Operation) -> FlowGraph:
    builder = GraphBuilder()
    # node_map = NodeMap()
    # port_map = PortMap()
    # edges = EdgeMap()
    # plugs = PlugMap()
    # node_refs: RefRegistry[Node] = RefRegistry('n', 'abstract_node_id', registry=node_map)
    # port_refs:  RefRegistry[Port] = RefRegistry('p', 'port_id', registry=port_map)
    #
    # request_ref = node_refs.new_ref()
    # response_ref = node_refs.new_ref()
    parsePath = ParsePath('#/paths/%s/%s' % (path.replace('/', '\\/'), method))

    _attach_request_node(path, method, op, builder, parsePath)
    _attach_response_node(op, builder, parsePath)

    return builder.build()


def operation_id_fixer():
    def inner(op_id: Optional[str]):
        if op_id is None:
            inner.base += 1
            return 'm%d' % inner.base
        return op_id
    inner.base = 0
    return inner


def operation_to_module(path: str, op: Operation, graph: FlowGraph, mod_id: str) -> Module:
    request: RequestNode = cast(RequestNode, graph.nodes[graph.request_id])
    return Module(method=request.method, url=path, operation_id=op.operation_id,
                  tag=mod_id, status='OK')


def convert(api: Spec) -> Tuple[Dict[str, Module], Dict[str,FlowGraph]]:
    path: str
    path_object: Path
    fixer = operation_id_fixer()
    graphs = {}
    modules = {}
    for path, path_object in api.paths.items():
        if path.startswith('/dev'):
            continue
        else:
            method: str
            operation: Operation
            for method, operation in path_object.operations.items():
                mod_id = fixer(operation.operation_id)
                graph = operation_to_graph(path, method, operation)
                graphs[mod_id] = graph

                module = operation_to_module(path, operation, graph, mod_id)
                modules[mod_id] = module
                break
    return modules, graphs
