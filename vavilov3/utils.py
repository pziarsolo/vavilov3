from zipfile import is_zipfile, ZipFile

from vavilov3.entities.tags import INSTITUTE_CODE, GERMPLASM_NUMBER


def extract_files_from_zip(fhand, extract_dir=None):
    try:
        fpath = fhand.name
    except AttributeError:
        raise ValueError('File must be a zipfile')

    if not is_zipfile(fpath):
        raise ValueError('File must be a zipfile')
    zip_file = ZipFile(fpath)
    for member in zip_file.filelist:
        if member.is_dir():
            continue
        directory_tree = member.filename.split('/')
        try:
            study = directory_tree[-2]
            accession = directory_tree[-3]
            institute_code, germplasm_number = accession.split(':', 1)
        except (IndexError, ValueError):
            raise ValueError("The zip file's Directory tree is wrong!")

        image_path = zip_file.extract(member, path=extract_dir)
        yield {'study': study, INSTITUTE_CODE: institute_code,
               GERMPLASM_NUMBER: germplasm_number, 'image_path': image_path}
