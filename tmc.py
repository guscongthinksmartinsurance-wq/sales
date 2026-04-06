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
    
    # KIỂM TRA VÀ TỰ ĐỘNG THÊM CỘT NẾU THIẾU (Sửa lỗi KeyError)
    columns_to_add = [
        ('logo_app', 'TEXT'),
        ('img_national', 'TEXT'),
        ('img_iul', 'TEXT')
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            c.execute(f"ALTER TABLE profile ADD COLUMN {col_name} {col_type}")
        except:
            pass # Cột đã tồn tại
            
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
    # Kiểm tra cột logo_app (Dùng get để tránh lỗi nếu fetch fail)
    logo_path = prof.get('logo_app')
    if logo_path and os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
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
        if st.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    else:
        selected = "Trang Chủ"
        st.info("🔓 Đăng nhập để quản lý")

# --- 3. ĐIỀU HƯỚNG TẦNG ---
query_params = st.query_params
id_khach = query_params.get("id")

if id_khach:
    # TẦNG KHÁCH HÀNG
    conn = sqlite3.connect(DB_NAME)
    df_k = pd.read_sql(f"SELECT * FROM leads WHERE phone = '{id_khach}'", conn)
    if not df_k.empty:
        row = df_k.iloc[0]
        # Logic ghi mắt thần... (đã tối ưu)
        t_now = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
        view_log = f"<div class='history-entry'><span class='note-time'>{t_now}</span> <span style='color:#f57c00; font-weight:bold;'>🔥 KHÁCH VỪA XEM LINK</span></div>"
        if "KHÁCH VỪA XEM LINK" not in str(row['note'])[:150]:
            new_note = view_log + str(row['note'])
            conn.execute("UPDATE leads SET note = ?, last_updated = ? WHERE phone = ?", (new_note, datetime.now(NY_TZ).isoformat(), id_khach))
            conn.commit()

        st.markdown(f"<h1 style='color:#00263e;'>🛡️ Chào {row['name']}</h1>", unsafe_allow_html=True)
        img_i = prof.get('img_iul')
        if img_i and os.path.exists(img_i):
            st.image(img_i, use_container_width=True)
        st.info("Kế hoạch tài chính cá nhân hóa của bạn từ National Life Group.")
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
        st.write("Sản phẩm Indexed Universal Life (IUL) của National Life Group mang lại sự bảo vệ và tích lũy an toàn.")
        st.markdown("- Bảo vệ tài chính trọn đời.\n- Tích lũy lãi kép dựa trên thị trường.\n- Đảm bảo 0% sàn.\n- Quyền lợi sống ưu việt.")
        
        img_i = prof.get('img_iul')
        if img_i and os.path.exists(img_i):
            st.image(img_i, use_container_width=True)
            
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
        img_n = prof.get('img_national')
        if img_n and os.path.exists(img_n):
            st.image(img_n, use_container_width=True)
        else:
            st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)

elif selected == "Mắt Thần":
    st.markdown("<div class='main-card'><h2 style='color:#00263e;'>👁️ THEO DÕI KHÁCH HÀNG</h2></div>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM leads", conn)
    viewing = df[df['note'].str.contains("KHÁCH VỪA XEM LINK", na=False)]
    if not viewing.empty:
        for _, r in viewing.iterrows():
            with st.container(border=True):
                st.write(f"🔥 **{r['name']}** ({r['phone']}) - Sale: {r['owner']}")
                st.caption(f"Lịch sử: {r['note'][:150]}...")
    else:
        st.info("Hiện chưa có khách nào đang truy cập link.")
    conn.close()

elif selected == "Vận Hành":
    st.markdown("<div class='main-card'><h2 style='color:#00263e;'>⚙️ VẬN HÀNH DỮ LIỆU</h2></div>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    # Phần thêm lead và bảng quản lý như cũ
    tab1, tab2 = st.tabs(["➕ Thêm Lead", "📊 Quản lý"])
    with tab1:
        with st.form("add"):
            n, p, o = st.text_input("Tên"), st.text_input("Phone"), st.selectbox("Sale", ["Cong", "Sale1"])
            if st.form_submit_button("Lưu"):
                try:
                    conn.execute("INSERT INTO leads (name, phone, owner) VALUES (?,?,?)", (n,p,o))
                    conn.commit()
                    st.success("Đã thêm thành công!"); st.rerun()
                except: st.error("Lỗi: Số điện thoại đã tồn tại.")
    with tab2:
        df_all = pd.read_sql("SELECT * FROM leads", conn)
        st.dataframe(df_all, use_container_width=True)
    conn.close()

elif selected == "Cấu Hình":
    st.markdown("<div class='main-card'><h2 style='color:#00263e;'>👤 CÀI ĐẶT GIAO DIỆN</h2></div>", unsafe_allow_html=True)
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
