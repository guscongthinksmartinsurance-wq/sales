import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import io
import os
from streamlit_option_menu import option_menu

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

# Load giao diện
try:
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except: pass

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Bảng Leads
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, phone TEXT UNIQUE, state TEXT,
                    status TEXT DEFAULT 'New', owner TEXT,
                    note TEXT DEFAULT '', last_updated TIMESTAMP)''')
    # Bảng Profile (Thêm các cột lưu ảnh anh tự upload)
    c.execute('''CREATE TABLE IF NOT EXISTS profile (
                    id INTEGER PRIMARY KEY, slogan TEXT, 
                    logo_app TEXT, img_national TEXT, img_iul TEXT)''')
    
    c.execute("SELECT count(*) FROM profile")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO profile (id, slogan) VALUES (1, 'Mang lại sự bình yên và thịnh vượng cho mọi gia đình')")
    conn.commit()
    conn.close()

init_db()

def get_profile():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM profile WHERE id=1", conn)
    conn.close()
    return df.iloc[0]

# --- 2. SIDEBAR & ĐIỀU HƯỚNG ---
prof = get_profile()
with st.sidebar:
    # Ưu tiên hiện Logo App anh upload
    if prof['logo_app'] and os.path.exists(prof['logo_app']):
        st.image(prof['logo_app'], use_container_width=True)
    else:
        st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    
    st.divider()
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        selected = option_menu(
            menu_title=None,
            options=["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"],
            icons=["house", "eye", "gear", "person-badge"],
            styles={"nav-link-selected": {"background-color": "#0056D2"}}
        )
        if st.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    else:
        selected = "Trang Chủ"
        st.info("🔓 Đăng nhập để quản lý")

# --- 3. LOGIC TẦNG KHÁCH HÀNG (ID TRÊN URL) ---
query_params = st.query_params
id_khach = query_params.get("id")

if id_khach:
    conn = sqlite3.connect(DB_NAME)
    df_k = pd.read_sql(f"SELECT * FROM leads WHERE phone = '{id_khach}'", conn)
    if not df_k.empty:
        row = df_k.iloc[0]
        # Xử lý ghi Mắt thần vào note... (logic giữ nguyên)
        st.markdown(f"<h1 style='color:#0056D2;'>🛡️ Chào {row['name']}</h1>", unsafe_allow_html=True)
        if prof['img_iul'] and os.path.exists(prof['img_iul']):
            st.image(prof['img_iul'], use_container_width=True)
        st.info("Giải pháp tài chính cá nhân hóa của bạn.")
    conn.close()
    st.stop()

# --- 4. CÁC TRANG CHỨC NĂNG ---
if selected == "Trang Chủ":
    st.markdown('<div class="hero-banner"><h1>NATIONAL LIFE GROUP</h1><p>Experience the Peace of Mind Since 1848</p></div>', unsafe_allow_html=True)
    
    col_text, col_img = st.columns([1.2, 1], gap="large")
    with col_text:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<p class="section-header">Giải Pháp IUL Cho Gia Đình Việt</p>', unsafe_allow_html=True)
        st.write(f"**{prof['slogan']}**")
        st.write("""
        Sản phẩm Indexed Universal Life (IUL) của National Life Group không chỉ bảo vệ tài chính 
        mà còn là công cụ tích lũy an toàn, rút tiền không thuế cho hưu trí và tương lai.
        """)
        st.markdown("- Bảo vệ trọn đời trước biến cố.\n- Tích lũy lãi kép dựa trên thị trường chứng khoán.\n- Bảo đảm 0% sàn, không lo lỗ vốn.\n- Quyền lợi sống vượt trội.")
        
        if prof['img_iul'] and os.path.exists(prof['img_iul']):
            st.image(prof['img_iul'], use_container_width=True, caption="Minh họa giải pháp IUL")
            
        if not st.session_state.authenticated:
            st.divider()
            with st.expander("TRUY CẬP QUẢN TRỊ"):
                u = st.text_input("Username", key="u_home")
                p = st.text_input("Password", type="password", key="p_home")
                if st.button("XÁC NHẬN"):
                    if u == "Cong" and p == "admin123":
                        st.session_state.authenticated, st.session_state.role, st.session_state.username = True, "Admin", "Cong"
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_img:
        if prof['img_national'] and os.path.exists(prof['img_national']):
            st.image(prof['img_national'], use_container_width=True)
        else:
            st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)

elif selected == "Mắt Thần":
    st.markdown("<div class='main-card'><h2 class='tmc-title'>👁️ THEO DÕI KHÁCH HÀNG</h2></div>", unsafe_allow_html=True)
    # Thêm logic hiển thị khách đang online tại đây...

elif selected == "Vận Hành":
    st.markdown("<div class='main-card'><h2 class='tmc-title'>⚙️ VẬN HÀNH DỮ LIỆU</h2></div>", unsafe_allow_html=True)
    # Thêm logic Thêm/Sửa/Xóa Lead tại đây...

elif selected == "Cấu Hình":
    st.markdown("<div class='main-card'><h2 class='tmc-title'>👤 CÀI ĐẶT GIAO DIỆN</h2></div>", unsafe_allow_html=True)
    with st.form("config_form"):
        new_slogan = st.text_input("Slogan Trang Chủ", value=prof['slogan'])
        c1, c2, c3 = st.columns(3)
        up_logo = c1.file_uploader("Logo App", type=["png", "jpg"])
        up_nat = c2.file_uploader("Ảnh National Life", type=["png", "jpg"])
        up_iul = c3.file_uploader("Ảnh dòng IUL", type=["png", "jpg"])
        
        if st.form_submit_button("LƯU TẤT CẢ"):
            conn = sqlite3.connect(DB_NAME)
            if up_logo:
                with open("logo_app.png", "wb") as f: f.write(up_logo.getbuffer())
                conn.execute("UPDATE profile SET logo_app='logo_app.png' WHERE id=1")
            if up_nat:
                with open("img_nat.jpg", "wb") as f: f.write(up_nat.getbuffer())
                conn.execute("UPDATE profile SET img_national='img_nat.jpg' WHERE id=1")
            if up_iul:
                with open("img_iul.jpg", "wb") as f: f.write(up_iul.getbuffer())
                conn.execute("UPDATE profile SET img_iul='img_iul.jpg' WHERE id=1")
            conn.execute("UPDATE profile SET slogan=? WHERE id=1", (new_slogan,))
            conn.commit()
            conn.close()
            st.success("Đã lưu thành công!"); st.rerun()
