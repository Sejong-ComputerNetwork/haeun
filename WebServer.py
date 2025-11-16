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

def route_http(method, path, body):
    # HTML 폼 관련
    if method == "GET" and path == "/":
        return load_html("index.html"), "200 OK"
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
    # REST API / JSON 처리
    elif path.startswith("/api/user"):
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
    return load_html("404.html"), "404 Not Found"


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
