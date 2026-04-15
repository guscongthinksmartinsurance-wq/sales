import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import base64

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

# CSS Elite: Tập trung vào Card và độ thoáng, không can thiệp sâu vào nút hệ thống
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f1f5f9; }
    
    /* Card Trang Chủ */
    .home-card {
        background: white; padding: 0; border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        text-align: center; margin-bottom: 30px; overflow: hidden;
        border: 1px solid #e2e8f0; height: 580px;
    }
    .home-img { height: 350px; width: 100%; object-fit: cover; border-bottom: 1px solid #f1f5f9; }
    .home-content { padding: 25px; }
    .home-content h3 { color: #00263e; font-size: 22px; margin-bottom: 15px; font-weight: 800; }
    .home-content p { color: #64748b; font-size: 14px; line-height: 1.6; }

    /* Card Vận Hành */
    .client-card {
        background: white; padding: 25px; border-radius: 15px;
        border: 1px solid #e2e8f0; margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .name-link { font-size: 22px; font-weight: 800; color: #00263e !important; text-decoration: none; }
    .id-link { color: #0ea5e9 !important; font-weight: 700; text-decoration: none; font-size: 16px; }
    .meta-tag { font-size: 13px; color: #94a3b8; font-weight: 600; text-transform: uppercase; }
    .meta-value { font-size: 14px; color: #1e293b; font-weight: 500; margin-bottom: 10px; }
    
    /* Nút Icon */
    .btn-icon { font-size: 24px; text-decoration: none !important; margin-right: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DATABASE ---
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
def get_prof_data():
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
    res = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()
    return dict(res) if res else {'slogan': 'Sâu sắc - Tận tâm - Chuyên nghiệp'}

def to_b64(p):
    if p and os.path.exists(p):
        with open(p, "rb") as f: return base64.b64encode(f.read()).decode()
    return ""

prof = get_prof_data()

# --- 3. TẦNG KHÁCH HÀNG ---
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
            st.markdown(f"<h2 style='text-align:center;'>Xin chào {row['name']}</h2>", unsafe_allow_html=True)
            st.download_button("📂 MỞ HỒ SƠ MINH HỌA (PDF)", data=row['pdf_file'], file_name=f"{row['name']}_IUL.pdf", mime="application/pdf", use_container_width=True)
    conn.close(); st.stop()

# --- 4. SIDEBAR ---
if 'auth' not in st.session_state: st.session_state.auth = False
with st.sidebar:
    logo = prof.get('logo_app')
    if logo and os.path.exists(logo): st.image(logo, use_container_width=True)
    else: st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    if st.session_state.auth:
        from streamlit_option_menu import option_menu
        selected = option_menu(None, ["Trang Chủ", "Vận Hành", "Mắt Thần", "Cấu Hình"], icons=['house', 'command', 'eye', 'gear'])
        if st.button("🚪 Đăng xuất"): st.session_state.auth = False; st.rerun()
    else: selected = "Trang Chủ"

# --- TRANG CHỦ ---
if selected == "Trang Chủ":
    st.markdown(f"<h1 style='text-align:center; color:#00263e; padding:30px 0;'>{prof.get('slogan')}</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        img_n = to_b64(prof.get('img_national'))
        st.markdown(f"""<div class="home-card">
            <img src="data:image/jpeg;base64,{img_n}" class="home-img" onerror="this.src='https://via.placeholder.com/600x400'">
            <div class="home-content">
                <h3>National Life Group</h3>
                <p>Đồng hành cùng các gia đình Mỹ từ năm 1848. Chúng tôi cung cấp các giải pháp bảo vệ tài chính và hưu trí với sự cam kết về giá trị bền vững và niềm tin tuyệt đối.</p>
            </div>
        </div>""", unsafe_allow_html=True)
    with c2:
        img_i = to_b64(prof.get('img_iul'))
        st.markdown(f"""<div class="home-card">
            <img src="data:image/jpeg;base64,{img_i}" class="home-img" onerror="this.src='https://via.placeholder.com/600x400'">
            <div class="home-content">
                <h3>Giải pháp IUL Elite</h3>
                <p>{prof.get('slogan')}. Giải pháp linh hoạt giúp tích lũy tài sản, bảo vệ thu nhập và chuẩn bị cho một tương lai tài chính thịnh vượng.</p>
            </div>
        </div>""", unsafe_allow_html=True)
    if not st.session_state.auth:
        with st.expander("🔐 QUẢN TRỊ"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.button("ĐĂNG NHẬP"):
                if u == "Cong" and p == "admin123": st.session_state.auth = True; st.rerun()

# --- VẬN HÀNH ---
elif selected == "Vận Hành":
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    t1, t2 = st.tabs(["📊 DANH SÁCH", "➕ THÊM MỚI"])
    with t1:
        for idx, row in df.iterrows():
            with st.container():
                st.markdown(f"""<div class="client-card">
                    <div style="display: flex; justify-content: space-between;">
                        <div style="flex: 7;">
                            <a href="tel:{row['cell']}" class="name-link">👤 {row['name']}</a> <br>
                            <div style="margin-top:8px;">
                                <a href="{row['crm_link']}" target="_blank" class="id-link">🆔 Mã CRM: {row['crm_id']}</a> | 
                                <a href="tel:{row['work']}" style="color:#64748b; text-decoration:none; font-weight:600;">🏢 Work: {row['work']}</a>
                            </div>
                            <div style="color:#94a3b8; font-size:13px; margin-top:8px;">
                                ✉️ {row['email']} | 📍 {row['state']} | 👤 {row['owner']} | 🏷️ {row['tags']} | 🚩 <b>{row['status']}</b>
                            </div>
                        </div>
                        <div style="flex: 3; text-align: right;">
                            <a href="rcmobile://sms?number={row['cell']}" class="btn-icon">💬</a>
                            <a href="mailto:{row['email']}" class="btn-icon">✉️</a>
                            <a href="https://calendar.google.com/calendar/r/eventedit?text=Meeting_{row['name']}" target="_blank" class="btn-icon">📅</a>
                            <div style="margin-top:15px;"><code style="color:#10b981;">{row['cell']}</code></div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
                
                c_nt, c_up, c_ed = st.columns([5, 2.5, 2.5])
                with c_nt:
                    with st.expander("📝 Ghi chú"):
                        with st.form(f"nt_{row['id']}", clear_on_submit=True):
                            ni = st.text_input("Nội dung", label_visibility="collapsed")
                            if st.form_submit_button("LƯU"):
                                n_n = f"<div>{datetime.now(NY_TZ).strftime('%H:%M')} {ni}</div>" + str(row['note'])
                                conn.execute("UPDATE leads SET note=? WHERE id=?", (n_n, row['id'])); conn.commit(); st.rerun()
                with c_up:
                    with st.expander("📁 PDF"):
                        f = st.file_uploader("Upload", type="pdf", key=f"f_{row['id']}")
                        if st.button("LƯU PDF", key=f"b_{row['id']}"):
                            if f: conn.execute("UPDATE leads SET pdf_file=? WHERE id=?", (f.read(), row['id'])); conn.commit(); st.success("Xong!"); st.rerun()
                with c_ed:
                    with st.expander("⚙️ SỬA"):
                        with st.form(f"e_{row['id']}"):
                            st.write("Cập nhật 10 trường")
                            un = st.text_input("Tên", row['name']); ui = st.text_input("ID", row['crm_id']); ul = st.text_input("Link", row['crm_link'])
                            uc = st.text_input("Cell", row['cell']); uw = st.text_input("Work", row['work']); ue = st.text_input("Email", row['email'])
                            us = st.text_input("State", row['state']); uo = st.text_input("Owner", row['owner']); ut = st.text_input("Tags", row['tags']); ust = st.selectbox("Status", ["New", "Contacted", "Following", "Closed"])
                            if st.form_submit_button("CẬP NHẬT"):
                                conn.execute("UPDATE leads SET name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=?, status=? WHERE id=?", (un, ui, ul, uc, uw, ue, us, uo, ut, ust, row['id'])); conn.commit(); st.rerun()

    with t2:
        with st.form("add_full"):
            st.markdown("### ➕ THIẾT LẬP HỒ SƠ (10 TRƯỜNG)")
            c1, c2, c3 = st.columns(3)
            an = c1.text_input("Tên"); ai = c2.text_input("CRM ID"); al = c3.text_input("Link CRM")
            ac = c1.text_input("Cell"); aw = c2.text_input("Work"); ae = c3.text_input("Email")
            as_ = c1.text_input("State"); ao = c2.text_input("Owner", value="Cong"); at = c3.text_input("Tags")
            ast = st.selectbox("Trạng thái", ["New", "Contacted", "Following", "Closed"])
            if st.form_submit_button("LƯU HỒ SƠ"):
                conn.execute("INSERT INTO leads (name, crm_id, crm_link, cell, work, email, state, owner, tags, status, last_updated) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (an, ai, al, ac, aw, ae, as_, ao, at, ast, datetime.now(NY_TZ).isoformat()))
                conn.commit(); st.success("Đã thêm!"); st.rerun()
    conn.close()

# --- MẮT THẦN ---
elif selected == "Mắt Thần":
    st.markdown("## 👁️ Mắt Thần Soi PDF")
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT * FROM leads WHERE note LIKE '%ĐANG XEM%' ORDER BY last_updated DESC LIMIT 15", conn)
    for _, row in df.iterrows():
        st.error(f"🔥 Khách {row['name']} đang xem PDF! | {row['note']}")
    conn.close()

# --- CẤU HÌNH ---
elif selected == "Cấu Hình":
    st.markdown("## ⚙️ Cấu Hình Giao Diện")
    with st.form("conf"):
        sl = st.text_input("Slogan dòng IUL", value=prof.get('slogan'))
        c1, c2, c3 = st.columns(3); ul = c1.file_uploader("Logo Sidebar"); un = c2.file_uploader("Ảnh National"); ui = c3.file_uploader("Ảnh IUL")
        if st.form_submit_button("LƯU CẤU HÌNH"):
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
