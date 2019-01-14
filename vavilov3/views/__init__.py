DETAIL = 'detail'


def format_error_message(msg):
    if not isinstance(msg, (tuple, list)):
        msg = [msg]
    return {DETAIL: msg}
