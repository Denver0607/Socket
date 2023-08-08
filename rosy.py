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

def download_file(url, save_path):
    # Extract the hostname and path from the URL
    hostname, path = extract_hostname_and_path(url)

    try:
        # Create a socket object
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the server using port 80 (HTTP)
        client_socket.connect((hostname, 80))

        # Send an HTTP GET request to the server
        request = f"GET {path} HTTP/1.1\r\nHost: {hostname}\r\n\r\n"
        client_socket.sendall(request.encode())

        # Receive and parse the response from the server
        response = b""
        while True:
            chunk = client_socket.recv(100000)
            if not chunk:
                break
            response += chunk

            # Check if the response headers have been received
            if b"\r\n\r\n" in response:
                headers, file_data = response.split(b"\r\n\r\n", 1)

                # Check for the status code in the headers
                status_line = headers.split(b"\r\n", 1)[0]
                status_code = int(status_line.split(b" ")[1])

                if status_code == 200:
                    # Save the file data to the specified file path
                    with open(save_path, 'wb') as f:
                        f.write(file_data)

                    print(f"File downloaded and saved to {save_path}")
                    with open('logo.png', "rb") as file:
                        response_content = file.read()
                else:
                    print(f"Failed to download file. Status code: {status_code}")

                break

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the socket
        client_socket.close()

def download_image(url, save_path):
      # Extract the hostname and path from the URL
    hostname, path = extract_hostname_and_path(url)

    try:
        # Create a socket object
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the server using port 80 (HTTP)
        client_socket.connect((hostname, 80))

        # Send an HTTP GET request to the server
        request = f"GET {path} HTTP/1.1\r\nHost: {hostname}\r\n\r\n"
        client_socket.sendall(request.encode())

        # Receive and parse the response from the server
        response = b""
        while True:
            chunk = client_socket.recv(8192)
            if not chunk:
                break
            response += chunk

        # Check if the response headers have been received
        if b"\r\n\r\n" in response:
            headers, file_data = response.split(b"\r\n\r\n", 1)

            # Check for the status code in the headers
            status_line = headers.split(b"\r\n", 1)[0]
            status_code = int(status_line.split(b" ")[1])

            if status_code == 200:
                # Find the content type in the headers
                content_type = None
                for header in headers.split(b"\r\n"):
                    if b"Content-Type: " in header:
                        content_type = header.split(b"Content-Type: ")[1].strip()
                        break

                # Save the image data to the specified file path
                with open(save_path, 'wb') as f:
                    f.write(file_data)

                print(f"Image downloaded and saved to {save_path}")
                with open('logo.png', "rb") as file:
                        response_content = file.read()

            else:
                print(f"Failed to download image. Status code: {status_code}")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the socket
        client_socket.close()
if __name__ == "__main__":
    # Replace 'YOUR_FILE_URL' with the actual file URL you want to download
    file_url = 'http://oosc.online/img/login/logo.png'

    # Replace 'file.txt' with the desired file name and extension for saving the file
    file_path = 'D:\Rosy\study\Year1\HK3\MMT\logo.png'

    download_image(file_url, file_path)