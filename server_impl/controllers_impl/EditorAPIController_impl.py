from server_impl.projects_fs import ProjectWrapper


def get_graph(proj_id, mod_id):
    wrapper = ProjectWrapper(proj_id)
    if wrapper is None:
        return 404

    graph_wrapper = wrapper.wrap_graph(mod_id)
    return graph_wrapper.graph
