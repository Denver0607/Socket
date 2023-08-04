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

class ProxyHandler:
    def __init__(self, client_socket, client_address):
        self.client_socket = client_socket
        self.client_address = client_address
        
    def handle_request(self):
        request = receive_data(self.client_socket)
        method, url = self.parse_request(request)
        content_length = self.get_content_length(request)

        if method and url and self.is_whitelisted(url) and self.is_time_allowed():
        # if method:
            if method == "GET":
                self.handle_get_request(url)
            elif method == "POST":
                self.handle_post_request(url, request, content_length)
            elif method == "HEAD":
                self.handle_head_request(url)
            else:
                # Unsupported method, return 403 Forbidden
                self.send_forbidden_response()
        else:
            # URL not whitelisted or access not allowed, return 403 Forbidden
            self.send_forbidden_response()

        self.client_socket.close()

    def parse_request(self, request):
        lines = request.split(b"\r\n")
        if not lines:
            return None, None

        # Extract HTTP method and URL from the first line of the request
        method, url, _ = lines[0].split(b" ")

        return method.decode(), url.decode()


    def get_content_length(self, request):
        content_length_header = b"Content-Length: "
        index = request.find(content_length_header)
        if index != -1:
            end_index = request.find(b"\r\n", index + len(content_length_header))
            content_length = request[index + len(content_length_header):end_index].strip()
            return int(content_length)
        return 0

    def receive_request_body(self, content_length):
        # Receive the request body with the given content length
        return self.client_socket.recv(content_length)

    def is_whitelisted(self, url):
        # Implement whitelisting logic from the config file
        # Return True if URL is whitelisted, otherwise False
        return True

    def is_time_allowed(self):
        # Implement time-based access restrictions from the config file
        # Return True if access is allowed, otherwise False
        return True
    
    def handle_get_request(self, url):
        cached_data = self.get_cached_data(url)
        if cached_data:
            # Send cached data back to the client
            self.send_cached_response(cached_data)
        else:
            # Forward the GET request to the web server
            response = self.forward_request("GET", url, b"")
            if response:
                if response.startswith(b"HTTP/1.1 404"):
                    # Web server returned a 404 error, send custom 404 Not Found page
                    self.send_not_found_response()
                else:
                    # Cache the response and send it back to the client
                    self.cache_response(url, response)
                    self.send_response(response)
            else:
                # Web server returned an error, send 404 Not Found
                self.send_not_found_response()

    def handle_post_request(self, url, request, content_length):
        request_body = self.receive_request_body(content_length)
        response = self.forward_request("POST", url, request, request_body)
        if response:
            # Cache the response and send it back to the client
            self.cache_response(url, response)
            self.send_response(response)
        else:
            # Web server returned an error, send 404 Not Found
            self.send_not_found_response()

    def handle_head_request(self, url):
        response = self.forward_request(method, url, request)
        if response:
            self.send_response(response)
        else:
            # Web server returned an error, send 404 Not Found
            self.send_not_found_response()      
    
    def get_cached_data(self, url):
        # Check if the URL is cached and not expired, return cached data if available
        # Otherwise, return None
        return None

    def cache_response(self, url, response):
        # Cache the response data for the given URL
        # Save the data in the cache directory with a unique filename
        pass

    def forward_request(self, method, url, request, body=None):
        # Implement forwarding logic for GET, POST, and HEAD requests
        # Use the 'socket' module to create a new connection to the web server
        # Forward the request and receive the response from the web server
        pass

    def send_response(self, response):
        # Send the received response from the web server back to the client
        # Use the client socket to send the response data
        pass

    def send_cached_response(self, cached_data):
        # Send the cached data back to the client as the response
        # Use the client socket to send the response data
        pass

    def send_forbidden_response(self):
        # Respond with 403 Forbidden and the content of the custom 403.html page
        response_content = b""
        with open(FORBIDDEN_PAGE, "rb") as file:
            response_content = file.read()

        response = b"HTTP/1.1 403 Forbidden\r\n"
        response += b"Content-Type: text/html\r\n"
        response += b"Content-Length: " + str(len(response_content)).encode() + b"\r\n"
        response += b"\r\n"
        response += response_content

        self.client_socket.sendall(response)

    def send_not_found_response(self):
        # Respond with 404 Not Found and the content of the custom 404.html page
        response_content = b""
        with open(NOT_FOUND_PAGE, "rb") as file:
            response_content = file.read()

        response = b"HTTP/1.1 200 Not Found\r\n"
        response += b"Content-Type: text/html\r\n"
        response += b"Content-Length: " + str(len(response_content)).encode() + b"\r\n"
        response += b"\r\n"
        response += response_content

        self.client_socket.sendall(response)

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
            proxy_handler = ProxyHandler(client_socket, client_address)
            threading.Thread(target=proxy_handler.handle_request).start()
    except KeyboardInterrupt:
        print("Shutting down proxy server")
        proxy_server.close()

if __name__ == "__main__":
    main()
