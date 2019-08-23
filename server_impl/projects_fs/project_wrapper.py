from jsonschema import ValidationError
from typing import List
from werkzeug.datastructures import FileStorage
import datetime
from openapi_server.models import ProjectDetails, Module
from server_impl.errors.custom_errors import ENotFound, EConflict
from server_impl.projects_fs.file_names import FileNames
from server_impl.projects_fs.fs_internals import read_yaml, save_yaml
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
        if file.filename.endswith('.json'):
            content_type = 'text/json'
        elif file.filename.endswith('.yaml') or file.filename.endswith('.yml'):
            content_type = 'text/yaml'
        else:
            raise EBadRequest('File must have a .json, .yaml, or .yml extension')

        spec_dir = self.spec_dir()
        if os.path.exists(spec_dir):
            raise EConflict("An API was already uploaded to this project.")
        os.makedirs(spec_dir)
        dest = os.path.join(spec_dir, file.filename)
        print("Saving API file to '%s'" % dest)
        file.save(dest)

        file.stream.seek(0)
        try:
            content = yaml.safe_load(file.stream)
        except Exception:
            raise EBadRequest("Failed to parse file. The file must be valid YAML or JSON")

        valid_or_raise(content)

        self.target.api_version = content['info']['version']
        self.target.api_filename = file.filename


        # file.save(dest)

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
        # return read_yaml(filepath)

    def spec_dir(self):
        return os.path.join(self.dirname, 'spec')
