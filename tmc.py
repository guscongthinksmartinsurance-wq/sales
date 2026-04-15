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
    
    /* Card danh sách siêu phẳng */
    .client-card {
        background: white; padding: 15px 25px; border-radius: 12px;
        border: 1px solid #e2e8f0; margin-bottom: 8px;
        display: flex; align-items: center; justify-content: space-between;
    }
    .client-info { display: flex; gap: 30px; align-items: center; flex: 7; }
    .name-link { font-size: 18px; font-weight: 800; color: #00263e !important; text-decoration: none; }
    .id-link { color: #0ea5e9 !important; font-weight: 700; text-decoration: none; font-size: 15px; }
    .meta-text { color: #64748b; font-size: 13px; font-weight: 500; }
    
    /* Nhóm Icon hành động */
    .action-group { display: flex; gap: 15px; align-items: center; flex: 3; justify-content: flex-end; }
    .icon-btn { font-size: 20px; text-decoration: none !important; }

    /* Fix uploader Streamlit */
    [data-testid="stFileUploader"] { padding: 0 !important; }
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
            st.download_button("📂 XEM HỒ SƠ PDF", data=row['pdf_file'], file_name=f"{row['name']}_IUL.pdf", mime="application/pdf", use_container_width=True)
    conn.close(); st.stop()

# --- SIDEBAR ---
if 'auth' not in st.session_state: st.session_state.auth = False
with st.sidebar:
    st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    if st.session_state.auth:
        selected = st.radio("MENU", ["Trang Chủ", "Vận Hành", "Mắt Thần", "Cấu Hình"])
        if st.button("🚪 Đăng xuất"): st.session_state.auth = False; st.rerun()
    else: selected = "Trang Chủ"

# --- 4. VẬN HÀNH (BẢN TINH GỌN TUYỆT ĐỐI) ---
if selected == "Vận Hành":
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    t1, t2 = st.tabs(["📊 DANH SÁCH", "➕ THÊM MỚI"])
    
    with t1:
        for idx, row in df.iterrows():
            with st.container():
                # Card 1 hàng duy nhất
                st.markdown(f"""
                <div class="client-card">
                    <div class="client-info">
                        <a href="tel:{row['cell']}" class="name-link">👤 {row['name']}</a>
                        <a href="{row['crm_link']}" target="_blank" class="id-link">🆔 {row['crm_id']}</a>
                        <a href="tel:{row['work']}" class="meta-text" style="text-decoration:none;">🏢 {row['work']}</a>
                        <div class="meta-text">📍 {row['state']} | 👤 {row['owner']} | 🏷️ {row['status']}</div>
                    </div>
                    <div class="action-group">
                        <a href="rcmobile://sms?number={row['cell']}" class="icon-btn">💬</a>
                        <a href="mailto:{row['email']}" class="icon-btn">✉️</a>
                        <a href="https://calendar.google.com/calendar/r/eventedit?text=Meeting_{row['name']}" target="_blank" class="icon-btn">📅</a>
                    </div>
                </div>""", unsafe_allow_html=True)
                
                # CÁC NÚT HỆ THỐNG GỌN GÀNG TRONG POPOVER (FIX CHỒNG CHỮ)
                c_link, c_nt, c_up, c_ed = st.columns([3, 2, 2, 2])
                with c_link:
                    st.code(f"https://tmc-elite.streamlit.app/?id={row['cell']}")
                with c_nt:
                    with st.popover("📝 NOTE"):
                        with st.form(f"nt_{row['id']}", clear_on_submit=True):
                            txt = st.text_input("Ghi chú nhanh")
                            if st.form_submit_button("LƯU"):
                                n_n = f"<div>{datetime.now(NY_TZ).strftime('%H:%M')} {txt}</div>" + str(row['note'])
                                conn.execute("UPDATE leads SET note=? WHERE id=?", (n_n, row['id'])); conn.commit(); st.rerun()
                with c_up:
                    with st.popover("📁 PDF"):
                        f = st.file_uploader("Upload", type="pdf", key=f"f_{row['id']}")
                        if st.button("SAVE", key=f"b_{row['id']}"):
                            if f: conn.execute("UPDATE leads SET pdf_file=? WHERE id=?", (f.read(), row['id'])); conn.commit(); st.success("Xong!"); st.rerun()
                with c_ed:
                    with st.popover("⚙️ EDIT"):
                        with st.form(f"e_{row['id']}"):
                            un = st.text_input("Tên", row['name']); ui = st.text_input("ID", row['crm_id']); ul = st.text_input("Link", row['crm_link'])
                            uc = st.text_input("Cell", row['cell']); uw = st.text_input("Work", row['work']); ue = st.text_input("Email", row['email'])
                            us = st.text_input("State", row['state']); uo = st.text_input("Owner", row['owner']); ut = st.text_input("Tags", row['tags'])
                            if st.form_submit_button("CẬP NHẬT"):
                                conn.execute("UPDATE leads SET name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=? WHERE id=?", (un, ui, ul, uc, uw, ue, us, uo, ut, row['id'])); conn.commit(); st.rerun()
    conn.close()

# --- TRANG CHỦ & CẤU HÌNH PHỤC HỒI ĐẦY ĐỦ ---
elif selected == "Trang Chủ":
    st.markdown(f"<h1 style='text-align:center; color:#00263e;'>{prof.get('slogan')}</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    def get_img(p): 
        if p and os.path.exists(p):
            with open(p, "rb") as f: return base64.b64encode(f.read()).decode()
        return ""
    with c1:
        st.markdown(f"<div style='background:white; padding:15px; border-radius:15px; border:1px solid #e2e8f0; text-align:center;'><h3>National Life Group</h3><img src='data:image/jpeg;base64,{get_img(prof.get('img_national'))}' style='width:100%; border-radius:10px; height:300px; object-fit:cover;'><p style='margin-top:10px; color:#64748b;'>Uy tín từ 1848.</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='background:white; padding:15px; border-radius:15px; border:1px solid #e2e8f0; text-align:center;'><h3>Giải pháp IUL</h3><img src='data:image/jpeg;base64,{get_img(prof.get('img_iul'))}' style='width:100%; border-radius:10px; height:300px; object-fit:cover;'><p style='margin-top:10px; color:#64748b;'>{prof.get('slogan')}</p></div>", unsafe_allow_html=True)
    if not st.session_state.auth:
        with st.expander("🔐 Đăng nhập"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.button("OK"):
                if u == "Cong" and p == "admin123": st.session_state.auth = True; st.rerun()

elif selected == "Cấu Hình":
    with st.form("conf"):
        sl = st.text_input("Slogan", value=prof.get('slogan'))
        c1, c2, c3 = st.columns(3); ul = c1.file_uploader("Logo"); un = c2.file_uploader("Ảnh Nat"); ui = c3.file_uploader("Ảnh IUL")
        if st.form_submit_button("LƯU"):
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
