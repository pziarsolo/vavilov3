import pytz
import uuid

from copy import deepcopy
from collections import OrderedDict
from datetime import datetime

from django.conf.global_settings import TIME_ZONE
from django.db import transaction
from django.db.utils import IntegrityError

from rest_framework.exceptions import ValidationError

from vavilov3.views import format_error_message
from vavilov3.entities.tags import (OBSERVATION_VARIABLE, OBSERVATION_UNIT,
                                    OBSERVATION_CREATION_TIME, OBSERVER, VALUE,
                                    INSTITUTE_CODE, GERMPLASM_NUMBER,
                                    OBSERVATION_STUDY, ACCESSION,
                                    OBSERVATION_ID, VALUE_BEAUTY)
from vavilov3.conf.settings import DATETIME_FORMAT
from vavilov3.models import (ObservationUnit, ObservationVariable, Observation,
                             Study, Accession)
from vavilov3.permissions import is_user_admin
from vavilov3.data_io import ORDINAL, NOMINAL, NUMERICAL


class ObservationValidationError(Exception):
    pass


TRAITS_IN_COLUMNS = 'traits_in_columns'
CREATE_OBSERVATION_UNITS = 'create_observation_units'

OBSERVATION_ALLOWED_FIELDS = [OBSERVATION_ID, OBSERVATION_VARIABLE, OBSERVATION_UNIT,
                              OBSERVATION_CREATION_TIME, OBSERVER, VALUE,
                              OBSERVATION_STUDY, ACCESSION, VALUE_BEAUTY]


def validate_observation_data(data, conf=None):

    if conf is None:
        conf = {}
    create_observation_units = conf.get(CREATE_OBSERVATION_UNITS, None)
    if OBSERVATION_VARIABLE not in data:
        raise ObservationValidationError('{} mandatory'.format(OBSERVATION_VARIABLE))
    if OBSERVATION_UNIT not in data and not create_observation_units:
        raise ObservationValidationError('{} mandatory'.format(OBSERVATION_UNIT))
    if VALUE not in data:
        raise ObservationValidationError('{} mandatory'.format(VALUE))

    not_allowed_fields = set(data.keys()).difference(OBSERVATION_ALLOWED_FIELDS)

    if not_allowed_fields:
        msg = 'Not allowes fields: {}'.format(', '.join(not_allowed_fields))
        raise ObservationValidationError(msg)


class ObservationStruct():

    def __init__(self, api_data=None, instance=None, fields=None):
        if api_data and instance:
            raise ValueError('Can not initialize with data and instance')

        if api_data is None and instance is None:
            self._data = {}

        elif api_data:
            payload = deepcopy(api_data)
            self._data = payload

        elif instance:
            self._data = {}
            self._populate_with_instance(instance, fields)

    @property
    def data(self):
        _data = deepcopy(self._data)
        return _data

    def get_api_document(self):
        return self.data

    @property
    def observation_id(self):
        return self._data.get(OBSERVATION_ID, None)

    @observation_id.setter
    def observation_id(self, observation_id):
        self._data[OBSERVATION_ID] = observation_id

    @property
    def observation_variable(self):
        return self._data.get(OBSERVATION_VARIABLE, None)

    @observation_variable.setter
    def observation_variable(self, observation_variable):
        self._data[OBSERVATION_VARIABLE] = observation_variable

    @property
    def observation_unit(self):
        return self._data.get(OBSERVATION_UNIT, None)

    @observation_unit.setter
    def observation_unit(self, observation_unit):
        self._data[OBSERVATION_UNIT] = observation_unit

    @property
    def creation_time(self):
        return self._data.get(OBSERVATION_CREATION_TIME, None)

    @creation_time.setter
    def creation_time(self, creation_time):
        self._data[OBSERVATION_CREATION_TIME] = creation_time

    @property
    def observer(self):
        return self._data.get(OBSERVER, None)

    @observer.setter
    def observer(self, observer: str):
        if observer:
            self._data[OBSERVER] = observer

    @property
    def value(self) -> str:
        return self._data.get(VALUE, None)

    @value.setter
    def value(self, value: str):
        if value:
            self._data[VALUE] = value

    @property
    def beauty_value(self) -> str:
        return self._data.get(VALUE_BEAUTY, None)

    @beauty_value.setter
    def beauty_value(self, beauty_value: str):
        if beauty_value:
            self._data[VALUE_BEAUTY] = beauty_value

    @property
    def accession(self) -> str:
        return self._data.get(ACCESSION, None)

    @accession.setter
    def accession(self, accession: str):
        if accession:
            self._data[ACCESSION] = accession

    @property
    def study(self) -> str:
        return self._data.get(OBSERVATION_STUDY, None)

    @study.setter
    def study(self, study: str):
        if study:
            self._data[OBSERVATION_STUDY] = study

    def _populate_with_instance(self, instance, fields):
        accepted_fields = OBSERVATION_ALLOWED_FIELDS
        if (fields is not None and
                len(set(fields).intersection(accepted_fields)) == 0):
            msg = format_error_message('Passed fields are not allowed')
            raise ValidationError(msg)

        if ((fields is None or OBSERVATION_ID in fields) and
                instance.observation_id is not None):
            self.observation_id = instance.observation_id
        if ((fields is None or OBSERVATION_VARIABLE in fields) and
                instance.observation_unit is not None):
            self.observation_variable = instance.observation_variable.name
        if ((fields is None or OBSERVATION_UNIT in fields) and
                instance.observation_unit is not None):
            self.observation_unit = instance.observation_unit.name
        if (fields is None or VALUE in fields) and instance.value is not None:
            self.value = instance.value
        if (fields is None or OBSERVER in fields) and instance.observer is not None:
            self.observer = instance.observer
        if ((fields is None or OBSERVATION_CREATION_TIME in fields) and
                instance.creation_time is not None):
            self.creation_time = instance.creation_time.strftime(DATETIME_FORMAT)

        if ((fields is None or OBSERVATION_STUDY in fields) and
                instance.observation_unit is not None and
                instance.observation_unit.study is not None):
            self.study = instance.observation_unit.study.name
        if ((fields is None or ACCESSION in fields) and
                instance.observation_unit is not None and
                instance.observation_unit.accession is not None):
            self.accession = {INSTITUTE_CODE: instance.observation_unit.accession.institute.code,
                              GERMPLASM_NUMBER: instance.observation_unit.accession.germplasm_number}

        if instance.beauty_value and fields and VALUE_BEAUTY in fields:
            self.beauty_value = instance.beauty_value

    def to_list_representation(self, fields):
        items = []
        for field in fields:
            getter = OBSERVATION_VARIABLE_CSV_FIELD_CONFS.get(field)['getter']
            items.append(getter(self))
        return items

    def populate_from_csvrow(self, row):

        for field, value in row.items():
            if not value:
                continue
            field_conf = OBSERVATION_VARIABLE_CSV_FIELD_CONFS.get(field)

            if field_conf:
                setter = field_conf['setter']
                setter(self, value)


