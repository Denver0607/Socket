import socket
import threading
import os
import datetime
# from urllib.parse import urlparse
import configparser
import time

CACHE_DIRECTORY = "../Socket/cache"
CONFIG_FILE = "config.ini"
FORBIDDEN_PAGE = "403.html"
NOT_FOUND_PAGE = "404.html"
BUFSIZE = 4096
PORT = 80

def read_config():
    # Read and parse the configuration file
    # Implement configuration file parsing logic and return settings
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    
    config_dict = {}
    for section in config.sections():
        config_dict[section] = {}
        for key, value in config[section].items():
            config_dict[section][key] = value.split(',')
    
    return config_dict

settings = read_config()
section = 'CONFIGURATION'
TIME_OUT = int(settings[section]['time_out'][0])
EXPIRATION_TIME = int(settings[section]['cache_time'][0])
images_path = {}

def receive_data(client_socket):
    data = b''
    
    while b'\r\n\r\n' not in data:
        data += client_socket.recv(BUFSIZE)
        
    first_line, headers, body = read_message_headers(data)
    
    data = data.split(b'\r\n\r\n', 1)[0]
    # solve Connection: keep-alive (Content-Length)
    content_length = 0
    
    if 'Content-Length' in headers:
        content_length = int(headers['Content-Length'])
    
        if content_length != 0:
            while content_length > len(body):
                body += client_socket.recv(BUFSIZE)
                
    # solve Connection: keep-alive (Transfer-Encoding)
    elif 'Transfer-Encoding' in headers:
        while b'\r\n\r\n' not in body:
            body += client_socket.recv(BUFSIZE)

    data += b'\r\n\r\n' + body
            
    return first_line, headers, data

def read_message_headers(request):
    http_message = request
    body = b''
    
    message = http_message.split(b'\r\n\r\n',1)
    message_headers = message[0]
    # print(message_headers.decode())
    # print()
    if (len(message) > 1):
        body = message[1]
    

    first_line, headers = message_headers.decode().split("\r\n", 1)
    first_line = first_line.split(' ', 3)

    header_dictionary = {}

    # separate by different headers
    # headers = headers.decode()
    headers = headers.split('\r\n')

    # filter makes sure that no empty strings are processed
    for header in filter(lambda x: x != "", headers):
        # split by colon(:), only do one split for an array of length 2
        split_header = header.split(': ', 1)

        # set the header field equal to the header value in the dictionary
        header_dictionary[split_header[0]] = split_header[1]

    return first_line, header_dictionary, body

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

def send_image_response(client_socket, file_path):
    response_content = b""
    try:
        with open(file_path, "rb") as file:
            response_content = file.read()
    except OSError:
        print('cannot open file ' + file_path)
    
    file_extension = os.path.splitext(file_path)
    file_extension = file_extension[1].split('.')
    content_type = "image/" + file_extension[1]

    response = b"HTTP/1.1 200 OK\r\n"
    # response += b"Content-Type: " + content_type.encode() + b"\r\n"
    # response += b"Content-Length: " + str(len(response_content)).encode() + b"\r\n"
    # response += image_header
    # response += b"\r\n"
    response += response_content

    send_response(client_socket, response)

def is_whitelisted(whitelisting, host_name):
    # Implement whitelisting logic from the config file
    # Return True if URL is whitelisted, otherwise False
    for allowed_web in whitelisting:
        if host_name == allowed_web:
            return True
    return False

# access time: all day
def is_time_allowed(allowed_time):
    # Implement time-based access restrictions from the config file
    # Return True if access is allowed, otherwise False
    
    return True
    
    tm = time.localtime()
    # tm = datetime.datetime.now()
    # current_time = time.strftime("%H:%M:%S", tm)
    # print(current_time)

    cur_time = datetime.time(tm.tm_hour, tm.tm_min, tm.tm_sec)
    # cur_time = datetime.time(7,59,0)
    start_time = datetime.time(int(allowed_time[0]))
    end_time = datetime.time(int(allowed_time[1]))

    if start_time <= cur_time and cur_time <= end_time:
        return True
    return False

#done
def make_file_path(host_name, url):
    basename = host_name + '_' + os.path.basename(url) 
    cache_filename = os.path.join(CACHE_DIRECTORY, basename)
    return cache_filename

