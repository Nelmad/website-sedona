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
        # print("\n----- Request Start ----->\n")
        # print(self.path)
        # print(self.request_path)
        # print(self.headers)
        # print("<----- Request End -----\n")

        request_dirname = self.request_dirname
        for route, func in self.routes.items():
            if route == request_dirname:
                func()

    def handler(self):
        path = self.request_path
        _, extension = os.path.splitext(path)
        file_type = extension.replace(".", "")

        if self.headers.get('Referer') is None:
            self.__read_text(file_type)

            query_dict = self.query_dict
            if path == '/index.html' and query_dict:
                address = os.environ.get('SMTP_SERVER')
                port = os.environ.get('SMTP_PORT')
                login = os.environ.get('LOGIN')
                password = os.environ.get('PASSWORD')

                receivers = os.environ.get('RECEIVERS').split(', ')
                subject = 'Simple test message'
                content = '\n'.join(f'{key}: {value}' for key, value in query_dict.items())

                message = mime_text_factory(login, receivers, subject, content)
                send_message(address, port, login, password, message)

        else:
            if file_type == 'css':
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
        return self.query_to_dict(urlparse(self.path).query)

    @staticmethod
    def query_to_dict(query_string):
        result = {}
        for token in (item for item in query_string.split('&') if item):
            pair = token.split('=', 1)
            result[pair[0]] = pair[1]
        return result


def main():
    port = 5125
    server = TCPServer(('127.0.0.1', port), Server)
    server.serve_forever()


if __name__ == "__main__":
    main()
