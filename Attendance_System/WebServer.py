import socket
import threading
import logging
import os
import json
import urllib.parse
from DataManager import DataManager

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

manager = DataManager()

def build_response(body, status="200 OK", content_type="text/html"):
    response = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: {content_type}; charset=utf-8\r\n"
        f"Content-Length: {len(body.encode('utf-8'))}\r\n"
        "\r\n"
        f"{body}"
    )
    return response

def route_http(method, path, body):
    # 윤희님이 만든 메인 페이지 (index.html) 보여주기
    if method == "GET" and path == "/":
        try:
            with open("./templates/index.html", "r", encoding="utf-8") as f:
                html = f.read()
            return html, "200 OK", "text/html"
        except FileNotFoundError:
            return "<h1>index.html 파일이 없습니다.</h1>", "404 Not Found", "text/html"

    elif method == "GET" and path.endswith(".css"):
        try:
            filename = path.lstrip("/") # "/style.css" -> "style.css"
            css_path = os.path.join("./templates", filename) 
            with open(css_path, "r", encoding="utf-8") as f:
                css_data = f.read()
            return css_data, "200 OK", "text/css"
        except:
            return "", "404 Not Found", "text/css"

    # API 경로 변경 (/api/checkin -> /api/attendance)
    elif method == "POST" and path == "/api/attendance":
        try:
            if not body:
                 return json.dumps({"message": "데이터가 없습니다."}), "400 Bad Request", "application/json"

            request_data = json.loads(body)
            student_id = request_data.get("id")
            name = request_data.get("name")

            # DataManager에게 일 시키기
            result = manager.mark_attendance(student_id, name)
            
            # [변경 3] 응답 키값 변경 ("msg" -> "message")
            if result == "SUCCESS":
                return json.dumps({"message": "출석 성공"}), "200 OK", "application/json"
            elif result == "ALREADY":
                # 윤희님 코드는 200이 아니면 오류로 띄우므로, 이미 출석했을 때도 오류 메시지처럼 보이게 할지,
                # 아니면 그냥 성공처럼 보이게 할지 결정해야 함. 일단 에러 메시지로 보냄.
                return json.dumps({"message": "이미 출석 처리가 된 상태입니다."}), "202 Accepted", "application/json"
            elif result == "NOT_FOUND":
                return json.dumps({"message": "학번 또는 이름이 일치하지 않습니다."}), "401 Unauthorized", "application/json"
            
        except Exception as e:
            return json.dumps({"message": f"서버 에러: {e}"}), "500 Internal Server Error", "application/json"

    return "<h1>404 Not Found</h1>", "404 Not Found", "text/html"


def parse_http_request(data):
    lines = data.split("\r\n")
    request_line = lines[0]
    if not request_line: return "GET", "/", ""
    
    parts = request_line.split()
    method = parts[0]
    path = parts[1]
    
    body = ""
    # Content-Length 확인 등의 복잡한 로직 대신 간단히 빈 줄 뒤를 바디로 인식
    if "\r\n\r\n" in data:
        body = data.split("\r\n\r\n", 1)[1]
        
    return method, path, body

def handle_client(client_socket, client_address):
    logging.info(f"Client connected: {client_address}")
    try:
        data = client_socket.recv(4096).decode("utf-8", errors="ignore")
        if not data:
            client_socket.close()
            return

        method, path, body = parse_http_request(data)
        logging.info(f"{method} {path}")

        result = route_http(method, path, body)
        
        if len(result) == 2:
            body, status = result
            content_type = "text/html"
        else:
            body, status, content_type = result

        response = build_response(body, status, content_type)
        client_socket.sendall(response.encode("utf-8"))
    except Exception as e:
        logging.error(f"클라이언트 처리 중 오류: {e}")
    finally:
        client_socket.close()

def main():
    # 로컬 테스트용
    HOST = '127.0.0.1' 
    PORT = 1234

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    logging.info(f"HTTP Server running on http://{HOST}:{PORT}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            thread.start()
    except KeyboardInterrupt:
        logging.info("서버 종료 중...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()
