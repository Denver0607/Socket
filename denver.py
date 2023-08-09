# Please use this file to test our proxy server.
# This file doesn't use OOP style. It suitable for us to understand the logic of proxy server.
import socket
import os
import time
from threading import Thread, enumerate
from datetime import datetime
from mimetypes import guess_type

# CACHE_DIRECTORY = "cache"
cache = {}
CONFIG_FILE = "config.ini"
FORBIDDEN_PAGE = "403.html"
NOT_FOUND_PAGE = "404.html"
BUFFER_SIZE = 4096

def receive_data(client_socket):
    data = b""
    while True:
        chunk = client_socket.recv(BUFFER_SIZE)
        if not chunk:
            break
        data += chunk
        if len(chunk) < BUFFER_SIZE:
            break
    return data

def parse_request(request):
    lines = request.split(b"\r\n")
    if not lines:
        return None, None, None
    str_line = lines[0].decode().split(' ')
    # print(str_lines)
    method = str_line[0]
    url =  str_line[1]
    protocol_version = str_line[2]
    str_line.clear()
    if (url == "http://detectportal.firefox.com/canonical.html" or url == "http://r3.o.lencr.org/" or url == "http://ocsp.digicert.com/" or url == "http://ocsp.pki.goog/gts1c3"):
        return method, None, None
    return method, url, protocol_version

# def get_content_length(request):
#     content_length_header = b"Content-Length: "
#     index = request.find(content_length_header)
#     if index != -1:
#         end_index = request.find(b"\r\n", index + len(content_length_header))
#         content_length = request[index + len(content_length_header):end_index].strip()
#         return int(content_length)
#     return 0

# def receive_request_body(client_socket, content_length):
#     return client_socket.recv(content_length)

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
    return True

def is_time_allowed():
    # Implement time-based access restrictions from the config file
    # Return True if access is allowed, otherwise False
    return True

# def get_file_size(resource):
#     file_size = 0
#     # a=isfile(resource)
#     # if isfile(resource):
#     file_size = os.stat(resource).st_size

#     return file_size


# def read_file(file):
#     file_data = b''

#     if get_file_size(file):
#         res = open(file, 'r+b')

#         for i in range(get_file_size(file)):
#             file_data += res.read()

#     return file_data

# def get_mime_type(file):
#     mime_type = b'text/html'

#     if get_file_size(file) > 0:
#         mime_type_and_encoding = guess_type(file)
#         if mime_type_and_encoding[0] is not None:
#             mime_type = mime_type_and_encoding[0].encode('ASCII')
            
#     return mime_type

# def get_response_headers(file):
#     response_headers = []

#     timestamp = datetime.utcnow()
#     date = timestamp.strftime('%a, %d %b %Y %H:%M:%S GMT')
#     response_headers.append(b'Date: ' + date.encode('ASCII') + b'\r\n')

#     content_length = get_file_size(file)
#     response_headers.append(b'Content-Length: ' + str(content_length).encode('ASCII') + b'\r\n')

#     response_headers.append(b'Content-Type: ' + get_mime_type(file) + b'\r\n')
#     response_headers.append(b'Connection: close\r\n')

#     return response_headers

# def get_status_line(file_size):
#     status_line = b'HTTP/1.1 '

#     if file_size > 0:
#         status_line += b'200 OK\r\n'
#     else:
#         status_line += b'404 Not Found\r\n'

#     return status_line

def handle_get_request(client_socket, url):
    a = url in cache
    if url in cache:
        cached_data = cache[url]
        response = f"HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\nContent-Length: {len(cached_data)}\r\n\r\n{cached_data}"
        client_socket.send(response.encode("utf-8"))
    else:
        # Fetch the image from the web server
        # Replace 'web_server_address' with the actual address
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect(("web_server_address", 80))
        server_socket.send(f"GET {url} HTTP/1.1\r\nHost: web_server_address\r\n\r\n".encode("utf-8"))

        response = b""
        while True:
            chunk = server_socket.recv(BUFFER_SIZE)
            if not chunk:
                break
            response += chunk
        server_socket.close()

        # Cache the image and update cache timestamp
        cache[url] = response
        cache[url + "_timestamp"] = time.time()

        response = f"HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\nContent-Length: {len(response)}\r\n\r\n"
        response = response.encode("utf-8") + response
        client_socket.send(response)
        

def handle_post_request(client_socket, url, request, content_length):
    response_body = "This is a POST request response."
    response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(response_body)}\r\n\r\n{response_body}"
    client_socket.send(response.encode("utf-8"))

    client_socket.close()
    pass

def handle_head_request(client_socket, url):
    if url in cache:
        cached_data = cache[url]
        content_length = len(cached_data)
        response = f"HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\nContent-Length: {content_length}\r\n\r\n"
        client_socket.send(response.encode("utf-8"))
    else:
        # Fetch the image from the web server
        # Replace 'web_server_address' with the actual address
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect(("web_server_address", 80))
        server_socket.send(f"GET {url} HTTP/1.1\r\nHost: web_server_address\r\n\r\n".encode("utf-8"))

        response = b""
        while True:
            chunk = server_socket.recv(BUFFER_SIZE)
            if not chunk:
                break
            response += chunk
        server_socket.close()

        # Cache the image and update cache timestamp
        cache[url] = response
        cache[url + "_timestamp"] = time.time()

        content_length = len(response)
        response = f"HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\nContent-Length: {content_length}\r\n\r\n"
        client_socket.send(response.encode("utf-8"))

    client_socket.close()
    pass

def handle_request(client_socket):
    request = receive_data(client_socket)
        
    method, url, protocol_version = parse_request(request)
    if method == None:
        return
    print("------------HTTP REQUEST------------")
    print(f"{method} {url} {protocol_version}")
    print("Host:", url)
    #content_length = get_content_length(request)
    
    if method and url and is_whitelisted(url) and is_time_allowed():
        if url != None:
            if method == "GET":
                handle_get_request(client_socket, url)
            #elif method == "POST":
                #handle_post_request(client_socket, url, request, content_length)
            elif method == "HEAD":
                handle_head_request(client_socket, url)
            else:
                # Unsupported method, return 403 Forbidden
                send_forbidden_response(client_socket)
        else:
            # URL not specified, return 404 Not Found
            send_not_found_response(client_socket)
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
            # chunk = client_socket.recv(4096)
            # chunk = receive_data(client_socket)
            # print("main request: ")
            # print(chunk.decode("utf8"))
            # print(client_socket.getsockname)
            handle_request(client_socket)
            # proxy_server.close()
            # threading.Thread(target=handle_request, args=(client_socket,)).start()
    except KeyboardInterrupt:
        print("Proxy server stopped.")
    finally:
        proxy_server.close()

main()
    

