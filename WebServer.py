import socket
import threading
import logging
import os
import json
import urllib.parse
from DataManager import DataManager

logging.basicConfig(level=logging.INFO)

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
    body = ""
    if method in ["POST", "PUT", "DELETE"]:
        body = data.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in data else ""
    return method, path, body


dataHandler = DataHandler()

manager = DataManager()

def route_http(method, path, body):
    # 1. 출석 체크 페이지 보여주기 (GET /)
    if method == "GET" and path == "/":
        try:
            # templates 폴더에 checkin.html이 있어야 합니다!
            with open("./templates/checkin.html", "r", encoding="utf-8") as f:
                html = f.read()
            return html, "200 OK", "text/html"
        except FileNotFoundError:
            return "<h1>HTML 파일이 없습니다 (checkin.html)</h1>", "404 Not Found", "text/html"

    # 2. [핵심] 클라이언트가 보낸 정보 처리 및 코드 응답 (POST /api/checkin)
    elif method == "POST" and path == "/api/checkin":
        try:
            # body가 비어있을 경우 방어
            if not body:
                 return json.dumps({"msg": "데이터가 없습니다."}), "400 Bad Request", "application/json"

            request_data = json.loads(body)
            student_id = request_data.get("id")
            name = request_data.get("name")

            # A. 학생인지 확인 (DataManager 사용)
            if manager.verify_student(student_id, name):
                # B. 출석 처리 시도
                result = manager.mark_attendance(student_id, name)
                
                if result == "SUCCESS":
                    # 성공: 200 OK
                    return json.dumps({"msg": "출석이 완료되었습니다!"}), "200 OK", "application/json"
                elif result == "ALREADY":
                    # 이미 함: 202 Accepted
                    return json.dumps({"msg": "이미 출석 처리가 된 상태입니다."}), "202 Accepted", "application/json"
            else:
                # 인증 실패: 401 Unauthorized
                return json.dumps({"msg": "학번 또는 이름이 일치하지 않습니다."}), "401 Unauthorized", "application/json"

        except json.JSONDecodeError:
             return json.dumps({"msg": "잘못된 JSON 형식입니다."}), "400 Bad Request", "application/json"
        except Exception as e:
            return json.dumps({"msg": f"서버 에러: {e}"}), "500 Internal Server Error", "application/json"

    # 3. (옵션) 파일/이미지 등 다른 요청이 올 경우 404 처리
    return "<h1>404 Not Found</h1>", "404 Not Found", "text/html"

def build_response(body, status="200 OK", content_type="text/html"): #응답만들기, 준비된 음식(body)를 그냥 주지 않고 HTTP라는 Protocol에 담아 줌 
    response = (
        f"HTTP/1.1 {status}\r\n" #HTTP 위에 주문 성공 (200 OK)또는 메뉴 없음(404)같은 상태 딱지를 붙임 
        f"Content-Type: {content_type}; charset=utf-8\r\n" #음식이 글자인지 데이터 인지 종류를 알려줌 
        f"Content-Length: {len(body.encode())}\r\n"
        "\r\n"
        f"{body}"
    )
    return response


def handle_client(client_socket, client_address): #주문받기, 전담직원이 일할차례 
    logging.info(f"Client connected: {client_address}")
    try:
        data = client_socket.recv(4096).decode("utf-8", errors="ignore")#손님(웹브라우저)이 http 요청 보냄, 직원은 일단 주문서 recv
        if not data:
            client_socket.close()
            return

        method, path, body = parse_http_request(data) #받은 정보가 복잡하므로 해석해서 중요한 정보만 뽑아냄 
        #method는 post인지 get인지, path는 메인페이지를 달라는건지 제출한다는건지 등 
        logging.info(f"{method} {path}")

        result = route_http(method, path, body)
        if len(result) == 2:
            body, status = result
            content_type = "text/html"
        else:
            body, status, content_type = result

        response = build_response(body, status, content_type)
        client_socket.sendall(response.encode("utf-8")) #전담 직원이 1:1전화기로 손님에게 이 쟁반(HTTP 응답)을 전달함
    except Exception as e:
        logging.error(f"클라이언트 처리 중 오류: {e}")
    finally:
        client_socket.close() #식사(응답)가 끝났으니 !:1 전화기를 끊음, 스레드는 퇴근하고 손님은 웹브라우저에서 페이지를 보게됨.


def main(): #코드는 메인 함수부터 시작
    HOST = '127.0.0.1' #socket.gethostname()
    PORT = 1234

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#전화기 개통(서버 소켓 개통)
    server_socket.bind((HOST, PORT))# 전화기를 localhost의 1234번이라는 전화번호 주소에 연결
    server_socket.listen(5) #전화가 너무 많이 와도 5명까지는 대기시킬 수 있게 설정
    logging.info(f"HTTP Server running on http://localhost:{PORT}") #식당 영업 시작
    try:
        while True: #손님 맞이 
            client_socket, client_address = server_socket.accept() #대표 전화기로 클라이언트가 전화를 검
             # 서버 수락 > 서버는 손님과 1:1로 전화할 전화기를 새로 만들어서 연결.
            thread = threading.Thread(target=handle_client, args=(client_socket, client_address)) #손님을 응대할 전담 직원(스레드) 고용, handle_client라는 업무 메뉴얼에 따라 응대 
            thread.start() 
    except KeyboardInterrupt:
        logging.info("서버 종료 중...")
    finally:
        server_socket.close()
        logging.info("서버가 정상적으로 종료되었습니다.")

if __name__ == "__main__":
    main()