# Please use this file to test our proxy server.
# This file doesn't use OOP style. It suitable for us to understand the logic of proxy server.
import socket
import threading
import os
import datetime
import time
from urllib.parse import urlparse

CACHE_DIRECTORY = "..\Socket\cache"
CONFIG_FILE = "config.ini"
FORBIDDEN_PAGE = "403.html"
NOT_FOUND_PAGE = "404.html"
EXPIRATION_TIME = 60
MAX_THREAD_RUNTIME = 600


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
                     

            else:
                print(f"Failed to download image. Status code: {status_code}")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the socket
        client_socket.close()

def get_cached_data(url,cache_expiration_time):
      #Create the cache directory if it doesn't exist
    if not os.path.exists(CACHE_DIRECTORY):
        os.mkdir(CACHE_DIRECTORY)

    basename = os.path.basename(url)
    cache_filename = os.path.join(CACHE_DIRECTORY, basename)

    try:
        # Check if the data is cached and still valid
        if os.path.exists(cache_filename):
            # Get the last modified time of the cached file
            cache_modified_time = os.path.getmtime(cache_filename)
            current_time = datetime.datetime.now().timestamp()
            # Calculate the age of the cached data in seconds
            cache_age = current_time - cache_modified_time

            # If the cached data is still valid, read and return it
            if cache_age < cache_expiration_time:
                with open(cache_filename, "rb") as file:
                    cached_data = file.read()
                print("HAVE ALREADY EXISTED")
                return cached_data
        else:
            print ("NOT YET")
            download_image(url,cache_filename)

    except Exception as e:
        # Handle any potential errors when accessing or reading the cache file
        print(f"Error while accessing cached data: {e}")
    print(cache_filename)
    return None

def cleanup_expired_cache(cache_expiration_time):
    start_time = time.time()  # Record the start time
    while time.time() - start_time < MAX_THREAD_RUNTIME:
        current_time = datetime.datetime.now().timestamp()
        current_time = datetime.datetime.now().timestamp()
        for cached_file in os.listdir(CACHE_DIRECTORY):
            cached_file_path = os.path.join(CACHE_DIRECTORY, cached_file)
            cache_modified_time = os.path.getmtime(cached_file_path)
            if current_time - cache_modified_time > cache_expiration_time:
                # The cached data has expired, remove the cached file
                os.remove(cached_file_path)
                print(f"Expired cached file '{cached_file}' removed.")
        time.sleep(1)  # Sleep for 2 seconds before the next iteration



if __name__ == "__main__":
    background_thread = threading.Thread(target=cleanup_expired_cache, args=(EXPIRATION_TIME,))
    background_thread.start()

    # Replace 'YOUR_FILE_URL' with the actual file URL you want to download
    file_url = 'http://testphp.vulnweb.com/images/logo.gif'
    get_cached_data(file_url, EXPIRATION_TIME)

    file_url = 'http://testphp.vulnweb.com/images/logo.gif'
    get_cached_data(file_url, EXPIRATION_TIME)
    
    file_url = 'http://oosc.online/img/login/logo.png'
    get_cached_data(file_url, EXPIRATION_TIME)
    
    file_url = 'http://oosc.online/img/login/logo.png'
    get_cached_data(file_url, EXPIRATION_TIME)

    file_url = 'http://oosc.online/img/login/govt_logo.png'
    get_cached_data(file_url, EXPIRATION_TIME)


    # Now, join the background thread to wait for it to finish
    background_thread.join()

    print("Background thread has finished.")