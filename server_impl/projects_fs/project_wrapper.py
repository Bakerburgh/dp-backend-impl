from jsonschema import ValidationError
from typing import List
from werkzeug.datastructures import FileStorage
import datetime
from openapi_server.models import ProjectDetails, Module
from server_impl.errors.custom_errors import ENotFound, EConflict
from server_impl.projects_fs.file_names import FileNames
from server_impl.spec_utils import valid_or_raise

from .fs import lookup_tag, update_project
import os
from server_impl.errors import EBadRequest
import yaml
import re

pattern_v3_major = re.compile(r'^3\.\d+\.\d+$')


class ProjectWrapper:
    def __init__(self, tag: str):
        match = lookup_tag(tag)
        if match:
            self.target, self.dirname = match
        else:
            raise ENotFound('No project exists with tag %s' % tag)
        self.dirty = False

    def set_api(self, file: FileStorage):
        print('~~~~ SET API ' + str(self.target.api_filename))
        if self.target.api_filename:
            raise EConflict("Project API already exists")

        try:
            content = yaml.safe_load(file.stream)
        except Exception:
            raise EBadRequest("Failed to parse file. The file must be valid YAML or JSON")

        valid_or_raise(content)

        self.target.api_version = content['info']['version']

        self.dirty = True
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
        return []
