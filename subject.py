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

    for index, row in subject.iterrows():
        code = str(int(row['Code'])).zfill(7) if pd.notna(row['Code']) else '0000000' 
        
        # Tag에서 태그 추출
        tags = set(row['Tag'].split(',')) if isinstance(row['Tag'], str) else set()
        tags = {tag.strip() for tag in tags if tag.strip()}

        # Tag2에서 태그 추출
        tags2 = set(row['Tag2'].split(',')) if isinstance(row['Tag2'], str) else set()
        tags2 = {tag.strip() for tag in tags2 if tag.strip()}

        # 겹치는 태그 제거
        unique_tags_set = tags.union(tags2)  # Tag과 Tag2의 태그를 합친 집합

        # 원-핫 인코딩
        vector = [1 if t in unique_tags_set else 0 for t in unique_tags]
        one_hot_data.append((code, row['Title1'], row['Title'], row['Name'], row['Des'], row['Pro'], row['Time'], row['Course'], row['Credit'], row['Tag'], row['Tag2']) + tuple(vector))
    
    return pd.DataFrame(one_hot_data, columns=['Code','Title1','Title','Name','Des','Pro','Time','Course','Credit','Tag','Tag2'] + unique_tags)

# 태그 유사도 계산 함수
def calculate_tag_similarity(tag1, tag2):
    """Calculate cosine similarity between two tag strings."""
    vectorizer = CountVectorizer()
    if not tag1 or not tag2:  # 태그가 비어있는 경우
        return 0.0
    vectors = vectorizer.fit_transform([tag1, tag2])
    return cosine_similarity(vectors)[0][1]

# 유사한 수업 찾기 함수
def find_similar_subject(subject_name, professor_name, one_hot_df, is_major=True):
    sub_vector = None
    input_tag = ""
    similar_scores = []

    # 입력된 수업명과 교수로 벡터 찾기
    for index, row in one_hot_df.iterrows():
        if subject_name.lower() in row['Name'].lower() and professor_name.lower() in row['Pro'].lower():
            sub_vector = row[11:].values.reshape(1, -1)  # 원-핫 벡터
            input_tag = f"{row['Tag']},{row['Tag2']}"  # 태그 병합
            break

    if sub_vector is None:
        return None  # 입력된 수업의 벡터를 찾지 못한 경우

    # 입력된 교수의 수업 제외하고 유사도 계산
    for index, row in one_hot_df.iterrows():
        vector = row[11:].values.reshape(1, -1)
        name_similarity = cosine_similarity(sub_vector, vector)[0][0]  # 원-핫 벡터 유사도
        target_tag = f"{row['Tag']},{row['Tag2']}"  # 태그 병합
        tag_similarity = calculate_tag_similarity(input_tag, target_tag)  # 태그 유사도 계산

        # 최종 유사도: 가중치를 조정
        final_similarity = 0.2 * name_similarity + 0.8 * tag_similarity

        # 전공/교양에 따라 필터링
        if is_major and final_similarity >= 0.75:  # 전공 유사도 기준
            similar_scores.append((row['Code'], row['Title1'], row['Title'], row['Name'], row['Des'], row['Pro'], row['Time'], row['Course'], row['Credit'], final_similarity))
        elif not is_major and final_similarity >= 0.75:  # 교양 유사도 기준
            similar_scores.append((row['Code'], row['Title1'], row['Title'], row['Name'], row['Des'], row['Pro'], row['Time'], row['Course'], row['Credit'], final_similarity))

    # 유사도 기준으로 정렬
    similar_scores.sort(key=lambda x: x[9], reverse=True)

    # 중복 제거: 같은 수업명을 가진 데이터 하나씩만 반환
    seen_names = set()
    unique_similar_scores = []
    for code, title1, title, name, des, pro, time, course, credit, score in similar_scores:
        if name not in seen_names:
            unique_similar_scores.append((code, title1, title, name, des, pro, time, course, credit, score))
            seen_names.add(name)
        if len(unique_similar_scores) >= 5:  # 최대 3개 추천
            break

    return unique_similar_scores

# Streamlit
st.header("에듀매치가 수업을 추천해드릴게요!")
st.caption('자신이 수강했던 수업 중 가장 재미있게 들었던 수업을 입력해주세요. 에듀매치가 가장 비슷한 유형의 수업을 추천해드릴게요🤓')

# 세션 상태 초기화
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'credits' not in st.session_state:
    st.session_state.credits = {'교양': 0, '전공': 0}

# 로그인 페이지
if st.session_state.page == 'login':
    st.subheader("로그인")
    username = st.text_input("학번:")
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
