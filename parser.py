import datetime
import os
import urllib.parse

from http_codes import ANSWER_CODES, OK, BAD_REQUEST, FORBIDDEN, NOT_FOUND


CONTENT_TYPES = {
    'html': 'text/html',
    'css': 'text/css',
    'js': 'application/javascript',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'swf': 'application/x-shockwave-flash'
}
DEFAULT_PAGE = 'index.html'
DEFAULT_ENCODING = 'utf-8'
HTTP_V = 'HTTP/1.1'
SERVER_NAME = 'Morelia'
SUPPORTED_HEADERS = ['GET', 'HEAD']


def response_ok(**kwargs):
    apppend_file = kwargs.get('file') if kwargs.get('file') else b''
    return (
        '{http_type} {code} {code_val}\r\n'
        'Date: {date}\r\n'
        'Server: {server_name}\r\n'
        'Content-Length: {content_length}\r\n'
        'Content-Type: {content_type}\r\n'
        'Connection: Closed\r\n\r\n'
    ).format(server_name=SERVER_NAME, http_type=HTTP_V, **kwargs).encode() + apppend_file


def response_bad(**kwargs):
    return (
        '{http_type} {code} {code_val}\r\n'
        'Date: {date}\r\n'
        'Server: {server_name}\r\n'
        'Connection: Closed\r\n\r\n'
    ).format(server_name=SERVER_NAME, http_type=HTTP_V, **kwargs).encode()


def response_builder(code, file=None, file_path=None, is_head=False):
    code_val = ANSWER_CODES.get(code)
    date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    content_length = len(file) if file else 0
    file = None if is_head else file
    try:
        expansion = file_path.rsplit('.').pop() if file_path else None
        content_type = \
            CONTENT_TYPES.get(expansion, 'application/octet-stream') \
            if file_path else 'application/octet-stream'

    except Exception:
        return response_builder(NOT_FOUND)

    if code == OK:
        return response_ok(
            code=code, code_val=code_val, date=date,
            content_length=content_length,
            content_type=content_type, file=file)
    return response_bad(code=code, code_val=code_val, date=date)


def parser(request, doc_root):
    split_request = request.splitlines()[0]
    try:
        request_type, path, protocol = split_request.split(' ')
    except Exception:
        return response_builder(BAD_REQUEST)

    if request_type not in SUPPORTED_HEADERS:
        return response_builder(BAD_REQUEST)

    path = path_checker(path)
    if '../' in path:
        return response_builder(FORBIDDEN)

    whole_path = os.path.join(doc_root, path)
    if os.path.isdir(whole_path):
        whole_path = os.path.join(whole_path, DEFAULT_PAGE)
        if not os.path.exists(whole_path):
            return response_builder(FORBIDDEN)

    if os.path.exists(whole_path):
        with open(whole_path, 'rb') as handle:
            file = handle.read()
            is_head = False
            if request_type == 'HEAD':
                is_head = True
            return response_builder(OK, file, whole_path, is_head)
    return response_builder(NOT_FOUND)


def path_checker(path):
    new_path = path.split('?')[0]
    new_path = urllib.parse.unquote(new_path)
    while '/' is new_path[0] and len(new_path) > 1:
        new_path = new_path[1:]
    return new_path
