from vavilov3.entities.accession import (AccessionValidationError,
                                         AccessionStruct,
                                         validate_accession_data,
                                         update_accession_in_db,
                                         create_accession_in_db)

from vavilov3.serializers.shared import VavilovListSerializer, VavilovSerializer


class AccessionMixinSerializer():
    data_type = 'accession'

    def update_item_in_db(self, payload, instance, user):
        return update_accession_in_db(payload, instance, user)

    def create_item_in_db(self, item, user):
        return create_accession_in_db(item, user)

    def validate_data(self, data):
        return validate_accession_data(data)


class AccessionListSerializer(AccessionMixinSerializer, VavilovListSerializer):
    pass


class AccessionSerializer(AccessionMixinSerializer, VavilovSerializer):

    class Meta:
        list_serializer_class = AccessionListSerializer
        Struct = AccessionStruct
        ValidationError = AccessionValidationError
