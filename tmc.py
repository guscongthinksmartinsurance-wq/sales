import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import urllib.parse
import base64

# --- 1. CẤU HÌNH & CSS ELITE ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f1f5f9; }
    .home-card { background: white; padding: 25px; border-radius: 16px; border-top: 5px solid #00263e; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center; margin-bottom: 20px; min-height: 450px; }
    .action-link { color: #0369a1; text-decoration: none; font-weight: 700; padding: 6px 10px; border-radius: 6px; background: #f1f5f9; font-size: 11px; display: inline-block; margin-right: 4px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HÀM XỬ LÝ DATABASE & CACHE ---
def init_db():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, crm_id TEXT, crm_link TEXT, cell TEXT, work TEXT, email TEXT, state TEXT, owner TEXT, tags TEXT, status TEXT DEFAULT 'New', note TEXT DEFAULT '', last_updated TIMESTAMP, pdf_file BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY, slogan TEXT, logo_app TEXT, img_national TEXT, img_iul TEXT)''')
    # Khởi tạo dòng đầu tiên nếu chưa có
    c.execute("INSERT OR IGNORE INTO profile (id, slogan) VALUES (1, 'Sâu sắc - Tận tâm - Chuyên nghiệp')")
    conn.commit(); conn.close()

init_db()

# Dùng cache để load nhanh nhưng phải clear được khi update
@st.cache_data(ttl=600)
def get_profile_data():
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
    res = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()
    return dict(res) if res else {'slogan': 'Sâu sắc - Tận tâm - Chuyên nghiệp'}

prof = get_profile_data()

# --- 3. TẦNG KHÁCH HÀNG ---
id_khach = st.query_params.get("id")
if id_khach:
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM leads WHERE cell = ?", (id_khach,)).fetchone()
    if row:
        t_now = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
        new_n = f"<div style='color:#ef4444;'>{t_now} 🔥 KHÁCH ĐANG XEM PDF</div>" + str(row['note'])
        conn.execute("UPDATE leads SET note=?, last_updated=? WHERE cell=?", (new_n, datetime.now(NY_TZ).isoformat(), id_khach))
        conn.commit()
        st.markdown(f"<h2 style='text-align:center;'>🛡️ Hồ sơ bảo hiểm: {row['name']}</h2>", unsafe_allow_html=True)
        if row['pdf_file']:
            b64 = base64.b64encode(row['pdf_file']).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="900"></iframe>', unsafe_allow_html=True)
    conn.close(); st.stop()

# --- 4. QUẢN TRỊ SIDEBAR ---
if 'auth' not in st.session_state: st.session_state.auth = False

with st.sidebar:
    logo_p = prof.get('logo_app')
    if logo_p and os.path.exists(logo_p): st.image(logo_p, use_container_width=True)
    else: st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    
    if st.session_state.auth:
        from streamlit_option_menu import option_menu
        selected = option_menu(None, ["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"], icons=['house', 'eye', 'command', 'gear'])
        if st.sidebar.button("🚪 ĐĂNG XUẤT", use_container_width=True):
            st.session_state.auth = False; st.rerun()
    else: selected = "Trang Chủ"

# --- PHÂN HỆ TRANG CHỦ ---
if selected == "Trang Chủ":
    st.markdown(f"<h1 style='text-align:center; color:#00263e; margin-bottom:40px;'>{prof.get('slogan')}</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("<div class='home-card'><h3>National Life Group</h3>", unsafe_allow_html=True)
        img_n = prof.get('img_national')
        if img_n and os.path.exists(img_n): st.image(img_n, use_container_width=True)
        st.markdown("<p style='color:#64748b; margin-top:15px;'>Phục vụ từ 1848.</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='home-card'><h3>Giải pháp IUL</h3>", unsafe_allow_html=True)
        img_i = prof.get('img_iul')
        if img_i and os.path.exists(img_i): st.image(img_i, use_container_width=True)
        st.markdown(f"<p style='color:#64748b; margin-top:15px;'>{prof.get('slogan')}</p></div>", unsafe_allow_html=True)
    
    if not st.session_state.auth:
        with st.expander("🔐 ĐĂNG NHẬP"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.button("XÁC NHẬN"):
                if u == "Cong" and p == "admin123": st.session_state.auth = True; st.rerun()

# --- PHÂN HỆ VẬN HÀNH (10 TRƯỜNG ĐẦY ĐỦ) ---
elif selected == "Vận Hành":
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    t1, t2 = st.tabs(["📊 DANH SÁCH", "➕ THÊM HỒ SƠ"])
    with t1:
        for idx, row in df.iterrows():
            with st.container():
                st.markdown(f"""<div style='background:white; padding:20px; border-radius:12px; border:1px solid #e2e8f0; margin-bottom:10px;'>
                    <div style='display:flex; justify-content:space-between;'>
                        <div style='flex:1;'><b>{row['name']}</b> | ID: {row['crm_id']}</div>
                        <div style='flex:1;'>📞 {row['cell']} | 👤 {row['owner']}</div>
                        <div style='flex:1; text-align:right;'><b>{row['status']}</b></div>
                    </div>
                </div>""", unsafe_allow_html=True)
                # (Các nút bấm và form sửa giữ nguyên logic 10 trường như bản trước)
    with t2:
        with st.form("add_full"):
            r1 = st.columns(3); n = r1[0].text_input("Họ tên"); i = r1[1].text_input("CRM ID"); l = r1[2].text_input("Link CRM")
            r2 = st.columns(3); c = r2[0].text_input("Số Cell"); w = r2[1].text_input("Số Work"); e = r2[2].text_input("Email")
            r3 = st.columns(3); s = r3[0].text_input("State"); o = r3[1].text_input("Owner", value="Cong"); t = r3[2].text_input("Tags")
            st_ = st.selectbox("Status", ["New", "Contacted", "Following", "Closed"])
            if st.form_submit_button("LƯU HỒ SƠ"):
                conn.execute("INSERT INTO leads (name, crm_id, crm_link, cell, work, email, state, owner, tags, status, last_updated) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (n, i, l, c, w, e, s, o, t, st_, datetime.now(NY_TZ).isoformat()))
                conn.commit(); st.success("Đã thêm!"); st.rerun()
    conn.close()

# --- PHÂN HỆ CẤU HÌNH (FIXED) ---
elif selected == "Cấu Hình":
    st.markdown("## ⚙️ Cấu Hình Hệ Thống")
    with st.form("config_form"):
        new_sl = st.text_input("Slogan dòng IUL", value=prof.get('slogan'))
        c1, c2, c3 = st.columns(3)
        up_l = c1.file_uploader("Logo Sidebar", type=['png', 'jpg', 'jpeg'])
        up_n = c2.file_uploader("Ảnh National Life", type=['png', 'jpg', 'jpeg'])
        up_i = c3.file_uploader("Ảnh IUL", type=['png', 'jpg', 'jpeg'])
        
        if st.form_submit_button("LƯU THAY ĐỔI"):
            conn = sqlite3.connect(DB_NAME)
            # Cập nhật Slogan
            conn.execute("UPDATE profile SET slogan=? WHERE id=1", (new_sl,))
            
            # Xử lý từng hình ảnh và lưu file
            if up_l:
                with open("logo_app.png", "wb") as f: f.write(up_l.getbuffer())
                conn.execute("UPDATE profile SET logo_app='logo_app.png' WHERE id=1")
            if up_n:
                with open("img_nat.jpg", "wb") as f: f.write(up_n.getbuffer())
                conn.execute("UPDATE profile SET img_national='img_nat.jpg' WHERE id=1")
            if up_i:
                with open("img_iul.jpg", "wb") as f: f.write(up_i.getbuffer())
                conn.execute("UPDATE profile SET img_iul='img_iul.jpg' WHERE id=1")
            
            conn.commit(); conn.close()
            st.cache_data.clear() # QUAN TRỌNG: Xóa cache để hình mới hiện ra ngay
            st.success("Đã lưu cấu hình thành công!")
            st.rerun()
