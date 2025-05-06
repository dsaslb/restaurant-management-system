import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import requests
import json
import logging
from functools import wraps
import os
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# 서버 설정
SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:5000')
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')

# 현재 로그인된 사용자 정보
current_user = None

# 현재 위치 확인 함수
def get_current_location():
    try:
        response = requests.get("http://ip-api.com/json/")
        data = response.json()
        location = f"{data['regionName']} {data['city']} {data['isp']}"
        return location, data['lat'], data['lon']
    except Exception as e:
        logger.error(f"위치 확인 중 오류 발생: {str(e)}")
        return "위치 확인 실패", 0, 0

# 출퇴근 기록 저장 함수
def record_attendance(action):
    try:
        now = datetime.now()
        location, lat, lon = get_current_location()
        
        # 서버에 출퇴근 기록 전송
        data = {
            'id': current_user['id'],
            'name': current_user['name'],
            'store': current_user['store'],
            'action': action,
            'latitude': lat,
            'longitude': lon
        }
        
        response = requests.post(f"{SERVER_URL}/attendance", json=data)
        result = response.json()
        
        if response.status_code == 200:
            status_label.config(text=f"{action} 기록됨: {now.strftime('%H:%M:%S')}\n위치: {result.get('address', location)}")
        else:
            status_label.config(text=f"오류 발생: {result.get('message', '알 수 없는 오류')}")
            
    except Exception as e:
        logger.error(f"출퇴근 기록 중 오류 발생: {str(e)}")
        status_label.config(text=f"오류 발생: {str(e)}")

# 직원 출퇴근 GUI
def open_employee_window():
    employee_window = tk.Tk()
    employee_window.title(f"{current_user['store']} - 직원 출퇴근 관리")
    employee_window.geometry("400x300")

    # 상단 정보 표시
    info_frame = tk.Frame(employee_window)
    info_frame.pack(pady=20)
    
    tk.Label(info_frame, text=f"매장: {current_user['store']}", font=('Arial', 12)).pack()
    tk.Label(info_frame, text=f"이름: {current_user['name']}", font=('Arial', 12)).pack()

    # 버튼 프레임
    button_frame = tk.Frame(employee_window)
    button_frame.pack(pady=20)

    tk.Button(button_frame, text="출근", command=lambda: record_attendance("출근"),
             width=15, height=2, bg='#4CAF50', fg='white').pack(pady=5)
    tk.Button(button_frame, text="퇴근", command=lambda: record_attendance("퇴근"),
             width=15, height=2, bg='#f44336', fg='white').pack(pady=5)

    # 상태 표시 레이블
    global status_label
    status_label = tk.Label(employee_window, text="", font=('Arial', 10))
    status_label.pack(pady=20)

    employee_window.mainloop()

# 로그인 확인 함수
def login():
    try:
        user_id = id_entry.get()
        password = pw_entry.get()
        selected_store = store_var.get()

        # 서버에 로그인 요청
        data = {
            'username': user_id,
            'password': password,
            'store': selected_store
        }
        
        response = requests.post(f"{SERVER_URL}/login", json=data)
        result = response.json()
        
        if response.status_code == 200:
            global current_user
            current_user = result
            messagebox.showinfo("로그인 성공", f"{current_user['name']}님 환영합니다!")
            login_window.destroy()
            if current_user['role'] == 'employee':
                open_employee_window()
            else:
                messagebox.showinfo("알림", "관리자 권한입니다.")
        else:
            messagebox.showerror("로그인 실패", result.get('message', '정보를 다시 확인하세요.'))
            
    except Exception as e:
        logger.error(f"로그인 중 오류 발생: {str(e)}")
        messagebox.showerror("오류", f"로그인 중 오류가 발생했습니다: {str(e)}")

# 로그인 GUI 생성
login_window = tk.Tk()
login_window.title("장소 기반 로그인")
login_window.geometry("300x250")

