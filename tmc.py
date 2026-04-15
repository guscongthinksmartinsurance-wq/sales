import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import urllib.parse
import base64

# --- 1. CẤU HÌNH & CSS (TỐI GIẢN - KHÔNG CAN THIỆP CHỮ) ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f1f5f9; }
    
    /* Card khách hàng Elite */
    .client-card {
        background: white; padding: 15px 25px; border-radius: 12px;
        border: 1px solid #e2e8f0; margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    .link-direct { text-decoration: none !important; font-weight: 700; transition: 0.2s; }
    .name-link { font-size: 18px; color: #00263e !important; }
    .id-link { color: #0ea5e9 !important; font-size: 15px; }
    
    /* Ép khung Popover to ra để không bị chồng chữ */
    div[data-testid="stPopover"] div[data-testid="stPopoverContent"] {
        min-width: 400px !important;
    }
    
    /* Nút Copy Link PDF */
    .btn-copy {
        background: #10b981; color: white !important; 
        padding: 5px 12px; border-radius: 6px; 
        font-size: 12px; font-weight: 700; text-decoration: none;
        display: inline-block;
    }
    </style>
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

# --- TẦNG KHÁCH HÀNG (HIỂN THỊ PDF) ---
id_khach = st.query_params.get("id")
if id_khach:
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM leads WHERE cell = ?", (id_khach,)).fetchone()
    if row:
        t_now = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
        new_n = f"<div style='color:red;'>{t_now} 🔥 ĐANG XEM PDF</div>" + str(row['note'])
        conn.execute("UPDATE leads SET note=?, last_updated=? WHERE cell=?", (new_n, datetime.now(NY_TZ).isoformat(), id_khach))
        conn.commit()
        if row['pdf_file']:
            b64 = base64.b64encode(row['pdf_file']).decode('utf-8')
            pdf_display = f'<embed src="data:application/pdf;base64,{b64}" width="100%" height="1000" type="application/pdf">'
            st.markdown(pdf_display, unsafe_allow_html=True)
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
                st.markdown(f"""
                <div class="client-card">
                    <div style="display: flex; gap: 25px; align-items: center; border-bottom: 1px solid #f8fafc; padding-bottom: 10px;">
                        <a href="tel:{row['cell']}" class="link-direct name-link">👤 {row['name']}</a>
                        <a href="{row['crm_link']}" target="_blank" class="link-direct id-link">🆔 {row['crm_id']}</a>
                        <a href="tel:{row['work']}" class="link-direct" style="color:#64748b; font-size:14px;">🏢 Work: {row['work']}</a>
                    </div>
                    <div style="margin-top: 12px; display: flex; gap: 10px; align-items: center;">
                        <a href="rcmobile://sms?number={row['cell']}" style="text-decoration:none; font-size:20px;">💬</a>
                        <a href="mailto:{row['email']}" style="text-decoration:none; font-size:20px;">✉️</a>
                        <a href="https://calendar.google.com/calendar/r/eventedit?text=Meeting_{row['name']}" target="_blank" style="text-decoration:none; font-size:20px;">📅</a>
                        <a href="https://tmc-elite.streamlit.app/?id={row['cell']}" target="_blank" class="btn-copy">🔗 VIEW/COPY LINK PDF</a>
                    </div>
                </div>""", unsafe_allow_html=True)
                
                c_nt, c_up, c_ed = st.columns([5, 2.5, 2.5])
                with c_nt:
                    with st.form(f"nt_{row['id']}", clear_on_submit=True):
                        ni = st.text_input("Note", label_visibility="collapsed", placeholder="Nhập ghi chú...")
                        if st.form_submit_button("LƯU"):
                            t_s = datetime.now(NY_TZ).strftime('[%H:%M]'); n_n = f"<div>{t_s} {ni}</div>" + str(row['note'])
                            conn.execute("UPDATE leads SET note=? WHERE id=?", (n_n, row['id'])); conn.commit(); st.rerun()
                with c_up:
                    with st.popover("📁 PDF"):
                        # Để tiếng Anh nguyên bản để không bị chồng chữ
                        f = st.file_uploader("Upload PDF File", type="pdf", key=f"up_{row['id']}")
                        if st.button("SAVE TO DATABASE", key=f"btn_{row['id']}"):
                            if f: 
                                conn.execute("UPDATE leads SET pdf_file=? WHERE id=?", (f.read(), row['id']))
                                conn.commit(); st.success("Done!"); st.rerun()
                with c_ed:
                    with st.popover("⚙️ EDIT"):
                        with st.form(f"ed_{row['id']}"):
                            un = st.text_input("Name", row['name']); ui = st.text_input("ID", row['crm_id']); ul = st.text_input("Link", row['crm_link'])
                            uc = st.text_input("Cell", row['cell']); uw = st.text_input("Work", row['work']); ue = st.text_input("Email", row['email'])
                            us = st.text_input("State", row['state']); uo = st.text_input("Owner", row['owner']); ut = st.text_input("Tags", row['tags'])
                            if st.form_submit_button("UPDATE"):
                                conn.execute("UPDATE leads SET name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=? WHERE id=?", (un, ui, ul, uc, uw, ue, us, uo, ut, row['id'])); conn.commit(); st.rerun()
    conn.close()

elif selected == "Trang Chủ":
    st.markdown(f"<h1 style='text-align:center; color:#00263e; padding: 30px 0;'>{prof.get('slogan')}</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    def get_b64(p): return base64.b64encode(open(p, "rb").read()).decode() if p and os.path.exists(p) else ""
    with c1: st.markdown(f"<div class='home-card'><div style='height:320px;'><img src='data:image/jpeg;base64,{get_b64(prof.get('img_national'))}' style='width:100%; height:100%; object-fit:cover;'></div><div style='padding:20px;'><h3>National Life Group</h3><p>Uy tín từ 1848.</p></div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='home-card'><div style='height:320px;'><img src='data:image/jpeg;base64,{get_b64(prof.get('img_iul'))}' style='width:100%; height:100%; object-fit:cover;'></div><div style='padding:20px;'><h3>Giải pháp IUL</h3><p>{prof.get('slogan')}</p></div></div>", unsafe_allow_html=True)

elif selected == "Cấu Hình":
    with st.form("conf"):
        sl = st.text_input("Slogan", value=prof.get('slogan'))
        c1, c2, c3 = st.columns(3); ul = c1.file_uploader("Logo"); un = c2.file_uploader("Ảnh Nat"); ui = c3.file_uploader("Ảnh IUL")
        if st.form_submit_button("SAVE CONFIG"):
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
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT * FROM leads WHERE note LIKE '%ĐANG XEM%' ORDER BY last_updated DESC LIMIT 10", conn)
    for _, row in df.iterrows():
        st.error(f"🔥 {row['name']} đang xem PDF!")
    conn.close()
