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

# Load CSS
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
    # Bảng Profile
    c.execute('''CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY, slogan TEXT)''')
    
    # Tự động thêm các cột lưu ảnh nếu chưa có
    cols = [('logo_app', 'TEXT'), ('img_national', 'TEXT'), ('img_iul', 'TEXT')]
    for col_name, col_type in cols:
        try: c.execute(f"ALTER TABLE profile ADD COLUMN {col_name} {col_type}")
        except: pass
            
    c.execute("SELECT count(*) FROM profile")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO profile (id, slogan) VALUES (1, 'Mang lại sự bình yên và thịnh vượng cho mọi gia đình')")
    conn.commit()
    conn.close()

init_db()

def get_profile():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    res = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()
    return dict(res) if res else {}

# --- 2. SIDEBAR & ĐIỀU HƯỚNG ---
prof = get_profile()

with st.sidebar:
    logo_app = prof.get('logo_app')
    if logo_app and os.path.exists(logo_app):
        st.image(logo_app, use_container_width=True)
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
            styles={"nav-link-selected": {"background-color": "#00263e"}}
        )
        if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    else:
        selected = "Trang Chủ"

# --- 3. LOGIC TẦNG KHÁCH HÀNG (ƯU TIÊN) ---
query_params = st.query_params
id_khach = query_params.get("id")

if id_khach:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM leads WHERE phone = ?", (id_khach,)).fetchone()
    if row:
        # Ghi log mắt thần
        t_now = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
        view_log = f"<div class='history-entry'><span class='note-time'>{t_now}</span> <span style='color:#f57c00; font-weight:bold;'>🔥 KHÁCH ĐANG XEM</span></div>"
        if "KHÁCH ĐANG XEM" not in str(row['note'])[:150]:
            new_note = view_log + str(row['note'])
            conn.execute("UPDATE leads SET note = ?, last_updated = ? WHERE phone = ?", 
                         (new_note, datetime.now(NY_TZ).isoformat(), id_khach))
            conn.commit()

        st.markdown(f"<h1 style='color:#00263e;'>🛡️ Chào {row['name']}</h1>", unsafe_allow_html=True)
        img_i = prof.get('img_iul')
        if img_i and os.path.exists(img_i): st.image(img_i, use_container_width=True)
    conn.close()
    st.stop()

# --- 4. CÁC HÀM HIỂN THỊ GIAO DIỆN ---

def show_home_page():
    # Banner chính
    st.markdown('<div class="hero-banner"><h1>NATIONAL LIFE GROUP</h1><p>Experience the Peace of Mind Since 1848</p></div>', unsafe_allow_html=True)
    
    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<p class="section-header">Tập Đoàn National Life Group</p>', unsafe_allow_html=True)
        img_n = prof.get('img_national')
        if img_n and os.path.exists(img_n):
            st.image(img_n, use_container_width=True)
        else:
            st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
        st.write("National Life Group là biểu tượng tin cậy tại Hoa Kỳ từ năm 1848, mang đến giải pháp bảo vệ tài chính bền vững.")
        st.markdown("- **Uy tín:** 170+ năm hoạt động.\n- **Cam kết:** Giữ trọn lời hứa.\n- **Vững mạnh:** Top đầu tài chính.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<p class="section-header">Giải Pháp Tài Chính IUL</p>', unsafe_allow_html=True)
        img_i = prof.get('img_iul')
        if img_i and os.path.exists(img_i):
            st.image(img_i, use_container_width=True)
        else:
            st.info("Vào mục Cấu Hình để upload ảnh IUL.")
        st.write(f"**{prof.get('slogan')}**")
        st.write("IUL kết hợp bảo vệ sinh mạng và tích lũy hưu trí không thuế, an toàn vốn trước biến động thị trường.")
        st.markdown("- **An toàn:** Bảo đảm 0% sàn.\n- **Linh hoạt:** Rút tiền không thuế.\n- **Toàn diện:** Quyền lợi sống ưu việt.")
        st.markdown('</div>', unsafe_allow_html=True)

    if not st.session_state.authenticated:
        st.write("<br>", unsafe_allow_html=True)
        with st.expander("🔐 QUẢN TRỊ HỆ THỐNG"):
            u = st.text_input("Username", key="login_u")
            p = st.text_input("Password", type="password", key="login_p")
            if st.button("XÁC NHẬN"):
                if u == "Cong" and p == "admin123":
                    st.session_state.authenticated, st.session_state.role, st.session_state.username = True, "Admin", "Cong"
                    st.rerun()

# --- 5. ĐIỀU HƯỚNG CHÍNH ---

if selected == "Trang Chủ":
    show_home_page()

elif selected == "Mắt Thần":
    st.markdown("<div class='main-card'><h2 style='color:#00263e;'>👁️ THEO DÕI REAL-TIME</h2></div>", unsafe_allow_html=True)
    st.info("Phân hệ Mắt Thần đang sẵn sàng để anh chỉnh sửa tính năng.")

elif selected == "Vận Hành":
    st.markdown("<div class='main-card'><h2 style='color:#00263e;'>⚙️ QUẢN LÝ HỆ THỐNG</h2></div>", unsafe_allow_html=True)
    st.info("Phân hệ Vận Hành đang sẵn sàng để anh chỉnh sửa tính năng.")

elif selected == "Cấu Hình":
    st.markdown("<div class='main-card'><h2 style='color:#00263e;'>👤 CÀI ĐẶT HỆ THỐNG</h2></div>", unsafe_allow_html=True)
    with st.form("config_form"):
        st.markdown("### 📝 Thay đổi Slogan")
        new_slogan = st.text_input("Slogan dòng IUL", value=prof.get('slogan'), label_visibility="collapsed")
        st.write("---")
        st.markdown("### 🖼️ Cập nhật Hình ảnh")
        c1, c2, c3 = st.columns(3)
        with c1: up_logo = st.file_uploader("Logo Sidebar", type=["png", "jpg"], key="up_l")
        with c2: up_nat = st.file_uploader("Ảnh National Life", type=["png", "jpg"], key="up_n")
        with c3: up_iul = st.file_uploader("Ảnh dòng IUL", type=["png", "jpg"], key="up_i")
        
        if st.form_submit_button("💾 LƯU TẤT CẢ THAY ĐỔI", use_container_width=True):
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
