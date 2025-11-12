import socket
import threading
import logging

logging.basicConfig(level=logging.INFO)

def parse_http_request(data):
    lines = data.split("\r\n")
    request_line = lines[0]
    method, path, version = request_line.split()
    return method, path

def route(path):
    if path == '/':
        return "<h1>Welcome to My Web Server</h1>"
    elif path == '/about':
        return "<h1>About This Server</h1>"
    else:
        return "<h1>404 Not Found</h1>"

def build_response(body, status="200 OK", content_type="text/html"):
    response = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body.encode())}\r\n"
        "\r\n"
        f"{body}"
    )
    return response

def handle_client(client_socket, client_address):
    logging.info(f"Client connected: {client_address}")
    data = client_socket.recv(1024).decode()
    if not data:
        client_socket.close()
        return

    method, path = parse_http_request(data)
    body = route(path)
    response = build_response(body)
    client_socket.sendall(response.encode())
    client_socket.close()

def main():
    HOST = "0.0.0.0"
    PORT = 9999

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    logging.info(f"HTTP Server running on {HOST}:{PORT}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            thread.start()
    except KeyboardInterrupt:
        logging.info("서버 종료 중... (Ctrl + C 입력됨)")
    finally:
        server_socket.close()
        logging.info("서버가 정상적으로 종료되었습니다.")

if __name__ == "__main__":
    main()
