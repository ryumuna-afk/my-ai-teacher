import streamlit as st
import google.generativeai as genai
import PyPDF2
import os
import datetime

# =========================================================
# [설정] 모델 및 파일 이름
# =========================================================
MODEL_NAME = "models/gemini-2.0-flash"
TARGET_FILES = ["lesson.pdf"] 
TEACHER_PASSWORD = "takeit" # 선생님 비밀번호

st.set_page_config(page_title="Muna E. Teacher", page_icon="🏫")

# =========================================================
# [긴급 조치] 채팅 로그 공유 메모리
# =========================================================
@st.cache_resource
def get_shared_logs():
    return []

chat_logs = get_shared_logs()

# =========================================================
# 1. 사이드바 (API 키 + ★초기화 버튼★)
# =========================================================
with st.sidebar:
    st.header("⚙️ 설정")
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")
    
    st.divider()
    # ★ 화면이 안 보일 때 누르는 비상 탈출 버튼 ★
    if st.button("🔄 초기화 (로그아웃)"):
        st.session_state.clear() # 모든 기억 삭제
        st.rerun() # 새로고침

# =========================================================
# 2. 로그인 화면 (입장 전)
# =========================================================
if "student_info" not in st.session_state:
    st.title("🔒 수업 입장하기")
    st.info("왼쪽 사이드바에 API 키가 입력되었는지 확인해주세요.")
    
    with st.form("login_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            grade = st.selectbox("학년", ["1학년", "2학년", "3학년"])
        with col2:
            class_num = st.text_input("반", placeholder="숫자만 (예: 3)")
        with col3:
            number = st.text_input("번호", placeholder="숫자만 (예: 15)")
            
        name = st.text_input("이름", placeholder="이름 (선생님은 비밀번호 입력)")
        
        if st.form_submit_button("입장하기"):
            # 공백 제거 (실수 방지)
            name = name.strip()
            class_num = class_num.strip()
            number = number.strip()

            # [교사 모드] 비밀번호 확인
            if name == TEACHER_PASSWORD:
                st.session_state["student_info"] = "TEACHER_MODE"
                st.rerun()
            
            # [학생 모드] 빈칸 확인
            elif class_num and number and name:
                full_info = f"{grade} {class_num}반 {number}번 {name}"
                st.session_state["student_info"] = full_info
                st.rerun()
            else:
                st.error("빈칸을 모두 채워주세요!")
    
    st.stop() # 여기서 멈춤 (로그인 안 하면 아래 내용 안 보여줌)

# =========================================================
# 3. 교사 전용 화면 (CCTV)
# =========================================================
if st.session_state["student_info"] == "TEACHER_MODE":
    st.title("👨‍🏫 교사 전용 대시보드")
    st.success(f"관리자 모드 접속 완료 ({TEACHER_PASSWORD})")
    
    col_a, col_b = st.columns([4, 1])
    with col_a:
        st.write("학생들의 질문 기록입니다. (최신순)")
    with col_b:
        if st.button("새로고침"):
            st.rerun()
            
    st.divider()

    if len(chat_logs) > 0:
        for log in reversed(chat_logs):
            # log = [시간, 학생정보, 질문]
            st.markdown(f"**⏰ {log[0]} | 👤 {log[1]}**")
            st.info(f"{log[2]}") # 질문 내용을 파란 박스에 표시
    else:
        st.write("아직 질문이 없습니다.")
        
    st.stop() # 교사는 여기서 끝

# =========================================================
# 4. 학생 전용 화면 (챗봇)
# =========================================================
student_info = st.session_state["student_info"]

st.title("🏫 Muna E. Teacher")
st.caption(f"로그인: {student_info}")

# PDF 파일 읽기
pdf_content = ""
for file_name in TARGET_FILES:
    if os.path.exists(file_name):
        try:
            with open(file_name, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    pdf_content += page.extract_text() + "\n"
        except:
            pass # 에러 나도 조용히 넘어감

# 성격 설정
if pdf_content:
    SYSTEM_PROMPT = f"""
    [역할] 유쾌한 영어 선생님 'Muna E. Teacher'.
    [자료] {pdf_content}
    [지침] 자료 기반 설명. 친절하고 재미있게.
    """
else:
    SYSTEM_PROMPT = "자료가 없습니다."

# Gemini 연결
if not api_key:
    st.error("API 키가 없습니다. 선생님께 말씀드리세요.")
    st.stop()

genai.configure(api_key=api_key)
try:
    model = genai.GenerativeModel(MODEL_NAME)
except:
    st.error(f"모델 이름 오류: {MODEL_NAME}")
    st.stop()

# 채팅 기록
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hi! 영어 공부 도와줄게. 질문해봐! 😎"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 입력 처리
if prompt := st.chat_input("질문을 입력하세요"):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"
