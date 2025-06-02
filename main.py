import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import openrouteservice
import streamlit.components.v1 as components   # 🚩 새 탭 오픈용 추가

# ------------------ 1. 제목 변경 ------------------
st.title("서울 중고등학교 찾아보기")  # ★ 변경

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

# 주소에서 지역 추출 함수 (예: 서울특별시 강남구)
def extract_region(address):
    if isinstance(address, str) and address.startswith("서울특별시 "):
        temp = address.split("서울특별시 ")[1]
        region = temp.split(" ")[0]
        return region
    else:
        return ""
df["지역"] = df["주소"].apply(extract_region)

# 빈칸이 아닌 학교명/지역만 목록에 추가
school_list = sorted([s for s in df["학교명"].unique() if str(s).strip()])
region_list = sorted([r for r in df["지역"].unique() if str(r).strip()])

# 사용자 입력 UI
st.subheader("학교명 또는 지역으로 검색")
search_mode = st.radio("검색 방법을 선택하세요:", ("학교명", "지역"))

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

# ------------------ 2. 지도보기 버튼(새 탭) ------------------
import uuid
import os

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

    # 지도 HTML 임시 파일 저장
    tmp_map_filename = f"map_{uuid.uuid4().hex}.html"
    m.save(tmp_map_filename)
    with open(tmp_map_filename, "r", encoding="utf-8") as f:
        html_data = f.read()

    # 지도보기 버튼 → 새 탭
    st.markdown(
        f'<a href="data:text/html;charset=utf-8,{html_data}" target="_blank">'
        f'<button style="font-size:18px;padding:8px 20px;background:#77c1fa;color:white;border:none;border-radius:6px;">지도보기</button></a>',
        unsafe_allow_html=True,
    )
    # 임시 파일 삭제
    os.remove(tmp_map_filename)
else:
    if (search_mode == "학교명" and search_school) or (search_mode == "지역" and search_region):
        st.warning("검색 결과가 없습니다. 이름 또는 지역명을 다시 확인해 주세요.")

# ------------------ 3. A학교→B학교 실제 도로경로 + 거리/시간 ------------------
st.subheader("A학교에서 B학교 실제 도로 경로 표시")

ORS_API_KEY = "5b3ce3597851110001cf624857837061d874456e9b9c1fa109068420"

col1, col2 = st.columns(2)
with col1:
    A_school = st.selectbox("출발 학교 선택 (A학교)", school_list, key="A_school_real")
with col2:
    B_school = st.selectbox("도착 학교 선택 (B학교)", school_list, key="B_school_real")

if ORS_API_KEY and A_school and B_school and A_school != B_school:
    try:
        client = openrouteservice.Client(key=ORS_API_KEY)
        A_row = df[df["학교명"] == A_school].iloc[0]
        B_row = df[df["학교명"] == B_school].iloc[0]
        coords = (
            (A_row["경도"], A_row["위도"]),
            (B_row["경도"], B_row["위도"])
        )
        route = client.directions(coords, profile="driving-car", format="geojson")
        route_coords = [
            [point[1], point[0]] for point in route['features'][0]['geometry']['coordinates']
        ]
        # 거리와 시간 정보 추출
        summary = route['features'][0]['properties']['summary']
        distance_km = summary['distance'] / 1000
        duration_min = summary['duration'] / 60

        route_map = folium.Map(
            location=[(A_row["위도"] + B_row["위도"]) / 2, (A_row["경도"] + B_row["경도"]) / 2],
            zoom_start=13
        )
        folium.Marker(
            location=[A_row["위도"], A_row["경도"]],
            popup=f"출발: {A_row['학교명']}",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(route_map)
        folium.Marker(
            location=[B_row["위도"], B_row["경도"]],
            popup=f"도착: {B_row['학교명']}",
            icon=folium.Icon(color="blue", icon="flag")
        ).add_to(route_map)
        folium.PolyLine(
            locations=route_coords,
            color="orange", weight=5, tooltip=f"{A_school} → {B_school} 도로 경로"
        ).add_to(route_map)
        st.markdown(f"**{A_school}**에서 **{B_school}**(으)로 이동하는 실제 도로 경로입니다.")
        st.markdown(f"🚗 **차로 이동 거리:** `{distance_km:.2f} km` &nbsp;&nbsp;&nbsp; 🕒 **예상 소요 시간:** `{duration_min:.1f} 분`")
        st_folium(route_map, width=800, height=600)
    except Exception as e:
        st.warning(f"경로 탐색 중 오류가 발생했습니다: {e}")
elif A_school == B_school:
    st.warning("출발 학교와 도착 학교가 동일합니다. 다른 학교를 선택하세요.")
