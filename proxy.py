import socket
import threading
import os
import time
import configparser

# Define the proxy server IP and port
proxy_ip = "127.0.0.1"  # Change this to the appropriate IP if the proxy is running on a different machine
proxy_port = 8888       # Change this to the appropriate port used by your proxy server

# Define global variables to store configuration values
CACHE_EXPIRATION_TIME = 0
ALLOWED_START_TIME = 0
ALLOWED_END_TIME = 0
whitelisted_domains = []

# Define the cache directory
CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Load configurations from config file
def load_config():
    config = configparser.ConfigParser()
    config.read("config.txt")

    # Read CACHE_EXPIRATION_TIME from the config file
    global CACHE_EXPIRATION_TIME
    CACHE_EXPIRATION_TIME = int(config.get('CACHE', 'cache_time').strip())

    # Read ALLOWED_START_TIME and ALLOWED_END_TIME from the config file
    global ALLOWED_START_TIME, ALLOWED_END_TIME
    time_range = config.get('CACHE', 'time').strip().split('-')
    ALLOWED_START_TIME = int(time_range[0])
    ALLOWED_END_TIME = int(time_range[1])

    # Read whitelisted_domains from the config file
    global whitelisted_domains
    whitelisted_domains = [domain.strip() for domain in config.get('CACHE', 'whitelisting').split(',')]

# Load the cache from file (for persistent caching)
def load_cache():
    cached_objects = {}
    for cached_file in os.listdir(CACHE_DIR):
        file_path = os.path.join(CACHE_DIR, cached_file)
        url = os.path.basename(file_path)

        with open(file_path, 'rb') as f:
            cached_data = f.read()
        
        cached_objects[url] = cached_data

    return cached_objects

# Save the cache to file (for persistent caching)
def save_cache(url, data):
    # Create the file path for the cached object
    cache_file_path = os.path.join(CACHE_DIR, url)

    # Write the data to the cache file
    with open(cache_file_path, 'wb') as f:
        f.write(data)

# Check if a URL is whitelisted
def is_whitelisted(url):
    # Your code to check if the URL is whitelisted here...
    for domain in whitelisted_domains:
        if domain in url:
            return True
    return False

# Function to fetch an image from the web server
def fetch_image_from_web_server(url):
    try:
        # Parse the URL to get the host and path
        _, _, host, path = url.split('/', 3)

        # Open a socket connection to the web server
        web_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        web_socket.connect((host, 80))

        # Create the HTTP request to fetch the image
        request = f"GET /{path} HTTP/1.1\r\nHost: {host}\r\n\r\n"

        # Send the request to the web server
        web_socket.sendall(request.encode())

        # Receive the response from the web server
        response = b""
        while True:
            chunk = web_socket.recv(4096)
            if not chunk:
                break
            response += chunk

        # Close the socket connection
        web_socket.close()

        # Find the start and end of the image data in the response
        start_index = response.find(b"\r\n\r\n") + 4
        image_data = response[start_index:]

        # Return the image data
        return image_data

    except Exception as e:
        # Handle any exceptions (e.g., connection error, invalid URL, etc.)
        print(f"Error fetching image from {url}: {e}")
        return None

# Process the web request and return the response
def process_request(client_socket, request_data):
    # Your code to process the request here...
    request_lines = request_data.split('\r\n')
    request_line = request_lines[0]
    method, url, _ = request_line.split(' ')

    if method not in ['GET', 'POST', 'HEAD']:
        # Return 403 Forbidden for unsupported methods
        response = "HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\n<h1>403 Forbidden</h1>"
        client_socket.sendall(response.encode())
        client_socket.close()
        return

    if not is_whitelisted(url):
        # Return 403 Forbidden for non-whitelisted URLs
        response = "HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\n<h1>403 Forbidden</h1>"
        client_socket.sendall(response.encode())
        client_socket.close()
        return

    current_hour = int(time.strftime("%H"))
    if current_hour < ALLOWED_START_TIME or current_hour >= ALLOWED_END_TIME:
        # Return 403 Forbidden for requests outside the allowed time range
        response = "HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\n<h1>403 Forbidden</h1>"
        client_socket.sendall(response.encode())
        client_socket.close()
        return

    if method == 'GET' and 'image' in url:
        # Check cache for the image
        image_path = os.path.join(CACHE_DIR, url)
        if os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                image_data = f.read()
                response_headers = "HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\nConnection: Keep-alive\r\n\r\n"
                client_socket.sendall(response_headers.encode() + image_data)
            client_socket.close()
            return
        else:
            # Fetch the image from the web server
            image_data = fetch_image_from_web_server(url)

            # Cache the image
            save_cache(url, image_data)

            # Send the image data as a response
            response_headers = "HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\nConnection: Keep-alive\r\n\r\n"
            client_socket.sendall(response_headers.encode() + image_data)
            client_socket.close()
            return

    elif method == 'POST':
        # Your code to handle POST requests here...
        # This is just a simple example response for POST requests
        response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<h1>POST Request Received</h1>"
        client_socket.sendall(response.encode())
        client_socket.close()
        return

    elif method == 'HEAD':
        # Your code to handle HEAD requests here...
        # This is just a simple example response for HEAD requests
        response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
        client_socket.sendall(response.encode())
        client_socket.close()
        return
    
    # ... (code to handle other types of requests)

# Define the proxy server function to handle requests
def proxy_server(client_socket, addr):
    # Receive the request data from the client
    request_data = client_socket.recv(4096).decode()

    # Process the request and send the response
    process_request(client_socket, request_data)

# Main function to set up the proxy server
def main():
    # Load configurations from the config file
    load_config()

    # Load the cache from file
    load_cache()

    # Your setup logic for the proxy server here...
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((proxy_ip, proxy_port))
    server_socket.listen(5)
    print(f"Proxy server listening on {proxy_ip}:{proxy_port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Received connection from {addr[0]}:{addr[1]}")
        proxy_thread = threading.Thread(target=proxy_server, args=(client_socket, addr))
        proxy_thread.start()

if __name__ == "__main__":
    main()
