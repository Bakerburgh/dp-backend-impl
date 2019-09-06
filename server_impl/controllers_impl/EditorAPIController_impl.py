from openapi_server.models import FlowGraph
from server_impl.projects_fs import ProjectWrapper


def get_graph(proj_id, mod_id) -> FlowGraph:
    wrapper = ProjectWrapper(proj_id)
    if wrapper is None:
        return 404

    return wrapper.mock_graph()

    # graph_wrapper = wrapper.wrap_graph(mod_id)
    # return graph_wrapper.graph
