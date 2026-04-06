import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import urllib.parse

# --- 1. CẤU HÌNH ---
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
    # Khởi tạo bảng với đầy đủ các trường anh yêu cầu
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, crm_id TEXT, crm_link TEXT,
                    cell TEXT UNIQUE, work TEXT, email TEXT,
                    state TEXT, owner TEXT, tags TEXT,
                    status TEXT DEFAULT 'New', note TEXT DEFAULT '', 
                    last_updated TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY, slogan TEXT, logo_app TEXT, img_national TEXT, img_iul TEXT)''')
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

# --- 2. SIDEBAR & MENU ---
with st.sidebar:
    logo = prof.get('logo_app')
    if logo and os.path.exists(logo): st.image(logo, use_container_width=True)
    else: st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    
    st.divider()
    if 'authenticated' not in st.session_state: st.session_state.authenticated = False
    
    if st.session_state.authenticated:
        from streamlit_option_menu import option_menu
        selected = option_menu(None, ["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"], 
                               styles={"nav-link-selected": {"background-color": "#00263e"}})
        if st.sidebar.button("ĐĂNG XUẤT", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    else:
        selected = "Trang Chủ"

# --- 3. ĐIỀU HƯỚNG ---

if selected == "Trang Chủ":
    st.markdown('<div class="hero-banner"><h1>NATIONAL LIFE GROUP</h1><p>Experience the Peace of Mind Since 1848</p></div>', unsafe_allow_html=True)
    col_left, col_right = st.columns(2, gap="small")
    with col_left:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<p class="section-header">Tập Đoàn National Life Group</p>', unsafe_allow_html=True)
        img_n = prof.get('img_national')
        if img_n and os.path.exists(img_n): st.image(img_n, use_container_width=True)
        else: st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
        st.write("Biểu tượng tin cậy tại Hoa Kỳ từ năm 1848.")
        st.markdown("- **Uy tín:** 170+ năm.\n- **Cam kết:** Giữ trọn lời hứa.")
        st.markdown('</div>', unsafe_allow_html=True)
    with col_right:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<p class="section-header">Giải Pháp Tài Chính IUL</p>', unsafe_allow_html=True)
        img_i = prof.get('img_iul')
        if img_i and os.path.exists(img_i): st.image(img_i, use_container_width=True)
        else: st.info("Vào mục Cấu Hình để upload ảnh IUL.")
        st.write(f"**{prof.get('slogan', 'Sâu sắc - Tận tâm - Chuyên nghiệp')}**")
        st.write("IUL kết hợp bảo vệ sinh mạng và tích lũy hưu trí không thuế.")
        st.markdown("- **An toàn:** Bảo đảm 0% sàn.\n- **Linh hoạt:** Rút tiền không thuế.")
        st.markdown('</div>', unsafe_allow_html=True)
    if not st.session_state.authenticated:
        with st.expander("🔐 QUẢN TRỊ HỆ THỐNG"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("XÁC NHẬN"):
                if u == "Cong" and p == "admin123":
                    st.session_state.authenticated = True
                    st.rerun()

elif selected == "Vận Hành":
    st.markdown("<div class='main-card'><h2>HỆ THỐNG VẬN HÀNH DỮ LIỆU</h2></div>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    df_m = pd.read_sql("SELECT * FROM leads", conn)
    n_ny = datetime.now(NY_TZ)

    tab_list, tab_add = st.tabs(["DANH SÁCH LEAD", "THÊM MỚI HỒ SƠ"])

    with tab_list:
        # DASHBOARD CHỈ SỐ
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f"<div class='db-card'><p style='margin:0; font-weight:1000;'>TỔNG LEAD</p><div class='db-num-capsule'>{len(df_m)}</div></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='db-card'><p style='margin:0; font-weight:1000; color:green;'>MỚI</p><div class='db-num-capsule'>{len(df_m[df_m['status'] == 'New'])}</div></div>", unsafe_allow_html=True)
        with m3:
            def is_late(r):
                try: 
                    dt = datetime.fromisoformat(r['last_updated'])
                    return (n_ny - NY_TZ.localize(dt) if dt.tzinfo is None else n_ny - dt).days > 7
                except: return False
            st.markdown(f"<div class='db-card'><p style='margin:0; font-weight:1000; color:red;'>TRỄ (>7D)</p><div class='db-num-capsule' style='color:red;'>{len(df_m[df_m.apply(is_late, axis=1)])}</div></div>", unsafe_allow_html=True)
        with m4: st.markdown(f"<div class='db-card'><p style='margin:0; font-weight:1000; color:blue;'>CHỐT</p><div class='db-num-capsule' style='color:blue;'>{len(df_m[df_m['status'] == 'Closed'])}</div></div>", unsafe_allow_html=True)

        st.divider()
        q_s = st.text_input("TÌM KIẾM HỒ SƠ...", key="q_search").lower().strip()
        filtered = df_m[df_m.apply(lambda r: q_s in str(r).lower(), axis=1)]

        for idx, row in filtered.iterrows():
            u_key = f"ld_{row['id']}"
            c_cell = clean_phone(row['cell'])
            c_work = clean_phone(row.get('work', ''))
            
            with st.container(border=True):
                ci, ce = st.columns([9.5, 0.5])
                with ci:
                    st.markdown(f"<span class='client-title'>{row['name']}</span> | <a href='{row.get('crm_link','#')}' target='_blank'>ID: {row.get('crm_id','N/A')}</a>", unsafe_allow_html=True)
                    st.markdown(f"BANG: {row.get('state','')} | OWNER: {row['owner']} | STATUS: **{row['status']}** | TAGS: *{row.get('tags', '')}*")
                    st.markdown(f"CELL: <a href='tel:{c_cell}'>{c_cell}</a> | WORK: <a href='tel:{c_work}'>{c_work}</a>", unsafe_allow_html=True)
                    
                    # Nút tương tác (Không icon)
                    a1, a2 = st.columns([1, 9])
                    a1.markdown(f"<a href='rcmobile://sms?number={c_cell}'>SMS</a>", unsafe_allow_html=True)
                    a1.markdown(f"<a href='mailto:{row.get('email','')}'>EMAIL</a>", unsafe_allow_html=True)

                with ce:
                    with st.popover("SỬA"):
                        # FORM ĐẦY ĐỦ 10 TRƯỜNG NHƯ ANH YÊU CẦU
                        with st.form(f"f_ed_{u_key}"):
                            un = st.text_input("Tên", row['name'])
                            ui = st.text_input("ID", row.get('crm_id', ''))
                            ul = st.text_input("Link", row.get('crm_link', ''))
                            uc = st.text_input("Cell", row['cell'])
                            uw = st.text_input("Work", row.get('work', ''))
                            ue = st.text_input("Email", row.get('email', ''))
                            us = st.text_input("State", row.get('state', ''))
                            uo = st.text_input("Owner", row.get('owner', ''))
                            utg = st.text_input("Tags", row.get('tags', ''))
                            st_list = ["New", "Contacted", "Following", "Closed"]
                            ust = st.selectbox("Status", st_list, index=st_list.index(row['status']) if row['status'] in st_list else 0)
                            
                            if st.form_submit_button("CẬP NHẬT"):
                                conn.execute("""UPDATE leads SET 
                                    name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=?, status=?, last_updated=?
                                    WHERE id=?""", (un, ui, ul, uc, uw, ue, us, uo, utg, ust, datetime.now(NY_TZ).isoformat(), row['id']))
                                conn.commit()
                                st.success("Đã cập nhật!")
                                st.rerun()

    with tab_add:
        st.markdown("### NHẬP HỒ SƠ MỚI")
        with st.form("add_new_lead", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            an = c1.text_input("Tên khách hàng")
            ai = c2.text_input("CRM ID")
            al = c3.text_input("CRM Link")
            
            c4, c5, c6 = st.columns(3)
            ac = c4.text_input("Số Cell")
            aw = c5.text_input("Số Work")
            ae = c6.text_input("Email")
            
            c7, c8, c9 = st.columns(3)
            as_ = c7.text_input("Tiểu bang (State)")
            ao = c8.text_input("Người phụ trách (Owner)", value="Cong")
            at = c9.text_input("Thẻ (Tags)")
            
            if st.form_submit_button("LƯU HỒ SƠ MỚI", use_container_width=True):
                if an and ac:
                    try:
                        conn.execute("""INSERT INTO leads (name, crm_id, crm_link, cell, work, email, state, owner, tags, last_updated) 
                                        VALUES (?,?,?,?,?,?,?,?,?,?)""",
                                     (an, ai, al, ac, aw, ae, as_, ao, at, datetime.now(NY_TZ).isoformat()))
                        conn.commit(); st.success("Thêm thành công!"); st.rerun()
                    except: st.error("Số điện thoại này đã tồn tại!")
                else: st.warning("Điền Tên và Số Cell.")
    conn.close()

elif selected == "Cấu Hình":
    st.markdown("<div class='main-card'><h2>CÀI ĐẶT HỆ THỐNG</h2></div>", unsafe_allow_html=True)
    with st.form("config_form"):
        new_slogan = st.text_input("Slogan dòng IUL", value=prof.get('slogan'))
        c1, c2, c3 = st.columns(3)
        up_l = c1.file_uploader("Logo Sidebar", type=["png", "jpg"])
        up_n = c2.file_uploader("Ảnh National Life", type=["png", "jpg"])
        up_i = c3.file_uploader("Ảnh dòng IUL", type=["png", "jpg"])
        if st.form_submit_button("LƯU TẤT CẢ"):
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
            conn.execute("UPDATE profile SET slogan=? WHERE id=1", (new_slogan,))
            conn.commit(); conn.close(); st.success("Đã lưu!"); st.rerun()
