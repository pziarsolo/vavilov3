import tempfile
from zipfile import is_zipfile, ZipFile
from rest_framework.exceptions import ValidationError
from vavilov3.entities.tags import INSTITUTE_CODE, GERMPLASM_NUMBER

ZIP_FILE = '/home/peio/devel/vavilov/vavilov3_dev/vavilov3/tests/data/images/images.zip'


def extract_files_from_zip(fhand, extract_path=tempfile.tempdir):
    if not is_zipfile(fhand.name):
        raise ValidationError('File must be a zipfile')
    zip_file = ZipFile(fhand.name)
    for member in zip_file.filelist:
        if member.is_dir():
            continue
        directory_tree = member.filename.split('/')
        study = directory_tree[-2]
        accession = directory_tree[-3]
        institute_code, germplasm_number = accession.split(':')
        image_path = zip_file.extract(member, path=extract_path)
        yield {'study': study, INSTITUTE_CODE: institute_code,
               GERMPLASM_NUMBER: germplasm_number, 'image_path': image_path}
