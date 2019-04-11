import os
import subprocess
from zipfile import is_zipfile, ZipFile

from vavilov3.entities.tags import INSTITUTE_CODE, GERMPLASM_NUMBER


def extract_files_from_zip(fhand, extract_dir=None, make_group_writable=False):
    if not is_zipfile(fhand):
        raise ValueError('File must be a zipfile')
    zip_file = ZipFile(fhand)
    for member in zip_file.filelist:
        try:
            # this.method exists strting in python 3.6
            is_dir = member.is_dir()
        except AttributeError:
            is_dir = member.filename.endswith('/')

        if is_dir:
            continue
        directory_tree = member.filename.split('/')
        try:
            study = directory_tree[-2]
            accession = directory_tree[-3]
            institute_code, germplasm_number = accession.split(':', 1)
        except (IndexError, ValueError):
            raise ValueError("The zip file's Directory tree is wrong!")

        image_path = zip_file.extract(member, path=extract_dir)
        if make_group_writable:
            extract_dir2 = extract_dir
            for tree_leaf in directory_tree:
                extract_dir2 = os.path.join(extract_dir2, tree_leaf)
                subprocess.run(['chmod', 'g+w', extract_dir2])
                subprocess.run(['chmod', 'g+s', extract_dir2])

        yield {'study': study, INSTITUTE_CODE: institute_code,
               GERMPLASM_NUMBER: germplasm_number, 'image_path': image_path}
