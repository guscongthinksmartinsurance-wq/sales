import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import io

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="TMC Financial System", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

# Load CSS
try:
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except: pass

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, phone TEXT UNIQUE, state TEXT,
                    status TEXT DEFAULT 'New', owner TEXT,
                    note TEXT DEFAULT '', last_updated TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. SIDEBAR & LOGO UPLOAD ---
with st.sidebar:
    st.title("🛡️ TMC SYSTEM")
    # Chỗ để anh upload Logo của anh
    uploaded_logo = st.file_uploader("Tải Logo của anh lên", type=["png", "jpg", "jpeg"])
    if uploaded_logo:
        st.image(uploaded_logo, use_container_width=True)
    else:
        st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", width=150)
    
    st.divider()
    
    # Khởi tạo trạng thái đăng nhập
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    # CHỈ HIỆN MENU ĐẦY ĐỦ NẾU ĐÃ ĐĂNG NHẬP
    if st.session_state.authenticated:
        menu_options = ["🏠 Trang chủ giới thiệu", "👁️ Mắt Thần (Sale & Khách)", "⚙️ Vận hành Admin"]
    else:
        menu_options = ["🏠 Trang chủ giới thiệu"]
    
    menu = st.radio("MENU CHÍNH", menu_options)
    
    if st.session_state.authenticated:
        if st.button("🚪 Đăng xuất"):
            st.session_state.authenticated = False
            st.rerun()

# --- 3. ĐIỀU HƯỚNG CHI TIẾT ---
query_params = st.query_params
id_khach = query_params.get("id")

# TẦNG KHÁCH HÀNG (Ưu tiên số 1 - Luôn chạy khi có ID)
if id_khach:
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql(f"SELECT * FROM leads WHERE phone = '{id_khach}'", conn)
    if not df.empty:
        row = df.iloc[0]
        st.title(f"Chào chị {row['name']}")
        st.info("Kế hoạch hưu trí National Life Group của chị.")
        # Logic ghi nhận mắt thần giữ nguyên...
    st.stop()

# TẦNG 1: TRANG CHỦ & ĐĂNG NHẬP
if menu == "🏠 Trang chủ giới thiệu":
    st.markdown("<h1 style='color:#0056D2;'>TMC FINANCIAL GROUP</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Về National Life Group")
        st.write("Giải pháp bảo vệ người Việt tại Mỹ hơn 170 năm qua.")
    with col2:
        if not st.session_state.authenticated:
            with st.container(border=True):
                st.subheader("🔐 Đăng nhập Quản lý")
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                if st.button("Vào hệ thống", use_container_width=True):
                    if u == "Cong" and p == "admin123":
                        st.session_state.authenticated, st.session_state.role, st.session_state.username = True, "Admin", "Cong"
                        st.rerun()
                    else: st.error("Sai thông tin!")
        else:
            st.success(f"Chào mừng quay trở lại, {st.session_state.username}!")

# TẦNG 2: MẮT THẦN
elif menu == "👁️ Mắt Thần (Sale & Khách)":
    st.title("👁️ DANH SÁCH KHÁCH ĐANG TRUY CẬP")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM leads", conn)
    # Lọc theo quyền (Anh Công thấy hết, Sale thấy của mình)
    if st.session_state.role != "Admin":
        df = df[df['owner'] == st.session_state.username]
    
    # Hiển thị những khách có log "KHÁCH VỪA XEM"
    viewing = df[df['note'].str.contains("KHÁCH VỪA XEM LINK", na=False)]
    if not viewing.empty:
        for idx, r in viewing.iterrows():
            st.warning(f"🔥 Khách {r['name']} ({r['phone']}) đang xem bảng minh họa!")
    else:
        st.info("Chưa có khách nào đang online.")
    conn.close()

# TẦNG 3: VẬN HÀNH ADMIN
elif menu == "⚙️ Vận hành Admin":
    st.title("⚙️ HỆ THỐNG VẬN HÀNH TỔNG")
    conn = sqlite3.connect(DB_NAME)
    # Thêm nút bấm quản lý Lead, Backup Excel tại đây như code cũ
    # ...
    conn.close()
