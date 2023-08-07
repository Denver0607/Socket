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
    # print("receive_data: ")
    # print(client_socket.getsockname)
    # print(0)
    data = client_socket.recv(4096)
    # print(data.decode("utf8"))
    # print(1)
    return data

def parse_request(request):
    # print("parse_request: ")
    # print(request.decode("utf8"))
    # print(5)
    lines = request.split(b"\r\n")
    if not lines:
        return None, None

    # Extract HTTP method and URL from the first line of the request
    # print("lines[0]: ")
    str_lines = lines[0].decode("utf8").split(' ')
    # print(str_lines)
    method = str_lines[0]
    url =  str_lines[1]
    return method, url

def get_content_length(request):
    content_length_header = b"Content-Length: "
    index = request.find(content_length_header)
    if index != -1:
        end_index = request.find(b"\r\n", index + len(content_length_header))
        content_length = request[index + len(content_length_header):end_index].strip()
        return int(content_length)
    return 0

def get_cached_data(url):
    #Create the cache directory if it doesn't exist
    if not os.path.exists(CACHE_DIRECTORY):
        os.mkdir(CACHE_DIRECTORY)

    cache_filename = os.path.join(CACHE_DIRECTORY, url.replace("/", "_"))

    try:
        # Check if the data is cached and still valid
        if os.path.exists(cache_filename):
            # Get the last modified time of the cached file
            cache_modified_time = os.path.getmtime(cache_filename)
            current_time = datetime.datetime.now().timestamp()
            # Calculate the age of the cached data in seconds
            cache_age = current_time - cache_modified_time

            # Cache expiration time in seconds (eg: 2min)
            cache_expiration_time = 120

            # If the cached data is still valid, read and return it
            if cache_age < cache_expiration_time:
                with open(cache_filename, "rb") as file:
                    cached_data = file.read()
                print(1)
                return cached_data
            else:
                # If the cached data is expired, remove the cache file
                os.remove(cache_filename)

    except Exception as e:
        # Handle any potential errors when accessing or reading the cache file
        print(f"Error while accessing cached data: {e}")
    print(cache_filename)
    return None

def extract_hostname_and_path(url):
    # Remove the scheme (e.g., 'https://') from the URL
    url_without_scheme = url.split('://', 1)[-1]

    # Find the first slash to separate the hostname from the path
    slash_index = url_without_scheme.find('/')
    if slash_index == -1:
        # If there is no slash, the entire URL is the hostname
        return url_without_scheme, '/'
    else:
        # Extract the hostname and path components
        hostname = url_without_scheme[:slash_index]
        path = url_without_scheme[slash_index:]
        return hostname, path

def download_image(url, save_path):
    # Extract the hostname and path from the URL
    hostname, path = extract_hostname_and_path(url)

    # Open a connection to the server
    conn = hostname
    conn.request('GET', path)

    # Get the response from the server
    response = conn.getresponse()

    # Check if the response is successful (status code 200)
    if response.status == 200:
        # Read the image data
        image_data = response.read()

        # Save the image to the specified file path
        with io.open(save_path, 'wb') as f:
            f.write(image_data)

        print(f"Image downloaded and saved to {save_path}")
    else:
        print(f"Failed to download image. Status code: {response.status}")

    # Close the connection
    conn.close()

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
    # print(client_socket.getsockname)
    # print(2)
    request = receive_data(client_socket)
    # print("request: ")
    # print(request.decode("utf8"))
    # print(3)
    method, url = parse_request(request)
    print(method)
    print(url)
    content_length = get_content_length(request)
    get_cached_data(url)
    if method and url and is_whitelisted(url) and is_time_allowed():
        if method == "GET":
            host_name = 'example.com'
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
    settings = read_config()

    proxy_host = "127.0.0.1"
    proxy_port = 10000

    proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_server.bind((proxy_host, proxy_port))
    proxy_server.listen(1)

    print(f"Proxy server is listening on {proxy_host}:{proxy_port}")

    try:
        while True:
            client_socket, client_address = proxy_server.accept()
            print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
            # chunk = client_socket.recv(4096)
            # chunk = receive_data(client_socket)
            # print("main request: ")
            # print(chunk.decode("utf8"))
            # print(client_socket.getsockname)
            handle_request(client_socket)
            print(4)
            # proxy_server.close()
            # threading.Thread(target=handle_request, args=(client_socket,)).start()
    except KeyboardInterrupt:
        print("Proxy server stopped.")
        proxy_server.close()
    finally:
        proxy_server.close()

if __name__ == "__main__":
    main()

