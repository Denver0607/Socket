import socket

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65431        # Port to listen on (non-privileged ports are >1023)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(2)

while True:
    conn, addr = s.accept()
    try:
        print('Connected by', addr)
        while True:
            data = conn.recv(1024)
            str_data = data.decode("utf8")
            if str_data == "quit":
                break

            print("Client: " + str_data)

            msg = input("Server: ")
            conn.sendall(bytes(msg, "utf8"))
    finally:
        conn.close()
s.close()
