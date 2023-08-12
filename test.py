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

def receive_data(client_socket):
    # print("receive_data: ")
    # print(client_socket.getsockname)
    # print(0)
    data = b''
    
    while b'\r\n\r\n' not in data:
        data += client_socket.recv(BUFSIZE)
        
    first_line, headers, body = read_message_headers(data)
    
    # solve Connection: keep-alive (Content-Length)
    content_length = 0
    
    if 'Content-Length' in headers:
        content_length = int(headers['Content-Length'])
    
        if content_length != 0:
            while content_length > len(body):
                # body += receive_request_body(client_socket, content_length)
                body += client_socket.recv(BUFSIZE)
                
    # solve Connection: keep-alive (Transfer-Encoding)
    elif 'Transfer-Encoding' in headers:
        while b'\r\n\r\n' not in body:
            # chunk = client_socket.recv(BUFSIZE)
            # if len(chunk) == 0:
            #     break
            # body += chunk
            body += client_socket.recv(BUFSIZE)
            
    return first_line, headers, body

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

def handle_request_message(client_socket, host_name, request):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.connect((host_name, PORT))
        print('Successfully connected to ' + host_name)
    except socket.gaierror:
        print("There was an error resolving the host")
        return
    
    try:
        server_socket.sendall(request)
        response_count = 0

        while True:
            try:
                server_socket.settimeout(TIME_OUT)
                # response = server_socket.recv(BUFSIZE)
                status, headers, body = receive_data(server_socket)
                
                if not status:
                    break
                
                response_count += 1
                print('Response #: ' + str(response_count))
                
                
                if status[1] < '400':
                    response = make_message(status, headers, body)
                    send_response(client_socket, response)
                    # client_socket.sendall(response)  # Send the response back to the client
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
        print('Close connection to web server')
        server_socket.close()

def handle_client(client_socket):
    try:
        request_count = 0
        # current_host_name = ''
        # web_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while 1:
            try: 
                client_socket.settimeout(TIME_OUT)
                request_line, headers, body = receive_data(client_socket)
                request = make_message(request_line, headers, body)
                
                request_count += 1
                print("Request #: " + str(request_count))
                
                method = request_line[0]
                url = request_line[1]
                print(method + ' ' + url)
                print()
                host_name, path = extract_hostname_and_path(url)
                
                if method in {'GET', 'POST', 'HEAD'} and is_whitelisted(settings[section]['whitelisting'], host_name) and is_time_allowed(settings[section]['time']):
    
                # if current_host_name != host_name:
                #     if socket.isConneted(web_server):
                #         print('Close connection to web server')
                #         web_server.close()
                #     current_host_name = host_name
                    
                    # try:
                    #     web_server.connect((current_host_name, PORT))
                    #     print('Successfully connected to ' + host_name)
                    # except socket.gaierror:
                    #     print("There was an error resolving the host")
                    #     return
                    # web_server.connect((current_host_name, PORT))
                
                    # handle_request_message(client_socket, host_name, request)
                    THREAD = threading.Thread(target=handle_request_message, args=(client_socket, host_name, request))
                    THREAD.start()
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
        THREAD = threading.Thread(target=handle_client, args=(client_socket,))
        THREAD.start()
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