_OBSERVATION_VARIABLE_CSV_FIELD_CONFS = [
    {'csv_field_name': 'OBSERVATION_ID', 'getter': lambda x: x.observation_id,
     'setter': lambda obj, val: setattr(obj, 'observation_id', val)},
    {'csv_field_name': 'OBSERVATION_VARIABLE', 'getter': lambda x: x.observation_variable,
     'setter': lambda obj, val: setattr(obj, 'observation_variable', val)},
    {'csv_field_name': 'OBSERVATION_UNIT', 'getter': lambda x: x.observation_unit,
     'setter': lambda obj, val: setattr(obj, 'observation_unit', val)},
    {'csv_field_name': 'CREATION_TIME', 'getter': lambda x: x.creation_time,
     'setter': lambda obj, val: setattr(obj, 'creation_time', val)},
    {'csv_field_name': 'OBSERVER', 'getter': lambda x: x.observer,
     'setter': lambda obj, val: setattr(obj, 'observer', val)},
    {'csv_field_name': 'VALUE', 'getter': lambda x: x.value,
     'setter': lambda obj, val: setattr(obj, 'value', val)},
    {'csv_field_name': 'VALUE_BEAUTY', 'getter': lambda x: x.beauty_value,
     'setter': lambda obj, val: setattr(obj, 'beauty_value', val)},
    {'csv_field_name': 'STUDY', 'getter': lambda x: x.study,
     'setter': lambda obj, val: setattr(obj, 'study', val)},
    {'csv_field_name': 'ACCESSION',
     'getter': lambda x: '{}:{}'.format(x.accession[INSTITUTE_CODE],
                                        x.accession[GERMPLASM_NUMBER]),
     'setter': lambda obj, val: setattr(obj, 'accession', val)},
]
OBSERVATION_VARIABLE_CSV_FIELD_CONFS = OrderedDict([(f['csv_field_name'], f) for f in _OBSERVATION_VARIABLE_CSV_FIELD_CONFS])


def _get_or_create_observation_unit(struct, create_observation_unit):
    if not create_observation_unit and not struct.observation_unit:
        msg = 'No observation unit provided'
        raise ValueError(msg)
    elif struct.observation_unit:
        try:
            observation_unit = ObservationUnit.objects.get(name=struct.observation_unit)
        except ObservationUnit.DoesNotExist:
            msg = 'This observation Unit {} does not exist in db'
            msg = msg.format(struct.observation_unit)
            raise ValueError(msg)
    elif not struct.observation_unit and create_observation_unit == 'foreach_observation':
        try:
            study = Study.objects.get(name=struct.study)
        except Study.DoesNotExist:
            msg = 'Not able to get or create an observation unit with the given conf'
            msg += ' {} study not found'
            raise ValueError(msg.format(struct.study))
        try:
            accession = Accession.objects.get(germplasm_number=struct.accession[GERMPLASM_NUMBER],
                                              institute__code=struct.accession[INSTITUTE_CODE])
        except Accession.DoesNotExist:
            msg = 'Not able to get or create an observation unit with the given conf '
            msg += '{} accession not found'
            raise ValueError(msg.format(struct.accession[GERMPLASM_NUMBER]))

        random_name = uuid.uuid4()
        observation_unit = ObservationUnit.objects.create(study=study,
                                                          accession=accession,
                                                          level='whole plant',
                                                          name=random_name)
    else:
        msg = 'Not able to get or create an observation unit with the given conf'
        raise ValueError(msg)
    return observation_unit


