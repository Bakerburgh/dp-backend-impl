from openapi_server.models import FlowGraph
from server_impl.errors import EBadRequest
from server_impl.errors.custom_errors import ENotFound
from server_impl.projects_fs import ProjectWrapper


def get_graph(proj_id, mod_id) -> FlowGraph:
    wrapper = ProjectWrapper(proj_id)
    if wrapper is None:
        raise ENotFound("No project exists with tag '%s'" % proj_id)

    return wrapper.get_graph(mod_id)

    # graph_wrapper = wrapper.wrap_graph(mod_id)
    # return graph_wrapper.graph
