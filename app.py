import streamlit as st
import google.generativeai as genai
import PyPDF2
import os
import datetime

# =========================================================
# [설정] 기본 환경 설정
# =========================================================
# [수정 완료] 아까 작동했던 모델 이름으로 변경했습니다!
MODEL_NAME = "models/gemini-pro-latest" 
TARGET_FILES = ["lesson.pdf"]  # PDF 파일 이름 (같은 폴더에 있어야 함)
TEACHER_PASSWORD = "takeit"    # 선생님 접속 비밀번호

st.set_page_config(page_title="Muna E. Teacher", page_icon="🏫")

# [디자인] 화면 깔끔하게 만들기 (메뉴, 푸터 숨김)
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display:none;}
.block-container {padding-top: 2rem;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# =========================================================
# [기능] 채팅 로그 저장소 (공유 메모리)
# =========================================================
@st.cache_resource
def get_shared_logs():
    return []

chat_logs = get_shared_logs()

# =========================================================
# 1. 사이드바 (API 키 설정)
# =========================================================
with st.sidebar:
    # 서버(Secrets)에 키가 있으면 자동으로 가져오고, 없으면 입력창 표시
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key를 입력하세요", type="password")

# =========================================================
# 2. 로그인 화면 (가장 먼저 실행됨)
# =========================================================
if "student_info" not in st.session_state:
    st.title("🔒 수업 입장하기")
    
    with st.form("login_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            grade = st.selectbox("학년", ["1학년", "2학년", "3학년"])
        with col2:
            class_num = st.text_input("반", placeholder="숫자만 (예: 3)")
        with col3:
            number = st.text_input("번호", placeholder="숫자만 (예: 15)")
            
        name = st.text_input("이름", placeholder="이름 (선생님은 비밀번호 입력)")
        
        submit = st.form_submit_button("입장하기")
        
        if submit:
            name = name.strip()
            class_num = class_num.strip()
            number = number.strip()

            # [교사 모드] 이름 칸에 비밀번호(takeit)를 입력했을 때
            if name == TEACHER_PASSWORD:
                st.session_state["student_info"] = "TEACHER_MODE"
                st.rerun()
            
            # [학생 모드] 빈칸 없이 잘 입력했는지 확인
            elif class_num and number and name:
                full_info = f"{grade} {class_num}반 {number}번 {name}"
                st.session_state["student_info"] = full_info
                st.rerun()
            else:
                st.error("빈칸을 모두 채워주세요!")
    
    st.stop() # 로그인이 안 됐으면 아래 코드는 실행 안 함

# =========================================================
# 3. 교사 전용 화면 (관리자 페이지)
# =========================================================
if st.session_state["student_info"] == "TEACHER_MODE":
    st.title("👨‍🏫 교사 전용 대시보드")
    st.success("관리자 모드로 접속했습니다.")
    
    col_a, col_b = st.columns([4, 1])
    with col_a:
        st.write(f"📊 총 질문 횟수: {len(chat_logs)}건")
    with col_b:
        if st.button("새로고침"):
            st.rerun()
            
    st.divider()
    st.write("🔽 **학생들의 실시간 질문 로그 (최신순)**")

    if len(chat_logs) > 0:
        for log in reversed(chat_logs):
            # log = [시간, 학생정보, 질문]
            st.markdown(f"**⏰ {log[0]} | 👤 {log[1]}**")
            st.info(f"Q. {log[2]}")
    else:
        st.write("아직 등록된 질문이 없습니다.")
        
    st.stop() # 교사는 챗봇 화면을 볼 필요 없으므로 여기서 끝

# =========================================================
# 4. 학생 전용 화면 (영어 선생님 챗봇)
# =========================================================
student_info = st.session_state["student_info"]

st.title("🏫 Muna E. Teacher")
st.caption(f"로그인 정보: {student_info}")

# (1) PDF 파일 읽기 (있으면 읽고, 없으면 패스)
pdf_content = ""
for file_name in TARGET_FILES:
    if os.path.exists(file_name):
        try:
            with open(file_name, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    pdf_content += page.extract_text() + "\n"
        except:
            pass 

# (2) [핵심] 챗봇 성격 설정 (구문 분석 전문)
if pdf_content:
    context_data = f"[수업 자료 참고]\n{pdf_content}"
else:
    context_data = "수업 자료 PDF가 없습니다. 일반적인 영어 지식으로 답변하세요."

SYSTEM_PROMPT = f"""
[역할]
당신은 고등학교 1학년을 위한 꼼꼼한 '영어 구문 분석 전문가' Muna E. Teacher입니다.
{context_data}

[절대 규칙]
학생이 영어 문장을 질문하면, **반드시 아래의 4단계 포맷을 엄격하게 지켜서** 답변하세요.
설명은 친절하고 구체적이어야 합니다.

[출력 포맷