def get_datetime_from_strdate(str_date):
    if not str_date:
        return None
    datetime.strftime(str_date, "")


def create_observation_in_db(api_data, user, conf=None):
    if conf is None:
        conf = {}
    create_observation_unit = conf.get(CREATE_OBSERVATION_UNITS, None)
    try:
        struct = ObservationStruct(api_data)
    except ObservationValidationError as error:
        print('a', error)
        raise
    try:
        observation_variable = ObservationVariable.objects.get(name=struct.observation_variable)
    except ObservationVariable.DoesNotExist:
        msg = 'Observation variable {} does not exist in db'
        msg = msg.format(struct.observation_variable)
        raise ValueError(msg)

    if struct.creation_time:
        timezone = pytz.timezone(TIME_ZONE)
        creation_time = timezone.localize(datetime.strptime(struct.creation_time,
                                                            DATETIME_FORMAT))
    else:
        creation_time = None
    try:
        values = validate_value(str(struct.value), observation_variable)
    except ValueError as error:
        if struct.observation_unit:
            error_row_id = struct.observation_unit
        elif struct.accession and struct.study:
            error_row_id = '{} - {}'.format(struct.accession[GERMPLASM_NUMBER],
                                            struct.study)
        else:
            error_row_id = 'Unknown'
        msg = '{}: {}'.format(error_row_id, error)
        raise ValidationError(msg)

    with transaction.atomic():
        observations = []
        for value in values:
            observation_unit = _get_or_create_observation_unit(struct, create_observation_unit)
            study_belongs_to_user = bool(user.groups.filter(name=observation_unit.study.group.name).count())

            if not study_belongs_to_user and not is_user_admin(user):
                msg = 'Can not add observation unit to a study you dont own: {}'
                msg = msg.format(observation_unit.study.group.name)
                raise ValueError(msg)

            try:
                observation = Observation.objects.create(
                    observation_variable=observation_variable,
                    observation_unit=observation_unit,
                    value=value,
                    observer=struct.observer,
                    creation_time=creation_time)
            except IntegrityError as error:
                if 'duplicate key value' in str(error):
                    msg = 'This observation already exists in db'
                    raise ValueError(msg)
                raise ValueError(str(error))
            observations.append(observation)

    # only when creating by bulk we would have more than one value.
    # In this cases the values are not returned. In most cases we can return
    # just the oly one observation

    if len(observations) == 1:
        return observations[0]

    return observations


def validate_value(value, observation_variable):
    scale = observation_variable.scale
    observation_variable
    values = []
    data_type = scale.data_type.name
    if ';' in value and data_type in (ORDINAL, NOMINAL):
        values = value.split(';')
    else:
        values = [value]

    for value in values:
        if data_type == NUMERICAL:
            float_value = float(value)
            if scale.min and float_value < scale.min:
                msg = 'Numericl value is less than minim: {} < {}'
                raise ValueError(msg.format(value, scale.min))
            elif scale.max and float_value > scale.max:
                msg = 'Numericl value is bigger than maxim: {} > {}'
                raise ValueError(msg.format(value, scale.max))
        else:
            valid_values = [valid['value'] for valid in scale.valid_values]
            if value not in valid_values:
                raise ValueError('{} not in valid_values'.format(value))
    return values


def update_observation_in_db(validated_data, instance, user):
    struct = ObservationStruct(api_data=validated_data)
    if struct.observation_id != instance.observation_id:
        msg = 'Can not change id in an update operation'
        raise ValidationError(format_error_message(msg))
    try:
        observation_variable = ObservationVariable.objects.get(name=struct.observation_variable)
    except ObservationVariable.DoesNotExist:
        msg = 'Observation variable {} does not exist in db'
        msg = msg.format(struct.observation_variable)
        raise ValueError(msg)
    try:
        observation_unit = ObservationUnit.objects.get(name=struct.observation_unit)
    except ObservationUnit.DoesNotExist:
        msg = 'Observation unit {} does not exist in db'
        msg = msg.format(struct.observation_unit)
        raise ValueError(msg)

    study_belongs_to_user = bool(user.groups.filter(name=observation_unit.study.group.name).count())
    if not study_belongs_to_user and not is_user_admin(user):
        msg = 'Can not change observation unit because this is in a study you dont own: {}'
        msg = msg.format(observation_unit.study.name)
        raise ValueError(msg)

    if struct.creation_time:
        timezone = pytz.timezone(TIME_ZONE)
        creation_time = timezone.localize(datetime.strptime(struct.creation_time,
                                                            DATETIME_FORMAT))
    else:
        creation_time = None

    instance.observation_variable = observation_variable
    instance.observation_unit = observation_unit
    instance.value = struct.value
    instance.observer = struct.observer
    instance.creation_time = creation_time

    instance.save()
    return instance
