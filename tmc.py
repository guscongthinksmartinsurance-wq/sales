import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import urllib.parse

# --- 1. CẤU HÌNH & CSS ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

try:
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except: pass

def clean_phone(p):
    return str(p).replace(".0", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

def format_note_for_edit(note_html):
    if not note_html: return ""
    return note_html.replace("<div class='history-entry'>", "").replace("</div>", "\n").replace("<span class='note-time'>", "").replace("</span>", "").strip()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, crm_id TEXT, crm_link TEXT,
                    cell TEXT, work TEXT, email TEXT,
                    state TEXT, owner TEXT, tags TEXT,
                    status TEXT DEFAULT 'New', note TEXT DEFAULT '', 
                    last_updated TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY, slogan TEXT, logo_app TEXT, img_national TEXT, img_iul TEXT)''')
    # Bổ sung các cột nếu thiếu
    full_cols = [('crm_link', 'TEXT'), ('work', 'TEXT'), ('email', 'TEXT'), ('tags', 'TEXT')]
    for col, ctype in full_cols:
        try: c.execute(f"ALTER TABLE leads ADD COLUMN {col} {ctype}")
        except: pass
    conn.commit()
    conn.close()

init_db()

# --- 2. SIDEBAR & MENU ---
conn = sqlite3.connect(DB_NAME)
prof = pd.read_sql("SELECT * FROM profile WHERE id=1", conn).to_dict('records')[0] if not pd.read_sql("SELECT * FROM profile WHERE id=1", conn).empty else {'slogan': 'Sâu sắc - Tận tâm'}
conn.close()

with st.sidebar:
    logo = prof.get('logo_app')
    st.image(logo if logo and os.path.exists(logo) else "https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    st.divider()
    if 'authenticated' not in st.session_state: st.session_state.authenticated = False
    if st.session_state.authenticated:
        from streamlit_option_menu import option_menu
        selected = option_menu(None, ["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"], styles={"nav-link-selected": {"background-color": "#00263e"}})
        if st.sidebar.button("ĐĂNG XUẤT", use_container_width=True):
            st.session_state.authenticated = False; st.rerun()
    else: selected = "Trang Chủ"

# --- 3. VẬN HÀNH (GIAO DIỆN CHUẨN ANH CÔNG) ---
if selected == "Vận Hành":
    st.markdown("<div class='main-card'><h2>HỆ THỐNG VẬN HÀNH DỮ LIỆU</h2></div>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    df_m = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    n_ny = datetime.now(NY_TZ)

    tab_list, tab_add = st.tabs(["DANH SÁCH LEAD", "THÊM MỚI HỒ SƠ"])

    with tab_list:
        # Dashboard số liệu
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f"<div class='db-card'><p>TỔNG LEAD</p><div class='db-num-capsule'>{len(df_m)}</div></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='db-card'><p style='color:green;'>MỚI</p><div class='db-num-capsule'>{len(df_m[df_m['status'] == 'New'])}</div></div>", unsafe_allow_html=True)
        with m3:
            def is_late(r):
                try: 
                    dt = datetime.fromisoformat(r['last_updated'])
                    return (n_ny - (NY_TZ.localize(dt) if dt.tzinfo is None else dt)).days > 7
                except: return False
            st.markdown(f"<div class='db-card'><p style='color:red;'>TRỄ (>7D)</p><div class='db-num-capsule' style='color:red;'>{len(df_m[df_m.apply(is_late, axis=1)])}</div></div>", unsafe_allow_html=True)
        with m4: st.markdown(f"<div class='db-card'><p style='color:blue;'>CHỐT</p><div class='db-num-capsule'>{len(df_m[df_m['status'] == 'Closed'])}</div></div>", unsafe_allow_html=True)

        st.divider()
        c_sch, c_sld = st.columns([7, 3])
        q_s = c_sch.text_input("🔍 Tìm kiếm lead...", key="q_v").lower().strip()
        days_limit = c_sld.slider("⏳ Lọc khách trễ (ngày)", 0, 90, 90)

        filtered = df_m[df_m.apply(lambda r: q_s in str(r).lower(), axis=1)]

        for idx, row in filtered.iterrows():
            u_key = f"ld_{row['id']}"
            c_cell = clean_phone(row['cell'])
            c_work = clean_phone(row.get('work', ''))
            
            with st.container(border=True):
                ci, cn, ce = st.columns([4.2, 5.3, 0.5])
                
                # Cột 1: Thông tin & Link RC (ĐÚNG CHUẨN ANH CẦN)
                with ci:
                    st.markdown(f"<span class='client-title'>{row['name']}</span> | <a href='{row['crm_link']}' target='_blank'>🆔 {row['crm_id']}</a>", unsafe_allow_html=True)
                    st.markdown(f"📍 {row['state']} | 👤 {row['owner']} | 🏷️ **{row['status']}** | 🏷️ *{row.get('tags', '')}*")
                    st.markdown(f"📱 <a href='tel:{c_cell}'>{c_cell}</a> (<a href='rcmobile://call?number={c_cell}'>RC</a>) | 🏢 <a href='tel:{c_work}'>{c_work}</a> (<a href='rcmobile://call?number={c_work}'>RC</a>)", unsafe_allow_html=True)
                    
                    # Dàn nút bấm SMS, Email, Calendar
                    a1, a2, a3, a4 = st.columns([1,1,1,7])
                    a1.markdown(f"<a href='rcmobile://sms?number={c_cell}' class='action-icon'>💬</a>", unsafe_allow_html=True)
                    a2.markdown(f"<a href='mailto:{row['email']}' class='action-icon'>✉️</a>", unsafe_allow_html=True)
                    a3.markdown(f"<a href='https://calendar.google.com/calendar/r/eventedit?text=Meeting_{urllib.parse.quote(row['name'])}' target='_blank' class='action-icon'>📅</a>", unsafe_allow_html=True)

                # Cột 2: Lịch sử & Ghi nhanh
                with cn:
                    st.markdown(f'<div class="history-container">{row["note"]}</div>', unsafe_allow_html=True)
                    c_n1, c_n2 = st.columns([8.5, 1.5])
                    with c_n1:
                        with st.form(key=f"f_nt_{u_key}", clear_on_submit=True):
                            ni = st.text_input("Ghi nhanh...", label_visibility="collapsed", key=f"in_{u_key}")
                            if st.form_submit_button("Lưu"):
                                t_str = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
                                new_note = f"<div class='history-entry'><span class='note-time'>{t_str}</span> {ni}</div>" + str(row['note'])
                                conn.execute("UPDATE leads SET note=?, last_updated=? WHERE id=?", (new_note, datetime.now(NY_TZ).isoformat(), row['id']))
                                conn.commit(); st.rerun()
                    with c_n2:
                        with st.popover("📝"):
                            en = st.text_area("Sửa History", value=format_note_for_edit(row['note']), height=250, key=f"area_{u_key}")
                            if st.button("Lưu lại", key=f"ed_note_{u_key}"):
                                fmt = "".join([f"<div class='history-entry'>{line.strip()}</div>" for line in en.split('\n') if line.strip()])
                                conn.execute("UPDATE leads SET note=? WHERE id=?", (fmt, row['id']))
                                conn.commit(); st.rerun()

                # Cột 3: Cài đặt (10 trường)
                with ce:
                    with st.popover("⚙️"):
                        with st.form(f"f_ed_{u_key}"):
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
        with st.form("add_new_10", clear_on_submit=True):
            st.markdown("### NHẬP HỒ SƠ MỚI")
            r1 = st.columns(3); an = r1[0].text_input("Họ và Tên"); ai = r1[1].text_input("CRM ID"); al = r1[2].text_input("CRM Link")
            r2 = st.columns(3); ac = r2[0].text_input("Số Cell"); aw = r2[1].text_input("Số Work"); ae = r2[2].text_input("Email")
            r3 = st.columns(3); as_ = r3[0].text_input("State"); ao = r3[1].text_input("Owner", value="Cong"); at = r3[2].text_input("Tags")
            ast = st.selectbox("Status", ["New", "Contacted", "Following", "Closed"])
            if st.form_submit_button("LƯU HỒ SƠ", use_container_width=True):
                if an and ac:
                    conn.execute("INSERT INTO leads (name, crm_id, crm_link, cell, work, email, state, owner, tags, status, last_updated) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                 (an, ai, al, ac, aw, ae, as_, ao, at, ast, datetime.now(NY_TZ).isoformat()))
                    conn.commit(); st.success("Thành công!"); st.rerun()

    conn.close()

# --- TRANG CHỦ & CẤU HÌNH (GIỮ NGUYÊN) ---
elif selected == "Trang Chủ":
    st.markdown('<div class="hero-banner"><h1>NATIONAL LIFE GROUP</h1><p>Since 1848</p></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown('<div class="main-card"><h3>National Life Group</h3></div>', unsafe_allow_html=True)
        if prof.get('img_national'): st.image(prof['img_national'], use_container_width=True)
    with c2:
        st.markdown('<div class="main-card"><h3>Giải pháp IUL</h3><p>'+prof.get('slogan','')+'</p></div>', unsafe_allow_html=True)
        if prof.get('img_iul'): st.image(prof['img_iul'], use_container_width=True)

elif selected == "Cấu Hình":
    st.markdown("<div class='main-card'><h2>CÀI ĐẶT</h2></div>", unsafe_allow_html=True)
    with st.form("config"):
        new_sl = st.text_input("Slogan", value=prof.get('slogan'))
        c1, c2, c3 = st.columns(3)
        up_l = c1.file_uploader("Logo Sidebar"); up_n = c2.file_uploader("Ảnh National"); up_i = c3.file_uploader("Ảnh IUL")
        if st.form_submit_button("LƯU"):
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
            conn.commit(); conn.close(); st.success("Đã lưu!"); st.rerun()
