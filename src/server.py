import socket
import threading

HOST = "127.0.0.1"
PORT = 8888


def handle_client(client_socket, client_address):
    print(f"[+] Handling {client_address}")

    try:
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

    except Exception as e:
        print(f"[!] Error with {client_address}: {e}")

    finally:
        client_socket.close()
        print(f"[-] Closed {client_address}\n")


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST, PORT))
    server_socket.listen(10)

    print(f"[+] Proxy server listening on {HOST}:{PORT}")

    while True:
        client_socket, client_address = server_socket.accept()

        thread = threading.Thread(
            target=handle_client,
            args=(client_socket, client_address),
            daemon=True
        )
        thread.start()


if __name__ == "__main__":
    start_server()
