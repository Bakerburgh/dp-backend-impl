import re
import yaml

from yaml.scanner import ScannerError

from werkzeug.datastructures import FileStorage

from openapi_server.models import TagStatus, NewProject, ProjectDetails
from ..db import Database
from .. import projects_fs as fs

from openapi_spec_validator import validate_spec
from openapi_spec_validator.exceptions import ValidationError
from datetime import datetime
urlSafe = re.compile('^[a-zA-Z0-9_-]*$')
# Project IDs that would conflict with other URLs
reservedTags = ['new']


def get_projects():
    """Get Project List

     # noqa: E501


    :rtype: List[ProjectBrief]
    """
    return fs.list_projects()


def get_project_details(proj_id: str):
    ret = fs.project_details(proj_id.lower())
    if ret is None:
        return None, 404
    return ret


def check_tag(tag):
    m = urlSafe.fullmatch(tag)
    if m is None:
        return TagStatus(legal=False, available=False, message='Only letters, numbers, _, and - are allowed')
    if tag in reservedTags:
        return TagStatus(legal=True, available=False)
    return TagStatus(legal=True, available=fs.project_tag_available(tag))


def add_project(proj: NewProject):
    tag_status = check_tag(proj.tag)
    if not tag_status.legal:
        return "Invalid project tag '%s'" % proj.tag, 400
    if not tag_status.available:
        return "Project Tag Conflict", 409

    #
    # content = specfile.read()
    # try:
    #     parsed = yaml.safe_load(content)
    # except ScannerError:
    #     return "Invalid JSON or YAML content", 400
    #
    # print(type(parsed))
    # try:
    #     validate_spec(parsed)
    # except ValidationError as e:
    #     return "Invalid OpenAPI specification", 400

    return fs.make_project(proj)


    # with specfile as f:
    #     print(type(f))
    #     print(f['openapi'])
    # print(specfile['openapi'])
    # validate_spec(specfile)
    # return None, 501


def delete_project(proj_id):
    return fs.delete_project(proj_id)