import streamlit as st
import google.generativeai as genai

# ==========================================
# [설정 1] 챗봇의 성격 (여기만 고치면 챗봇이 바뀝니다!)
# ==========================================
SYSTEM_PROMPT = """
당신은 고등학교 학생들을 가르치는 친절하고 유머러스한 '영어 전문가' 선생님입니다.
다음 원칙을 지켜서 대답하세요:
1. 학생 수준에 맞춰서 이해하기 쉽게 설명한다.
2. 너무 딱딱하지 않게, 가끔은 이모지(🏗️, 🧱)를 사용한다.
3. 답변은 3~4문장 정도로 간결하게 핵심만 말한다.
4. 모르는 내용은 솔직히 모른다고 한다.
"""

st.title("🏗️ Muna E. Teacher")

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
    st.session_state["messages"] = [{"role": "assistant", "content": "안녕! 건축 안전에 대해 궁금한 게 있니? 선생님이 알려줄게!"}]

# 3. 이전 대화 화면에 출력
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 4. 사용자 입력 처리
if prompt := st.chat_input("질문을 입력하세요"):
    # 사용자 메시지 표시 & 저장
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # ==========================================
    # [핵심 업그레이드] 시스템 프롬프트 + 문맥 정리
    # ==========================================
    full_prompt = SYSTEM_PROMPT + "\n\n" # 성격을 가장 먼저 주입
    
    # 최근 대화 10개만 기억하게 하기 (속도 향상 팁!)
    recent_messages = st.session_state.messages[-10:] 
    
    for msg in recent_messages:
        role = "User" if msg["role"] == "user" else "Model"
        full_prompt += f"{role}: {msg['content']}\n"
    
    # ==========================================
    # [핵심 업그레이드] 타자 치듯이 출력하기 (Streaming)
    # ==========================================
    with st.chat_message("assistant"):
        message_placeholder = st.empty() # 빈 공간을 만듦
        full_response = ""

        try:
            # stream=True 옵션이 핵심! 한 글자씩 받아옵니다.
            responses = model.generate_content(full_prompt, stream=True)
            
            for response in responses:
                if response.text:
                    full_response += response.text
                    # 한 글자씩 추가될 때마다 화면을 갱신
                    message_placeholder.markdown(full_response + "▌")
            
            # 다 끝나면 커서(▌) 제거하고 최종본 확정
            message_placeholder.markdown(full_response)
            
            # 대화 기록에 저장
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"오류가 났어요: {e}")
