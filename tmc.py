import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import urllib.parse
import base64

# --- 1. CẤU HÌNH & CSS ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f1f5f9; }
    
    /* Trang chủ Card Elite */
    .home-card {
        background: white; padding: 0; border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        text-align: center; margin-bottom: 30px; overflow: hidden;
        border: 1px solid #e2e8f0; height: 550px;
    }
    .home-img-container { height: 320px; width: 100%; overflow: hidden; }
    .home-img-container img { width: 100%; height: 100%; object-fit: cover; }
    .home-content { padding: 25px; }

    /* Vận hành Card Tinh gọn */
    .client-card {
        background: white; padding: 15px 25px; border-radius: 12px;
        border: 1px solid #e2e8f0; margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    .link-direct { text-decoration: none !important; font-weight: 700; transition: 0.2s; }
    .name-link { font-size: 18px; color: #00263e !important; }
    .id-link { color: #0ea5e9 !important; font-size: 15px; }
    .meta-text { color: #64748b; font-size: 13px; font-weight: 500; }
    
    /* Nút bấm hệ thống */
    .btn-action {
        text-decoration: none !important; color: #475569 !important;
        background: #f8fafc; padding: 5px 12px; border-radius: 6px;
        font-size: 12px; font-weight: 600; border: 1px solid #e2e8f0;
        display: inline-block;
    }
    .btn-action:hover { background: #00263e; color: white !important; }
    </style>
    
    <script>
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(function() {
            alert('Đã copy link PDF của khách hàng!');
        }, function(err) {
            console.error('Lỗi copy: ', err);
        });
    }
    </script>
""", unsafe_allow_html=True)

def init_db():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, crm_id TEXT, crm_link TEXT, cell TEXT, work TEXT, email TEXT, state TEXT, owner TEXT, tags TEXT, status TEXT DEFAULT 'New', note TEXT DEFAULT '', last_updated TIMESTAMP, pdf_file BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY, slogan TEXT, logo_app TEXT, img_national TEXT, img_iul TEXT)''')
    c.execute("INSERT OR IGNORE INTO profile (id, slogan) VALUES (1, 'Sâu sắc - Tận tâm - Chuyên nghiệp')")
    conn.commit(); conn.close()

init_db()

@st.cache_data(ttl=600)
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
        t_now = datetime.now(pytz.timezone('America/New_York')).strftime('[%m/%d %H:%M]')
        new_n = f"<div style='color:red;'>{t_now} 🔥 KHÁCH ĐANG XEM PDF</div>" + str(row['note'])
        conn.execute("UPDATE leads SET note=?, last_updated=? WHERE cell=?", (new_n, datetime.now(pytz.timezone('America/New_York')).isoformat(), id_khach))
        conn.commit()
        if row['pdf_file']:
            b64 = base64.b64encode(row['pdf_file']).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="900"></iframe>', unsafe_allow_html=True)
    conn.close(); st.stop()

# --- QUẢN TRỊ ---
if 'auth' not in st.session_state: st.session_state.auth = False
with st.sidebar:
    logo_p = prof.get('logo_app')
    st.image(logo_p if logo_p and os.path.exists(logo_p) else "https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    if st.session_state.auth:
        from streamlit_option_menu import option_menu
        selected = option_menu(None, ["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"], icons=['house', 'eye', 'command', 'gear'])
        if st.sidebar.button("🚪 ĐĂNG XUẤT", use_container_width=True): st.session_state.auth = False; st.rerun()
    else: selected = "Trang Chủ"

if selected == "Vận Hành":
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    t1, t2 = st.tabs(["📊 DANH SÁCH", "➕ THÊM MỚI"])
    
    with t1:
        for idx, row in df.iterrows():
            with st.container():
                # Dòng 1: Nhúng link trực tiếp vào các thông tin chính
                st.markdown(f"""
                <div class="client-card">
                    <div style="display: flex; gap: 30px; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 10px;">
                        <a href="tel:{row['cell']}" class="link-direct name-link">👤 {row['name']}</a>
                        <a href="{row['crm_link']}" target="_blank" class="link-direct id-link">🆔 {row['crm_id']}</a>
                        <a href="tel:{row['work']}" class="link-direct meta-text" style="color:#475569 !important;">🏢 Work: {row['work']}</a>
                        <div class="meta-text">📍 {row['state']} | 👤 {row['owner']} | 🏷️ {row['status']}</div>
                    </div>
                    <div style="margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap;">
                        <a href="rcmobile://sms?number={row['cell']}" class="btn-action">💬 SMS</a>
                        <a href="mailto:{row['email']}" class="btn-action">✉️ MAIL</a>
                        <a href="https://calendar.google.com/calendar/r/eventedit?text=Meeting_{urllib.parse.quote(str(row['name']))}" target="_blank" class="btn-action">📅 CALENDAR</a>
                        <button onclick="copyToClipboard('https://tmc-elite.streamlit.app/?id={row['cell']}')" 
                                style="background:#10b981; color:white; border:none; padding:5px 12px; border-radius:6px; font-size:12px; font-weight:700; cursor:pointer;">
                            🔗 COPY LINK PDF
                        </button>
                    </div>
                </div>""", unsafe_allow_html=True)
                
                # Dòng 2: Các nút hệ thống (Ghi chú, Upload, Sửa) dàn hàng ngang
                c_nt, c_up, c_ed = st.columns([5, 2.5, 2.5])
                with c_nt:
                    with st.form(f"nt_{row['id']}", clear_on_submit=True):
                        ni = st.text_input("Ghi chú nhanh", label_visibility="collapsed", placeholder="Nhập ghi chú...")
                        if st.form_submit_button("LƯU", use_container_width=True):
                            t_s = datetime.now(pytz.timezone('America/New_York')).strftime('[%H:%M]')
                            n_n = f"<div>{t_s} {ni}</div>" + str(row['note'])
                            conn.execute("UPDATE leads SET note=? WHERE id=?", (n_n, row['id'])); conn.commit(); st.rerun()
                with c_up:
                    with st.popover("📁 UPLOAD PDF", use_container_width=True):
                        f = st.file_uploader("Chọn file PDF", type="pdf", key=f"f_{row['id']}")
                        if st.button("XÁC NHẬN UP", key=f"b_{row['id']}"):
                            if f: conn.execute("UPDATE leads SET pdf_file=? WHERE id=?", (f.read(), row['id'])); conn.commit(); st.success("Xong!"); st.rerun()
                with c_ed:
                    with st.popover("⚙️ SỬA HỒ SƠ", use_container_width=True):
                        with st.form(f"e_{row['id']}"):
                            un = st.text_input("Tên", row['name']); ui = st.text_input("ID", row['crm_id']); ul = st.text_input("Link", row['crm_link'])
                            uc = st.text_input("Cell", row['cell']); uw = st.text_input("Work", row['work']); ue = st.text_input("Email", row['email'])
                            us = st.text_input("State", row['state']); uo = st.text_input("Owner", row['owner']); ut = st.text_input("Tags", row['tags'])
                            if st.form_submit_button("CẬP NHẬT"):
                                conn.execute("UPDATE leads SET name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=? WHERE id=?", (un, ui, ul, uc, uw, ue, us, uo, ut, row['id'])); conn.commit(); st.rerun()

    with t2:
        with st.form("add_new"):
            st.markdown("### ➕ THÊM HỒ SƠ (10 TRƯỜNG)")
            r1 = st.columns(3); n = r1[0].text_input("Họ tên"); i = r1[1].text_input("CRM ID"); l = r1[2].text_input("Link CRM")
            r2 = st.columns(3); c = r2[0].text_input("Số Cell"); w = r2[1].text_input("Số Work"); e = r2[2].text_input("Email")
            r3 = st.columns(3); s = r3[0].text_input("State"); o = r3[1].text_input("Owner", value="Cong"); t = r3[2].text_input("Tags")
            if st.form_submit_button("LƯU HỒ SƠ", use_container_width=True):
                conn.execute("INSERT INTO leads (name, crm_id, crm_link, cell, work, email, state, owner, tags, last_updated) VALUES (?,?,?,?,?,?,?,?,?,?)", (n, i, l, c, w, e, s, o, t, datetime.now(pytz.timezone('America/New_York')).isoformat()))
                conn.commit(); st.success("Đã thêm!"); st.rerun()
    conn.close()

elif selected == "Trang Chủ":
    st.markdown(f"<h1 style='text-align:center; color:#00263e; padding: 30px 0;'>{prof.get('slogan')}</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    def get_img(p): return base64.b64encode(open(p, "rb").read()).decode() if p and os.path.exists(p) else ""
    with c1:
        st.markdown(f"<div class='home-card'><div class='home-img-container'><img src='data:image/jpeg;base64,{get_img(prof.get('img_national'))}'></div><div class='home-content'><h3>National Life Group</h3><p>Uy tín từ 1848.</p></div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='home-card'><div class='home-img-container'><img src='data:image/jpeg;base64,{get_img(prof.get('img_iul'))}'></div><div class='home-content'><h3>Giải pháp IUL</h3><p>{prof.get('slogan')}</p></div></div>", unsafe_allow_html=True)
    if not st.session_state.auth:
        with st.expander("🔐 LOGIN"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.button("XÁC NHẬN"):
                if u == "Cong" and p == "admin123": st.session_state.auth = True; st.rerun()

elif selected == "Cấu Hình":
    with st.form("conf"):
        sl = st.text_input("Slogan", value=prof.get('slogan'))
        c1, c2, c3 = st.columns(3); ul = c1.file_uploader("Logo"); un = c2.file_uploader("Ảnh Nat"); ui = c3.file_uploader("Ảnh IUL")
        if st.form_submit_button("LƯU TẤT CẢ"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("UPDATE profile SET slogan=? WHERE id=1", (sl,))
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

elif selected == "Mắt Thần":
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT * FROM leads WHERE note LIKE '%ĐANG XEM%' ORDER BY last_updated DESC LIMIT 15", conn)
    for _, row in df.iterrows():
        st.error(f"🔥 {row['name']} đang xem PDF! | {row['note']}")
    conn.close()
