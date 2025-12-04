import streamlit as st
import google.generativeai as genai
import PyPDF2
import os

st.title("📄 Muna E. Teacher")

# =========================================================
# [설정] 여기에 GitHub에 올린 파일명을 정확히 적어주세요!
# =========================================================
TARGET_FILE_NAME = "lesson.pdf" 

# 1. 사이드바: API 키 관리
with st.sidebar:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")

# 2. 서버에 있는 PDF 파일 몰래 읽기
pdf_content = ""

# 파일이 진짜 있는지 확인
if os.path.exists(TARGET_FILE_NAME):
    try:
        # 업로드 버튼 대신, 서버에 있는 파일을 직접 엽니다
        with open(TARGET_FILE_NAME, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                pdf_content += page.extract_text() + "\n"
        # 학생들 눈에는 안 보이지만 학습 완료 메시지 띄우기 (선택)
        # st.success(f"✅ 선생님이 준비한 학습 자료가 로딩되었습니다!")
    except Exception as e:
        st.error(f"파일을 읽는 중 에러가 났어요: {e}")
else:
    st.error(f"⚠️ '{TARGET_FILE_NAME}' 파일을 찾을 수 없습니다. GitHub에 파일을 올리셨나요?")

# 3. 챗봇 성격 설정
if pdf_content:
    SYSTEM_PROMPT = f"""
    [당신의 역할]
    당신은 고등학교 영어 선생님 'Muna E. Teacher'입니다. 
    이미 학습된 [수업 자료]를 바탕으로 학생의 질문에 답변하세요.

    [수업 자료]
    {pdf_content}

    [행동 지침]
    1. 학생의 질문이 [수업 자료] 내용과 관련 있으면 상세히 설명하세요.
    2. 자료에 없는 엉뚱한 질문을 하면 "오늘 수업 내용과 관련 없는 질문이구나. 수업 내용에 집중해볼까?"라고 부드럽게 넘기세요.
    3. 한국어로 설명하되, 중요한 영어 표현은 원문을 인용하세요.
    """
else:
    SYSTEM_PROMPT = "자료가 로딩되지 않았습니다. 선생님께 문의하세요."

# 4. Gemini 연결
if not api_key:
    st.warning("API 키가 필요합니다.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("models/gemini-pro-latest")

# 5. 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hi! 오늘 수업 내용에 대해 궁금한 게 있니?"}]

# 6. 화면 출력
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 7. 사용자 입력 처리
if prompt := st.chat_input("질문을 입력하세요"):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

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
