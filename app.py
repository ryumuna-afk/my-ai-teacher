import streamlit as st
import google.generativeai as genai
import PyPDF2
import os
import datetime

# =========================================================
# [설정] 모델 이름 & 파일 이름
# =========================================================
MODEL_NAME = "models/gemini-2.0-flash"
TARGET_FILES = ["lesson.pdf"] 

# [보안 설정] 선생님 비밀번호 (이걸 입력해야 관리자 모드 진입)
TEACHER_PASSWORD = "takeit"

st.set_page_config(page_title="Muna E. Teacher", page_icon="🏫")
# 오른쪽 위 메뉴와 하단 푸터 숨기기 (더 깔끔하게)
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display:none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# =========================================================
# [핵심 기능] 공유 메모리 (질문 저장소)
# =========================================================
@st.cache_resource
def get_shared_logs():
    return []

chat_logs = get_shared_logs()

# 1. 사이드바: API 키 관리
with st.sidebar:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")

# =========================================================
# [로그인 화면] 겉보기엔 평범한 학생 로그인 화면
# =========================================================
if "student_info" not in st.session_state:
    st.title("🔒 수업 입장하기")
    
    with st.form("login_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            grade = st.selectbox("학년", ["1학년", "2학년", "3학년"]) # '교사' 항목 제거함
        with col2:
            class_num = st.text_input("반", placeholder="예: 3")
        with col3:
            number = st.text_input("번호", placeholder="예: 15")
            
        # 힌트 없이 그냥 '이름'이라고만 되어 있음
        name = st.text_input("이름", placeholder="본인 이름을 입력하세요")
        
        submit_button = st.form_submit_button("입장하기")
        
        if submit_button:
            # ★★★ [비밀 통로] 이름 칸에 'takeit'이라고 쓰면 선생님 모드 진입! ★★★
            if name == TEACHER_PASSWORD:
                st.session_state["student_info"] = "TEACHER_MODE"
                st.rerun()
            
            # [학생 모드] 정상적인 학생 로그인
            elif class_num.strip() and number.strip() and name.strip():
                full_info = f"{grade} {class_num}반 {number}번 {name}"
                st.session_state["student_info"] = full_info
                st.rerun()
            else:
                st.error("빈칸을 모두 채워주세요!")
    st.stop()

# =========================================================
# [교사 전용 화면] 실시간 모니터링
