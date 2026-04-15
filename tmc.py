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
n_ny = datetime.now(NY_TZ)
DB_NAME = "tmc_database.db"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f1f5f9; }
    
    /* Trang chủ Card */
    .home-card {
        background: white; padding: 25px; border-radius: 16px;
        border-top: 5px solid #00263e; box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        text-align: center; margin-bottom: 20px; transition: 0.3s;
    }
    .home-card:hover { transform: translateY(-5px); }
    
    /* Vận hành Card */
    .client-card {
        background: white; padding: 20px; border-radius: 12px;
        border: 1px solid #e2e8f0; margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    .info-label { font-size: 11px; color: #64748b; font-weight: 700; text-transform: uppercase; margin-top: 5px; }
    .info-value { font-size: 13px; color: #1e293b; font-weight: 500; margin-bottom: 5px; }
    
    /* Nút hành động */
    .action-link {
        color: #0369a1; text-decoration: none; font-weight: 700;
        padding: 6px 10px; border-radius: 6px; background: #f1f5f9;
        font-size: 11px; display: inline-block; margin-right: 4px; margin-bottom: 4px;
    }
    .action-link:hover { background: #00263e; color: white !important; }

    /* Mắt thần nhấp nháy */
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
    .eye-active { animation: pulse 2s infinite; color: #ef4444; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

def init_db():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, crm_id TEXT, crm_link TEXT, cell TEXT, work TEXT, email TEXT, state TEXT, owner TEXT, tags TEXT, status TEXT DEFAULT 'New', note TEXT DEFAULT '', last_updated TIMESTAMP, pdf_file BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY, slogan TEXT, logo_app TEXT, img_national TEXT, img_iul TEXT)''')
    conn.commit(); conn.close()

init_db()

@st.cache_data(ttl=600)
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
        t_now = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
        new_n = f"<div style='color:#ef4444;'>{t_now} 🔥 KHÁCH ĐANG XEM PDF</div>" + str(row['note'])
        conn.execute("UPDATE leads SET note=?, last_updated=? WHERE cell=?", (new_n, datetime.now(NY_TZ).isoformat(), id_khach))
        conn.commit()
        st.markdown(f"<h2 style='text-align:center;'>🛡️ Hồ sơ bảo hiểm: {row['name']}</h2>", unsafe_allow_html=True)
        if row['pdf_file']:
            b64 = base64.b64encode(row['pdf_file']).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="900"></iframe>', unsafe_allow_html=True)
        else: st.info("Hồ sơ đang được chuẩn bị...")
    conn.close(); st.stop()

# --- 3. QUẢN TRỊ ---
if 'auth' not in st.session_state: st.session_state.auth = False

with st.sidebar:
    logo_p = prof.get('logo_app')
    if logo_p and os.path.exists(logo_p): st.image(logo_p, use_container_width=True)
    else: st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    
    if st.session_state.auth:
        from streamlit_option_menu import option_menu
        selected = option_menu(None, ["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"], 
            icons=['house', 'eye', 'command', 'gear'], 
            styles={"nav-link-selected": {"background-color": "#00263e"}})
        if st.sidebar.button("🚪 ĐĂNG XUẤT", use_container_width=True):
            st.session_state.auth = False; st.rerun()
    else: selected = "Trang Chủ"

# --- PHÂN HỆ HIỂN THỊ ---
if selected == "Trang Chủ":
    st.markdown(f"<h1 style='text-align:center; color:#00263e; margin-bottom:40px;'>{prof.get('slogan')}</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("<div class='home-card'><h3>National Life Group</h3>", unsafe_allow_html=True)
        if prof.get('img_national'): st.image(prof['img_national'], use_container_width=True)
        st.markdown("<p style='color:#64748b; margin-top:15px;'>Đồng hành thịnh vượng từ 1848.</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='home-card'><h3>Giải pháp IUL</h3>", unsafe_allow_html=True)
        if prof.get('img_iul'): st.image(prof['img_iul'], use_container_width=True)
        st.markdown(f"<p style='color:#64748b; margin-top:15px;'>{prof.get('slogan')}</p></div>", unsafe_allow_html=True)
    
    if not st.session_state.auth:
        with st.expander("🔐 ĐĂNG NHẬP"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.button("XÁC NHẬN"):
                if u == "Cong" and p == "admin123": st.session_state.auth = True; st.rerun()

elif selected == "Vận Hành":
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    t1, t2 = st.tabs(["📊 DANH SÁCH", "➕ THÊM MỚI (10 TRƯỜNG)"])
    
    with t1:
        for idx, row in df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="client-card">
                    <div style="display: flex; gap: 15px;">
                        <div style="flex: 2.5;">
                            <div style="font-size: 18px; font-weight: 800; color: #0f172a;">{row['name']}</div>
                            <div class="info-label">Mã định danh (ID)</div><div class="info-value">🆔 {row['crm_id']}</div>
                            <div class="info-label">Trạng thái | Owner</div><div class="info-value"><b>{row['status']}</b> | 👤 {row['owner']}</div>
                        </div>
                        <div style="flex: 2.5;">
                            <div class="info-label">Liên hệ</div>
                            <div class="info-value">📞 Cell: {row['cell']}</div>
                            <div class="info-value">🏢 Work: {row['work']}</div>
                            <div class="info-value">✉️ Email: {row['email']}</div>
                        </div>
                        <div style="flex: 3; background: #f8fafc; border-radius: 8px; padding: 10px; font-size: 13px;">
                            <div class="info-label">Nhật ký hành vi</div>
                            <div style="height: 100px; overflow-y: auto;">{row['note']}</div>
                        </div>
                    </div>
                    <div style="margin-top: 10px; border-top: 1px solid #f1f5f9; padding-top: 10px;">
                        <a href="tel:{row['cell']}" class="action-link">📞 CALL</a>
                        <a href="rcmobile://sms?number={row['cell']}" class="action-link">💬 SMS</a>
                        <a href="{row['crm_link']}" target="_blank" class="action-link">🆔 CRM</a>
                        <a href="mailto:{row['email']}" class="action-link">✉️ EMAIL</a>
                        <a href="https://tmc-elite.streamlit.app/?id={row['cell']}" target="_blank" class="action-link" style="background:#10b981; color:white;">🔗 COPY LINK PDF</a>
                    </div>
                </div>""", unsafe_allow_html=True)
                
                c_n, c_up, c_s = st.columns([5, 3, 2])
                with c_n:
                    with st.form(key=f"nt_{row['id']}", clear_on_submit=True):
                        ni = st.text_input("Ghi chú nhanh", label_visibility="collapsed")
                        if st.form_submit_button("LƯU"):
                            t_s = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
                            n_n = f"<div>{t_s} {ni}</div>" + str(row['note'])
                            conn.execute("UPDATE leads SET note=? WHERE id=?", (n_n, row['id'])); conn.commit(); st.rerun()
                with c_up:
                    with st.popover("📁 UP PDF", use_container_width=True):
                        f = st.file_uploader("Chọn hồ sơ", type="pdf", key=f"f_{row['id']}")
                        if st.button("XÁC NHẬN LƯU", key=f"s_{row['id']}"):
                            if f: conn.execute("UPDATE leads SET pdf_file=? WHERE id=?", (f.read(), row['id'])); conn.commit(); st.success("Xong!"); st.rerun()
                with c_s:
                    with st.popover("⚙️ SỬA", use_container_width=True):
                        with st.form(f"ed_{row['id']}"):
                            un = st.text_input("Tên", row['name']); ui = st.text_input("ID", row['crm_id']); ul = st.text_input("Link", row['crm_link'])
                            uc = st.text_input("Cell", row['cell']); uw = st.text_input("Work", row['work']); ue = st.text_input("Email", row['email'])
                            us = st.text_input("State", row['state']); uo = st.text_input("Owner", row['owner']); ut = st.text_input("Tags", row['tags'])
                            if st.form_submit_button("CẬP NHẬT"):
                                conn.execute("UPDATE leads SET name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=? WHERE id=?", (un, ui, ul, uc, uw, ue, us, uo, ut, row['id'])); conn.commit(); st.rerun()

    with t2:
        st.markdown("### ➕ TIẾP NHẬN HỒ SƠ MỚI (10 TRƯỜNG)")
        with st.form("add_new"):
            r1 = st.columns(3); n = r1[0].text_input("Họ tên"); i = r1[1].text_input("CRM ID"); l = r1[2].text_input("Link CRM")
            r2 = st.columns(3); c = r2[0].text_input("Số Cell"); w = r2[1].text_input("Số Work"); e = r2[2].text_input("Email")
            r3 = st.columns(3); s = r3[0].text_input("State"); o = r3[1].text_input("Owner", value="Cong"); t = r3[2].text_input("Tags")
            st_ = st.selectbox("Status", ["New", "Contacted", "Following", "Closed"])
            if st.form_submit_button("LƯU HỒ SƠ", use_container_width=True):
                conn.execute("INSERT INTO leads (name, crm_id, crm_link, cell, work, email, state, owner, tags, status, last_updated) VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                             (n, i, l, c, w, e, s, o, t, st_, datetime.now(NY_TZ).isoformat()))
                conn.commit(); st.success("Đã thêm thành công!"); st.rerun()
    conn.close()

elif selected == "Mắt Thần":
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT * FROM leads WHERE note LIKE '%ĐANG XEM%' ORDER BY last_updated DESC LIMIT 10", conn)
    for _, row in df.iterrows():
        with st.container():
            st.markdown(f"""
            <div style="background:white; padding:20px; border-radius:12px; border-left:5px solid #ef4444; margin-bottom:15px;">
                <div style="display:flex; justify-content:space-between;">
                    <div style="font-size:18px; font-weight:700;">{row['name']}</div>
                    <div class="eye-active">🔥 ĐANG TRUY CẬP</div>
                </div>
                <div style="margin-top:10px; font-size:14px; color:#64748b;">ID: {row['crm_id']} | Phụ trách: {row['owner']}</div>
                <div style="margin-top:10px; background:#fef2f2; padding:10px; border-radius:8px; font-size:13px;">{row['note']}</div>
            </div>""", unsafe_allow_html=True)
    conn.close()

elif selected == "Cấu Hình":
    with st.form("config"):
        new_sl = st.text_input("Slogan", value=prof.get('slogan'))
        c1, c2, c3 = st.columns(3); up_l = c1.file_uploader("Logo"); up_n = c2.file_uploader("Ảnh Nat"); up_i = c3.file_uploader("Ảnh IUL")
        if st.form_submit_button("LƯU THAY ĐỔI"):
            conn = sqlite3.connect(DB_NAME)
            if up_l:
                with open("logo_app.png", "wb") as f: f.write(up_l.getbuffer())
                conn.execute("UPDATE profile SET logo_app='logo_app.png' WHERE id=1")
            if up_n:
                with open("img_nat.jpg", "wb") as f: f.write(up_n.getbuffer())
                conn.execute("UPDATE profile SET img_national='img_nat.jpg' WHERE id=1")
            if up_i:
                with open("img_iul.jpg", "wb") as f: f.write(up_i.getbuffer())
                conn.execute("UPDATE profile SET img_iul='img_iul.jpg' WHERE id=1")
            conn.execute("UPDATE profile SET slogan=? WHERE id=1", (new_sl,))
            conn.commit(); conn.close(); st.cache_data.clear(); st.success("Đã lưu!"); st.rerun()
