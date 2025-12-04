import streamlit as st
import google.generativeai as genai
from datetime import datetime

# ==========================================
# [설정 0] 현재 시간과 계절 계산
# ==========================================
now = datetime.now()
current_date = now.strftime("%Y년 %m월 %d일")

# ==========================================
# [설정 1] 영어 선생님 페르소나 (성격) 설정
# ==========================================
SYSTEM_PROMPT = f"""
[기본 정보]
- 오늘은 {current_date}입니다.
- 당신은 고등학교 1학년 학생들을 가르치는 열정적이고 친절한 '영어 선생님'입니다.
- 인터넷 검색은 할 수 없습니다.

[행동 지침]
1. 설명은 '한국어'로 하되, 예문은 반드시 '영어'로 보여주세요.
2. 학생이 문법이나 단어를 물어보면, 고등학생 수준에 맞는 유의어(Synonym)나 반의어를 하나씩 덧붙여 주세요. (꿀팁처럼!)
3. 학생이 영어 문장을 입력하면, 더 자연스러운 표현으로 교정(Correction)해주고 이유를 설명하세요.
4. 말투는 친근하게 해요. (예: "이건 시험에 자주 나오는 거야!", "아주 좋은 질문이야! 👍")
5. 모르는 내용은 솔직히 모른다고 하고, 함께 찾아보자고 격려하세요.
"""

st.title("🇺🇸 우리 반 영어 쌤 (AI)")

# 1. 금고에서 키 꺼내기
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except FileNotFoundError:
    st.error("서버에 키가 없습니다. Streamlit Secrets를 확인하세요.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("models/gemini-pro-latest")

# 2. 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": f"Hi there! 👋 영어 공부하다 막히는 거 있니? 문법, 독해, 작문 다 물어봐!"}]

# 3. 이전 대화 화면에 출력
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 4. 사용자 입력 처리
if prompt := st.chat_input("영어 질문이나 해석하고 싶은 문장을 입력하세요"):
    # 사용자 메시지 표시 & 저장
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 문맥 정리
    full_prompt = SYSTEM_PROMPT + "\n\n"
    
    # 최근 대화 10개만 기억
    recent_messages = st.session_state.messages[-10:] 
    
    for msg in recent_messages:
        role = "User" if msg["role"] == "user" else "Model"
        full_prompt += f"{role}: {msg['content']}\n"
    
    # 답변 생성 (타자 치는 효과)
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
            st.error(f"오류가 났어요: {e}")
