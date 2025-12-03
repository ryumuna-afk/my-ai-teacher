import streamlit as st
import google.generativeai as genai

# 1. 제목 설정
st.title("🤖 우리 반 AI 선생님")

# 2. 금고(Secrets)에서 비밀번호 꺼내오기
# (학생들 눈에는 이 과정이 안 보입니다!)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except FileNotFoundError:
    st.error("선생님! 서버에 키가 등록되지 않았어요. Secrets 설정을 확인해주세요.")
    st.stop()

# 3. Gemini 연결하기
genai.configure(api_key=api_key)
model = genai.GenerativeModel("models/gemini-pro-latest")

# 4. 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "안녕? 나는 AI 선생님이야. 무엇을 도와줄까?"}]

# 5. 이전 대화 화면에 보여주기
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 6. 학생 입력 처리
if prompt := st.chat_input("질문을 입력하세요"):
    # 학생 질문 표시
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # AI에게 질문 전달을 위한 문맥 정리
    full_prompt = "너는 친절한 고등학교 영어 교사야. 고등학생 수준에 맞춰서 쉽고 재미있게 설명해 줘."
    for msg in st.session_state.messages:
        role = "User" if msg["role"] == "user" else "Model"
        full_prompt += f"{role}: {msg['content']}\n"
    
    try:
        # AI 답변 생성
        response = model.generate_content(full_prompt)
        msg = response.text
        
        # 답변 표시
        st.chat_message("assistant").write(msg)
        st.session_state.messages.append({"role": "assistant", "content": msg})
        
    except Exception as e:
        st.error(f"오류가 발생했어요 ㅠㅠ: {e}")

