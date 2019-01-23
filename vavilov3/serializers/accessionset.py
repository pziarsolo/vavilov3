import csv
from collections import OrderedDict

from django.db import transaction
from django.db.utils import IntegrityError

from vavilov3.models import (Institute, AccessionSet, Accession)
from vavilov3.entities.tags import INSTITUTE_CODE, GERMPLASM_NUMBER
from vavilov3.entities.shared import VavilovSerializer, VavilovListSerializer
from vavilov3.entities.accessionset import (AccessionSetStruct,
                                            AccessionSetValidationError,
                                            validate_accessionset_data)


class AccessionSetListSerializer(VavilovListSerializer):

    def create_item_in_db(self, item, group):
        return create_accessionset_in_db(item, group)


class AccessionSetSerializer(VavilovSerializer):

    class Meta:
        list_serializer_class = AccessionSetListSerializer
        Struct = AccessionSetStruct
        ValidationError = AccessionSetValidationError

    def validate_data(self, data):
        return validate_accessionset_data(data)

    def create_item_in_db(self, item, user):
        return create_accessionset_in_db(item, user)


def create_accessionset_in_db(api_data, user, is_public=None):
    # when we are creating
    try:
        accessionset_struct = AccessionSetStruct(api_data=api_data)
    except AccessionSetValidationError as error:
        print(error)
        raise

    if (accessionset_struct.metadata.group or accessionset_struct.metadata.is_public):
        msg = 'can not set group or is public while creating the accession'
        raise ValueError(msg)

    try:
        institute = Institute.objects.get(code=accessionset_struct.institute_code)
    except Institute.DoesNotExist:
        msg = '{} does not exist in database'
        raise ValueError(msg.format(accessionset_struct.institute_code))

    # in the doc we must enter whole document
    if is_public is None:
        is_public = False
    group = user.groups.first()
    accessionset_struct.metadata.is_public = is_public
    accessionset_struct.metadata.group = group.name

    with transaction.atomic():
        try:
            accessionset = AccessionSet.objects.create(
                institute=institute,
                accessionset_number=accessionset_struct.accessionset_number,
                group=group,
                is_public=is_public,
                data=accessionset_struct.data)
        except IntegrityError:
            msg = 'This accessionset already exists in db: {} {}'
            raise ValueError(
                msg.format(institute.code,
                           accessionset_struct.accessionset_number))
        for accession in accessionset_struct.accessions:
            try:
                accession_instance = Accession.objects.get(
                    institute__code=accession[INSTITUTE_CODE],
                    germplasm_number=accession[GERMPLASM_NUMBER])
            except Accession.DoesNotExist:
                msg = "{}: accession not found {}:{}"
                msg = msg.format(accessionset_struct.accessionset_number,
                                 accession[INSTITUTE_CODE],
                                 accession[GERMPLASM_NUMBER])
                raise ValueError(msg)
            if accession_instance:
                accessionset.accessions.add(accession_instance)

    return accessionset


def serialize_accessionsets_from_csv(fhand):
    reader = csv.DictReader(fhand, delimiter=',')
    fields = reader.fieldnames
    data = []
    for row in reader:
        row = OrderedDict(((field, row[field]) for field in fields))
        accessionset_struct = AccessionSetStruct()
        accessionset_struct.populate_from_csvrow(row)
        data.append(accessionset_struct.get_api_document())
    return data
