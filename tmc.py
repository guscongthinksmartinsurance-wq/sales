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

# --- 2. SIDEBAR & ĐIỀU HƯỚNG ---
prof = get_profile()

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

# --- 3. VẬN HÀNH ---
if selected == "Vận Hành":
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
                    if dt.tzinfo is None: dt = NY_TZ.localize(dt)
                    return (n_ny - dt).days > 7
                except: return False
            late_count = len(df_m[df_m.apply(is_late, axis=1)])
            st.markdown(f"<div class='db-card'><p style='margin:0; font-weight:1000; color:red;'>TRỄ (>7D)</p><div class='db-num-capsule' style='color:red;'>{late_count}</div></div>", unsafe_allow_html=True)
        with m4: st.markdown(f"<div class='db-card'><p style='margin:0; font-weight:1000; color:blue;'>CHỐT</p><div class='db-num-capsule' style='color:blue;'>{len(df_m[df_m['status'] == 'Closed'])}</div></div>", unsafe_allow_html=True)

        st.divider()
        c_sch, c_sld = st.columns([7, 3])
        q_s = c_sch.text_input("TÌM KIẾM HỒ SƠ...", key="q_search").lower().strip()
        days_limit = c_sld.slider("LỌC KHÁCH TRỄ (NGÀY)", 0, 90, 90) 

        filtered = df_m[df_m.apply(lambda r: q_s in str(r).lower(), axis=1)]

        for idx, row in filtered.iterrows():
            u_key = f"ld_{row['id']}"
            c_cell = clean_phone(row['cell'])
            c_work = clean_phone(row.get('work', ''))
            
            with st.container(border=True):
                ci, ce = st.columns([9.5, 0.5])
                with ci:
                    st.markdown(f"<span class='client-title'>{row['name']}</span> | <a href='{row['crm_link']}' target='_blank'>ID: {row['crm_id']}</a>", unsafe_allow_html=True)
                    st.markdown(f"**TIỂU BANG:** {row['state']} | **OWNER:** {row['owner']} | **STATUS:** {row['status']} | **TAGS:** {row.get('tags', '')}")
                    st.markdown(f"**CELL:** <a href='tel:{c_cell}'>{c_cell}</a> | **WORK:** <a href='tel:{c_work}'>{c_work}</a>", unsafe_allow_html=True)
                    
                    c_act1, c_act2, c_act3 = st.columns([1, 1, 8])
                    c_act1.markdown(f"<a href='rcmobile://sms?number={c_cell}'>SMS</a>", unsafe_allow_html=True)
                    c_act2.markdown(f"<a href='mailto:{row['email']}'>EMAIL</a>", unsafe_allow_html=True)

                with ce:
                    with st.popover("SỬA"):
                        with st.form(f"f_ed_{u_key}"):
                            un = st.text_input("Tên", row['name'])
                            ui = st.text_input("ID", row['crm_id'])
                            ul = st.text_input("Link", row['crm_link'])
                            uc = st.text_input("Cell", row['cell'])
                            uw = st.text_input("Work", row['work'])
                            ue = st.text_input("Email", row['email'])
                            us = st.text_input("State", row['state'])
                            uo = st.text_input("Owner", row['owner'])
                            utg = st.text_input("Tags", row['tags'])
                            st_list = ["New", "Contacted", "Following", "Closed"]
                            ust = st.selectbox("Status", st_list, index=st_list.index(row['status']) if row['status'] in st_list else 0)
                            if st.form_submit_button("CẬP NHẬT"):
                                conn.execute("""UPDATE leads SET name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=?, status=?, last_updated=? WHERE id=?""",
                                             (un, ui, ul, uc, uw, ue, us, uo, utg, ust, datetime.now(NY_TZ).isoformat(), row['id']))
                                conn.commit(); st.rerun()

    with tab_add:
        st.markdown("### NHẬP HỒ SƠ KHÁCH HÀNG MỚI")
        with st.form("add_new_form", clear_on_submit=True):
            r1c1, r1c2, r1c3 = st.columns(3)
            an_name = r1c1.text_input("Tên khách hàng")
            an_id = r1c2.text_input("CRM ID")
            an_link = r1c3.text_input("CRM Link")
            
            r2c1, r2c2, r2c3 = st.columns(3)
            an_cell = r2c1.text_input("Số điện thoại (Cell)")
            an_work = r2c2.text_input("Số làm việc (Work)")
            an_email = r2c3.text_input("Email")
            
            r3c1, r3c2, r3c3 = st.columns(3)
            an_state = r3c1.text_input("Tiểu bang (State)")
            an_owner = r3c2.text_input("Người phụ trách", value="Cong")
            an_tags = r3c3.text_input("Thẻ (Tags)")
            
            if st.form_submit_button("LƯU HỒ SƠ", use_container_width=True):
                if an_name and an_cell:
                    try:
                        conn.execute("""INSERT INTO leads (name, crm_id, crm_link, cell, work, email, state, owner, tags, last_updated) 
                                        VALUES (?,?,?,?,?,?,?,?,?,?)""",
                                     (an_name, an_id, an_link, an_cell, an_work, an_email, an_state, an_owner, an_tags, datetime.now(NY_TZ).isoformat()))
                        conn.commit()
                        st.success(f"Đã thêm thành công!"); st.rerun()
                    except: st.error("Số điện thoại này đã tồn tại!")
                else: st.warning("Vui lòng điền Tên và Số điện thoại.")
    conn.close()

# --- TRANG CHỦ & CẤU HÌNH (GIỮ NGUYÊN) ---
elif selected == "Trang Chủ":
    # Giữ nguyên hàm show_home_page() của anh...
    pass
elif selected == "Cấu Hình":
    # Giữ nguyên phần config_form của anh...
    pass
