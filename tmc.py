import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import urllib.parse

# --- 1. CẤU HÌNH HỆ THỐNG & CSS ĐẶC TRỊ ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
n_ny = datetime.now(NY_TZ)
DB_NAME = "tmc_database.db"

# CSS TỔNG LỰC: DIỆT LỖI ĐÈ BÓNG CHỮ VÀ ICON
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* 1. FIX NÚT UPLOAD: TRIỆT TIÊU CHỮ CŨ */
    [data-testid="stFileUploaderDropzone"] div div { 
        opacity: 0 !important; 
        height: 0 !important;
        position: absolute !important;
    }
    [data-testid="stFileUploaderDropzone"]::before { 
        content: "Bấm để chọn File"; 
        color: #0369a1; font-weight: 700; font-size: 14px;
        display: block; width: 100%; text-align: center;
    }

    /* 2. FIX NÚT SỬA (POPOVER): DIỆT MŨI TÊN EXPAND_MORE */
    button[data-testid="stPopoverTarget"] svg { 
        display: none !important; 
        visibility: hidden !important; 
    }
    button[data-testid="stPopoverTarget"] p { 
        display: none !important; 
    }
    button[data-testid="stPopoverTarget"]::after { 
        content: "⚙️ SỬA"; 
        font-weight: 800; font-size: 13px; color: #1e293b;
        display: block; width: 100%; text-align: center;
    }
    /* Xóa bỏ khoảng trống thừa của icon đã ẩn */
    button[data-testid="stPopoverTarget"] div[data-testid="stMarkdownContainer"] {
        display: none !important;
    }

    /* Giao diện Card & Dashboard */
    .home-card { background: white; padding: 25px; border-radius: 15px; border-top: 5px solid #00263e; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; margin-bottom: 20px; }
    .client-card { background: white; padding: 25px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .action-link { color: #0369a1; text-decoration: none; font-weight: 600; padding: 7px 12px; border-radius: 6px; background: #f1f5f9; font-size: 13px; display: inline-block; margin: 2px; }
    .history-box { background: #fdfdfd; border-radius: 8px; padding: 12px; border-left: 3px solid #cbd5e1; height: 165px; overflow-y: auto; font-size: 14px; line-height: 1.6; }
    .section-tag { background: #f1f5f9; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 800; color: #475569; margin: 10px 0 5px 0; }
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

# --- 2. TẦNG KHÁCH HÀNG ---
id_khach = st.query_params.get("id")
if id_khach:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM leads WHERE cell = ?", (id_khach,)).fetchone()
    if row:
        t_now_str = n_ny.strftime('[%m/%d %H:%M]')
        new_note = f"<div class='history-entry'><span>{t_now_str}</span> 🔥 KHÁCH ĐANG XEM</div>" + str(row['note'])
        conn.execute("UPDATE leads SET note=?, last_updated=? WHERE cell=?", (new_note, n_ny.isoformat(), id_khach))
        conn.commit()
        st.markdown(f"<h1 style='text-align:center;'>🛡️ Chào mừng {row['name']}</h1>", unsafe_allow_html=True)
        if prof.get('img_iul'): st.image(prof['img_iul'], use_container_width=True)
    conn.close(); st.stop()

# --- 3. TẦNG QUẢN TRỊ ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False

with st.sidebar:
    logo = prof.get('logo_app')
    st.image(logo if logo and os.path.exists(logo) else "https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    if st.session_state.authenticated:
        from streamlit_option_menu import option_menu
        selected = option_menu(None, ["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"], styles={"nav-link-selected": {"background-color": "#00263e"}})
        if st.sidebar.button("🚪 ĐĂNG XUẤT", use_container_width=True):
            st.session_state.authenticated = False; st.rerun()
    else: selected = "Trang Chủ"

# --- 4. PHÂN HỆ CHI TIẾT ---
if selected == "Trang Chủ":
    st.markdown(f"<h2 style='text-align:center; color:#00263e; margin-bottom:30px;'>{prof.get('slogan')}</h2>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("<div class='home-card'><h3>National Life Group</h3></div>", unsafe_allow_html=True)
        if prof.get('img_national'): st.image(prof['img_national'], use_container_width=True)
        st.markdown("<p style='color:#64748b; font-size:15px; margin-top:15px;'>Phục vụ từ 1848 - Giá trị bền bỉ cùng thời gian.</p>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='home-card' style='border-top-color:#00a9e0;'><h3>Giải pháp IUL</h3></div>", unsafe_allow_html=True)
        if prof.get('img_iul'): st.image(prof['img_iul'], use_container_width=True)
        st.markdown(f"<p style='color:#64748b; font-size:15px; margin-top:15px;'>{prof.get('slogan')}</p>", unsafe_allow_html=True)
    
    if not st.session_state.authenticated:
        with st.expander("🔐 QUẢN TRỊ"):
            u = st.text_input("User", key="u_l"); p = st.text_input("Pass", type="password", key="p_l")
            if st.button("ĐĂNG NHẬP"):
                if u == "Cong" and p == "admin123": st.session_state.authenticated = True; st.rerun()

elif selected == "Vận Hành":
    conn = sqlite3.connect(DB_NAME)
    df_m = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    tab_list, tab_add = st.tabs(["📊 DANH SÁCH LEAD", "➕ TIẾP NHẬN HỒ SƠ"])
    
    with tab_list:
        q_s = st.text_input("🔍 Tìm kiếm hồ sơ...", placeholder="Tên, số điện thoại...")
        filtered = df_m[df_m.apply(lambda r: q_s in str(r).lower(), axis=1)]
        for idx, row in filtered.iterrows():
            u_key = f"ld_{row['id']}"; c_cell = clean_phone(row['cell']); c_work = clean_phone(row.get('work',''))
            with st.container():
                st.markdown(f"""
                <div class="client-card">
                    <div style="display: flex; justify-content: space-between;">
                        <div style="flex: 4.8;">
                            <div class="client-title">{row['name']} | <a href="{row['crm_link']}" target="_blank" style="text-decoration:none; color:#0ea5e9;">🆔 {row['crm_id']}</a></div>
                            <div style="margin: 8px 0; font-size: 14px; color:#64748b;">📍 {row['state']} | 👤 {row['owner']} | 🏷️ <b>{row['status']}</b></div>
                            <div>
                                <a href="tel:{c_cell}" class="action-link">📞 {c_cell}</a>
                                <a href="rcmobile://call?number={c_cell}" class="action-link">RC Cell</a>
                                <a href="rcmobile://call?number={c_work}" class="action-link">🏢 Work: {c_work}</a>
                                <a href="rcmobile://sms?number={c_cell}" class="action-link">💬 SMS</a>
                                <a href="mailto:{row['email']}" class="action-link">✉️ Email</a>
                                <a href="https://calendar.google.com/calendar/r/eventedit?text=Meeting_{urllib.parse.quote(str(row['name']))}" target="_blank" class="action-link">📅 Calendar</a>
                            </div>
                        </div>
                        <div style="flex: 5.2; border-left: 1px solid #e2e8f0; padding-left: 20px;"><div class="history-box">{row['note']}</div></div>
                    </div>
                </div>""", unsafe_allow_html=True)
                
                c_n, c_s = st.columns([8.2, 1.8])
                with c_n:
                    with st.form(key=f"nt_{u_key}", clear_on_submit=True):
                        ni = st.text_input("Ghi nhanh...", label_visibility="collapsed")
                        if st.form_submit_button("LƯU GHI CHÚ", use_container_width=True):
                            t_str = n_ny.strftime('[%m/%d %H:%M]')
                            new_n = f"<div class='history-entry'><span>{t_str}</span> {ni}</div>" + str(row['note'])
                            conn.execute("UPDATE leads SET note=?, last_updated=? WHERE id=?", (new_n, n_ny.isoformat(), row['id']))
                            conn.commit(); st.rerun()
                with c_s:
                    with st.popover("SỬA", use_container_width=True):
                        with st.form(f"f_ed_{u_key}"):
                            un = st.text_input("Tên", row['name'])
                            e1, e2 = st.columns(2); ui = e1.text_input("ID", row['crm_id']); ul = e2.text_input("Link", row['crm_link'])
                            e3, e4 = st.columns(2); uc = e3.text_input("Cell", row['cell']); uw = e4.text_input("Work", row.get('work',''))
                            ue = st.text_input("Email", row.get('email',''))
                            e5, e6 = st.columns(2); us = e5.text_input("State", row.get('state','')); uo = e6.text_input("Owner", row['owner'])
                            utg = st.text_input("Tags", row.get('tags',''))
                            st_l = ["New", "Contacted", "Following", "Closed"]
                            ust = st.selectbox("Status", st_l, index=st_l.index(row['status']) if row['status'] in st_l else 0)
                            if st.form_submit_button("CẬP NHẬT"):
                                conn.execute("UPDATE leads SET name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=?, status=?, last_updated=? WHERE id=?", 
                                             (un, ui, ul, uc, uw, ue, us, uo, utg, ust, n_ny.isoformat(), row['id']))
                                conn.commit(); st.rerun()

    with tab_add:
        st.markdown("### ➕ TIẾP NHẬN HỒ SƠ MỚI (10 TRƯỜNG)")
        with st.form("add_new_f", clear_on_submit=True):
            r1 = st.columns(3); an = r1[0].text_input("Họ tên"); ai = r1[1].text_input("ID"); al = r1[2].text_input("Link")
            r2 = st.columns(3); ac = r2[0].text_input("Cell"); aw = r2[1].text_input("Work"); ae = r2[2].text_input("Email")
            r3 = st.columns(3); as_ = r3[0].text_input("State"); ao = r3[1].text_input("Owner", value="Cong"); at = r3[2].text_input("Tags")
            ast = st.selectbox("Status", ["New", "Contacted", "Following", "Closed"])
            if st.form_submit_button("LƯU HỒ SƠ", use_container_width=True):
                conn.execute("INSERT INTO leads (name, crm_id, crm_link, cell, work, email, state, owner, tags, status, last_updated) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                             (an, ai, al, ac, aw, ae, as_, ao, at, ast, n_ny.isoformat()))
                conn.commit(); st.success("Thành công!"); st.rerun()
    conn.close()

elif selected == "Cấu Hình":
    st.markdown("<h2>⚙️ Cấu Hình</h2>", unsafe_allow_html=True)
    with st.form("config"):
        new_sl = st.text_input("Slogan dòng IUL", value=prof.get('slogan'))
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
            conn.commit(); conn.close(); st.success("Đã lưu!"); st.rerun()
