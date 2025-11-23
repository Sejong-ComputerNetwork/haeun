import json
import os

class DataManager:
    def __init__(self):
        self.filename = "./db/student-info.json"
        self.data = [] 
        self._load_data()

    def _load_data(self):
        if not os.path.exists(self.filename):
            print(f"[알림] {self.filename} 파일이 없습니다. 빈 리스트로 시작합니다.")
            self.data = []
        else:
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                print(f"[로드] {len(self.data)}명의 학생 정보를 불러왔습니다.")
            except Exception as e:
                print(f"[에러] DB 로딩 실패: {e}")
                self.data = []

    def _save_data(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def mark_attendance(self, student_id, name):
        # 1. 리스트를 돌면서 해당 학번과 이름이 맞는지 찾음
        found_student = None
        for student in self.data:
            # json 파일의 키값("id", "name")과 비교
            if student.get("id") == student_id and student.get("name") == name:
                found_student = student
                break
        
        # 2. 학생이 없으면 에러 (DB에 없는 사람)
        if not found_student:
            return "NOT_FOUND"

        # 3. 이미 출석했는지 확인 ("attend" 키 사용)
        if found_student.get("attend") is True:
            return "ALREADY"

        # 4. 출석 처리 및 저장
        found_student["attend"] = True
        self._save_data()
        return "SUCCESS"
        
def get_all_data(self):
        return self.data


# 테스트 코드
if __name__ == "__main__":
    dm = DataManager()
    print(dm.mark_attendance("2024001", "김철수"))
