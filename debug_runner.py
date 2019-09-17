from openapi_server.models import MethodType
# from openapi_types import OpenApi
from server_impl.projects_fs import ProjectWrapper
from server_impl.projects_fs.graph_wrapper import GraphBuilder
import yaml
proj = ProjectWrapper('kKj-ZQbfz')
# print(proj)
#
# g = proj.get_graph('getProjects')
from server_impl.projects_fs.fs_internals import read_yaml

mod = proj.modules.get_graph('getProjects')
spec = proj.read_api()



# api = OpenApi(yaml.safe_load(spec))

# gb = GraphBuilder(spec, api.operations[1])