from vavilov3.entities.accession import (AccessionValidationError,
                                         AccessionStruct,
                                         validate_accession_data,
                                         update_accession_in_db,
                                         create_accession_in_db)

from vavilov3.serializers.shared import VavilovListSerializer, VavilovSerializer
from vavilov3.entities.passport import PassportValidationError
from vavilov3.passport.validation import PassportValidationError as PassportValidationError2


class AccessionMixinSerializer():
    data_type = 'accession'

    def update_item_in_db(self, payload, instance, user):
        return update_accession_in_db(payload, instance, user)

    def create_item_in_db(self, item, user):
        return create_accession_in_db(item, user)

    def validate_data(self, data):
        try:
            return validate_accession_data(data)
        except (PassportValidationError, PassportValidationError2) as error:
            raise AccessionValidationError(error)


class AccessionListSerializer(AccessionMixinSerializer, VavilovListSerializer):
    pass


class AccessionSerializer(AccessionMixinSerializer, VavilovSerializer):

    class Meta:
        list_serializer_class = AccessionListSerializer
        Struct = AccessionStruct
        ValidationError = AccessionValidationError
