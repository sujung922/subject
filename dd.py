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
        if isinstance(tags, str):  # 문자열인지 확인
            for tag in tags.split(','):
                all_tags.append(tag.strip())
    
    # 'Tag2' 열에서 태그 추출
    for tags in subject['Tag2']:
        if isinstance(tags, str):  # 문자열인지 확인
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
        tags = [tag.strip() for tag in tags]

        tags2 = row['Tag2'].split(',') if isinstance(row['Tag2'], str) else []
        tags2 = [tag.strip() for tag in tags2]

        vector = [1 if t in tags else 0 for t in unique_tags] + [1 if t in tags2 else 0 for t in unique_tags]
        
        one_hot_data.append((row['Code'], row['Title1'], row['Title'], row['Name'], row['Des'], row['Pro'], row['Time'], row['Course'], row['Credit']) + tuple(vector))
    
    return pd.DataFrame(one_hot_data, columns=['Code', 'Title1', 'Title', 'Name', 'Des', 'Pro', 'Time', 'Course', 'Credit'] + unique_tags + unique_tags)

# 유사한 수업 찾기 함수 (부분 검색 추가)
def find_similar_subject(subject_name, one_hot_df):
    sub_vector = None
    similar_scores = []

    # 공백 제거 후 비교
    subject_name_cleaned = subject_name.replace(" ", "").lower()

    for index, row in one_hot_df.iterrows():
        if subject_name_cleaned in row['Name'].replace(" ", "").lower():  
            sub_vector = row[8:].values.reshape(1, -1)
            break

    if sub_vector is None:
        return None

    for index, row in one_hot_df.iterrows():
        if subject_name_cleaned not in row['Name'].replace(" ", "").lower(): 
            vector = row[8:].values.reshape(1, -1)
            similarity = cosine_similarity(sub_vector, vector)[0][0]
            if similarity >= 0.9:
                similar_scores.append((row['Code'], row['Title1'], row['Title'], row['Name'], row['Des'], row['Pro'], row['Time'], row['Course'], row['Credit'], similarity))

    similar_scores.sort(key=lambda x: x[8], reverse=True)

    seen_names = set()
    unique_similar_scores = []
    for code, title1, title, name, des, pro, time, course, credit, score in similar_scores:
        if name not in seen_names:
            unique_similar_scores.append((code, title1, title, name, des, pro, time, course, credit, score))
            seen_names.add(name)
        if len(unique_similar_scores) == 3:
            break
    return unique_similar_scores

# Streamlit 애플리케이션 시작
st.title("에듀매치가 수업을 추천해드릴게요 !")
st.caption('자신이 수강했던 수업 중 가장 재미있게 들었던 수업을 입력해주세요. 에듀매치가 가장 비슷한 유형의 수업을 추천해드릴게요🤓')

# 데이터 로드
subject = load_data()
unique_tags = get_unique_tags(subject)
one_hot_df = create_one_hot_df(subject, unique_tags)

# 사용자 입력 - 교양 또는 전공 선택
course_type = st.selectbox("추천받고 싶은 수업 종류를 선택하세요:", ["교양", "전공"])

# 사용자 입력 - 수업 이름
sub_name = st.text_input(f"{course_type} 수업명을 입력하세요:")

# 추천 버튼
if st.button("추천받기"):
    if sub_name:
        # 선택한 전공에 따라 필터링
        filtered_df = one_hot_df[one_hot_df['Title1'] == course_type]
        similar_subject = find_similar_subject(sub_name, filtered_df)

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
