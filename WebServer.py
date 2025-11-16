import socket
import threading
import logging
import os

logging.basicConfig(level=logging.INFO)

# HTML 파일 읽기 함수
def load_html(filename):
    filepath = os.path.join("templates", filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>404 File Not Found</h1>"

def parse_http_request(data):
    lines = data.split("\r\n")
    request_line = lines[0]
    method, path, version = request_line.split()
    return method, path

def route(path):
    if path == '/':
        return load_html("index.html")
    elif path == '/submit':
        return load_html("submit.html")
    else:
        return load_html("404.html")

def build_response(body, status="200 OK", content_type="text/html"):
    response = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: {content_type}; charset=utf-8\r\n"
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
    logging.info(f"HTTP Server running on http://localhost:{PORT}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            thread.start()
    except KeyboardInterrupt:
        logging.info("서버 종료 중...")
    finally:
        server_socket.close()
        logging.info("서버가 정상적으로 종료되었습니다.")

if __name__ == "__main__":
    main()
