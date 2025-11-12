	import socket

	import threading

	import logging

	import time

	import signal

	import sys

	 

	# 로깅 설정

	logging.basicConfig(

	    format='[%(levelname)s] %(message)s',

	    level=logging.INFO)

	logger = logging.getLogger("Server")

	 

	# 서버 설정 - localhost 사용

	HOST = "127.0.0.1"  # 로컬호스트 주소

	PORT = 9999        # 포트 번호

	 

	def handle_client(client_socket, client_address):

	    """클라이언트와의 통신을 처리하는 함수"""

	    logger.info(f"클라이언트 {client_address} 연결됨")

	    

	    try:

	        # 클라이언트 연결 환영 메시지 전송

	        client_socket.send("서버에 연결되었습니다!".encode('utf-8'))

	        

	        # 클라이언트와 통신

	        while True:

	            # 클라이언트로부터 데이터 수신

	            data = client_socket.recv(1024)

	            

	            # 빈 데이터 받으면 연결 종료로 간주

	            if not data or data == b'':

	                logger.info(f"클라이언트 {client_address} 연결 종료")

	                break

	                

	            # 받은 메시지 출력 후 응답

	            received_message = data.decode('utf-8').strip()

	            logger.info(f"클라이언트로부터 수신: {received_message}")

	            

	            # 응답 메시지 만들기

	            response = f"메시지 받음: '{received_message}'"

	            client_socket.send(response.encode('utf-8'))

	            

	    except Exception as e:

	        logger.error(f"클라이언트 처리 중 오류: {e}")

	    finally:

	        # 연결 종료

	        client_socket.close()

	 

	def main():

	    """서버 메인 함수"""

	    # 소켓 생성

	    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	    

	    # 소켓 옵션 설정 (주소 재사용)

	    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	    

	    # 소켓을 주소와 포트에 바인딩

	    server_socket.bind((HOST, PORT))

	    

	    # 연결 대기 상태로 전환 (최대 5개 연결 대기 가능)

	    server_socket.listen(5)

	    logger.info(f"서버가 {HOST}:{PORT}에서 시작되었습니다.")

	    

	    # Ctrl+C 처리

	    def signal_handler(sig, frame):

	        logger.info("서버를 종료합니다.")

	        server_socket.close()

	        sys.exit(0)

	        

	    signal.signal(signal.SIGINT, signal_handler)

	    

	    try:

	        while True:

	            # 클라이언트 연결 대기

	            logger.info("클라이언트 연결 대기 중...")

	            client_socket, client_address = server_socket.accept()

	            

	            # 새 스레드에서 클라이언트 처리

	            client_thread = threading.Thread(

	                target=handle_client,

	                args=(client_socket, client_address),

	                daemon=True

	            )

	            client_thread.start()

	            

	    except Exception as e:

	        logger.error(f"서버 실행 중 오류: {e}")

	    finally:

	        # 서버 소켓 닫기

	        server_socket.close()

	        logger.info("서버가 종료되었습니다.")

	 

	if __name__ == "__main__":

	    main()
