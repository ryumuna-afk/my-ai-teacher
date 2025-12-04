import streamlit as st
import google.generativeai as genai
import PyPDF2
import os
import datetime

# =========================================================
# [설정] 기본 환경 설정
# =========================================================
MODEL_NAME = "models/gemini-pro-latest" 
TARGET_FILES = ["lesson.pdf"]  # PDF 파일 이름
TEACHER_PASSWORD = "takeit"    # 선생님 비밀번호

st.set_page_config(page_title="Muna E. Teacher", page_icon="🏫")

# [디자인] 화면 깔끔하게 만들기
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
# [기능] 채팅 로그 저장소
# =========================================================
@st.cache_resource
def get_shared_logs():
    return []

chat_logs = get_shared_logs()

# =========================================================
# 1. 사이드바 (API 키 설정)
# =========================================================
with st.sidebar:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key를 입력하세요", type="password")

# =========================================================
# 2. 로그인 화면
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

            if name == TEACHER_PASSWORD:
                st.session_state["student_info"] = "TEACHER_MODE"
                st.rerun()
            
            elif class_num and number and name:
                full_info = f"{grade} {class_num}반 {number}번 {name}"
                st.session_state["student_info"] = full_info
                st.rerun()
            else:
                st.error("빈칸을 모두 채워주세요!")
    
    st.stop()

# =========================================================
# 3. 교사 전용 화면
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
            st.markdown(f"**⏰ {log[0]} | 👤 {log[1]}**")
            st.info(f"Q. {log[2]}")
    else:
        st.write("아직 등록된 질문이 없습니다.")
        
    st.stop()

# =========================================================
# 4. 학생 전용 화면 (영어 선생님 챗봇)
# =========================================================
student_info = st.session_state["student_info"]

st.title("🏫 Muna E. Teacher")
st.caption(f"로그인 정보: {student_info}")

# (1) PDF 파일 읽기
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

# (2) [핵심] 챗봇 성격 설정 (여기가 길어서 잘릴 수 있으니 주의하세요!)
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

[출력 포맷 예시] (이 형식을 그대로 따를 것)

1. **[직독직해]**
   - Studying English hard / is important / for your future.
   - 영어를 열심히 공부하는 것은 / 중요하다 / 너의 미래를 위해.

2. **[구문 분석]**
   - [S] Studying English hard
   - [V] is
   - [C] important
   - (M) for your future

3. **[상세 설명]**
   - 주어(S): Studying English hard (동명사구 주어)
   - 동사(V): is (be동사, 현재시제)
   - 보어(C): important (형용사)
   - 전치사구: (for your future)는 '너의 미래를 위해'라는 뜻으로 형용사 important를 수식하거나 문장 전체를 보충합니다.

4. **[핵심 문법]**
   - 동명사 주어: Studying처럼 동사에 -ing를 붙여 주어로 쓰면 '~하는 것'으로 해석합니다. 동명사 주어는 무조건 **단수 취급**하므로 동사 자리에 are가 아닌 is가 왔습니다.
""" 
# 👆 위 따옴표 3개(""")가 꼭 있어야 합니다!

# (3) Gemini 연결
if not api_key:
    st.warning("선생님이 아직 API 키를 입력하지 않으셨습니다.")
    st.stop()

genai.configure(api_key=api_key)
try:
    model = genai.GenerativeModel(MODEL_NAME)
except:
    st.error(f"모델 설정 오류: {MODEL_NAME}을 찾을 수 없습니다.")
    st.stop()

# (4) 채팅 기록 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hi there! 👋 해석이 안 되거나 분석하고 싶은 영어 문장을 입력해봐!"}]

# (5) 대화 화면 출력
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# (6) 사용자 입력 처리
if prompt := st.chat_input("영어 문장을 입력하세요..."):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 로그 저장
    now = datetime.datetime.now().strftime("%H:%M:%S")
    chat_logs.append([now, student_info, prompt]) 
    
    # 프롬프트 조립
    full_prompt = SYSTEM_PROMPT + "\n\n"
    recent_messages = st.session_state.messages[-10:]
    for msg in recent_messages:
        role = "User" if msg["role"] == "user" else "Model"
        full_prompt += f"{role}: {msg['content']}\n"
    
    # 답변 생성
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            responses = model.generate_content(full_prompt, stream=True)
            for response in responses:
                if response.text:
                    full_response += response.text
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")