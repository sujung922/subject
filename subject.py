import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

# 로그인 기능 
def login(username, password):
    if username == "admin" and password == "0000":
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
        overlapping_tags = tags.intersection(tags2)  # 겹치는 태그
        
        # 겹치는 태그 제거
        for tag in overlapping_tags:
            unique_tags_set.discard(tag)  # 겹치는 태그를 제거
        
        # 원-핫 인코딩: 겹치는 태그를 제외하고 설정
        vector = [1 if t in tags else 0 for t in unique_tags] + [2 if t in tags2 else 0 for t in unique_tags]
        
        # 겹치는 태그에 대해 가중치 설정
        for tag in overlapping_tags:
            if tag in unique_tags:
                index = unique_tags.index(tag)
                vector[index] = 0 
        
        one_hot_data.append((code, row['Title1'], row['Title'], row['Name'], row['Des'], row['Pro'], row['Time'], row['Course'], row['Credit']) + tuple(vector))
    
    return pd.DataFrame(one_hot_data, columns=['Code','Title1','Title','Name','Des','Pro','Time','Course','Credit'] + unique_tags + unique_tags)

# 유사한 수업 찾기 함수 (입력한 교수님의 수업을 기준으로 추천)
def find_similar_subject(subject_name, professor_name, one_hot_df, is_major=True):
    sub_vector = None
    similar_scores = []

    # 벡터 생성
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
            
            # 전공과 교양에 따라 유사도 기준 설정
            if is_major:
                if similarity >= 0.9:  # 전공 유사도 기준
                    similar_scores.append((row['Code'], row['Title1'], row['Title'], row['Name'], row['Des'], row['Pro'], row['Time'], row['Course'], row['Credit'], similarity))
            else:
                if similarity >= 0.8:  # 교양 유사도 기준을 높임
                    similar_scores.append((row['Code'], row['Title1'], row['Title'], row['Name'], row['Des'], row['Pro'], row['Time'], row['Course'], row['Credit'], similarity))

    similar_scores.sort(key=lambda x: x[8], reverse=False)

    seen_names = set()
    unique_similar_scores = []
    for code, title1, title, name, des, pro, time, course, credit, score in similar_scores:
        if name not in seen_names:  # 교수명과 일치하는 수업 제외
            unique_similar_scores.append((code, title1, title, name, des, pro, time, course, credit, score))
            seen_names.add(name)
        if len(unique_similar_scores) >= 3:  
            break

    return unique_similar_scores


# Streamlit
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

    # 수업 이름 입력
    sub_name = st.text_input(f"이전에 수강했던 {course_type} 수업명을 입력하세요:")

    # 교수님 이름 입력
    professor_name = st.text_input("교수님 이름을 입력하세요:")

    # 추천
    if st.button("추천받기"):
        if sub_name:
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
