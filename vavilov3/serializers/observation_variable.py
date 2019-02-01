from vavilov3.entities.observation_variable import (
    ObservationVariableStruct, validate_observation_variable_data,
    ObservationVariableValidationError, update_observation_variable_in_db,
    create_observation_variable_in_db)
from vavilov3.entities.tags import GROUP
from vavilov3.serializers.shared import VavilovListSerializer, VavilovSerializer


class ObservationVariableMixinSerializer():
    data_type = 'observation_variable'

    def validate_data(self, data):
        return validate_observation_variable_data(data)

    def update_item_in_db(self, payload, instance, user):
        return update_observation_variable_in_db(payload, instance, user)

    def create_item_in_db(self, item, user):
        return create_observation_variable_in_db(item, user)


class ObservationVariableListSerializer(ObservationVariableMixinSerializer,
                                        VavilovListSerializer):
    pass


class ObservationVariableSerializer(ObservationVariableMixinSerializer,
                                    VavilovSerializer):

    class Meta:
        list_serializer_class = ObservationVariableListSerializer
        Struct = ObservationVariableStruct
        ValidationError = ObservationVariableValidationError
        metadata_validation_fields = [GROUP]
