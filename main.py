import streamlit as st
import folium
from streamlit_folium import st_folium

st.title("🗺️ 서울 고등학교 위치 지도")

# 서울 고등학교 샘플 데이터 (학교명, 위도, 경도)
schools = [
    {"name": "서울고등학교", "lat": 37.484016, "lng": 126.982823},
    {"name": "경복고등학교", "lat": 37.589644, "lng": 126.968724},
    {"name": "용산고등학교", "lat": 37.535227, "lng": 126.991353},
    {"name": "한영고등학교", "lat": 37.498667, "lng": 127.130383},
    {"name": "중앙고등학교", "lat": 37.573833, "lng": 126.976961},
    # 필요한 만큼 추가
]

# 서울 중심 좌표
seoul_center = [37.5665, 126.9780]

# folium 지도 생성
m = folium.Map(location=seoul_center, zoom_start=11)

# 학교 위치 마커 추가
for school in schools:
    folium.Marker(
        location=[school["lat"], school["lng"]],
        popup=school["name"],
        icon=folium.Icon(color='blue', icon='info-sign')
    ).add_to(m)

# Streamlit에 folium 지도 표시
st_folium(m, width=700, height=500)

