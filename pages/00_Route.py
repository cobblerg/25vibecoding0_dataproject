import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import openrouteservice
import os
import requests

GOOGLE_API_KEY = "......"  # 🚩[수정/추가] 구글 Directions API 키 입력
ORS_API_KEY = "......."  # openrouteservice API 키

st.title("서울 중고등학교 실제 도로/도보/대중교통 경로 찾기")

csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "adress.csv")
try:
    df = pd.read_csv(csv_path, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(csv_path, encoding="cp949")

school_list = sorted([s for s in df["학교명"].unique() if str(s).strip()])

# 학교명 불용어 제거 함수
def simplify_school_name(name):
    for kw in ['중학교', '고등학교', '학교']:
        name = name.replace(kw, '')
    return name.strip()

df['검색용이름'] = df['학교명'].apply(simplify_school_name)

col1, col2 = st.columns(2)
with col1:
    start_school_select = st.selectbox("출발학교를 선택하세요", school_list)
    start_school_input = st.text_input("또는 출발학교 이름을 직접 입력하세요 (선택 사항)").strip()
    start_school_search = simplify_school_name(start_school_input) if start_school_input else simplify_school_name(start_school_select)
with col2:
    end_school_select = st.selectbox("도착학교를 선택하세요", school_list)
    end_school_input = st.text_input("또는 도착학교 이름을 직접 입력하세요 (선택 사항)").strip()
    end_school_search = simplify_school_name(end_school_input) if end_school_input else simplify_school_name(end_school_select)

def find_school_name(search, df):
    matches = df[df['검색용이름'] == search]
    if not matches.empty:
        return matches.iloc[0]['학교명']
    matches = df[df['검색용이름'].str.startswith(search)]
    if not matches.empty:
        return matches.iloc[0]['학교명']
    matches = df[df['검색용이름'].str.contains(search)]
    if not matches.empty:
        return matches.iloc[0]['학교명']
    return None

start_school = find_school_name(start_school_search, df)
end_school = find_school_name(end_school_search, df)

if ORS_API_KEY and start_school and end_school and start_school != end_school:
    try:
        client = openrouteservice.Client(key=ORS_API_KEY)
        start_row = df[df["학교명"] == start_school].iloc[0]
        end_row = df[df["학교명"] == end_school].iloc[0]
        coords = (
            (start_row["경도"], start_row["위도"]),
            (end_row["경도"], end_row["위도"])
        )

        # -------------------- 자동차(도로) 경로 --------------------
        car_route = client.directions(coords, profile="driving-car", format="geojson")
        car_coords = [
            [point[1], point[0]] for point in car_route['features'][0]['geometry']['coordinates']
        ]
        car_summary = car_route['features'][0]['properties']['summary']
        car_distance_km = car_summary['distance'] / 1000
        car_duration_min = car_summary['duration'] / 60

        # --------------------- 🚩[수정/추가] 도보 경로 ---------------------
        walk_route = client.directions(coords, profile="foot-walking", format="geojson")
        walk_coords = [
            [point[1], point[0]] for point in walk_route['features'][0]['geometry']['coordinates']
        ]
        walk_summary = walk_route['features'][0]['properties']['summary']
        walk_distance_km = walk_summary['distance'] / 1000
        walk_duration_min = walk_summary['duration'] / 60

        # -------------------- 지도 표시 --------------------
        min_lat = min(start_row["위도"], end_row["위도"])
        max_lat = max(start_row["위도"], end_row["위도"])
        min_lng = min(start_row["경도"], end_row["경도"])
        max_lng = max(start_row["경도"], end_row["경도"])
        map_center = [(min_lat + max_lat) / 2, (min_lng + max_lng) / 2]
        route_map = folium.Map(location=map_center, zoom_start=13)
        route_map.fit_bounds([[min_lat, min_lng], [max_lat, max_lng]])

        folium.Marker(
            location=[start_row["위도"], start_row["경도"]],
            popup=f"출발: {start_row['학교명']}",
            tooltip=start_row['학교명'],  # 🚩[수정/추가] 툴팁 추가
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(route_map)
        folium.Marker(
            location=[end_row["위도"], end_row["경도"]],
            popup=f"도착: {end_row['학교명']}",
            tooltip=end_row['학교명'],  # 🚩[수정/추가] 툴팁 추가
            icon=folium.Icon(color="blue", icon="flag")
        ).add_to(route_map)
        folium.PolyLine(
            locations=car_coords,
            color="orange", weight=5, tooltip=f"{start_school} → {end_school} 도로 경로"
        ).add_to(route_map)
        folium.PolyLine(
            locations=walk_coords,
            color="green", weight=5, tooltip=f"{start_school} → {end_school} 도보 경로"
        ).add_to(route_map)

        st.markdown(f"### 🚗 자동차(도로) 경로")
        st.markdown(f"**거리:** `{car_distance_km:.2f} km` &nbsp;&nbsp; **예상 소요 시간:** `{car_duration_min:.1f} 분`")
        st_folium(route_map, width=800, height=500)

        st.markdown(f"### 🚶 도보 경로")
        st.markdown(f"**거리:** `{walk_distance_km:.2f} km` &nbsp;&nbsp; **예상 소요 시간:** `{walk_duration_min:.1f} 분`")
        # 지도 중복 표시 피하기 위해 도보 경로만 별도로 추가로 지도에 그리고 싶으면 여기에 st_folium() 추가 가능

        # --------------------- 🚩[수정/추가] Google Directions API (대중교통) ---------------------
        st.markdown("### 🚊 대중교통(Transit) 경로 안내")
        if GOOGLE_API_KEY:
            origin = f"{start_row['위도']},{start_row['경도']}"
            destination = f"{end_row['위도']},{end_row['경도']}"
            params = {
                "origin": origin,
                "destination": destination,
                "mode": "transit",
                "language": "ko",
                "key": GOOGLE_API_KEY
            }
            url = "https://maps.googleapis.com/maps/api/directions/json"
            response = requests.get(url, params=params)
            data = response.json()
            if data['status'] == 'OK':
                leg = data['routes'][0]['legs'][0]
                transit_distance = leg['distance']['text']
                transit_duration = leg['duration']['text']
                st.markdown(f"**총 거리:** `{transit_distance}`  &nbsp;&nbsp;  **예상 소요시간:** `{transit_duration}`")
                st.markdown(f"**출발지:** {leg['start_address']}  \n**도착지:** {leg['end_address']}")

                # 세부 경로 안내 표
                steps = []
                for step in leg['steps']:
                    summary = step['html_instructions']
                    travel_mode = step['travel_mode']
                    if step.get('transit_details'):
                        transit = step['transit_details']
                        line = transit['line']['short_name'] if 'short_name' in transit['line'] else transit['line'].get('name', '')
                        vehicle = transit['line']['vehicle']['type']
                        summary += f" (노선: {line}, {vehicle})"
                    steps.append({"이동수단": travel_mode, "경로 요약": summary, "거리": step['distance']['text'], "시간": step['duration']['text']})
                st.dataframe(steps)
            else:
                st.warning(f"Google 대중교통 경로를 찾을 수 없습니다: {data['status']}")
        else:
            st.info("Google Directions API 키가 등록되어 있지 않습니다. 대중교통 안내를 위해 API 키를 입력해 주세요.")
        # ---------------------------------------------------------

    except Exception as e:
        st.warning(f"경로 탐색 중 오류가 발생했습니다: {e}")
elif start_school == end_school and start_school:
    st.warning("출발학교와 도착학교가 동일합니다. 다른 학교를 선택하세요.")
elif (start_school_search or end_school_search) and (not start_school or not end_school):
    st.warning("입력한 학교명을 찾을 수 없습니다. 정확한 학교명을 입력하거나 목록에서 선택해 주세요.")
