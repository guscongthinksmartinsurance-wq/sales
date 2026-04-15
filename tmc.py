import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import urllib.parse
import base64

# --- 1. CẤU HÌNH HỆ THỐNG & CACHE ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

# CSS ĐẶC TRỊ - DIỆT TẬN GỐC LỖI CHỒNG CHÉO
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; font-size: 14px; }
    .stApp { background-color: #f1f5f9; }
    
    /* Giao diện Card Khách hàng mới - Tinh tế & Thoáng */
    .elite-card {
        background: white; padding: 25px; border-radius: 16px;
        border: 1px solid #e2e8f0; margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .client-name { font-size: 20px; font-weight: 800; color: #0f172a; margin-bottom: 5px; }
    .tag-status { background: #e0f2fe; color: #0369a1; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; }
    
    /* Cột thông tin rõ ràng */
    .info-box { border-right: 1px solid #f1f5f9; padding-right: 15px; }
    .label { font-size: 11px; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
    .value { font-size: 14px; color: #334155; font-weight: 500; margin-bottom: 10px; }
    
    /* Nút bấm Liên lạc - Không bao giờ đè bóng */
    .btn-group { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 15px; }
    .btn-action { 
        text-decoration: none !important; color: #475569 !important; 
        background: #f8fafc; padding: 8px 14px; border-radius: 8px; 
        font-size: 12px; font-weight: 600; border: 1px solid #e2e8f0;
        transition: all 0.2s;
    }
    .btn-action:hover { background: #00263e; color: white !important; }
    .btn-copy { background: #10b981; color: white !important; border: none; }
    
    /* Mắt thần nhấp nháy */
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
    .eye-active { animation: pulse 2s infinite; color: #ef4444; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# --- 2. XỬ LÝ DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, crm_id TEXT, crm_link TEXT, cell TEXT, work TEXT, email TEXT, state TEXT, owner TEXT, tags TEXT, status TEXT DEFAULT 'New', note TEXT DEFAULT '', last_updated TIMESTAMP, pdf_file BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY, slogan TEXT, logo_app TEXT, img_national TEXT, img_iul TEXT)''')
    # Bổ sung cột nếu cũ
    try: c.execute("ALTER TABLE leads ADD COLUMN pdf_file BLOB")
    except: pass
    conn.commit(); conn.close()

init_db()

@st.cache_data(ttl=600)
def fetch_profile():
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
    res = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()
    return dict(res) if res else {'slogan': 'Sâu sắc - Tận tâm - Chuyên nghiệp'}

prof = fetch_profile()

def get_now(): return datetime.now(NY_TZ)

# --- 3. TẦNG KHÁCH HÀNG (CHIẾN THUẬT GẮN CHIP) ---
id_khach = st.query_params.get("id")
if id_khach:
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM leads WHERE cell = ?", (id_khach,)).fetchone()
    if row:
        t_now = get_now().strftime('[%m/%d %H:%M]')
        new_note = f"<div style='color:#ef4444;'>{t_now} 🔥 KHÁCH ĐANG XEM HỒ SƠ</div>" + str(row['note'])
        conn.execute("UPDATE leads SET note=?, last_updated=? WHERE cell=?", (new_note, get_now().isoformat(), id_khach))
        conn.commit()
        st.markdown(f"<h2 style='text-align:center;'>Chào mừng {row['name']}</h2>", unsafe_allow_html=True)
        if row['pdf_file']:
            b64_pdf = base64.b64encode(row['pdf_file']).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="900"></iframe>', unsafe_allow_html=True)
        else: st.info("Hồ sơ đang được chuẩn bị...")
    conn.close(); st.stop()

# --- 4. TẦNG QUẢN TRỊ ---
if 'auth' not in st.session_state: st.session_state.auth = False

with st.sidebar:
    logo = prof.get('logo_app')
    if logo and os.path.exists(logo): st.image(logo, use_container_width=True)
    else: st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    
    if st.session_state.auth:
        from streamlit_option_menu import option_menu
        selected = option_menu(None, ["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"], 
            icons=['house', 'eye', 'command', 'gear'], 
            styles={"nav-link-selected": {"background-color": "#00263e"}})
        if st.sidebar.button("🚪 ĐĂNG XUẤT", use_container_width=True):
            st.session_state.auth = False; st.rerun()
    else: selected = "Trang Chủ"

# --- PHÂN HỆ VẬN HÀNH (MƯỢT & ĐỦ 10 TRƯỜNG) ---
if selected == "Vận Hành":
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT id, name, crm_id, crm_link, cell, work, email, state, owner, tags, status, note FROM leads ORDER BY id DESC", conn)
    tab1, tab2 = st.tabs(["📊 DANH SÁCH HỒ SƠ", "➕ TIẾP NHẬN MỚI"])
    
    with tab1:
        search = st.text_input("🔍 Tìm nhanh hồ sơ...", placeholder="Tên hoặc Số điện thoại")
        for _, row in df.iterrows():
            if search.lower() in row['name'].lower() or search in str(row['cell']):
                with st.container():
                    st.markdown(f"""
                    <div class="elite-card">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom:15px;">
                            <div>
                                <span class="tag-status">{row['status']}</span>
                                <div class="client-name">{row['name']}</div>
                            </div>
                            <div style="text-align: right;">
                                <div class="label">Người phụ trách</div>
                                <div class="value">👤 {row['owner']}</div>
                            </div>
                        </div>
                        <div style="display: flex; gap: 30px; border-top: 1px solid #f8fafc; padding-top: 15px;">
                            <div style="flex: 2;" class="info-box">
                                <div class="label">Mã định danh (ID)</div><div class="value">🆔 {row['crm_id']}</div>
                                <div class="label">Khu vực (State)</div><div class="value">📍 {row['state']}</div>
                                <div class="label">Phân loại (Tags)</div><div class="value">🏷️ {row['tags']}</div>
                            </div>
                            <div style="flex: 2;" class="info-box">
                                <div class="label">Số Cell</div><div class="value">📱 {row['cell']}</div>
                                <div class="label">Số Work</div><div class="value">🏢 {row['work']}</div>
                                <div class="label">Email</div><div class="value">✉️ {row['email']}</div>
                            </div>
                            <div style="flex: 3;">
                                <div class="label">Nhật ký hành vi</div>
                                <div style="background:#f8fafc; border-radius:8px; padding:10px; height:120px; overflow-y:auto; font-size:13px;">
                                    {row['note']}
                                </div>
                            </div>
                        </div>
                        <div class="btn-group">
                            <a href="tel:{row['cell']}" class="btn-action">📞 GỌI</a>
                            <a href="rcmobile://sms?number={row['cell']}" class="btn-action">💬 SMS</a>
                            <a href="{row['crm_link']}" target="_blank" class="btn-action">🆔 CRM</a>
                            <a href="https://calendar.google.com/calendar/r/eventedit?text=Meeting_{row['name']}" target="_blank" class="btn-action">📅 LỊCH</a>
                            <a href="https://tmc-elite.streamlit.app/?id={row['cell']}" target="_blank" class="btn-action btn-copy">🔗 COPY LINK PDF</a>
                        </div>
                    </div>""", unsafe_allow_html=True)
                    
                    # Nút chức năng (Không nhét vào HTML để tránh load chậm)
                    c1, c2, c3 = st.columns([4, 4, 2])
                    with c1:
                        with st.form(key=f"note_{row['id']}", clear_on_submit=True):
                            txt = st.text_input("Ghi chú nhanh", label_visibility="collapsed")
                            if st.form_submit_button("LƯU"):
                                t_s = get_now().strftime('[%m/%d %H:%M]')
                                n_n = f"<div>{t_s} {txt}</div>" + str(row['note'])
                                conn.execute("UPDATE leads SET note=? WHERE id=?", (n_n, row['id'])); conn.commit(); st.rerun()
                    with c2:
                        with st.popover("📁 UP PDF MINH HỌA", use_container_width=True):
                            f = st.file_uploader("Chọn file PDF", type="pdf", key=f"f_{row['id']}")
                            if st.button("XÁC NHẬN LƯU PDF", key=f"s_{row['id']}"):
                                if f: conn.execute("UPDATE leads SET pdf_file=? WHERE id=?", (f.read(), row['id'])); conn.commit(); st.success("Đã up!"); st.rerun()
                    with c3:
                        with st.popover("⚙️ SỬA", use_container_width=True):
                            with st.form(f"ed_{row['id']}"):
                                un = st.text_input("Tên", row['name']); ui = st.text_input("ID", row['crm_id']); ul = st.text_input("Link CRM", row['crm_link'])
                                uc = st.text_input("Cell", row['cell']); uw = st.text_input("Work", row['work']); ue = st.text_input("Email", row['email'])
                                us = st.text_input("State", row['state']); uo = st.text_input("Owner", row['owner']); ut = st.text_input("Tags", row['tags'])
                                if st.form_submit_button("CẬP NHẬT"):
                                    conn.execute("UPDATE leads SET name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=? WHERE id=?", (un, ui, ul, uc, uw, ue, us, uo, ut, row['id'])); conn.commit(); st.rerun()

    with tab2:
        with st.form("add_new"):
            st.markdown("### ➕ THÊM HỒ SƠ MỚI (ĐỦ 10 TRƯỜNG)")
            r1 = st.columns(3); n = r1[0].text_input("Tên khách"); i = r1[1].text_input("CRM ID"); l = r1[2].text_input("Link CRM")
            r2 = st.columns(3); c = r2[0].text_input("Số Cell"); w = r2[1].text_input("Số Work"); e = r2[2].text_input("Email")
            r3 = st.columns(3); s = r3[0].text_input("Bang (State)"); o = r3[1].text_input("Owner", value="Cong"); t = r3[2].text_input("Tags")
            if st.form_submit_button("LƯU HỒ SƠ"):
                conn.execute("INSERT INTO leads (name, crm_id, crm_link, cell, work, email, state, owner, tags, last_updated) VALUES (?,?,?,?,?,?,?,?,?,?)", (n, i, l, c, w, e, s, o, t, get_now().isoformat()))
                conn.commit(); st.success("Đã thêm!"); st.rerun()
    conn.close()

# --- PHÂN HỆ MẮT THẦN (SOI REAL-TIME) ---
elif selected == "Mắt Thần":
    st.markdown("## 👁️ Mắt Thần Đang Soi...")
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT name, cell, owner, note FROM leads WHERE note LIKE '%ĐANG XEM%' ORDER BY last_updated DESC LIMIT 10", conn)
    for _, row in df.iterrows():
        with st.container():
            st.markdown(f"""
            <div style="background:white; padding:20px; border-radius:12px; border-left:5px solid #ef4444; margin-bottom:15px;">
                <div style="display:flex; justify-content:space-between;">
                    <div style="font-size:18px; font-weight:700;">{row['name']}</div>
                    <div class="eye-active">🔥 ĐANG TRUY CẬP</div>
                </div>
                <div style="margin-top:10px; font-size:14px; color:#64748b;">
                    SĐT: <b>{row['cell']}</b> | Phụ trách: <b>{row['owner']}</b>
                </div>
                <div style="margin-top:10px; background:#fef2f2; padding:10px; border-radius:8px; font-size:13px;">{row['note']}</div>
            </div>""", unsafe_allow_html=True)
    conn.close()

# --- PHÂN HỆ TRANG CHỦ & CẤU HÌNH ---
elif selected == "Trang Chủ":
    st.markdown(f"<h1 style='text-align:center; color:#00263e;'>{prof.get('slogan')}</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("<div class='home-card' style='height:450px;'><h3>National Life Group</h3>", unsafe_allow_html=True)
        if prof.get('img_national'): st.image(prof['img_national'], use_container_width=True)
    with c2:
        st.markdown("<div class='home-card' style='height:450px;'><h3>Giải pháp IUL</h3>", unsafe_allow_html=True)
        if prof.get('img_iul'): st.image(prof['img_iul'], use_container_width=True)
    if not st.session_state.auth:
        with st.expander("🔐 QUẢN TRỊ"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.button("OK"):
                if u == "Cong" and p == "admin123": st.session_state.auth = True; st.rerun()

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
