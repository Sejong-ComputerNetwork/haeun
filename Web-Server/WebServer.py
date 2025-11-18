import socket
import threading
import logging
import os
import json
import urllib.parse

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

def route_http(method, path, body): #주문 전달 함수 직원이 주문내용을 해석했읜 어디로 가야할지 결정해야함
    # HTML 폼 관련
    if method == "GET" and path == "/": #손님이 get으로 /를 요청했다면 HTML 내용을 가져옴 
        return load_html("index.html"), "200 OK"
    elif method == "POST" and path == "/submit": #손님이 post로 submit 요청 > body에 담긴 학번과 이름을 datahandler에 넘겨 저장 
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
    # REST API / JSON 처리
    elif path.startswith("/api/user"): #매니저(API)에게 특별요청(JSON). 메서드에 따라 데이터를 조회하거나 생성/수정/삭제함 
        response_dict = {}
        try:
            if method == "GET":
                if "?" in path:
                    # 예: /api/user?id=123
                    query = urllib.parse.urlparse(path).query
                    params = urllib.parse.parse_qs(query)
                    user_id = params.get("id", [""])[0]
                    data = dataHandler.getEntry(user_id)
                    response_dict = {"message":"GET: 유저 정보 조회", "data":data}
                else:
                    response_dict = {"message":"GET: 전체 유저 목록"}
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
    return load_html("404.html"), "404 Not Found" #위의 모든 경우가 아닌경우 404 not found처리 
#라우팅 결과 손님에게 줄 음식(HTML또는 JSON 데이터)이 준비됨 

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