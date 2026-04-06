import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
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
    
    # Tự động thêm các cột lưu ảnh nếu chưa có (Tránh lỗi KeyError)
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
    # Chuyển về Dictionary để truy cập an toàn bằng .get()
    conn.row_factory = sqlite3.Row
    res = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()
    return dict(res) if res else {}

# --- 2. SIDEBAR & ĐIỀU HƯỚNG ---
prof = get_profile()

with st.sidebar:
    # Hiển thị Logo App từ Cấu hình
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

# --- 3. LOGIC TẦNG KHÁCH HÀNG ---
query_params = st.query_params
id_khach = query_params.get("id")

if id_khach:
    conn = sqlite3.connect(DB_NAME)
    row = conn.execute("SELECT * FROM leads WHERE phone = ?", (id_khach,)).fetchone()
    if row:
        # Ghi log mắt thần...
        st.markdown(f"<h1 style='color:#00263e;'>🛡️ Chào {row[1]}</h1>", unsafe_allow_html=True)
        img_i = prof.get('img_iul')
        if img_i and os.path.exists(img_i): st.image(img_i, use_container_width=True)
    conn.close()
    st.stop()

# =========================================================
# PHẦN 1: TRANG CHỦ (BỐ CỤC 2 BÊN CHỈNH CHU)
# =========================================================
if selected == "Trang Chủ":
    # Banner rộng toàn màn hình
    st.markdown('<div class="hero-banner"><h1>NATIONAL LIFE GROUP</h1><p>Experience the Peace of Mind Since 1848</p></div>', unsafe_allow_html=True)
    
    # Chia 2 cột chính
    col_left, col_right = st.columns(2, gap="large")

    # BÊN TRÁI: NHÀ SẢN XUẤT (NATIONAL LIFE GROUP)
    with col_left:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<p class="section-header">Tập Đoàn National Life Group</p>', unsafe_allow_html=True)
        
        img_n = prof.get('img_national')
        if img_n and os.path.exists(img_n):
            st.image(img_n, use_container_width=True)
        else:
            st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
            
        st.write("""
        Được thành lập từ năm 1848, National Life Group là một trong những tập đoàn tài chính 
        lâu đời và uy tín nhất Hoa Kỳ. Chúng tôi cam kết mang lại giá trị thực và sự bảo vệ 
        vững chắc cho hàng triệu gia đình qua nhiều thế hệ.
        """)
        st.markdown("- **Lịch sử:** 170+ năm kinh nghiệm tài chính.\n- **Sứ mệnh:** Giữ trọn lời hứa với khách hàng.\n- **Uy tín:** Xếp hạng tài chính mức cao từ các tổ chức quốc tế.")
        st.markdown('</div>', unsafe_allow_html=True)

    # BÊN PHẢI: GIẢI PHÁP (DÒNG IUL)
    with col_right:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<p class="section-header">Giải Pháp Tài Chính IUL</p>', unsafe_allow_html=True)
        
        img_i = prof.get('img_iul')
        if img_i and os.path.exists(img_i):
            st.image(img_i, use_container_width=True)
        else:
            st.info("Anh vào mục Cấu Hình để upload ảnh minh họa IUL tại đây.")
            
        st.write(f"**{prof.get('slogan')}**")
        st.write("""
        Indexed Universal Life (IUL) là giải pháp đột phá, kết hợp hoàn hảo giữa bảo vệ sinh mạng 
        và tích lũy tài sản thông minh. Đây là công cụ hưu trí và bảo vệ tối ưu cho người Việt tại Mỹ.
        """)
        st.markdown("- **Tích lũy:** Lãi suất theo chỉ số thị trường, bảo đảm 0% sàn.\n- **Thuế:** Rút tiền sử dụng không chịu thuế thu nhập.\n- **Quyền lợi sống:** Nhận tiền bồi thường khi mắc bệnh hiểm nghèo.")
        st.markdown('</div>', unsafe_allow_html=True)

    # NÚT ĐĂNG NHẬP (Để ở cuối, tinh tế)
    if not st.session_state.authenticated:
        st.write("<br>", unsafe_allow_html=True)
        with st.expander("🔐 TRUY CẬP HỆ THỐNG QUẢN TRỊ"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("XÁC NHẬN"):
                if u == "Cong" and p == "admin123":
                    st.session_state.authenticated, st.session_state.role, st.session_state.username = True, "Admin", "Cong"
                    st.rerun()

# =========================================================
# CÁC PHẦN KHÁC (GIỮ NGUYÊN KHUNG)
# =========================================================
elif selected == "Cấu Hình":
    st.markdown("<div class='main-card'><h2 style='color:#00263e;'>👤 CÀI ĐẶT HỆ THỐNG</h2></div>", unsafe_allow_html=True)
    with st.form("config_form"):
        new_slogan = st.text_input("Slogan dòng IUL", value=prof.get('slogan'))
        c1, c2, c3 = st.columns(3)
        up_logo = c1.file_uploader("Logo App (Sidebar)", type=["png", "jpg"])
        up_nat = c2.file_uploader("Ảnh National Life (Cột trái)", type=["png", "jpg"])
        up_iul = c3.file_uploader("Ảnh dòng IUL (Cột phải)", type=["png", "jpg"])
        
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

elif selected == "Mắt Thần":
    st.write("Phần tính năng Mắt Thần đang đợi anh chỉnh sửa...")

elif selected == "Vận Hành":
    st.write("Phần tính năng Vận Hành đang đợi anh chỉnh sửa...")
