# Please use this file to test our proxy server.
# This file doesn't use OOP style. It suitable for us to understand the logic of proxy server.
import socket
import threading
import os
import datetime
# from urllib.parse import urlparse
import configparser
import time

CACHE_DIRECTORY = "cache"
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

# not use yet
def parse_request(request):
    # print("parse_request: ")
    # print(request.decode())
    # print(5)
    lines = request.split(b"\r\n")
    if not lines:
        return None, None

    # Extract HTTP method and URL from the first line of the request
    # print("lines[0]: ")
    str_line = lines[0].decode().split(' ')
    # print(str_lines)
    method = str_line[0]
    url =  str_line[1]
    str_line.clear()
    # method = None
    # url = None
    return method, url

def read_message_headers(request):
    http_message = request
    body = b''
    
    message = http_message.split(b'\r\n\r\n',1)
    message_headers = message[0]
    print(message_headers.decode())
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
    
# not use yet
def get_content_length(request):
    content_length_header = b"Content-Length: "
    index = request.find(content_length_header)
    if index != -1:
        end_index = request.find(b"\r\n", index + len(content_length_header))
        content_length = request[index + len(content_length_header):end_index].strip()
        return int(content_length)
    return 0

# not use yet
def receive_request_body(client_socket, content_length):
    return client_socket.recv(content_length)

# not use yet
def get_file_size(resource):
    """
    This method gets the size of the resource.
    :param resource: resource to get size from
    :return: the file size as an integer
    """

    # file_size = 0
    # if isfile(resource):
    #     file_size = stat(resource).st_size

    # return file_size
    pass

# not use yet
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

# not use yet
def get_response_headers(file):
    # response_headers = []

    # timestamp = datetime.utcnow()
    # date = timestamp.strftime('%a, %d %b %Y %H:%M:%S GMT')
    # response_headers.append(b'Date: ' + date.encode('ASCII') + b'\r\n')

    # content_length = get_file_size(file)
    # response_headers.append(b'Content-Length: ' + str(content_length).encode('ASCII') + b'\r\n')

    # response_headers.append(b'Content-Type: ' + get_mime_type(file) + b'\r\n')
    # response_headers.append(b'Connection: close\r\n')

    # return response_headers
    pass

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

# always True now
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

def handle_get_request(host_name, request):
    # ... (same implementation as before)
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        print(host_name)
        # host = socket.gethostbyname('www.example.com')
        # host = socket.gethostbyname(host_name)
    except socket.gaierror:
        # this means could not resolve the host
        print ("there was an error resolving the host")
        return
    
    # print('Handle_get_request:')
    # print(host_name)
    # print(PORT)
    
    # connecting to the server
    connection.connect((host_name, PORT))
    
    print('Successfully connecting to ' + host_name)
    
    #send request and get response
    connection.sendall(request)
    status, headers, body = receive_data(connection)
    
    connection.close()
    
    #send response to the client
    print('Response body length: ')
    print(len(body))
    
    response = status[1].encode()
    if response != b'404' and response != b'403':
        response = make_message(status, headers, body)
    
    return response

def handle_post_request(host_name, request):
    # ... (same implementation as before)
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # connecting to the server
    connection.connect((host_name, PORT))
    
    print('Successfully connecting to ' + host_name)
    
    #send request and get response
    connection.sendall(request)
    status, headers, body = receive_data(connection)
    
    connection.close()
    
    #send response to the client
    print('Response body length: ')
    print(len(body))
    
    response = status[1].encode()
    if response != b'404' and response != b'403':
        response = make_message(status, headers, body)
    
    return response

def handle_head_request(host_name, request):
    # ... (same implementation as before)
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # connecting to the server
    connection.connect((host_name, PORT))
    
    print('Successfully connecting to ' + host_name)
    
    #send request and get response
    connection.sendall(request)
    status, headers, body = receive_data(connection)
    
    connection.close()
    
    #send response to the client
    print('Response body length: ')
    print(len(body))
    
    response = status[1].encode()
    if response != b'404' and response != b'403':
        response = make_message(status, headers, body)
    
    return response

def handle_request(client_socket):
    # print(client_socket.getsockname)
    # print(2)
    # request = receive_data(client_socket)
    # print("request: ")
    # print(request.decode())
    # print(3)
    request_line, headers, body = receive_data(client_socket)
    print('Request body length: ')
    print(len(body))
    print('\r\n')
    
    # print('Request:')
    # print(request_line)
    # print(headers)
    
    method = request_line[0]
    url = request_line[1]
    # method, url = parse_request(request)
    # content_length = get_content_length(request)
    host_name, path = extract_hostname_and_path(url)

    section = 'CONFIGURATION'
    if method and url and is_whitelisted(settings[section]['whitelisting'], host_name) and is_time_allowed(settings[section]['time']):
        print("all parameters are not None")
        response = b'403'
        request = make_message(request_line, headers, body)
        
        if method == "GET":
            # print('Test_line: ')
            # a, b, c = read_message_headers(request)
            # # c = receive_request_body()
            # print('Body length: ' + str(len(c)))
            # test_line1, test_line2 = read_message_headers(request)
            # print(test_line1)
            # print(test_line2)
            
            response = handle_get_request(host_name, request)
                
        elif method == "POST":
            response = handle_post_request(host_name, request)
        elif method == "HEAD":
            response = handle_head_request(host_name, request)
        else:
            # Unsupported method, return 403 Forbidden
            send_forbidden_response(client_socket)
            
        if response == b'403':
            send_forbidden_response(client_socket)
        elif response == b'404':
            send_not_found_response(client_socket)
        else:
            send_response(client_socket, response)
            
    else:
        # URL not whitelisted or access not allowed, return 403 Forbidden
        send_forbidden_response(client_socket)

    client_socket.close()

def accept_incoming_connections(proxy_server):
    while 1:
        print('From another thread')
        print()
        client_socket, client_address = proxy_server.accept()
        print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
        # clients[client_socket] = client_socket
        print('Proxy is waiting for resquest')
        THREAD = threading.Thread(target=handle_request, args=(client_socket,))
        THREAD.start()
        # handle_request(settings, client_socket)
        print('\r\n\r\n')
    
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
        # while True:
        ACCEPT_THREAD = threading.Thread(target=accept_incoming_connections, args=(proxy_server,))
        ACCEPT_THREAD.start()
        ACCEPT_THREAD.join()
            
    except KeyboardInterrupt:
        print("Proxy server stopped.")
        proxy_server.close()
    finally:
        proxy_server.close()

if __name__ == "__main__":
    main()
