import os

from typing import Tuple


# Find the directory storing the projects
PROJ_DIR = os.getenv('PROJECT_DIR')
if PROJ_DIR is None:
    raise Exception('Environmental variable "PROJECT_DIR" must be set')
if not os.path.isdir(PROJ_DIR):
    raise Exception('"PROJECT_DIR" is not set to a valid directory: "%s"' % PROJ_DIR)


class FileNames:
    name_brief = 'brief.yaml'
    name_details = 'details.yaml'

    @classmethod
    def project_dir(cls, tag: str) -> str:
        return os.path.join(PROJ_DIR, tag.lower())

    @classmethod
    def project_brief(cls, tag: str) -> str:
        return os.path.join(PROJ_DIR, tag.lower(), FileNames.name_brief)

    @classmethod
    def project_details(cls, tag: str) -> str:
        return os.path.join(PROJ_DIR, tag.lower(), FileNames.name_details)

    @classmethod
    def project_info(cls, tag: str) -> Tuple[str, str]:
        """
        Return the filenames for the brief and detailed info.
        :param tag: The ID of this project
        :type tag: str
        :return: (brief_filename, details_filename)
        :rtype: Tuple[str, str]
        """
        proj_dir = FileNames.project_dir(tag)
        return os.path.join(proj_dir, FileNames.name_brief), os.path.join(proj_dir, FileNames.name_details)

    @classmethod
    def mocks_dir(cls):
        return os.path.join(PROJ_DIR, 'mock')
