from jsonschema import ValidationError
import re

from openapi_spec_validator import validate_spec

from server_impl.errors import EBadRequest

pattern_v3_major = re.compile(r'^3\.\d+\.\d+$')


def valid_or_raise(content):
    """
    Validate that a dictionary is a valid OpenAPI specification file.
    :param content: The content of the API specification, parsed into a dictionary
    :type content: dict
    :return: Throws an exception that causes an 4XX return code if the spec is invalid.
    :rtype: None
    """
    if 'openapi' in content:
        openapi_version: str = content['openapi']
        if pattern_v3_major.match(openapi_version):
            print('VALID OPENAPI VERSION: %s' % openapi_version)
            try:
                validate_spec(content)
            except ValidationError as e:
                print(' --> Validation failed')
                print(e)
                raise EBadRequest('API file is not valid.')
        else:
            print('Received unsupported OpenAPI version: %s' % openapi_version)
            raise EBadRequest("Unsupported OpenAPI version")
