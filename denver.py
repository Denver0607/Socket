# Please use this file to test our proxy server.
# This file doesn't use OOP style. It suitable for us to understand the logic of proxy server.
import socket
import os
from os import stat
from threading import Thread, enumerate
from datetime import datetime
from os.path import isfile, join
from mimetypes import guess_type

CACHE_DIRECTORY = "cache"
CONFIG_FILE = "config.ini"
FORBIDDEN_PAGE = "403.html"
NOT_FOUND_PAGE = "404.html"

def receive_data(client_socket):
    data = client_socket.recv(4096)
    return data

def parse_request(request):
    lines = request.split(b"\r\n")
    if not lines:
        return None, None
    
    str_lines = lines[0].decode("utf8").split(' ')

    method = str_lines[0]
    if len(str_lines) > 1:
        url =  str_lines[1] 
    else:
        url = ""
    return method, url

def get_content_length(request):
    content_length_header = b"Content-Length: "
    index = request.find(content_length_header)
    if index != -1:
        end_index = request.find(b"\r\n", index + len(content_length_header))
        content_length = request[index + len(content_length_header):end_index].strip()
        return int(content_length)
    return 0

def receive_request_body(client_socket, content_length):
    return client_socket.recv(content_length)

def send_response(client_socket, response):
    try:
        client_socket.sendall(response)
    except ConnectionAbortedError:
        pass

def send_forbidden_response(client_socket):
    response_content = b""
    with open(FORBIDDEN_PAGE, "rb") as file:
        response_content = file.read()

    response = b"HTTP/1.1 403 Forbidden\r\n"
    response += b"Content-Type: text/html\r\n"
    response += b"Content-Length: " + str(len(response_content)).encode() + b"\r\n"
    response += b"\r\n"
    response += response_content

    send_response(client_socket, response)

def send_not_found_response(client_socket):
    response_content = b""
    with open(NOT_FOUND_PAGE, "rb") as file:
        response_content = file.read()

    response = b"HTTP/1.1 404 Not Found\r\n"
    response += b"Content-Type: text/html\r\n"
    response += b"Content-Length: " + str(len(response_content)).encode() + b"\r\n"
    response += b"\r\n"
    response += response_content

    send_response(client_socket, response)

def is_whitelisted(url):
    # Implement whitelisting logic from the config file
    # Return True if URL is whitelisted, otherwise False
    return False

def is_time_allowed():
    # Implement time-based access restrictions from the config file
    # Return True if access is allowed, otherwise False
    return True

def get_file_size(resource):
    """
    This method gets the size of the resource.
    :param resource: resource to get size from
    :return: the file size as an integer
    """

    file_size = 0
    if isfile(resource):
        file_size = stat(resource).st_size

    return file_size


def read_file(file):
    """
    This method reads the bytes from the resource and returns it.
    :param file: the resource to read bytes from
    :return: the read file as a bytes object
    """

    file_data = b''

    if get_file_size(file):
        res = open(file, 'r+b')

        for i in range(get_file_size(file)):
            file_data += res.read()

    return file_data

def get_mime_type(file):
    """
    This method gets the MIME type of the requested file.
    :param file: file to get MIME type from
    :return: the MIME type of the file
    """

    mime_type = b'text/html'

    if get_file_size(file) > 0:
        mime_type_and_encoding = guess_type(file)
        if mime_type_and_encoding[0] is not None:
            mime_type = mime_type_and_encoding[0].encode('ASCII')
            
    return mime_type

def get_response_headers(file):
    response_headers = []

    timestamp = datetime.utcnow()
    date = timestamp.strftime('%a, %d %b %Y %H:%M:%S GMT')
    response_headers.append(b'Date: ' + date.encode('ASCII') + b'\r\n')

    content_length = get_file_size(file)
    response_headers.append(b'Content-Length: ' + str(content_length).encode('ASCII') + b'\r\n')

    response_headers.append(b'Content-Type: ' + get_mime_type(file) + b'\r\n')
    response_headers.append(b'Connection: close\r\n')

    return response_headers

def get_status_line(file_size):
    """
    This method returns the status line for the HTTP response based on the file size.
    :param file_size: the size of the requested file
    :return: the status line as a bytes object
    """

    status_line = b'HTTP/1.1 '

    if file_size > 0:
        status_line += b'200 OK\r\n'
    else:
        status_line += b'404 Not Found\r\n'

    return status_line

# def handle_get_request(client_socket, url):
#     url = url[1:]
#     if url == '':
#         url = 'index.html'
        
#     file = join('url',url)
    
#     file_size = get_file_size(file)
#     http_response = get_status_line(file_size)
    
#     response_headers= get_response_headers(file)
#     print(response_headers)
    
#     for response_header in response_headers:
#         http_response +=  response_header
        
#     http_response+= b'\r\n'
#     http_response += read_file(file)
    
#     client_socket.sendall(http_response)

def handle_get_request(client_socket, url):
    url = url[1:]
    if url == '':
        url = 'index.html'
        
    file = os.path.join('url', url)
    http_response=b''
    
    if os.path.isfile(file):
        file_size = get_file_size(file)
        http_response = get_status_line(file_size)
        
        response_headers = get_response_headers(file)
        for response_header in response_headers:
            http_response += response_header
            
        http_response += b'\r\n'
        http_response += read_file(file)
    else:
        send_not_found_response(client_socket)
    
    client_socket.sendall(http_response)
    
def handle_post_request(client_socket, url, request, content_length):
    # ... (same implementation as before)
    pass

def handle_head_request(client_socket, url):
    # ... (same implementation as before)
    pass

def handle_request(client_socket):
    request = receive_data(client_socket)
    method, url = parse_request(request)

    print(method)
    print(url)
    content_length = get_content_length(request)
    
    if method and url and is_whitelisted(url) and is_time_allowed():
        if method == "GET":
            handle_get_request(client_socket, url)
        elif method == "POST":
            handle_post_request(client_socket, url, request, content_length)
        elif method == "HEAD":
            handle_head_request(client_socket, url)
        else:
            # Unsupported method, return 403 Forbidden
            send_forbidden_response(client_socket)
    else:
        # URL not whitelisted or access not allowed, return 403 Forbidden
        send_forbidden_response(client_socket)

    client_socket.close()

def read_config():
    # Read and parse the configuration file
    # Implement configuration file parsing logic and return settings
    pass

def main():
    # if not os.path.exists(CACHE_DIRECTORY):
    #     os.mkdir(CACHE_DIRECTORY)

    settings = read_config()

    proxy_host = "127.0.0.1"
    proxy_port = 8888

    proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_server.bind((proxy_host, proxy_port))
    proxy_server.listen(5)

    print(f"Proxy server is listening on {proxy_host}:{proxy_port}")

    try:
        while True:
            client_socket, client_address = proxy_server.accept()
            # print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
            # chunk = client_socket.recv(4096)
            # chunk = receive_data(client_socket)
            # print("main request: ")
            # print(chunk.decode("utf8"))
            # print(client_socket.getsockname)
            handle_request(client_socket)
            print(1)
            # proxy_server.close()
            # threading.Thread(target=handle_request, args=(client_socket,)).start()
    except KeyboardInterrupt:
        print("Proxy server stopped.")
    finally:
        proxy_server.close()

main()
    

