import streamlit as st
import google.generativeai as genai
import PyPDF2
import os
import datetime

st.title("📄 Muna E. Teacher")

# =========================================================
# [설정 1] ★여기를 고쳐주세요★ 아까 본 모델 이름을 따옴표 안에 넣으세요
# 예시: "models/gemini-2.0-flash-exp" 또는 "models/gemini-2.0-pro" 등
# =========================================================
MODEL_NAME = "models/gemini-2.0-flash-exp" 

# [설정 2] GitHub에 올린 PDF 파일 이름
TARGET_FILES = ["lesson.pdf"] 

# 1. 사이드바: API 키 관리
with st.sidebar:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")

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
    당신은 고등학교 영어 선생님 'Muna E. Teacher'입니다. 
    아래 [수업 자료]를 바탕으로 학생의 질문에 답변하세요.
    [수업 자료] {pdf_content}
    """
else:
    SYSTEM_PROMPT = "자료가 없습니다."

# 4. Gemini 연결
if not api_key:
    st.warning("API 키가 필요합니다.")
    st.stop()

genai.configure(api_key=api_key)

# ★ 선생님이 적은 모델 이름을 여기서 사용합니다
try:
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    st.error(f"모델 이름({MODEL_NAME})이 틀린 것 같아요. 정확한 이름을 확인해주세요!")
    st.stop()

# 5. 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hi! 질문이 있니?"}]

# 6. 화면 출력
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 7. 사용자 입력 처리
if prompt := st.chat_input("질문을 입력하세요"):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # [CCTV 기능] 서버 로그에 질문 기록
    now = datetime.datetime.now().strftime("%H시 %M분")
    print(f"\n[👀 학생 질문 - {now}] {prompt}")

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
