import socket

HOST = "127.0.0.1"   # localhost
PORT = 8888          # proxy port

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allow quick restart
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST, PORT))
    server_socket.listen(5)

    print(f"[+] Proxy server listening on {HOST}:{PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"[+] Connection from {client_address}")

        data = client_socket.recv(4096)
        print("----- RAW DATA START -----")
        print(data.decode(errors="ignore"))
        print("----- RAW DATA END -----")

        body = "Hello from proxy server!\n"

        response = (
        "HTTP/1.1 200 OK\r\n"
         f"Content-Length: {len(body)}\r\n"
         "Content-Type: text/plain\r\n"
         "Connection: close\r\n"
         "\r\n"
         f"{body}"
        )

        client_socket.sendall(response.encode())

        client_socket.close()
        print("[+] Connection closed\n")

if __name__ == "__main__":
    start_server()
