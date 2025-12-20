import socket
import threading

HOST = "127.0.0.1"
PORT = 8888

def parse_http_request(request_bytes):
    text = request_bytes.decode(errors="ignore")
    lines = text.split("\r\n")

    # Request line
    request_line = lines[0]
    method, target, version = request_line.split()

    host = None
    port = 80
    path = "/"

    # Case 1: Absolute URL (proxy style)
    if target.startswith("http://"):
        without_http = target[len("http://"):]
        parts = without_http.split("/", 1)

        host_port = parts[0]
        path = "/" + parts[1] if len(parts) > 1 else "/"

        if ":" in host_port:
            host, port = host_port.split(":")
            port = int(port)
        else:
            host = host_port

    # Case 2: Relative path + Host header
    else:
        path = target
        for line in lines:
            if line.lower().startswith("host:"):
                host = line.split(":", 1)[1].strip()
                break

    return method, host, port, path


def handle_client(client_socket, client_address):
    print(f"[+] Handling {client_address}")

    try:
        data = client_socket.recv(4096)
        method, host, port, path = parse_http_request(data)

       
        

        print("----- RAW DATA START -----")
        print("METHOD:", method)
        print("HOST  :", host)
        print("PORT  :", port)
        print("PATH  :", path)

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
