from vavilov3.entities.tags import GROUP, IS_PUBLIC


class MetadataValidationError(Exception):
    pass


def validate_metadata_data(data, fields_to_validate=None):
    if fields_to_validate is None:
        fields_to_validate = (IS_PUBLIC, GROUP)
    for key in fields_to_validate:
        if key not in data:
            msg = '{} is mandatory in metadata'.format(key)
            raise MetadataValidationError(msg)


class Metadata():

    def __init__(self, data=None):
        if data:
            self._data = data
        else:
            self._data = {}

    @property
    def group(self):
        return self._data[GROUP] if GROUP in self._data else None

    @group.setter
    def group(self, group):
        self._data[GROUP] = group

    @property
    def is_public(self):
        return self._data[IS_PUBLIC] if IS_PUBLIC in self._data else None

    @is_public.setter
    def is_public(self, is_public):
        assert isinstance(is_public, bool), "is_public must be a Boolean"
        self._data[IS_PUBLIC] = is_public

    @property
    def data(self):
        return self._data
