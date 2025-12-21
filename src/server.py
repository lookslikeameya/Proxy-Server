import socket
import threading
import os
HOST = "127.0.0.1"
PORT = 8888

def parse_http_request(request_bytes):
    text = request_bytes.decode(errors="ignore")
    lines = text.split("\r\n")

    
    request_line = lines[0]
    method, target, version = request_line.split()

    host = None
    port = 80
    path = "/"

    # if Absolute URL 
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

    # if Relative path + Host header
    else:
        path = target
        for line in lines:
            if line.lower().startswith("host:"):
                host = line.split(":", 1)[1].strip()
                break

    return method, host, port, path

blocked_domains=set()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCKLIST_PATH = os.path.join(BASE_DIR, "config", "blocked_domains.txt")

try:
    with open(BLOCKLIST_PATH) as f:
        for line in f:
            line=line.strip().lower()
            if line and not line.startswith("#"):
                    blocked_domains.add(line)
except FileNotFoundError:
        print(" blocked_domains.txt not found")



print(blocked_domains)




def handle_client(client_socket, client_address):
    print(f"[+] Handling {client_address}")

    try:
        data = client_socket.recv(4096)
        method, host, port, path = parse_http_request(data)

        if host.lower() in blocked_domains:
            print(f"BLOCKED: {host}")

            response = (
             "HTTP/1.1 403 Forbidden\r\n"
             "Content-Length: 13\r\n"
             "Connection: close\r\n"
             "\r\n"
             "403 Forbidden"
             )

            client_socket.sendall(response.encode())
            return


       
        

        
        print("Forwardinfg to: ", host,port)

        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_socket.connect((host,port))
        forward_request=(
            f"{method} {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            "Connection: close\r\n"
            "\r\n"
        )

        remote_socket.sendall(forward_request.encode())

        while True:
            response = remote_socket.recv(4096)
            if not response:
                break
            client_socket.sendall(response)


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
