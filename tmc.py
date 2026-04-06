import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import io

# --- 1. KHỞI TẠO & CẤU HÌNH ---
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
    # Bảng cấu hình Profile
    conn.execute('''CREATE TABLE IF NOT EXISTS profile (
                    id INTEGER PRIMARY KEY,
                    app_name TEXT, slogan TEXT, logo_url TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. XỬ LÝ PROFILE & SIDEBAR ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

with st.sidebar:
    st.markdown("<h2 style='color:#0056D2;'>🛡️ TMC SYSTEM</h2>", unsafe_allow_html=True)
    
    # Hiển thị Logo từ cài đặt hoặc mặc định
    st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", width=180)
    
    st.divider()
    # Điều hướng Menu
    if st.session_state.authenticated:
        menu = st.radio("CHỨC NĂNG", ["🏠 Trang Chủ", "👁️ Mắt Thần", "⚙️ Vận Hành Tổng", "👤 Cài Đặt Profile"])
        if st.button("🚪 Đăng xuất"):
            st.session_state.authenticated = False
            st.rerun()
    else:
        menu = "🏠 Trang Chủ"
        st.info("Đăng nhập tại Trang Chủ để mở rộng tính năng.")

# --- 3. ĐIỀU HƯỚNG TẦNG ---
query_params = st.query_params
id_khach = query_params.get("id")

# --- TẦNG KHÁCH HÀNG (Dành riêng cho khách) ---
if id_khach:
    conn = sqlite3.connect(DB_NAME)
    df_k = pd.read_sql(f"SELECT * FROM leads WHERE phone = '{id_khach}'", conn)
    if not df_k.empty:
        row = df_k.iloc[0]
        # Mắt thần ghi log... (giữ nguyên logic cũ)
        st.markdown(f"<h1 class='tmc-title'>Chào {row['name']}</h1>", unsafe_allow_html=True)
        st.image("https://www.nationallife.com/img/National-Life-Group-Foundation.jpg", use_container_width=True)
        st.subheader("Giải pháp IUL cá nhân hóa của bạn")
    st.stop()

# --- PHẦN 1: TRANG CHỦ GIỚI THIỆU ---
if menu == "🏠 Trang Chủ":
    st.markdown("<h1 class='tmc-title' style='text-align:center;'>TMC FINANCIAL GROUP</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-style:italic;'>\"Bringing Peace of Mind to Every Family\"</p>", unsafe_allow_html=True)
    
    # Banner hình ảnh National Life
    st.image("https://www.nationallife.com/img/National-Life-Group-Foundation.jpg", caption="Hành trình 170 năm bảo vệ tài chính gia đình Mỹ")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏆 Về National Life Group")
        st.write("Được thành lập từ năm 1848, chúng tôi tự hào là đơn vị tiên phong cung cấp giải pháp bảo hiểm nhân thọ có giá trị tích lũy cao nhất thị trường.")
    with col2:
        st.markdown("### 📈 Giải pháp IUL")
        st.write("Sự kết hợp hoàn hảo giữa bảo vệ và đầu tư an toàn. Giúp quý khách hàng tích lũy hưu trí và rút tiền không thuế.")

    if not st.session_state.authenticated:
        st.divider()
        with st.container():
            st.subheader("🔐 Đăng nhập Quản trị")
            u, p = st.text_input("Username"), st.text_input("Password", type="password")
            if st.button("VÀO HỆ THỐNG"):
                if u == "Cong" and p == "admin123":
                    st.session_state.authenticated, st.session_state.role, st.session_state.username = True, "Admin", "Cong"
                    st.rerun()

# --- PHẦN 2: MẮT THẦN (THEO DÕI KHÁCH ONLINE) ---
elif menu == "👁️ Mắt Thần":
    st.markdown("<h1 class='tmc-title'>👁️ THEO DÕI KHÁCH HÀNG ĐANG XEM</h1>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM leads", conn)
    # Lọc khách đang online
    viewing = df[df['note'].str.contains("KHÁCH VỪA XEM LINK", na=False)]
    
    if not viewing.empty:
        for idx, r in viewing.iterrows():
            with st.container():
                st.markdown(f"#### 🔥 Khách: {r['name']} ({r['phone']})")
                st.write(f"Tiểu bang: {r['state']} | Sale phụ trách: {r['owner']}")
                st.divider()
    else:
        st.info("Hiện tại chưa có khách hàng nào đang truy cập link.")
    conn.close()

# --- PHẦN 3: VẬN HÀNH TỔNG (QUẢN LÝ DỮ LIỆU) ---
elif menu == "⚙️ Vận Hành Tổng":
    st.markdown("<h1 class='tmc-title'>⚙️ VẬN HÀNH DỮ LIỆU TỔNG</h1>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    
    # 1. Thêm mới Lead
    with st.expander("➕ Thêm Khách Hàng Mới"):
        with st.form("add"):
            n, p, s, o = st.text_input("Tên"), st.text_input("Số Phone"), st.text_input("State"), st.selectbox("Sale", ["Cong", "Sale1"])
            if st.form_submit_button("Lưu"):
                conn.execute("INSERT INTO leads (name, phone, state, owner) VALUES (?,?,?,?)", (n,p,s,o))
                conn.commit()
                st.success("Đã thêm thành công!"); st.rerun()

    # 2. Bảng quản lý tổng có nút Xóa/Sửa
    df_all = pd.read_sql("SELECT * FROM leads", conn)
    st.dataframe(df_all, use_container_width=True)
    
    if st.button("📥 XUẤT BACKUP EXCEL"):
        output = io.BytesIO()
        df_all.to_excel(output, index=False)
        st.download_button("Tải file Excel", output.getvalue(), "TMC_Backup.xlsx")
    conn.close()

# --- PHẦN 4: CÀI ĐẶT PROFILE ---
elif menu == "👤 Cài Đặt Profile":
    st.markdown("<h1 class='tmc-title'>👤 THÔNG TIN PROFILE & HỆ THỐNG</h1>", unsafe_allow_html=True)
    with st.container():
        st.text_input("Tên hiển thị hệ thống", value="TMC FINANCIAL GROUP")
        st.text_area("Slogan của anh", value="Bringing Peace of Mind to Every Family")
        st.file_uploader("Thay đổi Logo cá nhân của anh")
        if st.button("CẬP NHẬT PROFILE"):
            st.success("Đã cập nhật thông tin thành công!")
