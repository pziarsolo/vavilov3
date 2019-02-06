from vavilov3.serializers.shared import VavilovSerializer, VavilovListSerializer
from vavilov3.entities.accessionset import (AccessionSetStruct,
                                            AccessionSetValidationError,
                                            validate_accessionset_data,
                                            create_accessionset_in_db,
                                            update_accessionset_in_db)


class AccessionSetMixinSerializer():
    data_type = 'accessionset'

    def create_item_in_db(self, item, user):
        return create_accessionset_in_db(item, user)

    def update_item_in_db(self, payload, instance, user):
        return update_accessionset_in_db(payload, instance, user)

    def validate_data(self, data):
        return validate_accessionset_data(data)


class AccessionSetListSerializer(AccessionSetMixinSerializer, VavilovListSerializer):
    pass


class AccessionSetSerializer(AccessionSetMixinSerializer, VavilovSerializer):

    class Meta:
        list_serializer_class = AccessionSetListSerializer
        Struct = AccessionSetStruct
        ValidationError = AccessionSetValidationError
