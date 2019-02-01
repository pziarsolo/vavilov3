from vavilov3.serializers.shared import VavilovListSerializer, VavilovSerializer
from vavilov3.entities.observation_unit import (ObservationUnitStruct,
                                                ObservationUnitValidationError,
                                                validate_observation_unit_data,
                                                update_observation_unit_in_db,
                                                create_observation_unit_in_db)


class ObservationUnitMixinSerializer():
    data_type = 'observation_unit'

    def validate_data(self, data):
        return validate_observation_unit_data(data)

    def update_item_in_db(self, payload, instance, user):
        return update_observation_unit_in_db(payload, instance, user)

    def create_item_in_db(self, item, user):
        return create_observation_unit_in_db(item, user)


class ObservationUnitListSerializer(ObservationUnitMixinSerializer,
                                    VavilovListSerializer):
    pass


class ObservationUnitSerializer(ObservationUnitMixinSerializer,
                                VavilovSerializer):

    class Meta:
        list_serializer_class = ObservationUnitListSerializer
        Struct = ObservationUnitStruct
        ValidationError = ObservationUnitValidationError
        metadata_validation_fields = []