# done
def download_image(body, save_path):
    try:
        with open(save_path, 'wb') as f:
            f.write(body)
        print(f"Image downloaded and saved to {save_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

#done
def is_cached_data(cache_filename):
    try:
        # Check if the data is cached and still valid
        if os.path.exists(cache_filename):
            # Get the last modified time of the cached file
            cache_modified_time = os.path.getmtime(cache_filename)
            current_time = datetime.datetime.now().timestamp()
            # Calculate the age of the cached data in seconds
            cache_age = current_time - cache_modified_time

            # If the cached data is still valid, read and return it
            if cache_age < EXPIRATION_TIME:
                print("HAVE ALREADY EXISTED")
                return True
        else:
            # print ("NOT YET")
            return False

    except Exception as e:
        # Handle any potential errors when accessing or reading the cache file
        print(f"Error while accessing cached data: {e}")
        return False

# not done
def cleanup_expired_cache():
    # start_time = time.time()  # Record the start time
    # while time.time() - start_time < MAX_THREAD_RUNTIME:
    while 1:
        current_time = datetime.datetime.now().timestamp()
        for cached_file in os.listdir(CACHE_DIRECTORY):
            cached_file_path = os.path.join(CACHE_DIRECTORY, cached_file)
            cache_modified_time = os.path.getmtime(cached_file_path)
            if current_time - cache_modified_time > EXPIRATION_TIME:
                # The cached data has expired, remove the cached file
                os.remove(cached_file_path)
                print(f"Expired cached file '{cached_file}' removed.")
        time.sleep(30)  # Sleep for 30 seconds before the next iteration

# not use yet
def make_message(first_line, headers, body):
    request = b''
    
    # add request/status line
    for item in first_line:
        request += item.encode() + b' '
    request = request[:-1]
    request += b'\r\n'
    
    # add headers
    for key, value in headers.items():
        request += key.encode() + b': ' + value.encode() + b'\r\n'
    request += b'\r\n'
    
    # add body
    request += body
    
    return request

def handle_request_message(client_socket, host_name, request, save_path):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.connect((host_name, PORT))
        # print('Successfully connected to ' + host_name)
    except socket.gaierror:
        print("There was an error connecting to the host")
        return
    
    try:
        server_socket.sendall(request)
        # response_count = 0

        while True:
            try:
                server_socket.settimeout(TIME_OUT)
                status, headers, response = receive_data(server_socket)
                
                if not status:
                    break
                
                # response_count += 1
                # print('Response #: ' + str(response_count))
                
                if status[1] < '400':
                    # response = make_message(status, headers, body)
                    send_response(client_socket, response)
                    
                    if 'Content-Type' in headers:
                        if 'image' in headers['Content-Type']:
                            print('this is an image')
                            test_data = response.split(b'\r\n', 1)
                            # image_header = test_data[1].split(b'\r\n\r\n')
                            download_image(test_data[1], save_path)
                            
                elif status[1] == '404':
                    send_not_found_response(client_socket)
                    
                else:
                    send_forbidden_response(client_socket)
                    
                if 'Connection' in headers:
                    if headers['Connection'] == 'close':
                        break
                
            except socket.timeout:
                print('Server time out')
                break

    except OSError as e:
        if isinstance(e, socket.timeout):
            print("OSError (socket.timeout): No more responses will be received.")
        else:
            print("OSError:", e)
    
    finally:
        # print('Close connection to web server')
        server_socket.close()

def handle_client(client_socket):
    try:
        request_count = 0
        while 1:
            try: 
                client_socket.settimeout(TIME_OUT)
                request_line, headers, request = receive_data(client_socket)
                # request = make_message(request_line, headers, body)
                
                request_count += 1
                print("Request #: " + str(request_count))
                
                method = request_line[0]
                url = request_line[1]
                print(method + ' ' + url)
                # print()
                host_name, __ = extract_hostname_and_path(url)
                
                if method in {'GET', 'POST', 'HEAD'} and is_whitelisted(settings[section]['whitelisting'], host_name) and is_time_allowed(settings[section]['time']):
                    file_path = make_file_path(host_name, url)
                    if is_cached_data(file_path):
                        send_image_response(client_socket, file_path)
                        
                    else:
                        REQUEST_THREAD = threading.Thread(target=handle_request_message, args=(client_socket, host_name, request, file_path))
                        REQUEST_THREAD.start()
                else:
                    send_forbidden_response(client_socket)
                    
                if 'Connection' in headers:
                    if headers['Connection'] == 'close':
                        break
                    
            except socket.timeout:
                print('Client time out')
                break
        
    except OSError as e:
        if isinstance(e, socket.timeout):
            print("OSError (socket.timeout): No more responses will be received.")
        else:
            print("OSError:", e)
    
    finally:
        print('Close connection to web client')
        client_socket.close()

def accept_incoming_connections(proxy_server):
    while 1:
        client_socket, client_address = proxy_server.accept()
        print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
        # clients[client_socket] = client_socket
        print('Proxy is waiting for resquest')
        CLIENT_THREAD = threading.Thread(target=handle_client, args=(client_socket,))
        CLIENT_THREAD.start()
        # handle_client(client_socket)

def main():
    if not os.path.exists(CACHE_DIRECTORY):
        os.mkdir(CACHE_DIRECTORY)

    proxy_host = "127.0.0.1"
    proxy_port = 10000

    proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_server.bind((proxy_host, proxy_port))
    proxy_server.listen(10)

    print(f"Proxy server is listening on {proxy_host}:{proxy_port}")

    try:
        CLEAN_CACHED = threading.Thread(target=cleanup_expired_cache)
        CLEAN_CACHED.start()
        
        ACCEPT_THREAD = threading.Thread(target=accept_incoming_connections, args=(proxy_server,))
        ACCEPT_THREAD.start() 
        ACCEPT_THREAD.join()
            
    except KeyboardInterrupt:
        print("Proxy server stopped.")
        # proxy_server.close()
    finally:
        proxy_server.close()

if __name__ == "__main__":
    main()