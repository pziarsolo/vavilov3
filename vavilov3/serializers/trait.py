from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from vavilov3.views import format_error_message
from vavilov3.serializers.shared import VavilovListSerializer, VavilovSerializer

from vavilov3.entities.trait import (TraitStruct, TraitValidationError,
                                     create_trait_in_db, update_trait_in_db,
                                     validate_trait_data)


class TraitMixinSerializer():
    data_type = 'trait'

    def validate_data(self, data):
        return validate_trait_data(data)

    def update_item_in_db(self, payload, instance, user):
        return update_trait_in_db(payload, instance, user)

    def create_item_in_db(self, item, user):
        return create_trait_in_db(item, user)


class TraitListSerializer(TraitMixinSerializer, VavilovListSerializer):
    pass


class TraitSerializer(TraitMixinSerializer, VavilovSerializer):

    class Meta:
        list_serializer_class = TraitListSerializer
        Struct = TraitStruct
        ValidationError = TraitValidationError

    def run_validation(self, data=empty):
        try:
            self.validate_data(data)
        except self.Meta.ValidationError as error:
            raise ValidationError(format_error_message(error))
        return data
