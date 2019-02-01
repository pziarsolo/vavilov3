from vavilov3.serializers.shared import VavilovListSerializer, VavilovSerializer
from vavilov3.entities.plant import (PlantStruct, PlantValidationError,
                                     validate_plant_data, update_plant_in_db,
                                     create_plant_in_db)
from vavilov3.entities.tags import GROUP


class PlantMixinSerializer():
    data_type = 'plant'

    def validate_data(self, data):
        return validate_plant_data(data)

    def update_item_in_db(self, payload, instance, user):
        return update_plant_in_db(payload, instance, user)

    def create_item_in_db(self, item, user):
        return create_plant_in_db(item, user)


class PlantListSerializer(PlantMixinSerializer, VavilovListSerializer):
    pass


class PlantSerializer(PlantMixinSerializer, VavilovSerializer):

    class Meta:
        list_serializer_class = PlantListSerializer
        Struct = PlantStruct
        ValidationError = PlantValidationError
        metadata_validation_fields = [GROUP]
