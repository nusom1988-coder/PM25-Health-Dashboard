import streamlit as st
import pandas as pd
import plotly.express as px

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Health & Environment Dashboard", layout="wide")
st.title("🏥 ระบบวิเคราะห์ความสัมพันธ์ฝุ่น PM2.5 และสุขภาพ")

# 2. โหลดข้อมูล
@st.cache_data # เพิ่ม Cache เพื่อให้โหลดเร็วขึ้น
def load_data():
    df = pd.read_csv('Master_Data_Looker.csv')
    df['Date'] = pd.to_datetime(df['Date']) # แปลงเป็นวันที่
    df['Year'] = df['Date'].dt.year # ดึงปีออกมา
    return df

try:
    df_raw = load_data()
except:
    st.error("ไม่พบไฟล์ข้อมูล Master_Data_Looker.csv กรุณาตรวจสอบการอัปโหลด")
    st.stop()

# --- ส่วน Sidebar ตัวเลือก ---
st.sidebar.header("⚙️ ตัวเลือกข้อมูล")

# 2.1 ตัวเลือกปี (Year Filter) - เพิ่มใหม่!
year_list = sorted(df_raw['Year'].unique(), reverse=True)
year_list.insert(0, "ทั้งหมด (All Years)") # เพิ่มตัวเลือกดูรวมทุกปี
selected_year = st.sidebar.selectbox("เลือกปีที่ต้องการดู:", year_list)

# กรองข้อมูลตามปีที่เลือก
if selected_year == "ทั้งหมด (All Years)":
    df = df_raw # ใช้ข้อมูลทั้งหมด
    year_text = "ทุกปี"
else:
    df = df_raw[df_raw['Year'] == selected_year] # ใช้เฉพาะปีที่เลือก
    year_text = f"ปี {selected_year}"

# 2.2 ตัวเลือกโรคและปัจจัย
st.sidebar.markdown("---")
disease = st.sidebar.selectbox("เลือกโรคที่ต้องการดู:",
                               ['Asthma', 'COPD', 'Ischemic_heart_disease', 'Eye_inflammation', 'Skin_inflammation'])

env_factor = st.sidebar.selectbox("เลือกปัจจัยสภาพอากาศ:",
                                  ['PM25_avg', 'Temp_avg', 'Wind Speed', 'Humidity'])

# ==========================================
# 🟢 ส่วนที่ 1: Key Metrics (อัปเดตตามปีที่เลือก)
# ==========================================
st.markdown(f"### 📊 ภาพรวมสถานการณ์: {disease} ({year_text})")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    total_cases = df[disease].sum()
    st.metric(label="ผู้ป่วยสะสม (คน)", value=f"{total_cases:,.0f}")

with col_m2:
    avg_cases = df[disease].mean()
    st.metric(label="ผู้ป่วยเฉลี่ยต่อเดือน", value=f"{avg_cases:,.0f}")

with col_m3:
    avg_env = df[env_factor].mean()
    st.metric(label=f"ค่าเฉลี่ย {env_factor}", value=f"{avg_env:.2f}")

with col_m4:
    max_env = df[env_factor].max()
    st.metric(label=f"ค่าสูงสุด {env_factor}", value=f"{max_env:.2f}")

st.markdown("---") # เส้นคั่น

# --- ส่วนแสดงผลกราฟ ---
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"📈 แนวโน้มผู้ป่วยรายเดือน ({year_text})")
    fig1 = px.line(df, x='Date', y=disease, markers=True)
    fig1.update_traces(line_color='#1f77b4')
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader(f"🔗 ความสัมพันธ์กับ {env_factor}")
    fig2 = px.scatter(df, x=env_factor, y=disease, trendline="ols",
                      title=f"Correlation: {env_factor} vs {disease}")
    fig2.update_traces(marker_color='#d62728')
    st.plotly_chart(fig2, use_container_width=True)

# ==========================================
# 🔴 ส่วนที่ 2: Correlation Heatmap
# ==========================================
st.markdown("---")
st.subheader(f"🔥 แผนภาพความสัมพันธ์รวม ({year_text})")

# คำนวณเฉพาะคอลัมน์ตัวเลข
numeric_df = df.select_dtypes(include=['float64', 'int64'])
corr = numeric_df.corr()

fig3 = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='RdBu_r',
                 title=f"Correlation Matrix ({year_text})")
st.plotly_chart(fig3, use_container_width=True)

# ส่วนตารางข้อมูลดิบ
with st.expander("ดูข้อมูลดิบ (Raw Data)"):
    st.dataframe(df)
