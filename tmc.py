import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import urllib.parse

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

# Load CSS từ file style.css của anh
try:
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except: pass

def clean_phone(p):
    return str(p).replace(".0", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Bảng Leads: Không để UNIQUE ở cell để anh nhập trùng thoải mái
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, crm_id TEXT, crm_link TEXT,
                    cell TEXT, work TEXT, email TEXT,
                    state TEXT, owner TEXT, tags TEXT,
                    status TEXT DEFAULT 'New', note TEXT DEFAULT '', 
                    last_updated TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS profile (
                    id INTEGER PRIMARY KEY, slogan TEXT, 
                    logo_app TEXT, img_national TEXT, img_iul TEXT)''')
    
    # Đảm bảo hồ sơ cũ đều có ngày để hiện lên danh sách
    c.execute("UPDATE leads SET last_updated = ? WHERE last_updated IS NULL OR last_updated = ''", (datetime.now(NY_TZ).isoformat(),))
    
    c.execute("SELECT count(*) FROM profile")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO profile (id, slogan) VALUES (1, 'Sâu sắc - Tận tâm - Chuyên nghiệp')")
    conn.commit()
    conn.close()

init_db()

def get_profile():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    res = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()
    return dict(res) if res else {}

prof = get_profile()

# --- 2. SIDEBAR & ĐIỀU HƯỚNG ---
with st.sidebar:
    logo_app = prof.get('logo_app')
    if logo_app and os.path.exists(logo_app):
        st.image(logo_app, use_container_width=True)
    else:
        st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    
    st.divider()
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        from streamlit_option_menu import option_menu
        selected = option_menu(
            menu_title=None,
            options=["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"],
            styles={"nav-link-selected": {"background-color": "#00263e"}}
        )
        if st.sidebar.button("ĐĂNG XUẤT", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    else:
        selected = "Trang Chủ"

# --- 3. LOGIC HIỂN THỊ ---

# A. TRANG CHỦ (Chia cột thoáng đạt)
if selected == "Trang Chủ":
    st.markdown('<div class="hero-banner"><h1>NATIONAL LIFE GROUP</h1><p>Since 1848</p></div>', unsafe_allow_html=True)
    
    # Dùng gap="large" để hai cột không bị dính vào nhau
    col_left, col_right = st.columns(2, gap="large")
    with col_left:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<p class="section-header">Tập Đoàn National Life Group</p>', unsafe_allow_html=True)
        img_n = prof.get('img_national')
        st.image(img_n if img_n and os.path.exists(img_n) else "https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
        st.write("Biểu tượng tin cậy tại Hoa Kỳ từ năm 1848.")
        st.markdown("- **Uy tín:** 170+ năm.\n- **Cam kết:** Giữ trọn lời hứa.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<p class="section-header">Giải Pháp Tài Chính IUL</p>', unsafe_allow_html=True)
        img_i = prof.get('img_iul')
        if img_i and os.path.exists(img_i): st.image(img_i, use_container_width=True)
        else: st.info("Vào Cấu Hình để upload ảnh IUL.")
        st.write(f"**{prof.get('slogan')}**")
        st.write("IUL kết hợp bảo vệ và tích lũy hưu trí không thuế.")
        st.markdown("- **An toàn:** 0% sàn.\n- **Linh hoạt:** Rút tiền không thuế.")
        st.markdown('</div>', unsafe_allow_html=True)

    if not st.session_state.authenticated:
        with st.expander("🔐 QUẢN TRỊ"):
            u = st.text_input("User", key="u_h"); p = st.text_input("Pass", type="password", key="p_h")
            if st.button("XÁC NHẬN"):
                if u == "Cong" and p == "admin123": st.session_state.authenticated = True; st.rerun()

# B. VẬN HÀNH (Đầy đủ 10 trường & Nhập trùng thoải mái)
elif selected == "Vận Hành":
    st.markdown("<div class='main-card'><h2>HỆ THỐNG VẬN HÀNH DỮ LIỆU</h2></div>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    df_m = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    n_ny = datetime.now(NY_TZ)

    def get_days_diff(val):
        try:
            dt = datetime.fromisoformat(str(val))
            if dt.tzinfo is None: dt = NY_TZ.localize(dt)
            return (n_ny - dt).days
        except: return 0
    df_m['days_diff'] = df_m['last_updated'].apply(get_days_diff)

    t1, t2 = st.tabs(["DANH SÁCH LEAD", "THÊM MỚI HỒ SƠ"])
    with t1:
        # Dashboard và Lọc... (Giữ nguyên logic Dashboard của anh)
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f"<div class='db-card'><p>TỔNG LEAD</p><h3>{len(df_m)}</h3></div>", unsafe_allow_html=True)
        st.divider()
        q_s = st.text_input("TÌM KIẾM...", key="q_v").lower().strip()
        days_limit = st.slider("LỌC KHÁCH TRỄ (NGÀY)", 0, 90, 90)
        filtered = df_m[(df_m.apply(lambda r: q_s in str(r).lower(), axis=1)) & (df_m['days_diff'] <= days_limit)]

        for idx, row in filtered.iterrows():
            with st.container(border=True):
                ci, ce = st.columns([9.3, 0.7])
                with ci:
                    st.markdown(f"**{row['name']}** | ID: {row['crm_id']} | STATUS: {row['status']}")
                    st.markdown(f"CELL: {row['cell']} | OWNER: {row['owner']}")
                with ce:
                    with st.popover("SỬA"):
                        with st.form(f"f_ed_{row['id']}"):
                            un = st.text_input("Tên", row['name']); ui = st.text_input("ID", row['crm_id'])
                            ul = st.text_input("Link", row['crm_link']); uc = st.text_input("Cell", row['cell'])
                            uw = st.text_input("Work", row['work']); ue = st.text_input("Email", row['email'])
                            us = st.text_input("State", row['state']); uo = st.text_input("Owner", row['owner'])
                            utg = st.text_input("Tags", row['tags'])
                            st_list = ["New", "Contacted", "Following", "Closed"]
                            ust = st.selectbox("Status", st_list, index=st_list.index(row['status']) if row['status'] in st_list else 0)
                            if st.form_submit_button("CẬP NHẬT"):
                                conn.execute("UPDATE leads SET name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=?, status=?, last_updated=? WHERE id=?",
                                             (un, ui, ul, uc, uw, ue, us, uo, utg, ust, datetime.now(NY_TZ).isoformat(), row['id']))
                                conn.commit(); st.rerun()

    with t2:
        st.markdown("### NHẬP HỒ SƠ MỚI (10 TRƯỜNG)")
        with st.form("add_10", clear_on_submit=True):
            r1 = st.columns(3); an = r1[0].text_input("Tên"); ai = r1[1].text_input("ID"); al = r1[2].text_input("Link")
            r2 = st.columns(3); ac = r2[0].text_input("Cell"); aw = r2[1].text_input("Work"); ae = r2[2].text_input("Email")
            r3 = st.columns(3); as_ = r3[0].text_input("State"); ao = r3[1].text_input("Owner", value="Cong"); at = r3[2].text_input("Tags")
            ast = st.selectbox("Status", ["New", "Contacted", "Following", "Closed"])
            if st.form_submit_button("LƯU HỒ SƠ", use_container_width=True):
                if an and ac:
                    conn.execute("INSERT INTO leads (name, crm_id, crm_link, cell, work, email, state, owner, tags, status, last_updated) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                 (an, ai, al, ac, aw, ae, as_, ao, at, ast, datetime.now(NY_TZ).isoformat()))
                    conn.commit(); st.success("Thành công!"); st.rerun()
    conn.close()

# C. CẤU HÌNH (Giữ nguyên 3 ô upload ảnh của anh)
elif selected == "Cấu Hình":
    st.markdown("<div class='main-card'><h2>CÀI ĐẶT HỆ THỐNG</h2></div>", unsafe_allow_html=True)
    with st.form("config"):
        new_sl = st.text_input("Slogan", value=prof.get('slogan'))
        c1, c2, c3 = st.columns(3)
        up_l = c1.file_uploader("Logo Sidebar"); up_n = c2.file_uploader("Ảnh National"); up_i = c3.file_uploader("Ảnh IUL")
        if st.form_submit_button("LƯU CẤU HÌNH"):
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
            conn.execute("UPDATE profile SET slogan=?", (new_sl,))
            conn.commit(); conn.close(); st.success("Đã cập nhật!"); st.rerun()
