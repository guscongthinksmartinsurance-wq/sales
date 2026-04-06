import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

# Load CSS
try:
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except: pass

def clean_phone(p):
    return str(p).replace(".0", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Bảng Leads: Đã bỏ ràng buộc UNIQUE ở cell để anh nhập trùng thoải mái
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, crm_id TEXT, crm_link TEXT,
                    cell TEXT, work TEXT, email TEXT,
                    state TEXT, owner TEXT, tags TEXT,
                    status TEXT DEFAULT 'New', note TEXT DEFAULT '', 
                    last_updated TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY, slogan TEXT, logo_app TEXT, img_national TEXT, img_iul TEXT)''')
    
    # Đảm bảo khách nào cũng có ngày cập nhật để hiện lên danh sách
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
    logo = prof.get('logo_app')
    if logo and os.path.exists(logo): st.image(logo, use_container_width=True)
    else: st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    st.divider()
    if 'authenticated' not in st.session_state: st.session_state.authenticated = False
    if st.session_state.authenticated:
        from streamlit_option_menu import option_menu
        selected = option_menu(None, ["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"], styles={"nav-link-selected": {"background-color": "#00263e"}})
        if st.sidebar.button("ĐĂNG XUẤT", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    else: selected = "Trang Chủ"

# --- 3. LOGIC HIỂN THỊ ---

if selected == "Trang Chủ":
    st.markdown('<div class="hero-banner"><h1>NATIONAL LIFE GROUP</h1><p>Since 1848</p></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="small")
    with c1: st.markdown('<div class="main-card"><h3>National Life Group</h3><p>Uy tín 170 năm.</p></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="main-card"><h3>Giải pháp IUL</h3><p>Bảo vệ và tích lũy.</p></div>', unsafe_allow_html=True)
    if not st.session_state.authenticated:
        with st.expander("🔐 QUẢN TRỊ"):
            u = st.text_input("User", key="u_h"); p = st.text_input("Pass", type="password", key="p_h")
            if st.button("VÀO"):
                if u == "Cong" and p == "admin123": st.session_state.authenticated = True; st.rerun()

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

    tab_list, tab_add = st.tabs(["DANH SÁCH LEAD", "THÊM MỚI HỒ SƠ"])

    with tab_list:
        # Dashboard
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f"<div class='db-card'><p>TỔNG LEAD</p><h3>{len(df_m)}</h3></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='db-card'><p style='color:green;'>MỚI</p><h3>{len(df_m[df_m['status'] == 'New'])}</h3></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='db-card'><p style='color:red;'>TRỄ (>7D)</p><h3 style='color:red;'>{len(df_m[df_m['days_diff'] > 7])}</h3></div>", unsafe_allow_html=True)
        with m4: st.markdown(f"<div class='db-card'><p style='color:blue;'>CHỐT</p><h3>{len(df_m[df_m['status'] == 'Closed'])}</h3></div>", unsafe_allow_html=True)

        st.divider()
        c_sch, c_sld = st.columns([6, 4])
        q_s = c_sch.text_input("TÌM KIẾM...", key="q_v").lower().strip()
        days_limit = c_sld.slider("LỌC KHÁCH TRỄ (NGÀY)", 0, 90, 90)

        filtered = df_m[(df_m.apply(lambda r: q_s in str(r).lower(), axis=1)) & (df_m['days_diff'] <= days_limit)]

        for idx, row in filtered.iterrows():
            with st.container(border=True):
                ci, ce = st.columns([9.3, 0.7])
                with ci:
                    st.markdown(f"**{row['name']}** | ID: {row['crm_id']} | STATUS: **{row['status']}**")
                    st.markdown(f"BANG: {row['state']} | OWNER: {row['owner']} | TAGS: {row['tags']}")
                    st.markdown(f"CELL: {row['cell']} | WORK: {row['work']} | EMAIL: {row['email']}")
                    st.caption(f"Cập nhật: {row['last_updated']}")
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

    with tab_add:
        st.markdown("### NHẬP HỒ SƠ MỚI (ĐẦY ĐỦ 10 TRƯỜNG)")
        with st.form("add_new_10", clear_on_submit=True):
            r1 = st.columns(3); an = r1[0].text_input("Họ và Tên"); ai = r1[1].text_input("CRM ID"); al = r1[2].text_input("CRM Link")
            r2 = st.columns(3); ac = r2[0].text_input("Số Cell"); aw = r2[1].text_input("Số Work"); ae = r2[2].text_input("Địa chỉ Email")
            r3 = st.columns(3); as_ = r3[0].text_input("Tiểu bang"); ao = r3[1].text_input("Owner", value="Cong"); at = r3[2].text_input("Thẻ (Tags)")
            ast = st.selectbox("Trạng thái", ["New", "Contacted", "Following", "Closed"])
            if st.form_submit_button("LƯU HỒ SƠ", use_container_width=True):
                if an and ac:
                    conn.execute("INSERT INTO leads (name, crm_id, crm_link, cell, work, email, state, owner, tags, status, last_updated) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                 (an, ai, al, ac, aw, ae, as_, ao, at, ast, datetime.now(NY_TZ).isoformat()))
                    conn.commit(); st.success("Đã thêm thành công!"); st.rerun()
                else: st.warning("Vui lòng điền Tên và Số Cell.")
    conn.close()

elif selected == "Cấu Hình":
    st.markdown("<div class='main-card'><h2>CÀI ĐẶT</h2></div>", unsafe_allow_html=True)
    with st.form("config"):
        new_sl = st.text_input("Slogan", value=prof.get('slogan'))
        if st.form_submit_button("LƯU"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("UPDATE profile SET slogan=? WHERE id=1", (new_sl,))
            conn.commit(); conn.close(); st.success("Đã lưu!"); st.rerun()
