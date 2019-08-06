from flask import jsonify
import re

from openapi_server.models import TagStatus
from ..db import Database

urlSafe = re.compile('^[a-zA-Z0-9_-]*$')

def get_projects():
    """Get Project List

     # noqa: E501


    :rtype: List[ProjectBrief]
    """
    db = Database()
    return db.projectList()


def get_project_details(proj_id):
    db = Database()
    return db.projectList()


def check_tag(tag):  # noqa: E501
    m = urlSafe.fullmatch(tag)
    if m is None:
        return TagStatus(legal=False, available=False, message='Only letters, numbers, _, and - are allowed')

    db = Database()
    return {
        'available': db.tagAvailable(tag),
        'lega': True
    }