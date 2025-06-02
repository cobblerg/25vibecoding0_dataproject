import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import openrouteservice

st.title("서울 중고등학교 실제 도로 경로 찾기")

# adress.csv를 상위 폴더에서 불러오기
import os
csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "adress.csv")
try:
    df = pd.read_csv(csv_path, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(csv_path, encoding="cp949")

school_list = sorted([s for s in df["학교명"].unique() if str(s).strip()])

# 출발/도착 학교 선택 및 직접 입력 지원
col1, col2 = st.columns(2)
with col1:
    start_school_select = st.selectbox("출발학교를 선택하세요", school_list)
    start_school_input = st.text_input("또는 출발학교 이름을 직접 입력하세요 (선택 사항)").strip()
    start_school = start_school_input if start_school_input else start_school_select
with col2:
    end_school_select = st.selectbox("도착학교를 선택하세요", school_list)
    end_school_input = st.text_input("또는 도착학교 이름을 직접 입력하세요 (선택 사항)").strip()
    end_school = end_school_input if end_school_input else end_school_select

# 실제 도로 경로 표시
ORS_API_KEY = "5b3ce3597851110001cf624857837061d874456e9b9c1fa109068420"  # 반드시 본인 키로 변경!
if ORS_API_KEY and start_school and end_school and start_school != end_school:
    try:
        # 학교명 정합성 체크
        if not ((df["학교명"] == start_school).any() and (df["학교명"] == end_school).any()):
            st.warning("입력하신 학교명이 목록에 없습니다. 올바르게 입력했는지 확인해 주세요.")
        else:
            client = openrouteservice.Client(key=ORS_API_KEY)
            start_row = df[df["학교명"] == start_school].iloc[0]
            end_row = df[df["학교명"] == end_school].iloc[0]
            coords = (
                (start_row["경도"], start_row["위도"]),
                (end_row["경도"], end_row["위도"])
            )
            route = client.directions(coords, profile="driving-car", format="geojson")
            route_coords = [
                [point[1], point[0]] for point in route['features'][0]['geometry']['coordinates']
            ]
            summary = route['features'][0]['properties']['summary']
            distance_km = summary['distance'] / 1000
            duration_min = summary['duration'] / 60

            route_map = folium.Map(
                location=[(start_row["위도"] + end_row["위도"]) / 2, (start_row["경도"] + end_row["경도"]) / 2],
                zoom_start=13
            )
            folium.Marker(
                location=[start_row["위도"], start_row["경도"]],
                popup=f"출발: {start_row['학교명']}",
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(route_map)
            folium.Marker(
                location=[end_row["위도"], end_row["경도"]],
                popup=f"도착: {end_row['학교명']}",
                icon=folium.Icon(color="blue", icon="flag")
            ).add_to(route_map)
            folium.PolyLine(
                locations=route_coords,
                color="orange", weight=5, tooltip=f"{start_school} → {end_school} 도로 경로"
            ).add_to(route_map)

            st.markdown(f"🚗 **차로 이동 거리:** `{distance_km:.2f} km` &nbsp;&nbsp; 🕒 **예상 소요 시간:** `{duration_min:.1f} 분`")
            st_folium(route_map, width=800, height=600)
    except Exception as e:
        st.warning(f"경로 탐색 중 오류가 발생했습니다: {e}")
elif start_school == end_school and start_school:
    st.warning("출발학교와 도착학교가 동일합니다. 다른 학교를 선택하세요.")

