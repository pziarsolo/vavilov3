import json
from vavilov3.serializers.institute import create_institute_in_db


def load_institutes_from_file(fpath):
    fhand = open(fpath)
    institutes = json.load(fhand)

    for institute in institutes:
        create_institute_in_db(institute)
