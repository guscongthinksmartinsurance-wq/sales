import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import urllib.parse

# --- 1. CẤU HÌNH HỆ THỐNG & CSS (FIX LỖI POPOVER & TẨY PHÈN) ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* Card khách hàng Elite */
    .client-card {
        background: white; padding: 24px; border-radius: 16px;
        border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
    }
    .client-title { font-size: 19px; font-weight: 700; color: #0f172a; }
    
    /* Dashboard Chỉ số */
    .db-card {
        background: white; padding: 20px; border-radius: 12px;
        border-top: 4px solid #00263e; text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .db-num { font-size: 32px; font-weight: 800; color: #1e293b; }

    /* Nút bấm thực chiến (Link RC, SMS, Email) */
    .action-link {
        color: #0369a1; text-decoration: none; font-weight: 600;
        padding: 6px 12px; border-radius: 6px; background: #f1f5f9;
        font-size: 13px; display: inline-block; margin: 2px;
    }
    .action-link:hover { background: #0ea5e9; color: white; }
    
    /* Lịch sử tương tác */
    .history-box {
        background: #fdfdfd; border-radius: 8px; padding: 12px;
        border-left: 3px solid #cbd5e1; height: 160px;
        overflow-y: auto; font-size: 14px; line-height: 1.6;
    }

    /* FIX LỖI ĐÈ CHỮ & MŨI TÊN Ở NÚT SỬA */
    button[data-testid="stPopoverTarget"] svg { display: none !important; }
    button[data-testid="stPopoverTarget"] p { font-weight: 700 !important; font-size: 13px !important; margin: 0 auto !important; }
    
    /* Khoảng cách trong Form sửa */
    .stTextInput, .stSelectbox { margin-bottom: 5px !important; }
    </style>
""", unsafe_allow_html=True)

def clean_phone(p):
    return str(p).replace(".0", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

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
    # Kiểm tra cột thiếu
    for col in [('crm_link', 'TEXT'), ('work', 'TEXT'), ('email', 'TEXT'), ('tags', 'TEXT'), ('last_updated', 'TEXT')]:
        try: c.execute(f"ALTER TABLE leads ADD COLUMN {col[0]} {col[1]}")
        except: pass
    conn.commit(); conn.close()

init_db()

# --- 2. SIDEBAR ---
conn = sqlite3.connect(DB_NAME)
prof_df = pd.read_sql("SELECT * FROM profile WHERE id=1", conn)
prof = prof_df.to_dict('records')[0] if not prof_df.empty else {'slogan': 'Sâu sắc - Tận tâm'}
conn.close()

with st.sidebar:
    st.image(prof.get('logo_app') if prof.get('logo_app') and os.path.exists(prof['logo_app']) else "https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    st.divider()
    if 'authenticated' not in st.session_state: st.session_state.authenticated = False
    if st.session_state.authenticated:
        from streamlit_option_menu import option_menu
        selected = option_menu(None, ["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"], styles={"nav-link-selected": {"background-color": "#00263e"}})
        if st.sidebar.button("ĐĂNG XUẤT", use_container_width=True):
            st.session_state.authenticated = False; st.rerun()
    else: selected = "Trang Chủ"

# --- 3. VẬN HÀNH (DỰA TRÊN CODE CHUẨN CỦA ANH) ---
if selected == "Vận Hành":
    st.markdown("<h2 style='color:#0f172a;'>Hệ Thống Điều Hành Lead</h2>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    df_m = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    n_ny = datetime.now(NY_TZ)

    def get_days(val):
        try:
            dt = datetime.fromisoformat(str(val))
            return (n_ny - (NY_TZ.localize(dt) if dt.tzinfo is None else dt)).days
        except: return 0
    df_m['days_diff'] = df_m['last_updated'].apply(get_days)

    # Dashboard 4 chỉ số
    d1, d2, d3, d4 = st.columns(4)
    d1.markdown(f"<div class='db-card'><p>TỔNG LEAD</p><div class='db-num'>{len(df_m)}</div></div>", unsafe_allow_html=True)
    d2.markdown(f"<div class='db-card' style='border-top-color:green;'><p>MỚI</p><div class='db-num'>{len(df_m[df_m['status'] == 'New'])}</div></div>", unsafe_allow_html=True)
    d3.markdown(f"<div class='db-card' style='border-top-color:red;'><p>TRỄ (>7D)</p><div class='db-num' style='color:red;'>{len(df_m[df_m['days_diff'] > 7])}</div></div>", unsafe_allow_html=True)
    d4.markdown(f"<div class='db-card' style='border-top-color:#0369a1;'><p>ĐÃ CHỐT</p><div class='db-num'>{len(df_m[df_m['status'] == 'Closed'])}</div></div>", unsafe_allow_html=True)

    tab_list, tab_add = st.tabs(["📊 QUẢN LÝ DANH SÁCH", "➕ TIẾP NHẬN HỒ SƠ"])

    with tab_list:
        c_sch, c_sld = st.columns([7, 3])
        q_s = c_sch.text_input("🔍 Tìm kiếm lead...", placeholder="Tên, số điện thoại, bang...")
        days_limit = c_sld.slider("⏳ Lọc khách trễ (ngày)", 0, 90, 90)

        filtered = df_m[(df_m.apply(lambda r: q_s in str(r).lower(), axis=1)) & (df_m['days_diff'] <= days_limit)]

        for idx, row in filtered.iterrows():
            u_key = f"ld_{row['id']}"
            c_cell = clean_phone(row['cell'])
            c_work = clean_phone(row.get('work', ''))
            
            with st.container():
                st.markdown(f"""
                <div class="client-card">
                    <div style="display: flex; justify-content: space-between;">
                        <div style="flex: 4.5;">
                            <div class="client-title">{row['name']} | <a href="{row['crm_link']}" target="_blank" style="text-decoration:none;">🆔 {row['crm_id']}</a></div>
                            <div style="margin: 8px 0; font-size: 14px; color:#475569;">
                                📍 {row['state']} | 👤 {row['owner']} | 🏷️ <b>{row['status']}</b> | 🏷️ <i>{row.get('tags','')}</i>
                            </div>
                            <div style="margin-top:12px;">
                                <a href="tel:{c_cell}" class="action-link">📞 {c_cell}</a>
                                <a href="rcmobile://call?number={c_cell}" class="action-link">RC Cell</a>
                                <a href="rcmobile://call?number={c_work}" class="action-link">🏢 Work: {c_work}</a>
                            </div>
                            <div style="margin-top:8px;">
                                <a href="rcmobile://sms?number={c_cell}" class="action-link">💬 SMS</a>
                                <a href="mailto:{row['email']}" class="action-link">✉️ Email</a>
                                <a href="https://calendar.google.com/calendar/r/eventedit?text=Meeting_{urllib.parse.quote(row['name'])}" target="_blank" class="action-link">📅 Calendar</a>
                            </div>
                        </div>
                        <div style="flex: 5.5; border-left: 1px solid #e2e8f0; padding-left: 20px;">
                            <div style="font-size: 12px; font-weight: 700; color: #94a3b8; margin-bottom: 5px;">LỊCH SỬ TƯƠNG TÁC</div>
                            <div class="history-box">{row['note']}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                c_act1, c_act2 = st.columns([8.5, 1.5])
                with c_act1:
                    with st.form(key=f"nt_{u_key}", clear_on_submit=True):
                        ni = st.text_input("Ghi nhanh...", label_visibility="collapsed")
                        if st.form_submit_button("LƯU"):
                            t_str = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
                            new_note = f"<div class='history-entry'><span class='note-time'>{t_str}</span> {ni}</div>" + str(row['note'])
                            conn.execute("UPDATE leads SET note=?, last_updated=? WHERE id=?", (new_note, datetime.now(NY_TZ).isoformat(), row['id']))
                            conn.commit(); st.rerun()
                with c_act2:
                    with st.popover("⚙️ SỬA"):
                        with st.form(f"f_ed_{u_key}"):
                            un = st.text_input("Tên", row['name']); ui = st.text_input("ID", row['crm_id'])
                            ul = st.text_input("Link", row['crm_link']); uc = st.text_input("Cell", row['cell'])
                            uw = st.text_input("Work", row.get('work','')); ue = st.text_input("Email", row.get('email',''))
                            us = st.text_input("State", row.get('state','')); uo = st.text_input("Owner", row['owner'])
                            utg = st.text_input("Tags", row.get('tags',''))
                            st_list = ["New", "Contacted", "Following", "Closed"]
                            ust = st.selectbox("Status", st_list, index=st_list.index(row['status']) if row['status'] in st_list else 0)
                            if st.form_submit_button("CẬP NHẬT"):
                                conn.execute("UPDATE leads SET name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=?, status=?, last_updated=? WHERE id=?", 
                                             (un, ui, ul, uc, uw, ue, us, uo, utg, ust, datetime.now(NY_TZ).isoformat(), row['id']))
                                conn.commit(); st.rerun()

    with tab_add:
        st.markdown("### NHẬP HỒ SƠ KHÁCH HÀNG MỚI (10 TRƯỜNG)")
        with st.form("add_new_lead", clear_on_submit=True):
            r1 = st.columns(3); an = r1[0].text_input("Họ và Tên"); ai = r1[1].text_input("CRM ID"); al = r1[2].text_input("CRM Link")
            r2 = st.columns(3); ac = r2[0].text_input("Số Cell"); aw = r2[1].text_input("Số Work"); ae = r2[2].text_input("Email")
            r3 = st.columns(3); as_ = r3[0].text_input("Tiểu bang"); ao = r3[1].text_input("Owner", value="Cong"); at = r3[2].text_input("Tags")
            ast = st.selectbox("Trạng thái", ["New", "Contacted", "Following", "Closed"])
            if st.form_submit_button("LƯU HỒ SƠ MỚI", use_container_width=True):
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
    if not st.session_state.authenticated:
        with st.expander("🔐 QUẢN TRỊ"):
            u = st.text_input("User", key="u_h"); p = st.text_input("Pass", type="password", key="p_h")
            if st.button("VÀO"):
                if u == "Cong" and p == "admin123": st.session_state.authenticated = True; st.rerun()

elif selected == "Mắt Thần":
    st.markdown("<h2>👁️ Theo dõi Real-time</h2>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    df_eye = pd.read_sql("SELECT * FROM leads WHERE note LIKE '%KHÁCH ĐANG XEM%' ORDER BY last_updated DESC", conn)
    for _, row in df_eye.iterrows():
        with st.container(border=True):
            st.write(f"Khách: **{row['name']}** ({row['cell']})"); st.markdown(row['note'], unsafe_allow_html=True)
    conn.close()

elif selected == "Cấu Hình":
    st.markdown("<h2>⚙️ Cấu Hình</h2>", unsafe_allow_html=True)
    with st.form("config"):
        new_sl = st.text_input("Slogan", value=prof.get('slogan'))
        c1, c2, c3 = st.columns(3); up_l = c1.file_uploader("Logo"); up_n = c2.file_uploader("Ảnh Nat"); up_i = c3.file_uploader("Ảnh IUL")
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
            conn.execute("UPDATE profile SET slogan=? WHERE id=1", (new_sl,))
            conn.commit(); conn.close(); st.success("Đã lưu!"); st.rerun()
