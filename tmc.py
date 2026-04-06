import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import urllib.parse

# --- 1. CẤU HÌNH HỆ THỐNG & CSS NÂNG CAO ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
n_ny = datetime.now(NY_TZ)
DB_NAME = "tmc_database.db"

# CSS ĐẶC TRỊ: GIỮ GIAO DIỆN SANG TRỌNG VÀ FIX ĐÈ NÚT
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* Card khách hàng */
    .client-card {
        background: white; padding: 25px; border-radius: 16px;
        border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    /* Nút bấm thực chiến */
    .action-link {
        color: #0369a1; text-decoration: none; font-weight: 600;
        padding: 8px 15px; border-radius: 8px; background: #f1f5f9;
        font-size: 13px; display: inline-block; margin-right: 5px; margin-bottom: 8px;
    }
    .action-link:hover { background: #0ea5e9; color: white; }
    
    /* Dashboard số liệu */
    .db-card {
        background: white; padding: 20px; border-radius: 12px;
        border-top: 4px solid #00263e; text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .db-num { font-size: 32px; font-weight: 800; color: #1e293b; }

    /* Lịch sử */
    .history-box {
        background: #fdfdfd; border-radius: 8px; padding: 12px;
        border-left: 3px solid #cbd5e1; height: 165px;
        overflow-y: auto; font-size: 14px; line-height: 1.6;
    }

    /* FIX LỖI ĐÈ NÚT: Tách biệt hoàn toàn khối Action */
    .stButton button { width: 100%; border-radius: 8px; font-weight: 700; }
    
    /* Ẩn mũi tên Popover */
    button[data-testid="stPopoverTarget"] svg { display: none !important; }
    button[data-testid="stPopoverTarget"] p { font-weight: 700 !important; margin: 0 auto !important; }
    </style>
""", unsafe_allow_html=True)

def clean_phone(p):
    return str(p).replace(".0", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, crm_id TEXT, crm_link TEXT, cell TEXT, work TEXT, email TEXT, state TEXT, owner TEXT, tags TEXT, status TEXT DEFAULT 'New', note TEXT DEFAULT '', last_updated TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY, slogan TEXT, logo_app TEXT, img_national TEXT, img_iul TEXT)''')
    for col in [('crm_link','TEXT'),('work','TEXT'),('email','TEXT'),('tags','TEXT'),('last_updated','TEXT')]:
        try: c.execute(f"ALTER TABLE leads ADD COLUMN {col[0]} {col[1]}")
        except: pass
    conn.commit(); conn.close()

init_db()

def get_profile():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    res = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()
    return dict(res) if res else {'slogan': 'Sâu sắc - Tận tâm - Chuyên nghiệp'}

prof = get_profile()

# --- 2. TẦNG KHÁCH HÀNG (Nhận diện link ?id=...) ---
id_khach = st.query_params.get("id")
if id_khach:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM leads WHERE cell = ?", (id_khach,)).fetchone()
    if row:
        t_now_str = n_ny.strftime('[%m/%d %H:%M]')
        view_log = f"<div class='history-entry'><span>{t_now_str}</span> 🔥 KHÁCH ĐANG XEM</div>"
        if "KHÁCH ĐANG XEM" not in str(row['note'])[:150]:
            new_note = view_log + str(row['note'])
            conn.execute("UPDATE leads SET note=?, last_updated=? WHERE cell=?", (new_note, n_ny.isoformat(), id_khach))
            conn.commit()
        st.markdown(f"<h1 style='text-align:center;'>🛡️ Chào mừng {row['name']}</h1>", unsafe_allow_html=True)
        if prof.get('img_iul'): st.image(prof['img_iul'], use_container_width=True)
    conn.close(); st.stop()

# --- 3. TẦNG QUẢN TRỊ ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False

with st.sidebar:
    logo_app = prof.get('logo_app')
    st.image(logo_app if logo_app and os.path.exists(logo_app) else "https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    st.divider()
    if st.session_state.authenticated:
        from streamlit_option_menu import option_menu
        selected = option_menu(None, ["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"], styles={"nav-link-selected": {"background-color": "#00263e"}})
        if st.sidebar.button("🚪 ĐĂNG XUẤT", use_container_width=True):
            st.session_state.authenticated = False; st.rerun()
    else: selected = "Trang Chủ"

# --- 4. HIỂN THỊ PHÂN HỆ ---

if selected == "Trang Chủ":
    st.markdown(f"<h2 style='text-align:center; color:#00263e;'>{prof.get('slogan')}</h2>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("<div style='background:white; padding:20px; border-radius:15px; border-top:5px solid #00263e;'><h3>Tập đoàn National Life</h3></div>", unsafe_allow_html=True)
        if prof.get('img_national'): st.image(prof['img_national'], use_container_width=True)
    with c2:
        st.markdown("<div style='background:white; padding:20px; border-radius:15px; border-top:5px solid #00a9e0;'><h3>Giải pháp IUL</h3></div>", unsafe_allow_html=True)
        if prof.get('img_iul'): st.image(prof['img_iul'], use_container_width=True)
    
    if not st.session_state.authenticated:
        with st.expander("🔐 QUẢN TRỊ VIÊN"):
            u = st.text_input("User", key="u_login"); p = st.text_input("Pass", type="password", key="p_login")
            if st.button("ĐĂNG NHẬP"):
                if u == "Cong" and p == "admin123": st.session_state.authenticated = True; st.rerun()

elif selected == "Mắt Thần":
    st.markdown("<h2>👁️ Theo dõi Real-time</h2>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    df_eye = pd.read_sql("SELECT * FROM leads WHERE note LIKE '%KHÁCH ĐANG XEM%' ORDER BY last_updated DESC", conn)
    for _, row in df_eye.iterrows():
        with st.container(border=True):
            st.write(f"Khách: **{row['name']}** ({row['cell']})"); st.markdown(row['note'], unsafe_allow_html=True)
    conn.close()

elif selected == "Vận Hành":
    conn = sqlite3.connect(DB_NAME)
    df_m = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    
    # Dashboard
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f"<div class='db-card'><p>TỔNG LEAD</p><div class='db-num'>{len(df_m)}</div></div>", unsafe_allow_html=True)
    m2.markdown(f"<div class='db-card' style='border-top-color:green;'><p style='color:green;'>MỚI</p><div class='db-num'>{len(df_m[df_m['status'] == 'New'])}</div></div>", unsafe_allow_html=True)
    m3.markdown(f"<div class='db-card' style='border-top-color:red;'><p style='color:red;'>CẦN CHĂM SÓC</p><div class='db-num'>{len(df_m)}</div></div>", unsafe_allow_html=True)
    m4.markdown(f"<div class='db-card' style='border-top-color:#0369a1;'><p>CHỐT</p><div class='db-num'>{len(df_m[df_m['status'] == 'Closed'])}</div></div>", unsafe_allow_html=True)

    tab_list, tab_add = st.tabs(["📊 QUẢN LÝ DANH SÁCH", "➕ THÊM MỚI"])
    
    with tab_list:
        q_s = st.text_input("🔍 Tìm kiếm hồ sơ...", placeholder="Tên, số điện thoại...")
        filtered = df_m[df_m.apply(lambda r: q_s in str(r).lower(), axis=1)]
        for idx, row in filtered.iterrows():
            u_key = f"ld_{row['id']}"; c_cell = clean_phone(row['cell']); c_work = clean_phone(row.get('work',''))
            with st.container():
                # Tầng 1: Thông tin
                st.markdown(f"""
                <div class="client-card">
                    <div style="display: flex; justify-content: space-between;">
                        <div style="flex: 5;">
                            <div class="client-title">{row['name']} | ID: {row['crm_id']}</div>
                            <div style="margin: 10px 0; font-size: 14px; color:#64748b;">📍 {row['state']} | 👤 {row['owner']} | 🏷️ <b>{row['status']}</b></div>
                            <div>
                                <a href="tel:{c_cell}" class="action-link">📞 {c_cell}</a>
                                <a href="rcmobile://call?number={c_cell}" class="action-link">RC Cell</a>
                                <a href="rcmobile://call?number={c_work}" class="action-link">🏢 Work Call</a>
                                <a href="rcmobile://sms?number={c_cell}" class="action-link">💬 SMS</a>
                                <a href="mailto:{row['email']}" class="action-link">✉️ Email</a>
                            </div>
                        </div>
                        <div style="flex: 5; border-left: 1px solid #e2e8f0; padding-left: 20px;">
                            <div class="history-box">{row['note']}</div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
                
                # Tầng 2: Nút bấm (TÁCH BIỆT HOÀN TOÀN ĐỂ KHÔNG ĐÈ NHAU)
                c_btn_note, c_btn_edit = st.columns([8, 2])
                with c_btn_note:
                    with st.form(key=f"nt_{u_key}", clear_on_submit=True):
                        ni = st.text_input("Ghi nhanh tương tác...", label_visibility="collapsed")
                        if st.form_submit_button("LƯU GHI CHÚ"):
                            t_str = n_ny.strftime('[%m/%d %H:%M]')
                            new_n = f"<div class='history-entry'><span>{t_str}</span> {ni}</div>" + str(row['note'])
                            conn.execute("UPDATE leads SET note=?, last_updated=? WHERE id=?", (new_n, n_ny.isoformat(), row['id']))
                            conn.commit(); st.rerun()
                with c_btn_edit:
                    with st.popover("⚙️ SỬA", use_container_width=True):
                        with st.form(f"f_ed_{u_key}"):
                            un = st.text_input("Tên", row['name'])
                            uc = st.text_input("Cell", row['cell'])
                            uo = st.text_input("Owner", row['owner'])
                            st_l = ["New", "Contacted", "Following", "Closed"]
                            ust = st.selectbox("Status", st_l, index=st_l.index(row['status']) if row['status'] in st_l else 0)
                            if st.form_submit_button("CẬP NHẬT"):
                                conn.execute("UPDATE leads SET name=?, cell=?, owner=?, status=? WHERE id=?", (un, uc, uo, ust, row['id']))
                                conn.commit(); st.rerun()
    conn.close()

elif selected == "Cấu Hình":
    with st.form("config"):
        new_sl = st.text_input("Slogan", value=prof.get('slogan'))
        c1, c2, c3 = st.columns(3); up_l = c1.file_uploader("Logo Sidebar"); up_n = c2.file_uploader("Ảnh National"); up_i = c3.file_uploader("Ảnh IUL")
        if st.form_submit_button("LƯU THAY ĐỔI"):
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
            conn.execute("UPDATE profile SET slogan=? WHERE id=1", (new_sl,))
            conn.commit(); conn.close(); st.rerun()
