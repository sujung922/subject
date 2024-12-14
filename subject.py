import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import streamlit as st

# 로그인 기능 
def login(username, password):
    if username == "20212390" and password == "0000":
        return True
    return False

# 데이터 로드 함수
@st.cache_data
def load_data():
    return pd.read_csv('sub01.csv')

# 모든 태그 중복 제거 후 추출
def get_unique_tags(subject):
    all_tags = set() 
    
    # Tag 열에서 태그 추출
    for tags in subject['Tag']:
        if isinstance(tags, str) and tags.strip():  # 문자열인지 확인하고 빈 문자열이 아닐 때
            for tag in tags.split(','):
                all_tags.add(tag.strip())
    
    # Tag2 열에서 태그 추출
    for tags in subject['Tag2']:
        if isinstance(tags, str) and tags.strip():  # 문자열인지 확인하고 빈 문자열이 아닐 때
            for tag in tags.split(','):
                all_tags.add(tag.strip())
    
    unique_tags = list(all_tags)  
    
    return unique_tags

# 원-핫 인코딩
def create_one_hot_df(subject, unique_tags):
    one_hot_data = []
    
    if 'Code' not in subject.columns:
        print('error')
        return None  

    for index, ro번:")
    password = st.text_input("비밀번호:", type="password")

    if st.button("로그인"):
        if login(username, password):
            st.session_state.page = 'credits'  # 로그인 성공 시 학점 입력 페이지로 이동
            st.success("로그인 성공!")
        else:
            st.error("로그인 실패! 사용자 이름 또는 비밀번호를 확인하세요.")

# 학점 입력 페이지
elif st.session_state.page == 'credits':
    st.subheader("이수한 학점 입력")
    st.session_state.credits['교양'] = st.number_input("이수한 교양 학점:", min_value=0, value=st.session_state.credits['교양'])
    st.session_state.credits['전공'] = st.number_input("이수한 전공 학점:", min_value=0, value=st.session_state.credits['전공'])

    if st.button("학점 입력"):
        st.session_state.page = 'recommend'  # 학점 입력 완료 시 수업 추천 페이지로 이동

# 수업 추천 페이지
elif st.session_state.page == 'recommend':
    st.write("현재 남은 학점:")
    st.write(f"교양: {45 - st.session_state.credits['교양']} 학점")
    st.write(f"전공: {54 - st.session_state.credits['전공']} 학점")

    # 데이터 로드
    subject = load_data()
    unique_tags = get_unique_tags(subject)
    one_hot_df = create_one_hot_df(subject, unique_tags)

    course_type = st.selectbox("추천받고 싶은 수업 종류를 선택하세요:", ["교양", "전공"])

    # 수업 이름 입력
    sub_name = st.text_input(f"이전에 수강했던 {course_type} 수업명을 입력하세요:")

    # 교수님 이름 입력
    professor_name = st.text_input("교수님 이름을 입력하세요:")

    # 추천
    if st.button("추천받기"):
        if not professor_name:  # 교수님 이름이 입력되지 않은 경우
            st.warning("교수님 이름을 입력해 주세요.")
        elif sub_name:
            filtered_df = one_hot_df[one_hot_df['Title1'] == course_type]
            is_major = (course_type == "전공")  # 전공인지 교양인지에 따라 유사도 기준 설정

            similar_subject = find_similar_subject(sub_name, professor_name, filtered_df, is_major)

            if similar_subject:
                st.write(f"**{sub_name}와 비슷한 {course_type} 수업**:")
                for code, title1, title, name, des, pro, time, course, credit, score in similar_subject:
                    with st.container():
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**코드:** {code}")
                            st.markdown(f"**전공/교양:** {title1}")
                            st.markdown(f"**영역:** {title}")
                            st.markdown(f"**수업명:** {name}")
                            st.markdown(f"**교수명:** {pro}")
                        with col2:
                            st.markdown(f"**요일:** {time}")
                            st.markdown(f"**학점:** {course}")
                            st.markdown(f"**평점:** {credit}")
                            st.markdown(f"**유사도:** {score * 100:.1f}%")
                        st.markdown(f"**수업설명:** {des}\n")
                        st.write('=' * 80)
            else:
                st.write(f"{sub_name}와 비슷한 {course_type} 수업을 찾을 수 없어요🥲.")
        else:
            st.write("수업 이름을 입력해 주세요.")
