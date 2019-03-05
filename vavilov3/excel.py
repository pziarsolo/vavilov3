import xlrd


def excel_dict_reader(fhand, sheet_name=None):
    if isinstance(fhand, str):
        book = xlrd.open_workbook(filename=fhand)
    else:
        book = xlrd.open_workbook(file_contents=fhand.read())

    if sheet_name:
        sheet = book.sheet_by_name(sheet_name)
    else:
        sheet = book.sheets()[0]

    header = [header.value for header in sheet.row(0)]

    first = True
    for row in sheet.get_rows():
        if first:
            first = False
            continue
        rowcells = [cell for cell in row]
        yield dict(zip(header, rowcells))
