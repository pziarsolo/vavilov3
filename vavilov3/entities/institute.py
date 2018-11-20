from vavilov3.entities.metadata import Metadata
from vavilov3.entities.tags import INSTITUTE_CODE, INSTITUTE_NAME


class InstituteValidationError(Exception):
    pass


def validate_institute_data(payload):
    if INSTITUTE_CODE not in payload:
        raise InstituteValidationError('{} mandatory'.format(INSTITUTE_CODE))


class InstituteStruct():

    def __init__(self, api_data=None, instance=None, fields=None):
        if api_data and instance:
            raise ValueError()

        if api_data is None and instance is None:
            self._data = {}
            self._metadata = Metadata()
        elif api_data:
            payload = api_data['data']
            self._metadata = Metadata(api_data['metadata'])
            validate_institute_data(payload)
            self._data = payload
        elif instance:
            self._data = {}
            self._metadata = Metadata()
            self._populate_with_instance(instance, fields)

    @property
    def data(self):
        return self._data

    def get_api_document(self):
        return {'data': self.data,
                'metadata': self.metadata.data}

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, metadata):
        self._metadata = metadata

    @property
    def institute_code(self):
        return self._data.get(INSTITUTE_CODE, None)

    @institute_code.setter
    def institute_code(self, code):
        self._data[INSTITUTE_CODE] = code

    @property
    def institute_name(self):
        return self._data.get(INSTITUTE_NAME, None)

    @institute_name.setter
    def institute_name(self, name):
        self._data[INSTITUTE_NAME] = name

    def _populate_with_instance(self, instance, fields):
        self.metadata.group = instance.group.name
        self.metadata.is_public = instance.is_public
        for field in fields:
            if field == 'code':
                self.institute_code = instance.code
            elif field == 'name':
                self.institute_name = instance.name
