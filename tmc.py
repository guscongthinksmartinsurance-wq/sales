import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
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
    
    /* Card danh sách phẳng & sạch */
    .client-card {
        background: white; padding: 20px; border-radius: 12px;
        border: 1px solid #e2e8f0; margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    .name-link { font-size: 19px; font-weight: 800; color: #00263e !important; text-decoration: none; }
    .id-link { color: #0ea5e9 !important; font-weight: 700; text-decoration: none; font-size: 15px; }
    .meta-text { color: #64748b; font-size: 13px; font-weight: 500; }
    
    /* Trang chủ Card chuyên nghiệp */
    .home-card {
        background: white; border-radius: 20px; overflow: hidden;
        border: 1px solid #e2e8f0; min-height: 520px; text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .home-img { height: 320px; width: 100%; object-fit: cover; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, crm_id TEXT, crm_link TEXT, cell TEXT, work TEXT, email TEXT, state TEXT, owner TEXT, tags TEXT, status TEXT DEFAULT 'New', note TEXT DEFAULT '', last_updated TIMESTAMP, pdf_file BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY, slogan TEXT, logo_app TEXT, img_national TEXT, img_iul TEXT)''')
    c.execute("INSERT OR IGNORE INTO profile (id, slogan) VALUES (1, 'Sâu sắc - Tận tâm - Chuyên nghiệp')")
    conn.commit(); conn.close()

init_db()

@st.cache_data(ttl=300)
def get_prof():
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
    res = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()
    return dict(res) if res else {'slogan': 'Sâu sắc - Tận tâm - Chuyên nghiệp'}

prof = get_prof()

# --- TẦNG KHÁCH HÀNG ---
id_khach = st.query_params.get("id")
if id_khach:
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM leads WHERE cell = ?", (id_khach,)).fetchone()
    if row:
        t_now = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
        new_n = f"<div>{t_now} 🔥 ĐANG XEM PDF</div>" + str(row['note'])
        conn.execute("UPDATE leads SET note=?, last_updated=? WHERE cell=?", (new_n, datetime.now(NY_TZ).isoformat(), id_khach))
        conn.commit()
        if row['pdf_file']:
            st.download_button("📂 MỞ HỒ SƠ PDF CỦA BẠN", data=row['pdf_file'], file_name=f"{row['name']}_IUL.pdf", mime="application/pdf", use_container_width=True)
    conn.close(); st.stop()

# --- SIDEBAR ---
if 'auth' not in st.session_state: st.session_state.auth = False
with st.sidebar:
    st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    if st.session_state.auth:
        selected = st.radio("QUẢN TRỊ", ["Trang Chủ", "Vận Hành", "Mắt Thần", "Cấu Hình"])
        if st.button("🚪 Đăng xuất"): st.session_state.auth = False; st.rerun()
    else: selected = "Trang Chủ"

# --- 4. VẬN HÀNH (SỬA LỖI BỐ CỤC) ---
if selected == "Vận Hành":
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    t1, t2 = st.tabs(["📊 DANH SÁCH", "➕ THÊM MỚI"])
    
    with t1:
        for idx, row in df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="client-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 7;">
                            <a href="tel:{row['cell']}" class="name-link">👤 {row['name']}</a> <br>
                            <div style="margin-top:5px;">
                                <a href="{row['crm_link']}" target="_blank" class="id-link">🆔 {row['crm_id']}</a> | 
                                <a href="tel:{row['work']}" style="color:#64748b; text-decoration:none; font-size:14px;">🏢 Work: {row['work']}</a>
                            </div>
                            <div class="meta-text" style="margin-top:5px;">📍 {row['state']} | 👤 {row['owner']} | 🏷️ {row['tags']} | 🚩 {row['status']}</div>
                        </div>
                        <div style="flex: 3; text-align: right;">
                            <a href="rcmobile://sms?number={row['cell']}" style="text-decoration:none; font-size:24px; margin-right:15px;">💬</a>
                            <a href="mailto:{row['email']}" style="text-decoration:none; font-size:24px; margin-right:15px;">✉️</a>
                            <a href="https://calendar.google.com/calendar/r/eventedit?text=Meeting_{row['name']}" target="_blank" style="text-decoration:none; font-size:24px;">📅</a>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
                
                # CÁC NÚT HỆ THỐNG GỌN GÀNG (EXPANDER KHÔNG CHỒNG CHỮ)
                c1, c2, c3, c4 = st.columns([3, 2, 2, 3])
                with c1:
                    st.button("🔗 COPY LINK PDF", key=f"cp_{row['id']}", on_click=lambda l=f"https://tmc-elite.streamlit.app/?id={row['cell']}": st.write(f"Đã copy: {l}"))
                with c2:
                    with st.expander("📝 NOTE"):
                        with st.form(f"n_{row['id']}", clear_on_submit=True):
                            txt = st.text_input("Ghi chú")
                            if st.form_submit_button("LƯU"):
                                n_n = f"<div>{datetime.now(NY_TZ).strftime('%H:%M')} {txt}</div>" + str(row['note'])
                                conn.execute("UPDATE leads SET note=? WHERE id=?", (n_n, row['id'])); conn.commit(); st.rerun()
                with c3:
                    with st.expander("📁 PDF"):
                        f = st.file_uploader("Upload", type="pdf", key=f"f_{row['id']}")
                        if st.button("LƯU", key=f"b_{row['id']}"):
                            if f: conn.execute("UPDATE leads SET pdf_file=? WHERE id=?", (f.read(), row['id'])); conn.commit(); st.success("Xong!"); st.rerun()
                with c4:
                    with st.expander("⚙️ SỬA"):
                        with st.form(f"e_{row['id']}"):
                            un = st.text_input("Tên", row['name']); ui = st.text_input("ID", row['crm_id']); ul = st.text_input("Link", row['crm_link'])
                            uc = st.text_input("Cell", row['cell']); uw = st.text_input("Work", row['work']); ue = st.text_input("Email", row['email'])
                            us = st.text_input("State", row['state']); uo = st.text_input("Owner", row['owner']); ut = st.text_input("Tags", row['tags'])
                            if st.form_submit_button("UPDATE"):
                                conn.execute("UPDATE leads SET name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=? WHERE id=?", (un, ui, ul, uc, uw, ue, us, uo, ut, row['id'])); conn.commit(); st.rerun()

# --- TRANG CHỦ & CẤU HÌNH PHỤC HỒI ---
elif selected == "Trang Chủ":
    st.markdown(f"<h1 style='text-align:center;'>{prof.get('slogan')}</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    def get_img_b64(p):
        if p and os.path.exists(p):
            with open(p, "rb") as f: return base64.b64encode(f.read()).decode()
        return ""
    with c1:
        st.markdown(f"<div class='home-card'><h3>National Life Group</h3><img src='data:image/jpeg;base64,{get_img_b64(prof.get('img_national'))}' class='home-img'><p>Uy tín từ 1848.</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='home-card'><h3>Giải pháp IUL</h3><img src='data:image/jpeg;base64,{get_img_b64(prof.get('img_iul'))}' class='home-img'><p>{prof.get('slogan')}</p></div>", unsafe_allow_html=True)
    if not st.session_state.auth:
        with st.expander("🔐 Đăng nhập"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.button("OK"):
                if u == "Cong" and p == "admin123": st.session_state.auth = True; st.rerun()

elif selected == "Cấu Hình":
    with st.form("conf"):
        sl = st.text_input("Slogan", value=prof.get('slogan'))
        c1, c2, c3 = st.columns(3); ul = c1.file_uploader("Logo"); un = c2.file_uploader("Ảnh Nat"); ui = c3.file_uploader("Ảnh IUL")
        if st.form_submit_button("LƯU CẤU HÌNH"):
            conn = sqlite3.connect(DB_NAME); conn.execute("UPDATE profile SET slogan=? WHERE id=1", (sl,))
            if ul: 
                with open("logo_app.png", "wb") as f: f.write(ul.getbuffer())
                conn.execute("UPDATE profile SET logo_app='logo_app.png' WHERE id=1")
            if un: 
                with open("img_nat.jpg", "wb") as f: f.write(un.getbuffer())
                conn.execute("UPDATE profile SET img_national='img_nat.jpg' WHERE id=1")
            if ui: 
                with open("img_iul.jpg", "wb") as f: f.write(ui.getbuffer())
                conn.execute("UPDATE profile SET img_iul='img_iul.jpg' WHERE id=1")
            conn.commit(); conn.close(); st.cache_data.clear(); st.rerun()
