import streamlit as st
import pandas as pd
import plotly.express as px

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Health & Environment Dashboard", layout="wide")
st.title("🏥 ระบบวิเคราะห์ความสัมพันธ์ฝุ่น PM2.5 และสุขภาพ")

# 2. โหลดข้อมูล
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('Master_Data_Looker.csv')
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Year'] = df['Date'].dt.year
        # เพิ่มคอลัมน์เดือน (ชื่อเต็มภาษาอังกฤษ)
        df['Month'] = df['Date'].dt.month_name()
        return df
    except:
        return None

df_raw = load_data()

if df_raw is None:
    st.error("ไม่พบไฟล์ข้อมูล Master_Data_Looker.csv หรือไฟล์อ่านไม่ได้")
    st.stop()

# --- ส่วน Sidebar ตัวเลือก ---
st.sidebar.header("⚙️ ตัวเลือกข้อมูล")

# 2.1 ตัวเลือกปี (Year)
# กรอง nan ออกและทำเป็นจำนวนเต็ม
unique_years = sorted(df_raw['Year'].dropna().astype(int).unique(), reverse=True)
year_options = ["ทั้งหมด (All Years)"] + list(unique_years)
selected_year = st.sidebar.selectbox("เลือกปี (Year):", year_options)

# 2.2 ตัวเลือกเดือน (Month) - เพิ่มใหม่!
month_order = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']
month_options = ["ทั้งหมด (All Months)"] + month_order
selected_month = st.sidebar.selectbox("เลือกเดือน (Month):", month_options)

# 2.3 ตัวเลือกโรคและปัจจัย
st.sidebar.markdown("---")
disease = st.sidebar.selectbox("เลือกโรคที่ต้องการดู:",
                               ['Asthma', 'COPD', 'Ischemic_heart_disease', 'Eye_inflammation', 'Skin_inflammation'])

env_factor = st.sidebar.selectbox("เลือกปัจจัยสภาพอากาศ:",
                                  ['PM25_avg', 'Temp_avg', 'Wind Speed', 'Humidity'])

# --- Logic การกรองข้อมูล (Filtering) ---
df = df_raw.copy() # เริ่มต้นจากข้อมูลทั้งหมด

# กรองปี
if selected_year != "ทั้งหมด (All Years)":
    df = df[df['Year'] == selected_year]

# กรองเดือน
if selected_month != "ทั้งหมด (All Months)":
    df = df[df['Month'] == selected_month]

# สร้างข้อความหัวข้อ (Title Text)
filter_text = f"ข้อมูลปี: {selected_year} | เดือน: {selected_month}"

# ==========================================
# 🟢 ส่วนที่ 1: Key Metrics
# ==========================================
st.markdown(f"### 📊 ภาพรวมสถานการณ์: {disease}")
st.caption(filter_text) # โชว์ว่าเราเลือกอะไรอยู่

col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    total_cases = df[disease].sum()
    st.metric(label="ผู้ป่วยสะสม (คน)", value=f"{total_cases:,.0f}")

with col_m2:
    # ถ้าเลือกเดือนเดียว ไม่ต้องหาค่าเฉลี่ยรายเดือน (เพราะมันคือเดือนนั้นอยู่แล้ว)
    if selected_month != "ทั้งหมด (All Months)" and selected_year != "ทั้งหมด (All Years)":
        avg_label = "ผู้ป่วยรายวันเฉลี่ย" # เปลี่ยนคำนิดนึงให้สมเหตุสมผล
    else:
        avg_label = "ผู้ป่วยเฉลี่ยต่อเดือน"

    avg_cases = df[disease].mean()
    st.metric(label=avg_label, value=f"{avg_cases:,.0f}")

with col_m3:
    avg_env = df[env_factor].mean()
    if pd.isna(avg_env): avg_env = 0
    st.metric(label=f"ค่าเฉลี่ย {env_factor}", value=f"{avg_env:.2f}")

with col_m4:
    max_env = df[env_factor].max()
    if pd.isna(max_env): max_env = 0
    st.metric(label=f"ค่าสูงสุด {env_factor}", value=f"{max_env:.2f}")

st.markdown("---")

# --- ส่วนแสดงผลกราฟ ---
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"📈 แนวโน้มจำนวนผู้ป่วย")
    if not df.empty:
        df_sorted = df.sort_values('Date')
        fig1 = px.line(df_sorted, x='Date', y=disease, markers=True)
        fig1.update_traces(line_color='#1f77b4')
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.warning("ไม่พบข้อมูลในช่วงเวลาที่เลือก")

with col2:
    st.subheader(f"🔗 ความสัมพันธ์กับ {env_factor}")
    if not df.empty:
        fig2 = px.scatter(df, x=env_factor, y=disease, trendline="ols",
                          title=f"Correlation: {env_factor} vs {disease}")
        fig2.update_traces(marker_color='#d62728')
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("ข้อมูลไม่เพียงพอสำหรับสร้างกราฟ")

# ==========================================
# 🔴 ส่วนที่ 2: Correlation Heatmap
# ==========================================
st.markdown("---")
st.subheader(f"🔥 แผนภาพความสัมพันธ์รวม")

if not df.empty and len(df) > 1:
    numeric_df = df.select_dtypes(include=['float64', 'int64'])
    corr = numeric_df.corr()
    fig3 = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='RdBu_r',
                     title=f"Correlation Matrix")
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("กรุณาเลือกช่วงเวลาที่มีข้อมูลมากกว่า 1 รายการเพื่อแสดง Heatmap")

with st.expander("ดูข้อมูลดิบ (Raw Data)"):
    st.dataframe(df)
