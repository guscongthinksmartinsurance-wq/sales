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
n_ny = datetime.now(NY_TZ)
DB_NAME = "tmc_database.db"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f8fafc; }
    .client-card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .info-label { font-size: 11px; color: #64748b; font-weight: 700; text-transform: uppercase; margin-bottom: 2px; }
    .info-value { font-size: 13px; color: #1e293b; font-weight: 500; margin-bottom: 8px; }
    .action-link { color: #0369a1; text-decoration: none; font-weight: 700; padding: 6px 10px; border-radius: 6px; background: #f1f5f9; font-size: 11px; display: inline-block; margin-right: 4px; margin-bottom: 4px; border: 1px solid #e2e8f0; }
    .action-link:hover { background: #0ea5e9; color: white !important; }
    .history-box { background: #fdfdfd; border-radius: 8px; padding: 10px; border-left: 3px solid #cbd5e1; height: 180px; overflow-y: auto; font-size: 13px; line-height: 1.5; }
    .section-tag { background: #f1f5f9; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 800; color: #475569; margin: 10px 0 5px 0; }
    @keyframes blinker { 50% { opacity: 0; } }
    .blink { animation: blinker 1.5s linear infinite; color: #ef4444; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

def clean_phone(p):
    return str(p).replace(".0", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

def init_db():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, crm_id TEXT, crm_link TEXT, cell TEXT, work TEXT, email TEXT, state TEXT, owner TEXT, tags TEXT, status TEXT DEFAULT 'New', note TEXT DEFAULT '', last_updated TIMESTAMP, pdf_file BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY, slogan TEXT, logo_app TEXT, img_national TEXT, img_iul TEXT)''')
    conn.commit(); conn.close()

init_db()

def get_profile():
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
    res = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()
    return dict(res) if res else {'slogan': 'Sâu sắc - Tận tâm - Chuyên nghiệp'}

prof = get_profile()

# --- 2. TẦNG KHÁCH HÀNG ---
id_khach = st.query_params.get("id")
if id_khach:
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM leads WHERE cell = ?", (id_khach,)).fetchone()
    if row:
        t_str = n_ny.strftime('[%m/%d %H:%M]')
        new_n = f"<div style='color:red;'>{t_str} 🔥 KHÁCH ĐANG XEM PDF</div>" + str(row['note'])
        conn.execute("UPDATE leads SET note=?, last_updated=? WHERE cell=?", (new_n, n_ny.isoformat(), id_khach))
        conn.commit()
        st.markdown(f"<h2 style='text-align:center;'>🛡️ Hồ sơ: {row['name']}</h2>", unsafe_allow_html=True)
        if row['pdf_file']:
            b64 = base64.b64encode(row['pdf_file']).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="900" type="application/pdf"></iframe>', unsafe_allow_html=True)
        else: st.info("Hồ sơ đang được cập nhật...")
    conn.close(); st.stop()

# --- 3. QUẢN TRỊ ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
with st.sidebar:
    logo_path = prof.get('logo_app')
    if logo_path and os.path.exists(logo_path): st.image(logo_path, use_container_width=True)
    else: st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    if st.session_state.authenticated:
        from streamlit_option_menu import option_menu
        selected = option_menu(None, ["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"], styles={"nav-link-selected": {"background-color": "#00263e"}})
        if st.sidebar.button("🚪 ĐĂNG XUẤT", use_container_width=True): st.session_state.authenticated = False; st.rerun()
    else: selected = "Trang Chủ"

if selected == "Vận Hành":
    conn = sqlite3.connect(DB_NAME); df_m = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    t_list, t_add = st.tabs(["📊 DANH SÁCH CHI TIẾT", "➕ THÊM MỚI"])
    
    with t_list:
        for idx, row in df_m.iterrows():
            c_cell = clean_phone(row['cell'])
            c_work = clean_phone(row['work'])
            with st.container():
                st.markdown(f"""
                <div class="client-card">
                    <div style="display: flex; gap: 20px;">
                        <div style="flex: 2.5;">
                            <div style="font-size: 19px; font-weight: 800; color: #00263e; margin-bottom: 12px;">{row['name']}</div>
                            <div class="info-label">CRM ID & Link</div>
                            <div class="info-value">🆔 {row['crm_id']} | <a href="{row['crm_link']}" target="_blank" style="color:#0ea5e9;">Mở CRM</a></div>
                            <div class="info-label">Trạng thái & Owner</div>
                            <div class="info-value"><b>{row['status']}</b> | 👤 {row['owner']}</div>
                            <div class="info-label">Bang / Tags</div>
                            <div class="info-value">{row['state']} | {row['tags']}</div>
                        </div>
                        <div style="flex: 2.5;">
                            <div class="info-label">Liên lạc</div>
                            <div class="info-value">📞 Cell: {c_cell}</div>
                            <div class="info-value">🏢 Work: {c_work}</div>
                            <div class="info-value">✉️ Email: {row['email']}</div>
                            <div style="margin-top: 10px;">
                                <a href="tel:{c_cell}" class="action-link">📞 CALL</a>
                                <a href="rcmobile://call?number={c_cell}" class="action-link">RC CELL</a>
                                <a href="rcmobile://call?number={c_work}" class="action-link">🏢 WORK</a>
                                <a href="rcmobile://sms?number={c_cell}" class="action-link">💬 SMS</a>
                                <a href="mailto:{row['email']}" class="action-link">✉️ EMAIL</a>
                                <a href="https://calendar.google.com/calendar/r/eventedit?text=Meeting_{urllib.parse.quote(str(row['name']))}" target="_blank" class="action-link">📅 CALENDAR</a>
                                <a href="https://tmc-elite.streamlit.app/?id={row['cell']}" target="_blank" class="action-link" style="background:#10b981; color:white;">🔗 COPY LINK PDF</a>
                            </div>
                        </div>
                        <div style="flex: 3;">
                            <div class="history-box">{row['note']}</div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
                
                c_n, c_up, c_s = st.columns([5, 3, 2])
                with c_n:
                    with st.form(key=f"nt_{row['id']}", clear_on_submit=True):
                        ni = st.text_input("Ghi chú...", label_visibility="collapsed")
                        if st.form_submit_button("LƯU", use_container_width=True):
                            t_s = n_ny.strftime('[%m/%d %H:%M]'); new_n = f"<div>{t_s} {ni}</div>" + str(row['note'])
                            conn.execute("UPDATE leads SET note=?, last_updated=? WHERE id=?", (new_n, n_ny.isoformat(), row['id'])); conn.commit(); st.rerun()
                with c_up:
                    with st.popover("📁 UP PDF", use_container_width=True):
                        f_pdf = st.file_uploader("Chọn PDF", type="pdf", key=f"f_{row['id']}")
                        if st.button("XÁC NHẬN UP", key=f"b_{row['id']}"):
                            if f_pdf: conn.execute("UPDATE leads SET pdf_file=? WHERE id=?", (f_pdf.read(), row['id'])); conn.commit(); st.success("Xong!"); st.rerun()
                with c_s:
                    with st.popover("⚙️ SỬA", use_container_width=True):
                        with st.form(f"ed_{row['id']}"):
                            st.markdown("<div class='section-tag'>HỒ SƠ</div>", unsafe_allow_html=True)
                            un = st.text_input("Tên", row['name']); ui = st.text_input("CRM ID", row['crm_id']); ul = st.text_input("Link", row['crm_link'])
                            st.markdown("<div class='section-tag'>LIÊN LẠC</div>", unsafe_allow_html=True)
                            uc = st.text_input("Cell", row['cell']); uw = st.text_input("Work", row['work']); ue = st.text_input("Email", row['email'])
                            st.markdown("<div class='section-tag'>PHÂN LOẠI</div>", unsafe_allow_html=True)
                            us = st.text_input("State", row['state']); uo = st.text_input("Owner", row['owner']); utg = st.text_input("Tags", row['tags'])
                            st_l = ["New", "Contacted", "Following", "Closed"]
                            ust = st.selectbox("Status", st_l, index=st_l.index(row['status']) if row['status'] in st_l else 0)
                            if st.form_submit_button("CẬP NHẬT"):
                                conn.execute("UPDATE leads SET name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=?, status=?, last_updated=? WHERE id=?", 
                                             (un, ui, ul, uc, uw, ue, us, uo, utg, ust, n_ny.isoformat(), row['id'])); conn.commit(); st.rerun()
    with t_add:
        st.markdown("### ➕ THÊM HỒ SƠ MỚI")
        with st.form("add_f", clear_on_submit=True):
            r1 = st.columns(3); an = r1[0].text_input("Tên"); ai = r1[1].text_input("CRM ID"); al = r1[2].text_input("Link CRM")
            r2 = st.columns(3); ac = r2[0].text_input("Số Cell"); aw = r2[1].text_input("Số Work"); ae = r2[2].text_input("Email")
            r3 = st.columns(3); as_ = r3[0].text_input("State"); ao = r3[1].text_input("Owner", value="Cong"); at = r3[2].text_input("Tags")
            ast = st.selectbox("Status", ["New", "Contacted", "Following", "Closed"])
            if st.form_submit_button("LƯU HỒ SƠ", use_container_width=True):
                conn.execute("INSERT INTO leads (name, crm_id, crm_link, cell, work, email, state, owner, tags, status, last_updated) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                             (an, ai, al, ac, aw, ae, as_, ao, at, ast, n_ny.isoformat())); conn.commit(); st.success("Xong!"); st.rerun()
    conn.close()

elif selected == "Mắt Thần":
    st.markdown("## 👁️ Mắt Thần Real-time")
    conn = sqlite3.connect(DB_NAME); df_eye = pd.read_sql("SELECT * FROM leads WHERE note LIKE '%ĐỌC HỒ SƠ PDF%' ORDER BY last_updated DESC", conn)
    for _, row in df_eye.iterrows():
        with st.container(border=True):
            st.markdown(f"Khách **{row['name']}** <span class='blink'>🔥 ĐANG XEM PDF</span>", unsafe_allow_html=True)
            st.write(f"ID: {row['crm_id']} | Owner: {row['owner']} | Cell: {row['cell']}")
            st.markdown(f"<div style='font-size:13px;'>{row['note']}</div>", unsafe_allow_html=True)
    conn.close()

elif selected == "Trang Chủ":
    st.markdown(f"<h2 style='text-align:center;'>{prof.get('slogan')}</h2>", unsafe_allow_html=True)
    c1, c2 = st.columns(2); c1.markdown("<div class='home-card'><h3>National Life</h3></div>", unsafe_allow_html=True)
    if prof.get('img_national'): c1.image(prof['img_national'])
    c2.markdown("<div class='home-card'><h3>Giải pháp IUL</h3></div>", unsafe_allow_html=True)
    if prof.get('img_iul'): c2.image(prof['img_iul'])
    if not st.session_state.authenticated:
        with st.expander("🔐 QUẢN TRỊ"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.button("OK"):
                if u == "Cong" and p == "admin123": st.session_state.authenticated = True; st.rerun()

elif selected == "Cấu Hình":
    with st.form("config"):
        new_sl = st.text_input("Slogan", value=prof.get('slogan'))
        c1, c2, c3 = st.columns(3); up_l = c1.file_uploader("Logo"); up_n = c2.file_uploader("Ảnh Nat"); up_i = c3.file_uploader("Ảnh IUL")
        if st.form_submit_button("LƯU"):
            conn = sqlite3.connect(DB_NAME)
            if up_l:
                with open("logo_app.png", "wb") as f: f.write(up_l.getbuffer())
                conn.execute("UPDATE profile SET logo_app='logo_app.png'")
            if up_n:
                with open("img_nat.jpg", "wb") as f: f.write(up_n.getbuffer())
                conn.execute("UPDATE profile SET img_national='img_nat.jpg'")
            if up_i:
                with open("img_iul.jpg", "wb") as f: f.write(up_i.getbuffer())
                conn.execute("UPDATE profile SET img_iul='img_iul.jpg'")
            conn.execute("UPDATE profile SET slogan=? WHERE id=1", (new_sl,)); conn.commit(); conn.close(); st.rerun()
