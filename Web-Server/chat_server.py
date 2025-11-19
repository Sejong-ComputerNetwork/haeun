# -*- coding: utf-8 -*-
import socket
import threading
from queue import Queue

def Send(group, send_queue):
    print('Thread Send Start')
    while True:
        try:
            # 1. 큐(Queue)에서 보낼 메시지를 꺼냅니다. (누군가 put 할 때까지 대기)
            recv = send_queue.get()
            
            # 2. 새 클라이언트 접속 시 그룹 갱신 신호 확인
            if recv == 'Group Changed':
                print('Group Changed')
                break # 루프를 깨고 나가서 이 스레드는 종료됨 (새 스레드가 생성되므로)

            # 3. 메시지 내용 분해 (메시지, 소켓, 스레드번호)
            msg_content = recv[0]
            sender_conn = recv[1]
            thread_count = recv[2]

            # 4. 접속한 모든 클라이언트(group)에게 방송
            for conn in group:
                msg = 'Client' + str(thread_count) + ' >> ' + str(msg_content)
                
                # 본인에게는 다시 보내지 않음
                if sender_conn != conn: 
                    conn.send(bytes(msg.encode()))
                else:
                    pass
        except:
            pass

def Recv(conn, count, send_queue):
    print('Thread Recv' + str(count) + ' Start')
    while True:
        try:
            # 1. 클라이언트의 메시지를 받습니다.
            data = conn.recv(1024).decode()
            if not data: break
            
            # 2. 받은 메시지를 '중앙 주문서(Queue)'에 넣습니다.
            send_queue.put([data, conn, count]) 
        except:
            break

# TCP Server Main
if __name__ == '__main__':
    send_queue = Queue()
    HOST = ''  # 모든 인터페이스에서 접속 허용
    PORT = 9000  # 웹 서버(1234)와 다른 포트 사용
    
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((HOST, PORT))
    server_sock.listen(10)

    count = 0
    group = [] # 연결된 클라이언트 소켓 리스트

    print(f"채팅 서버가 {PORT}번 포트에서 시작되었습니다.")

    while True:
        count = count + 1
        conn, addr = server_sock.accept()
        group.append(conn)
        print('Connected ' + str(addr))

        # 새 클라이언트가 올 때마다 Send 스레드에게 'Group Changed'를 보내 기존 스레드를 죽이고
        # 갱신된 group 리스트를 가진 새 Send 스레드를 시작함.
        if count > 1:
            send_queue.put('Group Changed')
            thread1 = threading.Thread(target=Send, args=(group, send_queue,))
            thread1.start()
        else:
            thread1 = threading.Thread(target=Send, args=(group, send_queue,))
            thread1.start()

        # 각 클라이언트마다 '듣기 전용(Recv)' 스레드 생성
        thread2 = threading.Thread(target=Recv, args=(conn, count, send_queue,))

        thread2.start()
