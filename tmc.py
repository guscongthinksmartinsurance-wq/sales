import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import base64

# --- 1. CẤU HÌNH & CSS (TỐI GIẢN) ---
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
        background: white; padding: 20px; border-radius: 12px;
        border: 1px solid #e2e8f0; margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    .link-direct { text-decoration: none !important; font-weight: 700; transition: 0.2s; }
    .name-link { font-size: 19px; color: #00263e !important; }
    .id-link { color: #0ea5e9 !important; font-size: 15px; }
    
    /* Nút hành động icon */
    .btn-icon { font-size: 22px; text-decoration: none !important; margin-right: 15px; }
    
    /* Fix lỗi chồng chữ: Không dùng Popover cho Uploader */
    .stExpander { border: none !important; background: #f8fafc !important; border-radius: 8px !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HÀM DATABASE ---
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

@st.cache_data(ttl=300)
def get_prof():
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
    res = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()
    return dict(res) if res else {'slogan': 'Sâu sắc - Tận tâm - Chuyên nghiệp'}

prof = get_prof()

# --- 3. TẦNG KHÁCH HÀNG (XỬ LÝ PDF) ---
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
            # Cách mở PDF an toàn nhất trên Cloud: Download/View button
            st.markdown(f"### 🛡️ Xin chào {row['name']}")
            st.download_button(label="📂 BẤM VÀO ĐÂY ĐỂ MỞ FILE MINH HỌA (PDF)", data=row['pdf_file'], file_name=f"IUL_{row['name']}.pdf", mime="application/pdf")
        else: st.warning("Hồ sơ của bạn đang được xử lý...")
    conn.close(); st.stop()

# --- 4. QUẢN TRỊ ---
if 'auth' not in st.session_state: st.session_state.auth = False
with st.sidebar:
    st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    if st.session_state.auth:
        from streamlit_option_menu import option_menu
        selected = option_menu(None, ["Trang Chủ", "Vận Hành", "Mắt Thần", "Cấu Hình"], icons=['house', 'gear', 'command', 'wrench'])
        if st.button("🚪 Đăng xuất"): st.session_state.auth = False; st.rerun()
    else: selected = "Trang Chủ"

if selected == "Vận Hành":
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    tab1, tab2 = st.tabs(["📊 DANH SÁCH", "➕ THÊM MỚI (10 TRƯỜNG)"])
    
    with tab1:
        for idx, row in df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="client-card">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex: 7;">
                            <a href="tel:{row['cell']}" class="link-direct name-link">👤 {row['name']}</a>
                            <div style="margin-top:5px;">
                                <a href="{row['crm_link']}" target="_blank" class="link-direct id-link">🆔 {row['crm_id']}</a> | 
                                <a href="tel:{row['work']}" style="color:#64748b; text-decoration:none; font-size:14px;">🏢 Work: {row['work']}</a>
                            </div>
                            <div style="color:#94a3b8; font-size:13px; margin-top:5px;">
                                ✉️ {row['email']} | 📍 {row['state']} | 👤 {row['owner']} | 🏷️ {row['tags']} | 🚩 <b>{row['status']}</b>
                            </div>
                        </div>
                        <div style="flex: 3; text-align: right;">
                            <a href="rcmobile://sms?number={row['cell']}" class="btn-icon">💬</a>
                            <a href="mailto:{row['email']}" class="btn-icon">✉️</a>
                            <a href="https://calendar.google.com/calendar/r/eventedit?text=Meeting_{row['name']}" target="_blank" class="btn-icon">📅</a>
                            <br><br>
                            <a href="https://tmc-elite.streamlit.app/?id={row['cell']}" target="_blank" 
                               style="background:#10b981; color:white; padding:5px 10px; border-radius:6px; font-size:12px; font-weight:700; text-decoration:none;">
                               🔗 COPY LINK PDF
                            </a>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
                
                # Phần xử lý (Ghi chú, Upfile, Sửa) dùng Expander để không bị chồng chữ
                c_nt, c_up, c_ed = st.columns([4, 3, 3])
                with c_nt:
                    with st.expander("📝 Ghi chú"):
                        with st.form(f"n_{row['id']}", clear_on_submit=True):
                            ni = st.text_input("Nội dung", label_visibility="collapsed")
                            if st.form_submit_button("LƯU"):
                                n_n = f"<div>{datetime.now(NY_TZ).strftime('%H:%M')} {ni}</div>" + str(row['note'])
                                conn.execute("UPDATE leads SET note=? WHERE id=?", (n_n, row['id'])); conn.commit(); st.rerun()
                with c_up:
                    with st.expander("📁 PDF"):
                        f = st.file_uploader("Upload", type="pdf", key=f"f_{row['id']}")
                        if st.button("XÁC NHẬN", key=f"b_{row['id']}"):
                            if f: conn.execute("UPDATE leads SET pdf_file=? WHERE id=?", (f.read(), row['id'])); conn.commit(); st.success("Xong!"); st.rerun()
                with c_ed:
                    with st.expander("⚙️ SỬA"):
                        with st.form(f"e_{row['id']}"):
                            un = st.text_input("Tên", row['name']); ui = st.text_input("ID", row['crm_id']); ul = st.text_input("Link", row['crm_link'])
                            uc = st.text_input("Cell", row['cell']); uw = st.text_input("Work", row['work']); ue = st.text_input("Email", row['email'])
                            us = st.text_input("State", row['state']); uo = st.text_input("Owner", row['owner']); ut = st.text_input("Tags", row['tags'])
                            if st.form_submit_button("CẬP NHẬT"):
                                conn.execute("UPDATE leads SET name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=? WHERE id=?", (un, ui, ul, uc, uw, ue, us, uo, ut, row['id'])); conn.commit(); st.rerun()
                st.markdown("---")

    with tab2:
        with st.form("add_new"):
            st.markdown("### ➕ THÊM HỒ SƠ (ĐỦ 10 TRƯỜNG)")
            c1, c2, c3 = st.columns(3)
            an = c1.text_input("Tên"); ai = c2.text_input("CRM ID"); al = c3.text_input("Link CRM")
            ac = c1.text_input("Cell"); aw = c2.text_input("Work"); ae = c3.text_input("Email")
            as_ = c1.text_input("State"); ao = c2.text_input("Owner", value="Cong"); at = c3.text_input("Tags")
            if st.form_submit_button("LƯU HỒ SƠ"):
                conn.execute("INSERT INTO leads (name, crm_id, crm_link, cell, work, email, state, owner, tags, last_updated) VALUES (?,?,?,?,?,?,?,?,?,?)", (an, ai, al, ac, aw, ae, as_, ao, at, datetime.now(NY_TZ).isoformat()))
                conn.commit(); st.success("Đã thêm!"); st.rerun()
    conn.close()

elif selected == "Trang Chủ":
    st.markdown(f"<h1 style='text-align:center;'>{prof.get('slogan')}</h1>", unsafe_allow_html=True)
    # (Phần 2 Card trang chủ giữ nguyên bố cục Elite)
    if not st.session_state.auth:
        with st.expander("🔐 LOGIN"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.button("OK"):
                if u == "Cong" and p == "admin123": st.session_state.auth = True; st.rerun()
