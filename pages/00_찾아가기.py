import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.title("서울 중고등학교 찾아보기")

# 데이터 불러오기
try:
    df = pd.read_csv("adress.csv", encoding='utf-8')
except UnicodeDecodeError:
    df = pd.read_csv("adress.csv", encoding='cp949')

# 학교 유형 자동 분류
if "학교유형" not in df.columns:
    def get_school_type(name):
        if "중" in name:
            return "중학교"
        elif "고" in name:
            return "고등학교"
        else:
            return "기타"
    df["학교유형"] = df["학교명"].apply(get_school_type)

# 주소에서 지역 추출 함수
def extract_region(address):
    if isinstance(address, str) and address.startswith("서울특별시 "):
        temp = address.split("서울특별시 ")[1]
        region = temp.split(" ")[0]
        return region
    else:
        return ""
df["지역"] = df["주소"].apply(extract_region)

school_list = sorted([s for s in df["학교명"].unique() if str(s).strip()])
region_list = sorted([r for r in df["지역"].unique() if str(r).strip()])

st.subheader("학교명 또는 지역으로 검색")
search_mode = st.radio("검색 방법을 선택하세요:", ("학교명", "지역"))

search_school = ""
search_region = ""

if search_mode == "학교명":
    selected_school = st.selectbox("학교명을 선택하거나 입력하세요:", school_list)
    manual_school = st.text_input("또는 학교명을 직접 입력하세요 (선택 사항):").strip()
    search_school = manual_school if manual_school else selected_school
    if search_school:
        filtered = df[df["학교명"].str.contains(search_school, case=False, na=False)]
    else:
        filtered = df.iloc[0:0]  # 빈 데이터프레임

elif search_mode == "지역":
    selected_region = st.selectbox("지역명을 선택하거나 입력하세요:", region_list)
    manual_region = st.text_input("또는 지역명을 직접 입력하세요 (예: 강남구):").strip()
    search_region = manual_region if manual_region else selected_region
    if search_region:
        filtered = df[df["지역"].str.contains(search_region, case=False, na=False)]
    else:
        filtered = df.iloc[0:0]  # 빈 데이터프레임

if not filtered.empty:
    map_center = [filtered["위도"].mean(), filtered["경도"].mean()]
    m = folium.Map(location=map_center, zoom_start=13)
    for idx, row in filtered.iterrows():
        color = "blue" if row["학교유형"] == "고등학교" else "green"
        folium.Marker(
            location=[row["위도"], row["경도"]],
            popup=f"{row['학교명']} ({row['학교유형']})",
            icon=folium.Icon(color=color)
        ).add_to(m)
    st.markdown("**파란색:** 고등학교, **초록색:** 중학교")
    st_folium(m, width=800, height=600)
else:
    if (search_mode == "학교명" and search_school) or (search_mode == "지역" and search_region):
        st.warning("검색 결과가 없습니다. 이름 또는 지역명을 다시 확인해 주세요.")
