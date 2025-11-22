import json
import os

class DataManager:
    def __init__(self, attendance_file="today_attendance.json"):
        self.attendance_file = attendance_file # 출석 기록용 파일 (새로 생김)
        self.db_folder = "./db/" # 기존 학생 정보가 있는 폴더
        self.attendance_data = {} # 메모리에 띄울 출석부
        
        self._load_attendance() # 서버 켜질 때 출석부 준비

    # [내부함수] 오늘의 출석부 파일 읽어오기
    def _load_attendance(self):
        if not os.path.exists(self.attendance_file):
            # 파일이 없으면 빈 출석부 생성
            self.attendance_data = {}
            self._save_attendance()
            print(f"[초기화] {self.attendance_file} 출석부를 새로 만들었습니다.")
        else:
            with open(self.attendance_file, 'r', encoding='utf-8') as f:
                self.attendance_data = json.load(f)
            print(f"[로드] 출석 기록을 불러왔습니다.")

    # [내부함수] 출석부 저장하기
    def _save_attendance(self):
        with open(self.attendance_file, 'w', encoding='utf-8') as f:
            json.dump(self.attendance_data, f, indent=4, ensure_ascii=False)

    # ==========================================================
    # [업그레이드된 핵심 기능] 기존 db 폴더와 연동!
    # ==========================================================

    # 1. 이름 & 학번 확인 함수 (기존 db 폴더 활용!)
    def verify_student(self, student_id, name):
        # 1) db 폴더에 해당 학번 파일이 있는지 확인
        target_file = os.path.join(self.db_folder, f"{student_id}.json")
        
        if os.path.exists(target_file):
            # 2) 파일이 있으면 열어서 이름이 맞는지 확인
            try:
                with open(target_file, 'r', encoding='utf-8') as f:
                    user_info = json.load(f)
                    # db 파일 안의 "name"과 입력받은 name이 같은지?
                    if user_info.get("name") == name:
                        return True # 인증 성공!
            except Exception as e:
                print(f"[에러] 파일 읽기 실패: {e}")
                return False
        
        return False # 파일이 없거나 이름이 틀림

    # 2. 출석체크 바꿔주는 함수
    # (출석하면 attendance_data에 기록됨)
    def mark_attendance(self, student_id, name):
        # 이미 출석부에 있는지 확인
        if student_id in self.attendance_data:
            return "ALREADY" # 이미 출석함
        
        # 출석부에 새로 추가 (학번: {이름, 시간, 출석여부})
        self.attendance_data[student_id] = {
            "name": name,
            "attendance": True
        }
        self._save_attendance() # 파일 저장
        return "SUCCESS"

    # 3. 데이터 확인 함수 (개인 상태)
    def get_student_status(self, student_id):
        if student_id in self.attendance_data:
            return True
        return False

    # 4. 데이터를 뱉어내는 함수 (전체 출석 명단)
    def get_all_data(self):
        # 딕셔너리를 리스트로 변환해서 반환
        result_list = []
        for s_id, info in self.attendance_data.items():
            entry = {
                "id": s_id,
                "name": info["name"],
                "attendance": info["attendance"]
            }
            result_list.append(entry)
        return result_list