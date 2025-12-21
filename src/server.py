import socket
import threading
import os
HOST = "127.0.0.1"
PORT = 8888
#PARSER FUNCTION
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
#LOAD BLOCKLIST
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


import datetime

LOG_FILE = "logs/proxy.log"

def log_request(
    client_addr,
    request_line,
    host,
    port,
    action,
    status,
    size
):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_line = (
        f"{timestamp} | "
        f"{client_addr[0]}:{client_addr[1]} | "
        f"{host}:{port} | "
        f"{request_line} | "
        f"{action} | "
        f"{status} | "
        f"{size} bytes\n"
    )

    with open(LOG_FILE, "a") as f:
        f.write(log_line)



#HANDLE CLIENT (THREAD)
def handle_client(client_socket, client_address):
    print(f"[+] Handling {client_address}")

    try:
        data = b""
        while b"\r\n\r\n" not in data:
          chunk = client_socket.recv(4096)
          if not chunk:
             break
          data += chunk

        request_line=data.decode(errors="ignore").split("\r\n")[0]
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
            log_request(
                client_address,
                request_line,
                host,
                port,
                "BLOCKED",
                403,
                0
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
        total_bytes = 0
        status_code = 200  # default


        while True:
           
            response = b""
            while b"\r\n\r\n" not in data:
                chunk = client_socket.recv(4096)
                if not chunk:
                 break
                data += chunk

            if not response:
                break

            total_bytes += len(response)
            if total_bytes == 0:
             try:
                status_code = int(response.split(b" ")[1])
             except:
              status_code = 0
            client_socket.sendall(response)

        log_request(
                client_address,
                request_line,
                host,
                port,
                "ALLOWED",
                status_code,
                total_bytes
            )        


    except Exception as e:
        print(f"[!] Error with {client_address}: {e}")

    finally:
        if 'remote_socket' in locals():
         remote_socket.close()
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
