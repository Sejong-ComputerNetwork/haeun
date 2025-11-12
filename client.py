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

	logger = logging.getLogger("Client")

	 

	# 서버 설정 - localhost 사용

	HOST = "127.0.0.1"  # 로컬호스트 주소

	PORT = 9999        # 포트 번호

	 

	def receive_messages(client_socket):

	    """서버로부터 메시지를 수신하는 함수"""

	    try:

	        while True:

	            # 서버로부터 응답 수신

	            data = client_socket.recv(1024)

	            

	            # 빈 데이터면 연결 종료로 간주

	            if not data or data == b'':

	                logger.info("서버와 연결이 종료되었습니다.")

	                break

	                

	            # 서버 메시지 출력

	            message = data.decode('utf-8')

	            logger.info(f"서버로부터 수신: {message}")

	            

	    except Exception as e:

	        logger.error(f"메시지 수신 중 오류: {e}")

	    finally:

	        # 연결 종료 처리

	        client_socket.close()

	        sys.exit(0)

	 

	def main():

	    """클라이언트 메인 함수"""

	    # 소켓 생성

	    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	    

	    try:

	        # 서버에 연결

	        logger.info(f"서버 {HOST}:{PORT}에 연결 시도 중...")

	        client_socket.connect((HOST, PORT))

	        logger.info("서버에 연결되었습니다.")

	        

	        # Ctrl+C 처리

	        def signal_handler(sig, frame):

	            logger.info("클라이언트를 종료합니다.")

	            client_socket.close()

	            sys.exit(0)

	            

	        signal.signal(signal.SIGINT, signal_handler)

	        

	        # 수신 스레드 시작

	        receive_thread = threading.Thread(

	            target=receive_messages,

	            args=(client_socket,),

	            daemon=True

	        )

	        receive_thread.start()

	        

	        # 사용자 입력을 서버로 전송

	        while True:

	            message = input("전송할 메시지: ")

	            

	            # 'quit' 입력 시 종료

	            if message.lower() == "quit":

	                logger.info("프로그램을 종료합니다.")

	                break

	                

	            # 메시지 전송

	            client_socket.send(message.encode('utf-8'))

	            

	    except ConnectionRefusedError:

	        logger.error("서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")

	    except Exception as e:

	        logger.error(f"클라이언트 실행 중 오류: {e}")

	    finally:

	        # 소켓 닫기

	        client_socket.close()

	        logger.info("클라이언트가 종료되었습니다.")

	 

	if __name__ == "__main__":

	    main()
