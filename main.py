import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.title("서울 중·고등학교 위치 지도")

# adress.csv 파일 불러오기
try:
    df = pd.read_csv("adress.csv", encoding='utf-8')
except UnicodeDecodeError:
    df = pd.read_csv("adress.csv", encoding='cp949')

st.write("데이터 미리보기", df.head())

# 학교 유형 컬럼이 없으면 자동 분류 (이름에 '중' 또는 '고' 포함)
if "학교유형" not in df.columns:
    def get_school_type(name):
        if "중" in name:
            return "중학교"
        elif "고" in name:
            return "고등학교"
        else:
            return "기타"
    df["학교유형"] = df["학교명"].apply(get_school_type)

# folium 지도 객체 생성 (서울 시청 기준)
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)

# 학교별 마커 표시 (중학교: green, 고등학교: blue)
for idx, row in df.iterrows():
    color = "blue" if row["학교유형"] == "고등학교" else "green"
    folium.Marker(
        location=[row["위도"], row["경도"]],
        popup=f"{row['학교명']} ({row['학교유형']})",
        icon=folium.Icon(color=color)
    ).add_to(m)

st.markdown("**파란색:** 고등학교, **초록색:** 중학교")
st_folium(m, width=800, height=600)

