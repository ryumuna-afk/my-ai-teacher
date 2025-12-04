import streamlit as st
import google.generativeai as genai
import PyPDF2 # PDF를 읽는 도구

# ==========================================
# [제목 수정] 여기에 원하시는 이름을 넣었습니다!
# ==========================================
st.title("📄 Muna E. Teacher")

# 1. 사이드바: API 키 입력 & 파일 업로드
with st.sidebar:
    # API 키 처리
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")
    
    # PDF 파일 업로드 기능
    uploaded_file = st.file_uploader("수업 자료(PDF)를 올려주세요", type=["pdf"])
    st.info("👆 교과서 본문이나 유인물 PDF를 올리면 AI가 내용을 학습합니다.")

# 2. 업로드된 PDF 내용 읽기
pdf_content = ""

if uploaded_file is not None:
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            pdf_content += page.extract_text() + "\n"
        st.success(f"✅ PDF 학습 완료! (총 {len(pdf_reader.pages)}페이지)")
    except Exception as e:
        st.error(f"PDF를 읽는 중 오류가 났어요: {e}")

# 3. 챗봇 성격 설정 (PDF 내용이 있으면 반영)
if pdf_content:
    SYSTEM_PROMPT = f"""
    [당신의 역할]
    당신은 고등학교 영어 선생님 'Muna E. Teacher'입니다. 
    아래 제공된 [PDF 수업 자료]를 바탕으로 학생의 질문에 답변하세요.

    [PDF 수업 자료]
    {pdf_content}

    [행동 지침]
    1. 학생 질문이 [PDF 수업 자료]와 관련 있다면, 그 내용을 바탕으로 상세히 설명하세요.
    2. 문법 설명은 한국어로, 예시는 자료 문장을 인용하세요.
    3. 자료에 없는 내용을 물어보면 "그건 업로드된 PDF에 없는 내용이야."라고 답하세요.
    """
else:
    # 파일이 없을 때의 기본 모드
    SYSTEM_PROMPT = """
    당신은 친절한 영어 선생님 'Muna E. Teacher'입니다. 
    현재 업로드된 자료가 없으므로, 일반적인 영어 지식으로 답변하세요.
    학생들에게 "좌측 사이드바에 PDF 자료를 올려주세요"라고 안내하면 좋습니다.
    """

# 4. Gemini 연결
if not api_key:
    st.warning("API 키가 필요합니다.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("models/gemini-pro-latest")

# 5. 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hello! I am Muna E. Teacher. PDF 자료를 올리고 질문해 주세요!"}]

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
