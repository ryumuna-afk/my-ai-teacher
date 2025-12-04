import streamlit as st
import google.generativeai as genai

st.title("🔍 내 계정의 Flash 모델 찾기")

# API 키 입력
api_key = st.text_input("Gemini API Key를 입력하세요", type="password")

if st.button("모델 명단 불러오기"):
    if not api_key:
        st.error("키를 입력해주세요!")
    else:
        try:
            genai.configure(api_key=api_key)
            st.write("### 👇 사용 가능한 모델 목록:")
            
            found_flash = False
            # 구글 서버에 있는 모델 명단을 다 가져옵니다
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    # 이름에 'flash'가 들어가는 녀석을 강조해서 보여줍니다
                    if 'flash' in m.name:
                        st.success(f"⚡ 찾았다! Flash 모델: {m.name}")
                        st.code(m.name) # 복사하기 좋게 표시
                        found_flash = True
                    else:
                        st.write(m.name)
            
            if not found_flash:
                st.error("Flash 모델이 안 보입니다. gemini-pro-latest를 계속 써야 할 것 같아요.")
                
        except Exception as e:
            st.error(f"에러 발생: {e}")
