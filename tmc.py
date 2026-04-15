import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import urllib.parse
import base64

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

# CSS Tối giản - Chỉ tập trung vào bố cục Card, không can thiệp nút hệ thống để tránh lỗi
st.markdown("""
    <style>
    .stApp { background-color: #f1f5f9; }
    .client-card {
        background: white; padding: 20px; border-radius: 12px;
        border: 1px solid #e2e8f0; margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .name-link { font-size: 20px; font-weight: 800; color: #00263e !important; text-decoration: none; }
    .id-link { color: #0ea5e9 !important; font-weight: 700; text-decoration: none; }
    .meta-info { color: #64748b; font-size: 14px; margin-top: 5px; }
    .btn-row { display: flex; gap: 15px; margin-top: 15px; align-items: center; }
    /* Card trang chủ */
    .home-card { background: white; padding: 20px; border-radius: 15px; text-align: center; border: 1px solid #e2e8f0; }
    </style>
""", unsafe_allow_html=True)

# --- 2. XỬ LÝ DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, crm_id TEXT, crm_link TEXT, 
        cell TEXT, work TEXT, email TEXT, state TEXT, owner TEXT, tags TEXT, 
        status TEXT DEFAULT 'New', note TEXT DEFAULT '', last_updated TIMESTAMP, pdf_file BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY, slogan TEXT, logo_app TEXT, img_national TEXT, img_iul TEXT)''')
    c.execute("INSERT OR IGNORE INTO profile (id, slogan) VALUES (1, 'Sâu sắc - Tận tâm - Chuyên nghiệp')")
    conn.commit(); conn.close()

init_db()

def get_prof():
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
    res = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()
    return dict(res) if res else {'slogan': 'Sâu sắc - Tận tâm - Chuyên nghiệp'}

prof = get_prof()

# --- 3. TẦNG KHÁCH HÀNG (MỞ PDF TRỰC TIẾP) ---
id_khach = st.query_params.get("id")
if id_khach:
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM leads WHERE cell = ?", (id_khach,)).fetchone()
    if row:
        t_now = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
        new_n = f"<div>{t_now} 🔥 KHÁCH ĐANG XEM PDF</div>" + str(row['note'])
        conn.execute("UPDATE leads SET note=?, last_updated=? WHERE cell=?", (new_n, datetime.now(NY_TZ).isoformat(), id_khach))
        conn.commit()
        if row['pdf_file']:
            # Dùng nút Download/Open để đảm bảo không bị chặn trên Cloud
            st.markdown(f"## 🛡️ Xin chào {row['name']}")
            st.download_button("📂 MỞ HỒ SƠ MINH HỌA PDF", data=row['pdf_file'], file_name=f"{row['name']}_IUL.pdf", mime="application/pdf")
    conn.close(); st.stop()

# --- 4. QUẢN TRỊ ---
if 'auth' not in st.session_state: st.session_state.auth = False

with st.sidebar:
    st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    if st.session_state.auth:
        selected = st.radio("MENU", ["Trang Chủ", "Vận Hành", "Mắt Thần", "Cấu Hình"])
        if st.button("🚪 Đăng xuất"): st.session_state.auth = False; st.rerun()
    else: selected = "Trang Chủ"

# --- PHÂN HỆ VẬN HÀNH ---
if selected == "Vận Hành":
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    tab1, tab2 = st.tabs(["📊 DANH SÁCH", "➕ THÊM MỚI"])
    
    with tab1:
        for idx, row in df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="client-card">
                    <a href="tel:{row['cell']}" class="name-link">👤 {row['name']}</a> <br>
                    <div class="meta-info">
                        Mã ID: <a href="{row['crm_link']}" target="_blank" class="id-link">{row['crm_id']}</a> | 
                        Cell: <b>{row['cell']}</b> | 
                        Work: <a href="tel:{row['work']}" style="color:#64748b; text-decoration:none;"><b>{row['work']}</b></a>
                    </div>
                    <div class="meta-info">
                        Email: {row['email']} | Bang: {row['state']} | Phụ trách: {row['owner']} | Tags: {row['tags']} | Status: <b>{row['status']}</b>
                    </div>
                    <div class="btn-row">
                        <a href="rcmobile://sms?number={row['cell']}" style="text-decoration:none; font-size:22px;">💬</a>
                        <a href="mailto:{row['email']}" style="text-decoration:none; font-size:22px;">✉️</a>
                        <a href="https://calendar.google.com/calendar/r/eventedit?text=Meeting_{row['name']}" target="_blank" style="text-decoration:none; font-size:22px;">📅</a>
                        <span style="background:#10b981; color:white; padding:4px 10px; border-radius:6px; font-size:12px; font-weight:700;">
                            Copy Link bên dưới gửi khách
                        </span>
                    </div>
                </div>""", unsafe_allow_html=True)
                st.code(f"https://tmc-elite.streamlit.app/?id={row['cell']}")
                
                # Chức năng ghi chú và sửa hồ sơ
                col_nt, col_up, col_ed = st.columns([5, 2.5, 2.5])
                with col_nt:
                    with st.expander("📝 Ghi chú"):
                        with st.form(f"nt_{row['id']}", clear_on_submit=True):
                            txt = st.text_input("Nội dung ghi chú")
                            if st.form_submit_button("LƯU"):
                                n_n = f"<div>{datetime.now(NY_TZ).strftime('%H:%M')} {txt}</div>" + str(row['note'])
                                conn.execute("UPDATE leads SET note=? WHERE id=?", (n_n, row['id'])); conn.commit(); st.rerun()
                with col_up:
                    with st.expander("📁 PDF"):
                        f = st.file_uploader("Upload PDF", type="pdf", key=f"f_{row['id']}")
                        if st.button("XÁC NHẬN", key=f"b_{row['id']}"):
                            if f: conn.execute("UPDATE leads SET pdf_file=? WHERE id=?", (f.read(), row['id'])); conn.commit(); st.rerun()
                with col_ed:
                    with st.expander("⚙️ SỬA"):
                        with st.form(f"e_{row['id']}"):
                            un = st.text_input("Tên", row['name']); ui = st.text_input("ID", row['crm_id']); ul = st.text_input("Link", row['crm_link'])
                            uc = st.text_input("Cell", row['cell']); uw = st.text_input("Work", row['work']); ue = st.text_input("Email", row['email'])
                            us = st.text_input("State", row['state']); uo = st.text_input("Owner", row['owner']); ut = st.text_input("Tags", row['tags'])
                            if st.form_submit_button("CẬP NHẬT"):
                                conn.execute("UPDATE leads SET name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=? WHERE id=?", (un, ui, ul, uc, uw, ue, us, uo, ut, row['id'])); conn.commit(); st.rerun()

    with tab2:
        with st.form("add_new"):
            st.markdown("### ➕ THÊM MỚI (ĐỦ 10 TRƯỜNG)")
            c1, c2, c3 = st.columns(3)
            an = c1.text_input("Tên"); ai = c2.text_input("CRM ID"); al = c3.text_input("Link CRM")
            ac = c1.text_input("Cell"); aw = c2.text_input("Work"); ae = c3.text_input("Email")
            as_ = c1.text_input("State"); ao = c2.text_input("Owner", value="Cong"); at = c3.text_input("Tags")
            if st.form_submit_button("LƯU HỒ SƠ"):
                conn.execute("INSERT INTO leads (name, crm_id, crm_link, cell, work, email, state, owner, tags, last_updated) VALUES (?,?,?,?,?,?,?,?,?,?)", (an, ai, al, ac, aw, ae, as_, ao, at, datetime.now(NY_TZ).isoformat()))
                conn.commit(); st.success("Đã thêm thành công!"); st.rerun()
    conn.close()

elif selected == "Trang Chủ":
    st.markdown(f"<h1 style='text-align:center;'>{prof.get('slogan')}</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: st.markdown("<div class='home-card'><h3>National Life Group</h3><p>Uy tín từ 1848.</p></div>", unsafe_allow_html=True)
    with c2: st.markdown("<div class='home-card'><h3>Giải pháp IUL</h3><p>Bảo vệ tài chính bền vững.</p></div>", unsafe_allow_html=True)
    if not st.session_state.auth:
        with st.expander("🔐 Đăng nhập"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.button("OK"):
                if u == "Cong" and p == "admin123": st.session_state.auth = True; st.rerun()

elif selected == "Mắt Thần":
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT * FROM leads WHERE note LIKE '%ĐANG XEM%' ORDER BY last_updated DESC LIMIT 10", conn)
    for _, row in df.iterrows():
        st.error(f"🔥 {row['name']} đang xem hồ sơ! | {row['note']}")
    conn.close()
