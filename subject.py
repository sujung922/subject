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
        unique_tags_set = tags.union(tags2)

        # 원-핫 인코딩
        vector = [1 if t in unique_tags_set else 0 for t in unique_tags]
        one_hot_data.append((code, row['Title1'], row['Title'], row['Name'], row['Des'], row['Pro'], row['Time'], row['Course'], row['Credit'], row['Tag'], row['Tag2']) + tuple(vector))
    
    return pd.DataFrame(one_hot_data, columns=['Code','Title1','Title','Name','Des','Pro','Time','Course','Credit','Tag','Tag2'] + unique_tags)

# 태그 유사도 계산 함수
def calculate_tag_similarity(tag1, tag2):
    vectorizer = CountVectorizer()
    if not tag1 or not tag2:  
        return 0.0
    vectors = vectorizer.fit_transform([tag1, tag2])
    return cosine_similarity(vectors)[0][1]

# 유사한 수업 찾기 함수
def find_similar_subject(subject_name, professor_name, one_hot_df, is_major=True):
    sub_vector = None
    input_tag = ""
    similar_scores = []

    subject_name = subject_name.replace(" ", "")  

    # 입력된 수업명과 교수로 벡터 찾기
    for index, row in one_hot_df.iterrows():
        course_name = row['Name'].replace(" ", "")
        if subject_name in row['Name'] and professor_name in row['Pro']:
            sub_vector = row[11:].values.reshape(1, -1)  
            input_tag = f"{row['Tag']},{row['Tag2']}" 
            break

    if sub_vector is None:
        return None  

    # 입력된 교수의 수업 제외하고 유사도 계산
    for index, row in one_hot_df.iterrows():
        if row['Pro'] != professor_name:
            vector = row[11:].values.reshape(1, -1)
            name_similarity = cosine_similarity(sub_vector, vector)[0][0]  # 원-핫 벡터 유사도
            target_tag = f"{row['Tag']},{row['Tag2']}"  
            tag_similarity = calculate_tag_similarity(input_tag, target_tag) 

        # 최종 유사도: 가중치를 조정
        final_similarity = 0.2 * name_similarity + 0.8 * tag_similarity

        # 전공/교양에 따라 필터링
        if is_major and final_similarity >= 0.75:  # 전공 유사도 
            similar_scores.append((row['Code'], row['Title1'], row['Title'], row['Name'], row['Des'], row['Pro'], row['Time'], row['Course'], row['Credit'], final_similarity))
        elif not is_major and final_similarity >= 0.7:  # 교양 유사도
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
        if len(unique_similar_scores) >= 3: #최대 추천
            break

    return unique_similar_scores

#Streamlit

st.header("에듀매치가 수업을 추천해드릴게요!")
st.caption('자신이 수강했던 수업 중 가장 재미있게 들었던 수업을 입력해주세요. 에듀매치가 가장 비슷한 유형의 수업을 추천해드릴게요🤓')

# 세션 초기화
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
            st.session_state.page = 'credits' 
            st.success("로그인 성공!")
        else:
            st.error("로그인 실패! 학번 또는 비밀번호를 확인하세요.")

# 이수 학점 입력 페이지
elif st.session_state.page == 'credits':
    st.subheader("이수한 학점 입력")
    st.caption("현재까지 이수한 학점을 입력해주세요.")

    st.session_state.credits['교양'] = st.number_input("이수한 교양 학점:", min_value=0, value=st.session_state.credits['교양'])
    st.session_state.credits['전공'] = st.number_input("이수한 전공 학점:", min_value=0, value=st.session_state.credits['전공'])

    if st.button("학점 입력"):
        st.session_state.page = 'recommend'  

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

    # 수업명 입력
    sub_name = st.text_input(f"이전에 수강했던 {course_type} 수업명을 입력하세요:")

    # 교수님 이름 입력
    professor_name = st.text_input("교수님 이름을 입력하세요:")

    # 추천받기
    if st.button("추천받기"):
        if not professor_name:  
            st.warning("교수님 이름을 입력해 주세요.")
        elif sub_name:
            filtered_df = one_hot_df[one_hot_df['Title1'] == course_type]
            is_major = (course_type == "전공")  # 전공/교양 유사도

            similar_subject = find_similar_subject(sub_name, professor_name, filtered_df, is_major)

            if similar_subject:
                st.write(f"**{professor_name} 교수님의 {sub_name} 수업과 비슷한 {course_type} 수업**:")
                for code, title1, title, name, des, pro, time, course, credit, score in similar_subject:
                    st.markdown(
                        f"""
                        <div style="border: 1px solid #ccc; border-radius: 5px; padding: 23px; margin: 15px 15px;">
                            <h4>{name} ({code})</h4>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <p><strong>전공/교양:</strong> {title1}</p>
                                <p><strong>영역:</strong> {title}</p>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <p><strong>요일:</strong> {time}</p>
                                <p><strong>학점:</strong> {course}</p>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <p><strong>평점:</strong> {credit}</p>
                                <p><strong>유사도:</strong> {score * 100:.1f}%</p>
                            </div>
                            <div style="display: flex; justify-content: flex-start; align-items: center;">
                                <p><strong>교수명:</strong> {pro}</p>
                            </div>
                            <p><strong>수업설명:</strong> {des}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.write(f"{sub_name}와 비슷한 {course_type} 수업을 찾을 수 없어요🥲.")
        else:
            st.write("수업 이름을 입력해 주세요.")
