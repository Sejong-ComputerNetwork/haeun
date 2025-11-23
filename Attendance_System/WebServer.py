import socket
import threading
import logging
import os
import json
import urllib.parse
from DataManager import DataManager 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataHandler:
    _dbPath = "./db/"

    def __init__(self):
        if not os.path.exists(self._dbPath):
            os.makedirs(self._dbPath)

    def addNewEntry(self, newId, newName):
        newEntry = {"id": newId, "name": newName}
        try:
            with open(self._dbPath + "{}.json".format(newId), "x", encoding="utf-8") as fp:
                json.dump(newEntry , fp, indent=4, ensure_ascii=False) 
        except FileExistsError:
            print("id:{} already exists".format(newId))
            raise

    def editEntry(self, id, newName): 
        try:
            data = self.getEntry(id) 
        except:
            print("failed to get data in editEntry")
            raise

        data["name"] = newName
        with open(self._dbPath + "{}.json".format(id), "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=4, ensure_ascii=False)

    def getEntry(self, id):
        try:
            with open(self._dbPath + "{}.json".format(id), "r", encoding="utf-8") as fp:
                data = json.load(fp) 
        except FileNotFoundError:
            print("id:{} does not exists".format(id))
            raise
        return data

# [전역 객체 생성]
dataHandler = DataHandler()   
manager = DataManager()      

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
    if not request_line: return "GET", "/", ""
    
    parts = request_line.split()
    method = parts[0]
    path = parts[1]
    
    body = ""
    if method in ["POST", "PUT", "DELETE"]:
        if "\r\n\r\n" in data:
            body = data.split("\r\n\r\n", 1)[1]
    return method, path, body

def build_response(body, status="200 OK", content_type="text/html"):
    response = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: {content_type}; charset=utf-8\r\n"
        f"Content-Length: {len(body.encode('utf-8'))}\r\n"
        "\r\n"
        f"{body}"
    )
    return response

# [라우팅 함수]
def route_http(method, path, body):
    
    # 1. 메인 페이지 (GET /) -> 윤희님의 index.html 보여주기
    if method == "GET" and path == "/":
        return load_html("index.html"), "200 OK"

    # 2. [추가] CSS 파일 처리 (style.css가 있다면)
    elif method == "GET" and path.endswith(".css"):
        try:
            filename = path.lstrip("/")
            css_path = os.path.join("./templates", filename)
            with open(css_path, "r", encoding="utf-8") as f:
                return f.read(), "200 OK", "text/css"
        except:
            return "", "404 Not Found", "text/css"

    # 3. [추가] 관리자 페이지 (GET /admin.html)
    elif method == "GET" and path == "/admin.html":
        return load_html("admin.html"), "200 OK"

    # 4.출석 체크 API (POST /api/attendance)
    elif method == "POST" and path == "/api/attendance":
        try:
            if not body:
                 return json.dumps({"message": "데이터가 없습니다."}), "400 Bad Request", "application/json"

            request_data = json.loads(body)
            student_id = request_data.get("id")
            name = request_data.get("name")

            # DataManager에게 일 시키기
            result = manager.mark_attendance(student_id, name)
            
            # 응답 메시지
            if result == "SUCCESS":
                return json.dumps({"message": "출석 성공"}), "200 OK", "application/json"
            elif result == "ALREADY":
                return json.dumps({"message": "이미 출석 처리가 된 상태입니다."}), "202 Accepted", "application/json"
            elif result == "NOT_FOUND":
                return json.dumps({"message": "학번 또는 이름이 일치하지 않습니다."}), "401 Unauthorized", "application/json"
            
        except Exception as e:
            return json.dumps({"message": f"서버 에러: {e}"}), "500 Internal Server Error", "application/json"

    # 5. 회원가입 폼 제출 (POST /submit) - 유지
    elif method == "POST" and path == "/submit":
        params = urllib.parse.parse_qs(body)
        name = params.get("name", [""])[0]
        student_id = params.get("student_id", [""])[0]

        try:
            dataHandler.addNewEntry(student_id, name)
        except:
            dataHandler.editEntry(student_id, name)

        html = load_html("submit.html")
        html = html.replace("{name}", name).replace("{student_id}", student_id)
        return html, "200 OK"

    # 6. 회원 관리 API (/api/user) - 유지
    elif path.startswith("/api/user"):
        response_dict = {}
        try:
            if method == "GET":
                if "?" in path:
                    query = urllib.parse.urlparse(path).query
                    params = urllib.parse.parse_qs(query)
                    user_id = params.get("id", [""])[0]
                    response_dict = {"message": "개별 조회는 아직"}
                else:
                    all_students = manager.get_all_data()
                    response_dict = {"message": "성공", "data": all_students}        
                status = "200 OK"
            elif method == "POST":
                data = json.loads(body)
                dataHandler.addNewEntry(data["id"], data["name"])
                response_dict = {"message":"POST: 새 유저 생성", "data":data}
                status = "201 Created"
            elif method == "PUT":
                data = json.loads(body)
                dataHandler.editEntry(data["id"], data["name"])
                response_dict = {"message":"PUT: 유저 정보 수정", "data":data}
                status = "200 OK"
            elif method == "DELETE":
                data = json.loads(body)
                os.remove(f"./db/{data['id']}.json")
                response_dict = {"message":"DELETE: 유저 삭제", "data":data}
                status = "200 OK"
            else:
                response_dict = {"message":"허용되지 않는 메서드"}
                status = "405 Method Not Allowed"
        except Exception as e:
            response_dict = {"message":"오류 발생", "error":str(e)}
            status = "400 Bad Request"

        return json.dumps(response_dict, ensure_ascii=False), status, "application/json"

    # 404 처리
    return load_html("404.html"), "404 Not Found"

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
        
        # 3개 반환값 처리 (JSON 대응)
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
    # [중요] 127.0.0.1로 고정 (localhost 접속용)
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

