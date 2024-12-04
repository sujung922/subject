import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

# 데이터 로드 함수
@st.cache_data
def load_data():
    return pd.read_csv('sub01.csv')

# 모든 태그 중복 제거 후 추출
def get_unique_tags(subject):
    all_tags = []
    
    # 'Tag' 열에서 태그 추출
    for tags in subject['Tag']:
        if isinstance(tags, str) and tags.strip():  # 문자열인지 확인하고 빈 문자열이 아닐 때
            for tag in tags.split(','):
                all_tags.append(tag.strip())
    
    # 'Tag2' 열에서 태그 추출
    for tags in subject['Tag2']:
        if isinstance(tags, str) and tags.strip():  # 문자열인지 확인하고 빈 문자열이 아닐 때
            for tag in tags.split(','):
                all_tags.append(tag.strip())
    
    # 중복 제거
    unique_tags = list(dict.fromkeys(all_tags))
    
    return unique_tags

# 원-핫 인코딩을 위한 데이터 리스트 초기화
def create_one_hot_df(subject, unique_tags):
    one_hot_data = []
    
    for index, row in subject.iterrows():
        tags = row['Tag'].split(',') if isinstance(row['Tag'], str) else []
        tags = [tag.strip() for tag in tags if tag.strip()]

        tags2 = row['Tag2'].split(',') if isinstance(row['Tag2'], str) else []
        tags2 = [tag.strip() for tag in tags2 if tag.strip()]

        vector = [1 if t in tags else 0 for t in unique_tags] + [1 if t in tags2 else 0 for t in unique_tags]
        
        one_hot_data.append((row['Code'], row['Title1'], row['Title'], row['Name'], row['Des'], row['Pro'], row['Time'], row['Course'], row['Credit']) + tuple(vector))
    
    return pd.DataFrame(one_hot_data, columns=['Code','Title1','Title','Name','Des','Pro','Time','Course','Credit'] + unique_tags + unique_tags)


# 유사한 수업 찾기 함수 (입력한 교수님의 수업을 기준으로 추천)
def find_similar_subject(subject_name, professor_name, one_hot_df):
    sub_vector = None
    similar_scores = []

    # 입력한 교수님의 수업을 찾아서 벡터를 생성
    for index, row in one_hot_df.iterrows():
        if subject_name.lower() in row['Name'].lower() and professor_name.lower() in row['Pro'].lower():  
            sub_vector = row[8:].values.reshape(1, -1)
            break

    if sub_vector is None:
        return None

    # 유사 수업을 찾는 과정
    for index, row in one_hot_df.iterrows():
        if subject_name.lower() not in row['Name'].lower(): 
            vector = row[8:].values.reshape(1, -1)
            similarity = cosine_similarity(sub_vector, vector)[0][0]
            if similarity >= 0.9:
                similar_scores.append((row['Code'], row['Title1'], row['Title'], row['Name'], row['Des'], row['Pro'], row['Time'], row['Course'], row['Credit'], similarity))

    similar_scores.sort(key=lambda x: x[8], reverse=True)

    seen_names = set()
    unique_similar_scores = []
    for code, title1, title, name, des, pro, time, course, credit, score in similar_scores:
        if name not in seen_names:  # 교수명과 일치하는 수업 제외
            unique_similar_scores.append((code, title1, title, name, des, pro, time, course, credit, score))
            seen_names.add(name)
        if len(unique_similar_scores) == 3:
            break

    return unique_similar_scores

# 로그인 기능 추가
def login(username, password):
    if username == "admin" and password == "0000":
        return True
    return False

# Streamlit 애플리케이션 시작
st.title("에듀매치가 수업을 추천해드릴게요!")
st.caption('자신이 수강했던 수업 중 가장 재미있게 들었던 수업을 입력해주세요. 에듀매치가 가장 비슷한 유형의 수업을 추천해드릴게요🤓')

# 세션 상태 초기화
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'credits' not in st.session_state:
    st.session_state.credits = {'교양': 0, '전공': 0}

# 로그인 페이지
if st.session_state.page == 'login':
    st.subheader("로그인")
    username = st.text_input("사용자 이름:")
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

    # 사용자 입력 - 수업 이름
    sub_name = st.text_input(f"{course_type} 수업명을 입력하세요:")

    # 사용자 입력 - 교수님 이름
    professor_name = st.text_input("교수님 이름을 입력하세요:")

    # 추천 버튼
    if st.button("추천받기"):
        if sub_name:
            filtered_df = one_hot_df[one_hot_df['Title1'] == course_type]
            similar_subject = find_similar_subject(sub_name, professor_name, filtered_df)

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
                            st.markdown(f"**유사도:** {score*100:.1f}%")
                        st.markdown(f"**수업설명:** {des}\n")
                        st.write('='*80)
            else:
                st.write(f"{sub_name}와 비슷한 {course_type} 수업을 찾을 수 없어요🥲.")
        else:
            st.write("수업 이름을 입력해 주세요.")
