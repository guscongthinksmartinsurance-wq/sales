import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import urllib.parse
import base64

# --- 1. CẤU HÌNH & CSS ĐẶC TRỊ (FIX CHỒNG CHỮ) ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f1f5f9; }
    
    /* DIỆT TẬN GỐC LỖI CHỒNG CHỮ TRÊN EXPANDER */
    /* Ẩn tiêu đề mặc định và các ký tự rác của expander */
    .stExpander details summary p { display: none !important; }
    .stExpander details summary svg { display: none !important; }
    
    /* Tạo nhãn mới sạch sẽ cho expander */
    .stExpander details summary::after {
        font-weight: 700; font-size: 13px; color: #475569;
    }
    /* Gán nhãn riêng cho từng nút để không bị lộn */
    div[data-testid="stExpander"]:nth-of-type(1) details summary::after { content: " 📝 GHI CHÚ"; }
    div[data-testid="stExpander"]:nth-of-type(2) details summary::after { content: " 📁 PDF"; }
    div[data-testid="stExpander"]:nth-of-type(3) details summary::after { content: " ⚙️ SỬA"; }

    /* Card Vận Hành */
    .client-card {
        background: white; padding: 25px; border-radius: 15px;
        border: 1px solid #e2e8f0; margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .link-direct { text-decoration: none !important; font-weight: 700; transition: 0.2s; }
    .name-link { font-size: 22px; color: #00263e !important; }
    .id-link { color: #0ea5e9 !important; font-size: 16px; }

    /* Home Card */
    .home-card {
        background: white; border-radius: 20px; overflow: hidden;
        border: 1px solid #e2e8f0; height: 550px; text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    .home-img-container { height: 350px; width: 100%; overflow: hidden; }
    .home-img-container img { width: 100%; height: 100%; object-fit: cover; }
    </style>
    
    <script>
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(function() {
            alert('Đã copy link PDF!');
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
            st.download_button("📂 MỞ HỒ SƠ PDF", data=row['pdf_file'], file_name=f"IUL_{row['name']}.pdf", mime="application/pdf", use_container_width=True)
    conn.close(); st.stop()

# --- SIDEBAR ---
if 'auth' not in st.session_state: st.session_state.auth = False
with st.sidebar:
    logo_p = prof.get('logo_app')
    st.image(logo_p if logo_p and os.path.exists(logo_p) else "https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    if st.session_state.auth:
        selected = st.selectbox("Menu", ["Trang Chủ", "Vận Hành", "Mắt Thần", "Cấu Hình"])
        if st.button("🚪 Đăng xuất"): st.session_state.auth = False; st.rerun()
    else: selected = "Trang Chủ"

# --- VẬN HÀNH ---
if selected == "Vận Hành":
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    t1, t2 = st.tabs(["📊 DANH SÁCH", "➕ THÊM MỚI"])
    
    with t1:
        for idx, row in df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="client-card">
                    <div style="display: flex; justify-content: space-between;">
                        <div style="flex: 7;">
                            <a href="tel:{row['cell']}" class="link-direct name-link">👤 {row['name']}</a> <br>
                            <div style="margin-top:8px;">
                                <a href="{row['crm_link']}" target="_blank" class="link-direct id-link">🆔 Mã CRM: {row['crm_id']}</a> | 
                                <a href="tel:{row['work']}" style="color:#64748b; text-decoration:none; font-weight:600;">🏢 Work: {row['work']}</a>
                            </div>
                            <div style="color:#94a3b8; font-size:13px; margin-top:8px;">
                                ✉️ {row['email']} | 📍 {row['state']} | 👤 {row['owner']} | 🏷️ {row['tags']} | 🚩 <b>{row['status']}</b>
                            </div>
                        </div>
                        <div style="flex: 3; text-align: right;">
                            <a href="rcmobile://sms?number={row['cell']}" style="text-decoration:none; font-size:24px; margin-right:15px;">💬</a>
                            <a href="mailto:{row['email']}" style="text-decoration:none; font-size:24px; margin-right:15px;">✉️</a>
                            <a href="https://calendar.google.com/calendar/r/eventedit?text=Meeting_{row['name']}" target="_blank" style="text-decoration:none; font-size:24px;">📅</a>
                            <br><br>
                            <button onclick="copyToClipboard('https://tmc-elite.streamlit.app/?id={row['cell']}')" 
                                    style="background:#10b981; color:white; border:none; padding:6px 12px; border-radius:6px; font-size:12px; font-weight:700; cursor:pointer;">
                                🔗 COPY LINK PDF
                            </button>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
                
                c_nt, c_up, c_ed = st.columns([5, 2.5, 2.5])
                with c_nt:
                    with st.expander(""): # Để trống nhãn để CSS tự điền
                        with st.form(f"nt_{row['id']}", clear_on_submit=True):
                            txt = st.text_input("Ghi chú", label_visibility="collapsed")
                            if st.form_submit_button("LƯU"):
                                n_n = f"<div>{datetime.now(NY_TZ).strftime('%H:%M')} {txt}</div>" + str(row['note'])
                                conn.execute("UPDATE leads SET note=? WHERE id=?", (n_n, row['id'])); conn.commit(); st.rerun()
                with c_up:
                    with st.expander(""):
                        f = st.file_uploader("Upload", type="pdf", key=f"f_{row['id']}", label_visibility="collapsed")
                        if st.button("LƯU FILE", key=f"b_{row['id']}"):
                            if f: conn.execute("UPDATE leads SET pdf_file=? WHERE id=?", (f.read(), row['id'])); conn.commit(); st.rerun()
                with c_ed:
                    with st.expander(""):
                        with st.form(f"e_{row['id']}"):
                            un = st.text_input("Tên", row['name']); ui = st.text_input("ID", row['crm_id']); ul = st.text_input("Link", row['crm_link'])
                            uc = st.text_input("Cell", row['cell']); uw = st.text_input("Work", row['work']); ue = st.text_input("Email", row['email'])
                            us = st.text_input("State", row['state']); uo = st.text_input("Owner", row['owner']); ut = st.text_input("Tags", row['tags'])
                            if st.form_submit_button("CẬP NHẬT"):
                                conn.execute("UPDATE leads SET name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=? WHERE id=?", (un, ui, ul, uc, uw, ue, us, uo, ut, row['id'])); conn.commit(); st.rerun()

    with t2:
        with st.form("add_new"):
            st.markdown("### ➕ THIẾT LẬP HỒ SƠ (10 TRƯỜNG)")
            c1, c2, c3 = st.columns(3)
            an = c1.text_input("Tên"); ai = c2.text_input("CRM ID"); al = c3.text_input("Link CRM")
            ac = c1.text_input("Cell"); aw = c2.text_input("Work"); ae = c3.text_input("Email")
            as_ = c1.text_input("State"); ao = c2.text_input("Owner", value="Cong"); at = c3.text_input("Tags")
            if st.form_submit_button("LƯU HỒ SƠ"):
                conn.execute("INSERT INTO leads (name, crm_id, crm_link, cell, work, email, state, owner, tags, last_updated) VALUES (?,?,?,?,?,?,?,?,?,?)", (an, ai, al, ac, aw, ae, as_, ao, at, datetime.now(NY_TZ).isoformat()))
                conn.commit(); st.success("Xong!"); st.rerun()
    conn.close()

elif selected == "Trang Chủ":
    st.markdown(f"<h1 style='text-align:center; padding:30px;'>{prof.get('slogan')}</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    def get_b64(p): return base64.b64encode(open(p, "rb").read()).decode() if p and os.path.exists(p) else ""
    with c1: st.markdown(f"<div class='home-card'><div class='home-img-container'><img src='data:image/jpeg;base64,{get_b64(prof.get('img_national'))}'></div><div style='padding:20px;'><h3>National Life Group</h3><p>Uy tín từ 1848.</p></div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='home-card'><div class='home-img-container'><img src='data:image/jpeg;base64,{get_b64(prof.get('img_iul'))}'></div><div style='padding:20px;'><h3>Giải pháp IUL</h3><p>{prof.get('slogan')}</p></div></div>", unsafe_allow_html=True)
    if not st.session_state.auth:
        with st.expander("🔐 LOGIN"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.button("OK"):
                if u == "Cong" and p == "admin123": st.session_state.auth = True; st.rerun()

elif selected == "Cấu Hình":
    with st.form("conf"):
        sl = st.text_input("Slogan", value=prof.get('slogan'))
        c1, c2, c3 = st.columns(3); ul = c1.file_uploader("Logo"); un = c2.file_uploader("Ảnh Nat"); ui = c3.file_uploader("Ảnh IUL")
        if st.form_submit_button("LƯU"):
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
