import streamlit as st
import google.generativeai as genai
import PyPDF2
import os
import datetime
import random
from gtts import gTTS 
import io 
import re 
import json # [추가] 파일을 다루기 위한 도구

# =========================================================
# [설정] 기본 환경 설정
# =========================================================
MODEL_NAME = "models/gemini-pro-latest" 
TARGET_FILES = ["lesson.pdf"]  
DAILY_LIMIT = 5 # 하루 질문 제한

# [보안] 비밀번호
if "TEACHER_PASSWORD" in st.secrets:
    TEACHER_PASSWORD = st.secrets["TEACHER_PASSWORD"]
else:
    TEACHER_PASSWORD = "admin" 

st.set_page_config(page_title="Muna Teacher", page_icon="🏫")

# [디자인] 화면 깔끔하게 만들기
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display:none;}
.block-container {padding-top: 2rem;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# =========================================================
# [핵심 기능] 파일 기반 데이터베이스 (DB)
# =========================================================
DB_FILE = "school_db.json" # 이 파일에 기록을 저장합니다

def load_db():
    """파일에서 데이터를 읽어옵니다."""
    if not os.path.exists(DB_FILE):
        return {"logs": [], "notice": "", "usage": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"logs": [], "notice": "", "usage": {}}

def save_db(data):
    """파일에 데이터를 저장합니다."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 앱이 실행될 때마다 최신 데이터를 불러옵니다
db = load_db()

# =========================================================
# [함수] 깔끔한 영어 추출기 (TTS용)
# =========================================================
def clean_english_for_tts(text):
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'[가-힣]+', '', text)
    text = re.sub(r'[^a-zA-Z0-9.,!?\'\"\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# =========================================================
# 1. 사이드바
# =========================================================
with st.sidebar:
    st.header("⚙️ 설정")
    
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")
        
    st.divider()

    # 질문 횟수 표시
    if "student_info" in st.session_state and st.session_state["student_info"] != "TEACHER_MODE":
        student_info = st.session_state["student_info"]
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        usage_key = f"{today_str}_{student_info}"
        
        # 파일(db)에서 횟수 확인
        current_count = db["usage"].get(usage_key, 0)
        remaining = DAILY_LIMIT - current_count
        
        if remaining > 0:
            st.success(f"🎫 **남은 질문: {remaining}회**")
            st.progress(current_count / DAILY_LIMIT)
        else:
            st.error("⛔ **오늘 질문 끝!**")

    st.divider()
    
    st.header("🧩 복습 퀴즈")
    if st.button("지금까지 내용으로 퀴즈 내줘!"):
        if "messages" in st.session_state and len(st.session_state.messages) > 1:
            st.session_state["quiz_requested"] = True
        else:
            st.warning("아직 대화 내용이 부족해요!")

    st.divider()
    st.info("📢 **학습 규칙**")
    st.caption(f"1. 하루 {DAILY_LIMIT}문제만 질문 가능!")
    st.caption("2. 정답만 묻기 없기! 🙅‍♂️")

# =========================================================
# 2. 로그인 화면
# =========================================================
if "student_info" not in st.session_state:
    st.title("🔒 수업 입장하기")
    
    with st.form("login_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            grade = st.selectbox("학년", ["1학년", "2학년", "3학년"])
        with col2:
            class_num = st.text_input("반", placeholder="숫자만 (예: 3)")
        with col3:
            number = st.text_input("번호", placeholder="숫자만 (예: 15)")
            
        name = st.text_input("이름", placeholder="이름 (선생님은 비밀번호 입력)")
        
        submit = st.form_submit_button("입장하기")
        
        if submit:
            name = name.strip()
            
            if name == TEACHER_PASSWORD:
                st.session_state["student_info"] = "TEACHER_MODE"
                st.rerun()
            
            elif class_num and number and name:
                full_info = f"{grade} {class_num}반 {number}번 {name}"
                st.session_state["student_info"] = full_info
                st.session_state["student_name"] = name 
                st.rerun()
            else:
                st.error("빈칸을 모두 채워주세요!")
    
    st.stop()

# =========================================================
# 3. 교사 전용 화면
# =========================================================
if st.session_state["student_info"] == "TEACHER_MODE":
    st.title("👨‍🏫 Muna Teacher 대시보드")
    
    st.subheader("📢 학생들에게 메세지 보내기")
    # 파일(db)에서 공지 불러오기
    current_notice = db.get("notice", "")
    new_notice = st.text_input("공지 내용을 입력하고 엔터를 치세요", value=current_notice)
    
    if new_notice != current_notice:
        db["notice"] = new_notice
        save_db(db) # 변경사항 저장
        st.success("공지가 업데이트되었습니다!")
        st.rerun()
    
    st.divider()
    
    col_a, col_b = st.columns([4, 1])
    with col_a:
        st.write(f"📊 총 질문 횟수: {len(db['logs'])}건")
    with col_b:
        if st.button("새로고침"):
            st.rerun()
            
    st.write("🔽 **실시간 질문 로그**")
    if len(db['logs']) > 0:
        for log in reversed(db['logs']):
            st.markdown(f"**⏰ {log[0]} | 👤 {log[1]}**")
            st.info(f"Q. {log[2]}")
    else:
        st.write("아직 질문이 없습니다.")
        
    st.stop()

# =========================================================
# 4. 학생 전용 화면 (영어 선생님 챗봇)
# =========================================================
student_info = st.session_state["student_info"]
student_name = st.session_state.get("student_name", "친구")

st.title("🏫 Muna Teacher")
st.caption(f"로그인 정보: {student_info}")

if db["notice"]:
    st.warning(f"📢 **선생님 말씀:** {db['notice']}")

# (1) PDF 파일 읽기
pdf_content = ""
for file_name in TARGET_FILES:
    if os.path.exists(file_name):
        try:
            with open(file_name, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    pdf_content += page.extract_text() + "\n"
        except:
            pass 

# (2) 챗봇 성격 설정
if pdf_content:
    context_data = f"[수업 자료 참고]\n{pdf_content}"
else:
    context_data = "수업 자료 PDF가 없습니다. 일반적인 영어 지식으로 답변하세요."

SYSTEM_PROMPT = f"""
[역할]
당신은 고등학교 1학년을 위한 '영어 구문 분석 전문가' Muna Teacher입니다.
{context_data}

[행동 지침]
1. 정답만 알려달라고 하면 정중히 거절하고 힌트를 주세요.
2. 학생이 영어 문장을 질문하면, **반드시 아래 4단계 포맷**을 지키세요.
3. 설명은 **핵심만 간결하게(단답형)** 작성하세요.

[분석 시 주의사항]
- **병렬 구조:** and/but 연결 확인.
- **5형식 동사:** 목적격 보어[OC] 구조 구별.

[출력 포맷 예시]
1. **[직독직해]** (끊어 읽기)
2. **[구문 분석]** ([S], [V], [O], [OC])
3. **[상세 설명]** (핵심만)
4. **[핵심 문법]** (한 줄 요약)
"""

# (3) Gemini 연결
if not api_key:
    st.warning("API 키 설정을 확인해주세요.")
    st.stop()

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

genai.configure(api_key=api_key)
try:
    model = genai.GenerativeModel(MODEL_NAME, safety_settings=safety_settings)
except:
    st.error(f"모델 설정 오류: {MODEL_NAME}을 찾을 수 없습니다.")
    st.stop()

# (4) 채팅 기록 초기화
if "messages" not in st.session_state:
    welcome_msg = f"안녕! 👋 {student_name}야. 영어 공부하다 막히는 거 있으면 언제든 물어봐!\n(하루에 {DAILY_LIMIT}개까지만 질문할 수 있어! 아껴 써야 해 😉)"
    st.session_state["messages"] = [{"role": "assistant", "content": welcome_msg}]

# (5) 대화 화면 출력
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# (6) 퀴즈 생성 처리
if st.session_state.get("quiz_requested"):
    st.session_state["quiz_requested"] = False
    with st.chat_message("assistant"):
        with st.spinner("퀴즈를 만들고 있어요... 🤔"):
            quiz_prompt = "지금까지의 대화 내용을 바탕으로 학생이 이해했는지 확인하는 **객관식 퀴즈 1문제**를 만들어줘. 정답과 해설은 맨 아래에 숨겨서(스포일러 방지) 출력해."
            full_context = ""
            for msg in st.session_state.messages[-10:]:
                full_context += f"{msg['role']}: {msg['content']}\n"
            try:
                response = model.generate_content(quiz_prompt + "\n\n" + full_context)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except:
                st.error("퀴즈 생성 실패")

# (7) 사용자 입력 처리
if prompt := st.chat_input("영어 문장을 입력하세요..."):
    
    # -----------------------------------------------------
    # [수정됨] 파일 DB에서 질문 횟수 체크
    # -----------------------------------------------------
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    usage_key = f"{today_str}_{student_info}"
    current_count = db["usage"].get(usage_key, 0)
    
    if current_count >= DAILY_LIMIT:
        st.error(f"⛔ **오늘의 질문 횟수({DAILY_LIMIT}회)를 모두 다 썼어!** 내일 다시 만나자 👋")
    else:
        st.chat_message("user").write(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 1. 로그 저장
        now = datetime.datetime.now().strftime("%H:%M:%S")
        db["logs"].append([now, student_info, prompt]) 
        
        # 2. 카운트 증가 및 파일 저장 (즉시 저장!)
        db["usage"][usage_key] = current_count + 1
        save_db(db) # 파일에 꽝! 박아넣기
        
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
                
                if random.random() < 0.2:
                    full_response += "\n\n---\n💡 **[Self-Check]** 스스로 고민해보고, 교과서와 비교해보세요! 👀"
                
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

                # 영어 발음만 골라서 읽어주기
                try:
                    clean_english = clean_english_for_tts(full_response)
                    if len(clean_english.split()) >= 3:
                        tts = gTTS(text=clean_english, lang='en')
                        audio_fp = io.BytesIO()
                        tts.write_to_fp(audio_fp)
                        st.audio(audio_fp, format='audio/mp3')
                except:
                    pass 

            except Exception as e:
                if "finish_reason" in str(e):
                     st.error("AI가 답변을 주저하고 있어요. (안전 필터)")
                else:
                     st.error(f"오류가 발생했습니다: {e}")
