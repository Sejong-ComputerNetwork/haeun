import json

while True:
    try:
        client_socket,addr=server_socket.accept()
        request_data=client_socket.recv(1024).decode('utf-8')
        
        method=""
        path=""
        body_part=""
        
        try:
            header_part,body_part=request_data.split('\r\n\r\n',1)
        except ValueError:
            header_part=request_data
            
        if header_part:
            request_line=header_part.split('\r\n')[0]
            parts=request_line.split(' ')
            if len(parts)>=2:
                method=parts[0]
                path=parts[1]
                
        response_dict={}
        status_line=""
        
        if method=="GET":
            if path=="/api/user":
                status_line="HTTP/1.1 200 OK"
                response_dict={"message":"GET: 유저 정보를 조회합니다."}
            else:
                status_line="HTTP/1.1 404 Not Found"
                response_dict={"message":"Not Found"}
                
        elif method=="POST":
            if path=="/api/user":
                try:
                    data=json.loads(body_part)
                    status_line="HTTP/1.1 201 Created"
                    response_dict={"message":"POST: 새 유저를 생성했습니다.","data":data}
                except json.JSONDecodeError:
                    status_line="HTTP/1.1 400 Bad Request"
                    response_dict={"message":"POST Error: 잘못된 JSON 형식입니다."}
            else:
                status_line="HTTP/1.1 404 Not Found"
                response_dict={"message":"Not Found"}
        elif method=="PUT":
            if path=="/api/user":
                try:
                    data=json.loads(body_part)
                    status_line="HTTP/1.1 200 OK"
                    response_dict={"message":"PUT: 유저 정보를 수정했습니다.","data":data}
                except json.JSONDecodeError:
                    status_line="HTTP/1.1 400 Found"
                    response_dict={"message":"Not Found"}
                    
        elif method=="DELETE":
            if path=="/api/user":
                status_line="HTTP/1.1 200 OK"
                response_dict={"message":"DELETE: 유저 정보를 삭제했습니다."}
            else:
                status_line="HTTP/1.1 405 Not Found"
                response_dict={"message":"허용되지 않는 메서드입니다."}
                
        else:
            status_line="HTTP/1.1 405 Method Not Allowed"
            response_dict={"message":"허용되지 않는 메서드입니다."}
            
        response_body=json.dumps(response_dict)
        content_type="Content-Type: application/json; charset=utf-8"
        
        response=f"""{status_line}\r\n{content_type}\r\nContent_Length:{len(response_body.encode('utf-8'))}\r\n\r\n{response_body}"""

        client_socket.sendall(response.encode('utf-8'))
        client_socket.close()
        
    except Exception as e:
        print(f"오류 발생: {e}")
        if 'client_socket' in locals():
            client_socket.close()