# 스타일 설정
style = ttk.Style()
style.configure('TButton', padding=5)
style.configure('TLabel', padding=5)

# 로그인 폼
form_frame = tk.Frame(login_window)
form_frame.pack(pady=20)

tk.Label(form_frame, text="아이디").pack()
id_entry = tk.Entry(form_frame)
id_entry.pack()

tk.Label(form_frame, text="비밀번호").pack()
pw_entry = tk.Entry(form_frame, show='*')
pw_entry.pack()

tk.Label(form_frame, text="매장 선택").pack()
store_var = tk.StringVar()
store_dropdown = ttk.Combobox(form_frame, textvariable=store_var, state='readonly')
store_dropdown.pack()

# 서버에서 매장 목록 가져오기
try:
    response = requests.get(f"{SERVER_URL}/stores")
    stores = response.json()
    store_dropdown['values'] = stores
    if stores:
        store_dropdown.current(0)
except Exception as e:
    logger.error(f"매장 목록 조회 중 오류 발생: {str(e)}")
    messagebox.showerror("오류", f"매장 목록을 가져오는 중 오류가 발생했습니다: {str(e)}")

# 로그인 버튼
login_button = ttk.Button(form_frame, text="로그인", command=login)
login_button.pack(pady=10)

login_window.mainloop()

