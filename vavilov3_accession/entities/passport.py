from passports.passport import Passport
from passports.validation import validate_passport_data as validate_passport

from vavilov3_accession.entities.metadata import Metadata


class PassportValidationError(Exception):
    pass


class PassportStruct(Passport):

    def __init__(self, api_data=None, instance=None, fields=None):
        if api_data and instance:
            raise ValueError('Can not initialize with data and instance')

        if api_data is None and instance is None:
            self._data = {}
            self._metadata = Metadata()
        else:
            if instance:
                api_data = self._deserialize_instance(instance, fields)
            super().__init__(api_data)
            self._metadata = Metadata()

    @staticmethod
    def _deserialize_instance(instance, fields):
        return instance.data
#         self.metadata.group = instance.group.name
#         self.metadata.is_public = instance.is_public


#         if fields is None or 'passport_institute' in fields:
#             self.institute_code = instance.institute.code
#         if fields is None or 'germplasmNumber' in fields:
#             self.germplasm_number = instance.number
def validate_passport_data(data):
    validate_passport(data)
