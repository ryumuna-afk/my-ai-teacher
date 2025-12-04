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

st.set_page_config(page_title="Muna E. Teacher", page_icon="🏫")

# =========================================================
# [꿀팁] 지저분한 메뉴와 'Manage app' 버튼 숨기기 (CSS)
# =========================================================
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display:none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 1. 사이드바: API 키 관리
with st.sidebar:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")

# =========================================================
# [기능 1] 입장 전 정보 입력받기 (학년/반/번호/이름)
# =========================================================
if "student_info" not in st.session_state:
    st.title("🔒 수업 입장하기")
    st.write("학생 정보를 정확히 입력해야 입장할 수 있습니다.")
    
    with st.form("login_form"):
        # 보기 좋게 3칸으로 나누기 (학년, 반, 번호)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            grade = st.selectbox("학년", ["1학년", "2학년", "3학년"])
        with col2:
            class_num = st.text_input("반", placeholder="예: 3")
        with col3:
            number = st.text_input("번호", placeholder="예: 15")
            
        name = st.text_input("이름", placeholder="예: 홍길동")
        
        submit_button = st.form_submit_button("수업 시작하기")
        
        if submit_button:
            # 빈칸이 하나라도 있으면 안 됨
            if class_num.strip() and number.strip() and name.strip():
                # 정보를 합쳐서 저장 (예: "1학년 3반 15번 홍길동")
                full_info = f"{grade} {class_num}반 {number}번 {name}"
                st.session_state["student_info"] = full_info
                st.rerun() # 새로고침
            else:
                st.error("빈칸을 모두 채워주세요!")
    
    st.stop() # 입력 전까지 멈춤

# =========================================================
# 로그인 통과 후 화면
# =========================================================
student_info = st.session_state["student_info"]
st.title(f"🏫 Muna E. Teacher")
st.caption(f"로그인 정보: {student_info}") # 상단에 작게 표시

# 2. 서버에 있는 PDF 파일들 읽기
pdf_content = ""
for file_name in TARGET_FILES:
    if os.path.exists(file_name):
        try:
            with open(file_name, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                file_text = ""
                for page in pdf_reader.pages:
                    file_text += page.extract_text() + "\n"
                pdf_content += f"\n--- [파일: {file_name}] ---\n{file_text}\n"
        except Exception:
            pass 

# 3. 챗봇 성격 설정
if pdf_content:
    SYSTEM_PROMPT = f"""
   [당신의 역할]
    당신은 에너지가 넘치고 친절한 고등학교 영어 선생님 'Muna E. Teacher'입니다.
    지루한 영어 수업은 딱 질색입니다! 아래 [수업 자료]를 바탕으로 재미있지만 유용하게 알려주세요.

    [수업 자료]
    {pdf_content}

    [행동 지침]
    1. 말투: "완전 좋은 질문이야! 😎", "이건 쌤이 딱 알려줄게!", "우리 제자 천재 아냐? ✨" 처럼 이모지를 섞어 친근하고 높은 텐션으로 말하세요.
    2. 설명 방식: 딱딱한 사전적 정의 금지! 학생들이 이해하기 쉬운 '재미있는 비유'나 '실생활 예시'를 들어 설명하세요.
    3. 피드백: 학생이 틀려도 "땡! 다시 해!"라고 하지 말고, "오~ 거의 다 왔어! 조금만 고쳐볼까? 🔥"라고 유쾌하게 격려해주세요.
    4. 자료 활용: 질문이 [수업 자료]에 있다면 그 내용을 바탕으로 설명하고, 
       자료에 없다면 "어라? 그건 우리 비법 노트(학습지)에는 없는 내용이네! 🕵️ 수업 내용 중에 궁금한 건 없어?"라고 재치 있게 넘기세요.
    """
else:
    SYSTEM_PROMPT = "자료가 없습니다. 선생님께 파일을 확인해달라고 하세요! 😅"

# 4. Gemini 연결
if not api_key:
    st.warning("API 키가 필요합니다.")
    st.stop()

genai.configure(api_key=api_key)
try:
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    st.error(f"모델 이름 오류: {MODEL_NAME}")
    st.stop()

# 5. 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": f"반가워, {student_info} 학생! 무엇을 도와줄까?"}]

# 6. 화면 출력
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 7. 사용자 입력 처리
if prompt := st.chat_input("질문을 입력하세요"):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # [CCTV 기능] 예: "[👀 1학년 3반 15번 홍길동 - 10:45:12] 질문내용"
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"\n[👀 {student_info} - {now}] {prompt}") 

    # 문맥 정리
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
            st.error(f"오류: {e}")



