###### 🚩 도로경로 표시용 코드: openrouteservice 활용 ######
import openrouteservice

st.subheader("A학교에서 B학교 실제 도로 경로 표시")

# openrouteservice API 키 입력 (여기에 본인의 키를 입력하세요)
ORS_API_KEY = "5b3ce3597851110001cf624857837061d874456e9b9c1fa109068420"  # ← 반드시 본인 키로 바꿔주세요!

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
        # 경로탐색 (자동차 경로: profile="driving-car", 도보: "foot-walking")
        route = client.directions(coords, profile="driving-car", format="geojson")
        route_coords = [
            [point[1], point[0]] for point in route['features'][0]['geometry']['coordinates']
        ]
        route_map = folium.Map(
            location=[(A_row["위도"] + B_row["위도"]) / 2, (A_row["경도"] + B_row["경도"]) / 2],
            zoom_start=13
        )
        # 출발, 도착지 마커
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
        # 🚩 실제 도로 경로 PolyLine
        folium.PolyLine(
            locations=route_coords,
            color="orange", weight=5, tooltip=f"{A_school} → {B_school} 도로 경로"
        ).add_to(route_map)
        st.markdown(f"**{A_school}**에서 **{B_school}**(으)로 이동하는 실제 도로 경로입니다.")
        st_folium(route_map, width=800, height=600)
    except Exception as e:
        st.warning(f"경로 탐색 중 오류가 발생했습니다: {e}")
elif A_school == B_school:
    st.warning("출발 학교와 도착 학교가 동일합니다. 다른 학교를 선택하세요.")
