import os
import datetime
import urllib.parse

import traceback
answer_codes = {
    200: 'OK',
    400: 'Bad Request',
    403: 'Forbidden',
    404: 'Not Found'
}
content_types = {
    'html': 'text/html',
    'css': 'text/css',
    'js': 'application/javascript',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'swf': 'application/x-shockwave-flash'
}
http_type = 'HTTP/1.1'
supported_types = ['GET', 'HEAD']


def response_ok(**kwargs):
    apppend_file = kwargs.get('file') if kwargs.get('file') else b''
    return (
        '{http_type} {code} {code_val}\r\n'
        'Date: {date}\r\n'
        'Server: Lera\r\n'
        'Content-Length: {content_length}\r\n'
        'Content-Type: {content_type}\r\n'
        'Connection: Closed\r\n\r\n'
    ).format(**kwargs, http_type=http_type).encode() + apppend_file


def response_bad(**kwargs):
    return (
        '{http_type} {code} {code_val}\r\n'
        'Date: {date}\r\n'
        'Server: Lera\r\n'
        'Connection: Closed\r\n\r\n'
    ).format(**kwargs, http_type=http_type).encode()


def response_builder(code, file=None, file_path=None, is_head=False):
    code_val = answer_codes.get(code)
    date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    content_length = len(file) if file else 0
    if is_head:
        file = None
    try:
        extention = file_path.rsplit('.')[-1] if file_path else None
        content_type = content_types.get(
            file_path.rsplit('.', 1)[1], 'unknown') if file_path else 'unknown'
    except Exception as e:
        print(traceback.print_tb(e.__traceback__))
        print(e)
        return response_builder(404)

    if code == 200:
        return response_ok(
            code=code, code_val=code_val, date=date,
            content_length=content_length,
            content_type=content_type, file=file)
    else:
        return response_bad(code=code, code_val=code_val, date=date)


def parser(request, doc_root):
    splitted = request.splitlines()
    try:
        request_type, path, protocol = splitted[0].rsplit(' ')
    except Exception:
        return response_builder(400)

    path = path.split('?')[0]
    path = urllib.parse.unquote(path)
    if request_type not in supported_types:
        return response_builder(400)

    whole_request = {}
    for kv in splitted[1:-2]:
        key, val = kv.rsplit(': ')
        whole_request[key] = val
    # print(request_type, path, protocol, whole_request)

    if path.startswith('/'):
        path = path[1:]
    if '../' in path:
        return response_builder(403)

    whole_path = os.path.join(doc_root, path)
    if os.path.isdir(whole_path):
        whole_path = os.path.join(whole_path, 'index.html')
        if not os.path.exists(whole_path):
            return response_builder(403)

    if os.path.exists(whole_path):
        with open(whole_path, 'rb') as handle:
            file = handle.read()
            is_head = False
            if request_type == 'HEAD':
                is_head = True
            return response_builder(200, file, whole_path, is_head)
    return response_builder(404)
