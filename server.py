import urllib
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

import os
from urllib.parse import urlparse

from email_sender import mime_text_factory, send_message


class Server(SimpleHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self.routes = {
            '/': self.handler,
            '/img': self.handler,
            '/css': self.handler,
            '/fonts/PT_Sans': self.handler,
        }
        super().__init__(request, client_address, server)

    def do_GET(self):
        request_dirname = self.request_dirname
        for route, func in self.routes.items():
            if route == request_dirname:
                func()

    def handler(self):
        path = self.request_path
        _, extension = os.path.splitext(path)
        file_type = extension.replace(".", "")

        if file_type == 'html':
            self.__read_text(file_type)
            query_dict = self.query_dict
            if path == '/index.html' and query_dict:
                address = os.environ.get('SMTP_SERVER')
                port = os.environ.get('SMTP_PORT')
                login = os.environ.get('LOGIN')
                password = os.environ.get('PASSWORD')

                receivers = os.environ.get('RECEIVERS').split(', ')
                subject = 'Simple test message'
                content = '\n'.join(f'{key}: {", ".join(value)}' for key, value in query_dict.items())

                message = mime_text_factory(login, receivers, subject, content)
                send_message(address, port, login, password, message, debug=os.environ.get('DEBUG') == 'True')

        elif file_type == 'css':
            self.__read_text(file_type)
        elif any((file_type == 'jpeg', file_type == 'jpg', file_type == 'png')):
            self.__read_data('image', file_type)
        elif file_type == 'woff2':
            self.__read_data('font', file_type)

    def __read_text(self, file_type):
        self.protocol_version = 'HTTP/1.1'
        self.send_response(200, 'OK')
        self.send_header('content-type', f'text/{file_type}')
        self.end_headers()

        with open(self.request_path[1:], encoding='utf-8') as handle:
            self.wfile.write(bytes(handle.read(), 'UTF-8'))

    def __read_data(self, data_type, file_type):
        path = self.request_path[1:]
        with open(path, 'rb') as handle:
            file = handle.read()

            self.protocol_version = 'HTTP/1.1'
            self.send_response(200, 'OK')
            self.send_header('content-type', f'{data_type}/{file_type}')
            self.send_header('content-length', os.stat(path).st_size)
            self.end_headers()

            self.wfile.write(file)

    @property
    def request_dirname(self):
        return os.path.dirname(self.__request_path)

    @property
    def request_basename(self):
        return os.path.basename(self.__request_path) or 'index.html'

    @property
    def __request_path(self):
        return urlparse(self.path).path

    @property
    def request_path(self):
        return os.path.join(self.request_dirname, self.request_basename)

    @property
    def query_dict(self):
        return urllib.parse.parse_qs(urlparse(self.path).query, keep_blank_values=True)


def main():
    ip = os.environ.get('SERVER_IP', '127.0.0.1')
    port = int(os.environ.get('SERVER_PORT', 80))
    server = TCPServer((ip, port), Server)
    server.serve_forever()


if __name__ == "__main__":
    main()
