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

st.set_page_config(page_title="Muna E. Teacher", page_icon="🏫")

# =========================================================
# [핵심 기능] 모든 학생의 질문을 저장하는 '공유 메모리' 만들기
# =========================================================
@st.cache_resource
def get_shared_logs():
    # 서버가 켜져 있는 동안 유지되는 리스트입니다.
    return []

# 공유된 로그 리스트를 가져옵니다.
chat_logs = get_shared_logs()

# 1. 사이드바: API 키 관리
with st.sidebar:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")

# =========================================================
# [로그인 화면] 교사 / 학생 구분
# =========================================================
if "student_info" not in st.session_state:
    st.title("🔒 수업 입장하기")
    
    with st.form("login_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            grade = st.selectbox("학년", ["1학년", "2학년", "3학년", "교사"])
        with col2:
            class_num = st.text_input("반", placeholder="반 (교사는 비워둠)")
        with col3:
            number = st.text_input("번호", placeholder="번호 (교사는 비워둠)")
            
        name = st.text_input("이름", placeholder="이름 (교사는 '교사' 입력)")
        
        submit_button = st.form_submit_button("입장하기")
        
        if submit_button:
            # [교사 모드] 이름에 '교사'라고 적으면 관리자 모드로 진입
            if grade == "교사" or name == "교사":
                st.session_state["student_info"] = "TEACHER_MODE"
                st.rerun()
            
            # [학생 모드]
            elif class_num.strip() and number.strip() and name.strip():
                full_info = f"{grade} {class_num}반 {number}번 {name}"
                st.session_state["student_info"] = full_info
                st.rerun()
            else:
                st.error("빈칸을 모두 채워주세요!")
    st.stop()

# =========================================================
# [교사 전용 화면] 실시간 질문 모니터링 (CCTV)
# =========================================================
if st.session_state["student_info"] == "TEACHER_MODE":
    st.title("👨‍🏫 실시간 학생 질문 모니터링")
    st.info("새로운 질문을 보려면 키보드의 'R'키를 누르거나 화면을 새로고침하세요.")
    
    if st.button("새로고침 (최신 질문 보기)"):
        st.rerun()

    st.divider()

    # 저장된 로그를 최신순(거꾸로)으로 보여줌
    if len(chat_logs) > 0:
        for log in reversed(chat_logs):
            # log는 [시간, 학생정보, 질문내용] 으로 되어 있음
            st.markdown(f"**⏰ {log[0]} | 👤 {log[1]}**")
            st.code(f"{log[2]}") # 질문 내용을 박스 안에 표시
            st.markdown("---")
    else:
        st.write("아직 등록된 질문이 없습니다.")
    
    st.stop() # 교사는 여기서 끝 (아래 챗봇 화면 안 보여줌)

# =========================================================
# [학생 전용 화면] 챗봇 수업 시작
# =========================================================
student_info = st.session_state["student_info"]
st.title("🏫 Muna E. Teacher")
st.caption(f"로그인: {student_info}")

# 2. PDF 읽기
pdf_content = ""
for file_name in TARGET_FILES:
    if os.path.exists(file_name):
        try:
            with open(file_name, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    pdf_content += page.extract_text() + "\n"
        except Exception:
            pass 

# 3. 프롬프트 설정
if pdf_content:
    SYSTEM_PROMPT = f"""
    [역할] 고등학교 영어 선생님 'Muna E. Teacher'. 유쾌하고 친절함.
    [자료] {pdf_content}
    [지침] 자료 기반 답변. 유쾌한 이모지 사용.
    """
else:
    SYSTEM_PROMPT = "자료 없음."

# 4. Gemini 연결
if not api_key:
    st.warning("API 키 필요")
    st.stop()
genai.configure(api_key=api_key)
try:
    model = genai.GenerativeModel(MODEL_NAME)
except Exception:
    st.error("모델 이름 오류")
    st.stop()

# 5. 대화 기록
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hi! 수업 내용 질문해봐! 😎"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 6. 질문 처리 및 ★로그 저장★
if prompt := st.chat_input("질문을 입력하세요"):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # [중요] 학생의 질문을 '공유 메모리'에 저장합니다! (선생님이 보도록)
    now = datetime.datetime.now().strftime("%H:%M:%S")
    # 리스트에 [시간, 이름, 질문] 형태로 추가
    chat_logs.append([now, student_info, prompt]) 
    
    # 문맥 정리 & 답변 생성
    full_prompt = SYSTEM_PROMPT + "\n\n"
    recent_messages = st.session_state.messages[-10:] 
    for msg in recent_messages:
        role = "User" if msg["role"] == "user" else "Model"
        full_prompt += f"{role}: {msg['content']}\n"
    
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
            st.error(f"오류: {e}")
