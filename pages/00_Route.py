import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import openrouteservice
import os

st.title("서울 중고등학교 실제 도로 경로 찾기")

csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "adress.csv")
try:
    df = pd.read_csv(csv_path, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(csv_path, encoding="cp949")

school_list = sorted([s for s in df["학교명"].unique() if str(s).strip()])

# 🚩 [수정] 학교명에서 '중학교', '고등학교', '학교' 등 불용어를 제거한 이름 만들기
def simplify_school_name(name):
    for kw in ['중학교', '고등학교', '학교']:
        name = name.replace(kw, '')
    return name.strip()

# 불용어가 제거된 학교명 컬럼 추가 (검색용)
df['검색용이름'] = df['학교명'].apply(simplify_school_name)

# 🚩 [수정] 입력값에서 불용어 제거하고 검색
col1, col2 = st.columns(2)
with col1:
    start_school_select = st.selectbox("출발학교를 선택하세요", school_list)
    start_school_input = st.text_input("또는 출발학교 이름을 직접 입력하세요 (선택 사항)").strip()
    start_school_search = simplify_school_name(start_school_input) if start_school_input else simplify_school_name(start_school_select)
with col2:
    end_school_select = st.selectbox("도착학교를 선택하세요", school_list)
    end_school_input = st.text_input("또는 도착학교 이름을 직접 입력하세요 (선택 사항)").strip()
    end_school_search = simplify_school_name(end_school_input) if end_school_input else simplify_school_name(end_school_select)

# 🚩 [수정] 불용어 제거된 이름으로 검색하여 학교명 매칭
def find_school_name(search, df):
    # 완전일치 우선, 없으면 포함일치
    matches = df[df['검색용이름'] == search]
    if not matches.empty:
        return matches.iloc[0]['학교명']
    # 부분일치(가장 앞에 포함) 우선
    matches = df[df['검색용이름'].str.startswith(search)]
    if not matches.empty:
        return matches.iloc[0]['학교명']
    # 아무데나 포함
    matches = df[df['검색용이름'].str.contains(search)]
    if not matches.empty:
        return matches.iloc[0]['학교명']
    return None

start_school = find_school_name(start_school_search, df)
end_school = find_school_name(end_school_search, df)

ORS_API_KEY = "5b3ce3597851110001cf624857837061d874456e9b9c1fa109068420"  # 본인 키로 바꿔주세요!

if ORS_API_KEY and start_school and end_school and start_school != end_school:
    try:
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

        # 🚩 [수정] 두 학교 모두 지도에 보이도록 지도 중심/zoom 자동 조정
        min_lat = min(start_row["위도"], end_row["위도"])
        max_lat = max(start_row["위도"], end_row["위도"])
        min_lng = min(start_row["경도"], end_row["경도"])
        max_lng = max(start_row["경도"], end_row["경도"])
        # 지도 중심
        map_center = [(min_lat + max_lat) / 2, (min_lng + max_lng) / 2]
        # Folium 지도 생성
        route_map = folium.Map(location=map_center, zoom_start=13)
        # 지도 bounds(최소/최대 위경도)에 맞게 fit
        route_map.fit_bounds([[min_lat, min_lng], [max_lat, max_lng]])

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
elif (start_school_search or end_school_search) and (not start_school or not end_school):
    st.warning("입력한 학교명을 찾을 수 없습니다. 정확한 학교명을 입력하거나 목록에서 선택해 주세요.")
