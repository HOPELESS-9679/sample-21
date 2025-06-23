import streamlit as st
import pandas as pd
import folium
import json
from folium.plugins import LocateControl
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval

# Page settings
st.set_page_config(page_title="Nursery Locator", layout="wide")
st.title("🌱 Public Nursery Locator")

# Load Excel directly (no upload required)
excel_path = "NURSARYDETAILS.xlsx"
try:
    df = pd.read_excel(excel_path)
except FileNotFoundError:
    st.error(f"❌ File not found: {excel_path}")
    st.stop()

# Fix typo in column name if exists
df.rename(columns={"Latitide": "Latitude"}, inplace=True)

# Ensure required columns are present
required_cols = ['Nursery Name', 'Latitude', 'Longitude', 'Name of the Incharge', 'Contact', 'NAME OF SPECIES']
if not all(col in df.columns for col in required_cols):
    st.error("❌ Excel must include: " + ", ".join(required_cols))
    st.stop()

# Ensure numeric coordinates
df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
df = df.dropna(subset=['Latitude', 'Longitude'])

# Get user location
loc = streamlit_js_eval(
    js_expressions="navigator.geolocation.getCurrentPosition((pos) => pos.coords)",
    key="get_user_location"
)

if loc and "latitude" in loc and "longitude" in loc:
    user_location = (loc["latitude"], loc["longitude"])
    st.success("📍 Your location detected.")
else:
    user_location = ( 20.302500,  82.755278)
    st.warning("⚠️ Using fallback location: Khariar.")

# Create the folium map
m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=11)
LocateControl(auto_start=True).add_to(m)

# (Optional) add Khariar boundary if available
try:
    with open("khariar_boundary.geojson", "r") as f:
        khariar_boundary = json.load(f)
    folium.GeoJson(
        khariar_boundary,
        name="Khariar Division",
        style_function=lambda x: {
            "fillColor": "orange",
            "color": "black",
            "weight": 2,
            "fillOpacity": 0.1,
        },
    ).add_to(m)
except:
    pass

# Show user marker
folium.Marker(
    location=user_location,
    tooltip="Your Location",
    icon=folium.Icon(color="blue", icon="user")
).add_to(m)

# Add nursery markers
for _, row in df.iterrows():
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        tooltip=row['Nursery Name'],
        popup=f"""
        <b>{row['Nursery Name']}</b><br>
        Incharge: {row['Name of the Incharge']}<br>
        Contact: {row['Contact']}<br>
        Species: {row['NAME OF SPECIES']}
        """,
        icon=folium.Icon(color="green", icon="leaf")
    ).add_to(m)

# Display map
st.subheader("🗺️ Nursery Map")
map_data = st_folium(m, width=1000, height=600)

# Show clicked nursery info
if map_data and map_data.get("last_object_clicked_tooltip"):
    name = map_data["last_object_clicked_tooltip"]
    row = df[df["Nursery Name"] == name].iloc[0]
    st.subheader(f"🏡 {name} Details")
    st.markdown(f"""
    **Incharge:** {row['Name of the Incharge']}  
    **Contact:** {row['Contact']}  
    """)
    st.markdown("### 🌿 Species Available")
    species = [s.strip() for s in str(row['NAME OF SPECIES']).split(",")]
    st.write(", ".join(species))
else:
    st.info("Click on a nursery marker to view its details.")