class EmployeeWindow:
    def __init__(self, root, user_id, username):
        self.root = root
        self.user_id = user_id
        self.username = username
        self.root.title(f"직원 관리 시스템 - {username}")
        self.root.geometry("800x600")
        
        # 스타일 설정
        self.style = ttk.Style()
        self.style.configure('TButton', padding=5)
        self.style.configure('TLabel', padding=5)
        self.style.configure('TEntry', padding=5)
        
        # 메인 프레임
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 상단 정보 표시
        self.create_header()
        
        # 탭 컨트롤
        self.tab_control = ttk.Notebook(self.main_frame)
        self.tab_control.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 각 탭 생성
        self.create_attendance_tab()
        self.create_schedule_tab()
        self.create_worklog_tab()
        self.create_feedback_tab()
        
        # 상태바
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 초기 상태 업데이트
        self.update_status()
        
    def create_header(self):
        """상단 정보 표시 영역 생성"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # 사용자 정보
        ttk.Label(header_frame, text=f"사용자: {self.username}").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(header_frame, text=f"ID: {self.user_id}").grid(row=0, column=1, sticky=tk.W)
        
        # 현재 시간
        self.time_label = ttk.Label(header_frame, text="")
        self.time_label.grid(row=0, column=2, sticky=tk.E)
        self.update_time()
        
    def create_attendance_tab(self):
        """출근/퇴근 탭 생성"""
        tab = ttk.Frame(self.tab_control)
        self.tab_control.add(tab, text='출근/퇴근')
        
        # 출근 버튼
        self.clock_in_btn = ttk.Button(tab, text="출근", command=self.clock_in)
        self.clock_in_btn.grid(row=0, column=0, padx=5, pady=5)
        
        # 퇴근 버튼
        self.clock_out_btn = ttk.Button(tab, text="퇴근", command=self.clock_out)
        self.clock_out_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # 출근 기록 표시
        self.attendance_tree = ttk.Treeview(tab, columns=('date', 'clock_in', 'clock_out'), show='headings')
        self.attendance_tree.heading('date', text='날짜')
        self.attendance_tree.heading('clock_in', text='출근 시간')
        self.attendance_tree.heading('clock_out', text='퇴근 시간')
        self.attendance_tree.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.attendance_tree.yview)
        scrollbar.grid(row=1, column=2, sticky=(tk.N, tk.S))
        self.attendance_tree.configure(yscrollcommand=scrollbar.set)
        
        # 출근 기록 로드
        self.load_attendance_records()
        
    def create_schedule_tab(self):
        """근무 일정 탭 생성"""
        tab = ttk.Frame(self.tab_control)
        self.tab_control.add(tab, text='근무 일정')
        
        # 캘린더 위젯
        self.calendar = ttk.Treeview(tab, columns=('date', 'schedule'), show='headings')
        self.calendar.heading('date', text='날짜')
        self.calendar.heading('schedule', text='일정')
        self.calendar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 일정 로드
        self.load_schedule()
        
    def create_worklog_tab(self):
        """근무 기록 탭 생성"""
        tab = ttk.Frame(self.tab_control)
        self.tab_control.add(tab, text='근무 기록')
        
        # 근무 기록 입력 폼
        form_frame = ttk.Frame(tab)
        form_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Label(form_frame, text="날짜:").grid(row=0, column=0)
        self.worklog_date = ttk.Entry(form_frame)
        self.worklog_date.grid(row=0, column=1)
        
        ttk.Label(form_frame, text="근무 내용:").grid(row=1, column=0)
        self.worklog_content = ttk.Entry(form_frame)
        self.worklog_content.grid(row=1, column=1)
        
        ttk.Button(form_frame, text="저장", command=self.save_worklog).grid(row=2, column=0, columnspan=2)
        
        # 근무 기록 표시
        self.worklog_tree = ttk.Treeview(tab, columns=('date', 'content'), show='headings')
        self.worklog_tree.heading('date', text='날짜')
        self.worklog_tree.heading('content', text='근무 내용')
        self.worklog_tree.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 근무 기록 로드
        self.load_worklogs()
        
    def create_feedback_tab(self):
        """피드백 탭 생성"""
        tab = ttk.Frame(self.tab_control)
        self.tab_control.add(tab, text='피드백')
        
        # 피드백 입력 폼
        form_frame = ttk.Frame(tab)
        form_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Label(form_frame, text="평가:").grid(row=0, column=0)
        self.feedback_rating = ttk.Combobox(form_frame, values=[1, 2, 3, 4, 5])
        self.feedback_rating.grid(row=0, column=1)
        
        ttk.Label(form_frame, text="의견:").grid(row=1, column=0)
        self.feedback_comment = ttk.Entry(form_frame)
        self.feedback_comment.grid(row=1, column=1)
        
        ttk.Button(form_frame, text="제출", command=self.submit_feedback).grid(row=2, column=0, columnspan=2)
        
        # 피드백 표시
        self.feedback_tree = ttk.Treeview(tab, columns=('date', 'rating', 'comment'), show='headings')
        self.feedback_tree.heading('date', text='날짜')
        self.feedback_tree.heading('rating', text='평가')
        self.feedback_tree.heading('comment', text='의견')
        self.feedback_tree.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 피드백 로드
        self.load_feedback()
        
    def update_time(self):
        """현재 시간 업데이트"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
        
    def update_status(self):
        """상태바 업데이트"""
        try:
            response = requests.get(f"http://localhost:5000/api/status/{self.user_id}")
            if response.status_code == 200:
                status = response.json()
                self.status_var.set(f"상태: {status['status']}")
            else:
                self.status_var.set("상태: 오프라인")
        except Exception as e:
            logger.error(f"상태 업데이트 중 오류 발생: {str(e)}")
            self.status_var.set("상태: 연결 오류")
            
    def clock_in(self):
        """출근 처리"""
        try:
            response = requests.post(f"http://localhost:5000/api/attendance/{self.user_id}/clock-in")
            if response.status_code == 200:
                messagebox.showinfo("성공", "출근이 기록되었습니다.")
                self.load_attendance_records()
            else:
                messagebox.showerror("오류", "출근 기록에 실패했습니다.")
        except Exception as e:
            logger.error(f"출근 처리 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", "서버 연결에 실패했습니다.")
            
    def clock_out(self):
        """퇴근 처리"""
        try:
            response = requests.post(f"http://localhost:5000/api/attendance/{self.user_id}/clock-out")
            if response.status_code == 200:
                messagebox.showinfo("성공", "퇴근이 기록되었습니다.")
                self.load_attendance_records()
            else:
                messagebox.showerror("오류", "퇴근 기록에 실패했습니다.")
        except Exception as e:
            logger.error(f"퇴근 처리 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", "서버 연결에 실패했습니다.")
            
    def load_attendance_records(self):
        """출근 기록 로드"""
        try:
            response = requests.get(f"http://localhost:5000/api/attendance/{self.user_id}")
            if response.status_code == 200:
                records = response.json()
                self.attendance_tree.delete(*self.attendance_tree.get_children())
                for record in records:
                    self.attendance_tree.insert('', 'end', values=(
                        record['date'],
                        record['clock_in'],
                        record['clock_out']
                    ))
        except Exception as e:
            logger.error(f"출근 기록 로드 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", "출근 기록을 불러오는데 실패했습니다.")
            
    def load_schedule(self):
        """근무 일정 로드"""
        try:
            response = requests.get(f"http://localhost:5000/api/schedule/{self.user_id}")
            if response.status_code == 200:
                schedules = response.json()
                self.calendar.delete(*self.calendar.get_children())
                for schedule in schedules:
                    self.calendar.insert('', 'end', values=(
                        schedule['date'],
                        schedule['schedule']
                    ))
        except Exception as e:
            logger.error(f"근무 일정 로드 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", "근무 일정을 불러오는데 실패했습니다.")
            
    def save_worklog(self):
        """근무 기록 저장"""
        try:
            data = {
                'date': self.worklog_date.get(),
                'content': self.worklog_content.get()
            }
            response = requests.post(
                f"http://localhost:5000/api/worklog/{self.user_id}",
                json=data
            )
            if response.status_code == 200:
                messagebox.showinfo("성공", "근무 기록이 저장되었습니다.")
                self.load_worklogs()
            else:
                messagebox.showerror("오류", "근무 기록 저장에 실패했습니다.")
        except Exception as e:
            logger.error(f"근무 기록 저장 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", "서버 연결에 실패했습니다.")
            
    def load_worklogs(self):
        """근무 기록 로드"""
        try:
            response = requests.get(f"http://localhost:5000/api/worklog/{self.user_id}")
            if response.status_code == 200:
                worklogs = response.json()
                self.worklog_tree.delete(*self.worklog_tree.get_children())
                for worklog in worklogs:
                    self.worklog_tree.insert('', 'end', values=(
                        worklog['date'],
                        worklog['content']
                    ))
        except Exception as e:
            logger.error(f"근무 기록 로드 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", "근무 기록을 불러오는데 실패했습니다.")
            
    def submit_feedback(self):
        """피드백 제출"""
        try:
            data = {
                'rating': int(self.feedback_rating.get()),
                'comment': self.feedback_comment.get()
            }
            response = requests.post(
                f"http://localhost:5000/api/feedback/{self.user_id}",
                json=data
            )
            if response.status_code == 200:
                messagebox.showinfo("성공", "피드백이 제출되었습니다.")
                self.load_feedback()
            else:
                messagebox.showerror("오류", "피드백 제출에 실패했습니다.")
        except Exception as e:
            logger.error(f"피드백 제출 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", "서버 연결에 실패했습니다.")
            
    def load_feedback(self):
        """피드백 로드"""
        try:
            response = requests.get(f"http://localhost:5000/api/feedback/{self.user_id}")
            if response.status_code == 200:
                feedbacks = response.json()
                self.feedback_tree.delete(*self.feedback_tree.get_children())
                for feedback in feedbacks:
                    self.feedback_tree.insert('', 'end', values=(
                        feedback['date'],
                        feedback['rating'],
                        feedback['comment']
                    ))
        except Exception as e:
            logger.error(f"피드백 로드 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", "피드백을 불러오는데 실패했습니다.") 