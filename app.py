import streamlit as st
import google.generativeai as genai

st.title("🤖 나만의 AI 비서 (Gemini)")

# 1. 사이드바에 키 입력창 배치
with st.sidebar:
    gemini_api_key = st.text_input("Gemini API Key를 입력하세요", key="chatbot_api_key", type="password")

# 2. 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "안녕하세요! 무엇이든 물어보세요."}]

# 3. 대화 내용 화면에 출력
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 4. 사용자 입력 처리
if prompt := st.chat_input():
    # 키가 없으면 멈춤
    if not gemini_api_key:
        st.info("왼쪽 사이드바에 API Key를 넣어주세요.")
        st.stop()

    # 내 메시지 화면에 표시 & 저장
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 5. Gemini 연결 (여기가 핵심!)
    genai.configure(api_key=gemini_api_key)
    
    # ★ 방금 찾은 모델 이름을 정확히 넣었습니다 ★
    model = genai.GenerativeModel("models/gemini-pro-latest")

    # 6. 대화 맥락 유지하기
    full_prompt = ""
    for msg in st.session_state.messages:
        role = "User" if msg["role"] == "user" else "Model"
        full_prompt += f"{role}: {msg['content']}\n"
    
    try:
        # AI에게 답변 요청
        response = model.generate_content(full_prompt)
        msg = response.text
        
        # AI 답변 화면에 표시 & 저장
        st.chat_message("assistant").write(msg)
        st.session_state.messages.append({"role": "assistant", "content": msg})
        
    except Exception as e:
        st.error(f"에러가 났어요: {e}")