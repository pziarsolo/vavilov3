from vavilov3.entities.study import (StudyStruct, validate_study_data,
                                     StudyValidationError, update_study_in_db,
                                     create_study_in_db)
from vavilov3.serializers.shared import VavilovListSerializer, VavilovSerializer


class StudyMixinSerializer():
    data_type = 'study'

    def validate_data(self, data):
        return validate_study_data(data)

    def update_item_in_db(self, payload, instance, user):
        return update_study_in_db(payload, instance, user)

    def create_item_in_db(self, item, user):
        return create_study_in_db(item, user)


class StudyListSerializer(StudyMixinSerializer, VavilovListSerializer):
    pass


class StudySerializer(StudyMixinSerializer, VavilovSerializer):

    class Meta:
        list_serializer_class = StudyListSerializer
        Struct = StudyStruct
        ValidationError = StudyValidationError
