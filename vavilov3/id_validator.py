import re


def validate_id(code):
    errors = []
#     if re.search(' ', code):
#         errors.append('Can not use spaces inside ids')

#     if re.search('[a-z]', code):
#         errors.append('Ids must be all upper case')

    if re.search('[\/*"<>]', code):
        errors.append('"\", "/", "*", "<", ">", """ are not allowed characters')

#     if re.search('^[1-9]*$', code):
#         errors.append('Id can not be just a number')

    if errors:
        raise ValueError("{}: ".format(code) + "  ".join(errors))


def validate_name(name):
    errors = []
    if re.search('^[1-9]*$', name):
        errors.append('Id can not be just a number')

    if re.search('[\/*"<>]', name):
        errors.append('{}: "\\", "/", "*", "<", ">", """ are not allowed characters'.format(name))

    if errors:
        raise ValueError(" ".join(errors))

# validate_name('-')
#
# validate_name('asad asd')
