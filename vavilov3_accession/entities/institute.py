from vavilov3_accession.entities.metadata import Metadata
from vavilov3_accession.entities.tags import INSTITUTE_CODE, INSTITUTE_NAME


class InstituteValidationError(Exception):
    pass


def validate_institute_data(payload):
    if INSTITUTE_CODE not in payload:
        raise InstituteValidationError('{} mandatory'.format(INSTITUTE_CODE))


class InstituteStruct():

    def __init__(self, api_data=None, instance=None, fields=None):
        if api_data and instance:
            raise ValueError('Can not initialize with data and instance')

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

        if fields is None or 'code' in fields:
            self.institute_code = instance.code
        if fields is None or 'name' in fields:
            self.institute_name = instance.name
        if fields is None or 'num_accessions' in fields:
            self._data['num_accessions'] = instance.num_accessions
        if fields is None or 'num_accessionsets' in fields:
            self._data['num_accessionsets'] = instance.num_accessionsets
        if fields is None or 'stats_by_county' in fields:
            self._data['stats_by_country'] = instance.stats_by_country
        if fields is None or 'stats_by_taxa' in fields:
            self._data['stats_by_taxa'] = instance.stats_by_taxa
