# Please use this file to test our proxy server.
# This file doesn't use OOP style. It suitable for us to understand the logic of proxy server.
import socket
import threading
import os
import datetime
from urllib.parse import urlparse

CACHE_DIRECTORY = "cache"
CONFIG_FILE = "config.ini"
FORBIDDEN_PAGE = "403.html"
NOT_FOUND_PAGE = "404.html"

def receive_data(client_socket):
    data = b""
    while True:
        chunk = client_socket.recv(4096)
        if not chunk:
            break
        data += chunk
    return data

def parse_request(request):
    lines = request.split(b"\r\n")
    if not lines:
        return None, None

    # Extract HTTP method and URL from the first line of the request
    method, url, _ = lines[0].split(b" ")
    return method.decode(), url.decode()

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
    return True

def is_time_allowed():
    # Implement time-based access restrictions from the config file
    # Return True if access is allowed, otherwise False
    return True

def handle_get_request(client_socket, url):
    # ... (same implementation as before)
    pass

def handle_post_request(client_socket, url, request, content_length):
    # ... (same implementation as before)
    pass

def handle_head_request(client_socket, url):
    # ... (same implementation as before)
    pass

def handle_request(client_socket):
    request = receive_data(client_socket)
    method, url = parse_request(request)
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
    if not os.path.exists(CACHE_DIRECTORY):
        os.mkdir(CACHE_DIRECTORY)

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
            print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
            threading.Thread(target=handle_request, args=(client_socket,)).start()
    except KeyboardInterrupt:
        print("Proxy server stopped.")
        proxy_server.close()

if __name__ == "__main__":
    main()
