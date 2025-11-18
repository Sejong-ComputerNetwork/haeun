import socket
import threading

def Send(client_sock):
    while True:
        try:
            # 사용자 입력 받기
            send_data = bytes(input().encode()) 
            client_sock.send(send_data) 
        except:
            break

def Recv(client_sock):
    while True:
        try:
            # 서버로부터 데이터 수신
            recv_data = client_sock.recv(1024).decode() 
            if not recv_data: break
            print(recv_data)
        except:
            break

# TCP Client Main
if __name__ == '__main__':
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    Host = 'localhost' 
    Port = 9000        
    
    try:
        client_sock.connect((Host, Port))
        print('서버에 연결되었습니다. 메시지를 입력하세요.')

        # 보내기 담당 스레드
        thread1 = threading.Thread(target=Send, args=(client_sock, ))
        thread1.start()

        # 받기 담당 스레드
        thread2 = threading.Thread(target=Recv, args=(client_sock, ))
        thread2.start()
    except ConnectionRefusedError:
        print("서버에 연결할 수 없습니다. chat_server.py를 먼저 실행했나요?")