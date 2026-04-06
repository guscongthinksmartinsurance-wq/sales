import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import io

# --- 1. THIẾT LẬP HỆ THỐNG ---
st.set_page_config(page_title="TMC Financial System", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

# Load CSS
try:
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except:
    pass

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, phone TEXT UNIQUE, state TEXT,
                    status TEXT DEFAULT 'New', owner TEXT,
                    note TEXT DEFAULT '', last_updated TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. KIỂM TRA LINK KHÁCH HÀNG (ƯU TIÊN SỐ 1) ---
query_params = st.query_params
id_khach = query_params.get("id")

if id_khach:
    # Nếu có ID khách, khóa toàn bộ App chỉ hiện trang chào khách
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql(f"SELECT * FROM leads WHERE phone = '{id_khach}'", conn)
    if not df.empty:
        row = df.iloc[0]
        # Ghi nhận Mắt Thần
        t_now = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
        view_log = f"<div class='history-entry'><span class='note-time'>{t_now}</span> <span style='color:#f57c00; font-weight:bold;'>🔥 KHÁCH VỪA XEM LINK</span></div>"
        if "KHÁCH VỪA XEM LINK" not in str(row['note'])[:150]:
            new_note = view_log + str(row['note'])
            conn.execute("UPDATE leads SET note = ?, last_updated = ? WHERE phone = ?", (new_note, datetime.now(NY_TZ).isoformat(), id_khach))
            conn.commit()
        
        st.markdown(f"<h1 style='color:#0056D2;'>🛡️ Xin chào {row['name']}</h1>", unsafe_allow_html=True)
        st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", width=200)
        st.info("Kế hoạch tài chính IUL cá nhân hóa của chị đang được bảo mật hiển thị.")
    st.stop()

# --- 3. GIAO DIỆN SIDEBAR (PHÂN CHIA 3 PHẦN) ---
st.sidebar.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", width=150)
st.sidebar.title("MENU HỆ THỐNG")

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Chọn trang
menu = st.sidebar.radio("Chọn chức năng:", ["🏠 Trang chủ giới thiệu", "👁️ Mắt Thần (Sale & Khách)", "⚙️ Vận hành Admin"])

# ==========================================
# PHẦN 1: TRANG CHỦ GIỚI THIỆU
# ==========================================
if menu == "🏠 Trang chủ giới thiệu":
    st.markdown("<h1 style='color:#0056D2;'>TMC FINANCIAL GROUP</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Về National Life Group")
        st.write("Hơn 170 năm đồng hành cùng các gia đình Mỹ. Chúng tôi cung cấp giải pháp bảo vệ và tích lũy an toàn nhất.")
    with col2:
        st.subheader("Giải pháp IUL")
        st.write("Bảo vệ trọn đời - Tích lũy không thuế - Lãi suất theo chỉ số thị trường.")
    
    if not st.session_state.authenticated:
        st.divider()
        with st.expander("🔐 Đăng nhập hệ thống nội bộ"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Đăng nhập"):
                if u == "Cong" and p == "admin123":
                    st.session_state.authenticated, st.session_state.role, st.session_state.username = True, "Admin", "Cong"
                    st.rerun()
                elif u == "Sale1" and p == "123":
                    st.session_state.authenticated, st.session_state.role, st.session_state.username = True, "Sale", "Sale1"
                    st.rerun()

# ==========================================
# PHẦN 2: MẮT THẦN (CHO SALE & KHÁCH)
# ==========================================
elif menu == "👁️ Mắt Thần (Sale & Khách)":
    if not st.session_state.authenticated:
        st.warning("Vui lòng đăng nhập tại Trang Chủ để sử dụng tính năng này.")
    else:
        st.markdown("<h1 style='color:#0056D2;'>👁️ THEO DÕI MẮT THẦN</h1>", unsafe_allow_html=True)
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql("SELECT * FROM leads", conn)
        # Sale chỉ thấy khách của mình
        if st.session_state.role != "Admin":
            df = df[df['owner'] == st.session_state.username]
        
        # Lọc ra những ai "Đang xem" (có chữ KHÁCH VỪA XEM LINK trong Note)
        df_viewing = df[df['note'].str.contains("KHÁCH VỪA XEM LINK", na=False)]
        
        if not df_viewing.empty:
            st.success(f"Đang có {len(df_viewing)} khách hàng đang quan tâm xem bảng minh họa!")
            for idx, row in df_viewing.iterrows():
                with st.container(border=True):
                    st.markdown(f"### 🔥 {row['name']} - {row['phone']}")
                    st.write(f"Nhân viên quản lý: {row['owner']}")
                    st.markdown(f"<div style='background:#fff3e0; padding:10px; border-radius:10px;'>{row['note']}</div>", unsafe_allow_html=True)
        else:
            st.info("Hiện tại chưa có khách nào đang truy cập link.")
        conn.close()

# ==========================================
# PHẦN 3: VẬN HÀNH ADMIN
# ==========================================
elif menu == "⚙️ Vận hành Admin":
    if not st.session_state.authenticated or st.session_state.role != "Admin":
        st.error("Chức năng này chỉ dành riêng cho Admin Công.")
    else:
        st.markdown("<h1 style='color:#0056D2;'>⚙️ HỆ THỐNG VẬN HÀNH</h1>", unsafe_allow_html=True)
        conn = sqlite3.connect(DB_NAME)
        
        # Thêm Lead
        with st.expander("➕ Thêm Lead mới"):
            with st.form("add"):
                n, p, o = st.text_input("Tên"), st.text_input("Phone"), st.selectbox("Sale", ["Cong", "Sale1"])
                if st.form_submit_button("Lưu"):
                    conn.execute("INSERT INTO leads (name, phone, owner) VALUES (?,?,?)", (n,p,o))
                    conn.commit()
                    st.rerun()

        # Bảng quản lý tổng
        df_all = pd.read_sql("SELECT * FROM leads", conn)
        st.dataframe(df_all, use_container_width=True)
        
        if st.button("📥 Xuất Backup Excel"):
            output = io.BytesIO()
            df_all.to_excel(output, index=False)
            st.download_button("Tải file về máy", output.getvalue(), "TMC_Backup.xlsx")
        conn.close()
