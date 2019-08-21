
class ModuleDef:
    """
    The definition for a single module. As in, a single operation type at a single path.
    """

class Spec:
    def __init__(self, spec_dict: dict):
        self.raw = spec_dict
        self._modules = None

    def _build_module_list(self):
        return

    @property
    def modules(self):
        if self._modules is None:
            self._build_module_list()
        return self._modules


def parse_spec_dict(data_dict: dict):
    """
    Parse the data from an API specification.
    :param data_dict: The content of an API specification file, as a dictionary.
    :type data_dict: dict
    :return: TODO
    :rtype:
    """