import streamlit as st
import google.generativeai as genai
import PyPDF2
import os

st.title("📄 Muna E. Teacher")

# =========================================================
# [설정] 읽어야 할 파일들의 이름을 리스트(목록)로 적으세요!
# 따옴표 안에 깃허브에 올린 파일명을 정확히 적고, 쉼표(,)로 구분합니다.
# =========================================================
TARGET_FILES = ["lesson.pdf", "reading.pdf"] 

# 1. 사이드바: API 키 관리
with st.sidebar:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")

# 2. 서버에 있는 PDF 파일들 몽땅 읽기
pdf_content = ""
read_files_count = 0

# 리스트에 있는 파일들을 하나씩 꺼내서 읽습니다
for file_name in TARGET_FILES:
    if os.path.exists(file_name):
        try:
            with open(file_name, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                file_text = ""
                for page in pdf_reader.pages:
                    file_text += page.extract_text() + "\n"
                
                # AI가 어떤 파일 내용인지 알 수 있게 파일 이름표를 붙여줍니다
                pdf_content += f"\n--- [파일: {file_name}] ---\n{file_text}\n"
                read_files_count += 1
        except Exception as e:
            st.error(f"⚠️ '{file_name}' 읽기 실패: {e}")
    else:
        # 파일이 없으면 경고 메시지 (학생에겐 안 보임, 로그용)
        print(f"파일을 찾을 수 없음: {file_name}")

# 3. 챗봇 성격 설정
if pdf_content:
    SYSTEM_PROMPT = f"""
    [당신의 역할]
    당신은 고등학교 영어 선생님 'Muna E. Teacher'입니다. 
    아래 제공된 [수업 자료들]을 모두 읽고 학생의 질문에 답변하세요.

    [수업 자료들]
    {pdf_content}

    [행동 지침]
    1. 학생의 질문이 [수업 자료들] 중 어디에 해당하는지 파악하고 상세히 설명하세요.
    2. 학습지 문제에 대한 질문이면, 함께 제공된 지문(reading) 내용을 근거로 설명해 주세요.
    3. 자료에 없는 질문을 하면 수업 내용에 집중하도록 유도하세요.
    4. 한국어로 설명하되, 영어 지문의 핵심 문장은 원문을 인용하세요.
    """
    # 성공 메시지 (선택 사항)
    # st.success(f"✅ 총 {read_files_count}개의 파일을 학습했습니다!")
else:
    SYSTEM_PROMPT = "업로드된 자료가 하나도 없습니다. GitHub에 파일을 확인해주세요."
    st.error("⚠️ GitHub에 파일이 없거나 이름을 잘못 적었습니다.")

# 4. Gemini 연결
if not api_key:
    st.warning("API 키가 필요합니다.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("models/gemini-pro-latest")

# 5. 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hi! 지문이랑 학습지 다 읽고 왔어. 무엇을 도와줄까?"}]

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
