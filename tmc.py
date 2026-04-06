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
DB_NAME = "tmc_database.db"

# CSS ĐẶC TRỊ: ẨN MŨI TÊN POPOVER & FIX DÍNH CHỮ
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* Card khách hàng */
    .client-card {
        background: white; padding: 25px; border-radius: 16px;
        border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }

    /* FIX LỖI ĐÈ CHỮ TRONG POPOVER (Ẩn icon mũi tên) */
    button[data-testid="stPopoverTarget"] svg {
        display: none !important;
    }
    button[data-testid="stPopoverTarget"] p {
        font-weight: 700 !important;
        font-size: 13px !important;
        margin: 0 auto !important;
    }

    /* Action Links */
    .action-link {
        color: #0369a1; text-decoration: none; font-weight: 600;
        padding: 8px 15px; border-radius: 8px; background: #f1f5f9;
        font-size: 13px; display: inline-block; margin-right: 5px; margin-bottom: 8px;
    }
    .action-link:hover { background: #0ea5e9; color: white; }
    
    /* Box lịch sử */
    .history-box {
        background: #fdfdfd; border-radius: 8px; padding: 12px;
        border-left: 3px solid #cbd5e1; height: 165px;
        overflow-y: auto; font-size: 14px; line-height: 1.6;
    }

    /* Căn chỉnh khoảng cách trong Form sửa */
    .stTextInput, .stSelectbox { margin-bottom: 5px !important; }
    .section-tag {
        background: #f1f5f9; padding: 4px 10px; border-radius: 4px;
        font-size: 11px; font-weight: 800; color: #475569; margin: 10px 0 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

# (Hàm init_db và get_profile giữ nguyên)
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
    conn.commit(); conn.close()

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
    st.image(prof.get('logo_app') if prof.get('logo_app') and os.path.exists(prof['logo_app']) else "https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    st.divider()
    if 'authenticated' not in st.session_state: st.session_state.authenticated = False
    if st.session_state.authenticated:
        from streamlit_option_menu import option_menu
        selected = option_menu(None, ["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"], styles={"nav-link-selected": {"background-color": "#00263e"}})
        if st.sidebar.button("🚪 ĐĂNG XUẤT", use_container_width=True):
            st.session_state.authenticated = False; st.rerun()
    else: selected = "Trang Chủ"

# --- 3. VẬN HÀNH ---
if selected == "Vận Hành":
    st.markdown("<h2 style='color:#0f172a;'>⚙️ Hệ Thống Vận Hành</h2>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    df_m = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    n_ny = datetime.now(NY_TZ)

    tab_list, tab_add = st.tabs(["📊 QUẢN LÝ DANH SÁCH", "➕ TIẾP NHẬN HỒ SƠ"])

    with tab_list:
        q_s = st.text_input("🔍 Tìm kiếm nhanh...", placeholder="Nhập tên, số điện thoại...")
        filtered = df_m[df_m.apply(lambda r: q_s in str(r).lower(), axis=1)]

        for idx, row in filtered.iterrows():
            u_key = f"ld_{row['id']}"
            c_cell = row['cell'] if row['cell'] else ""
            c_work = row.get('work','') if row.get('work','') else ""
            
            st.markdown(f"""
            <div class="client-card">
                <div style="display: flex; justify-content: space-between;">
                    <div style="flex: 5;">
                        <div style="font-size: 20px; font-weight: 700; color: #0f172a; margin-bottom:10px;">{row['name']} | <a href="{row['crm_link']}" target="_blank" style="text-decoration:none; color:#0ea5e9;">ID: {row['crm_id']}</a></div>
                        <div style="margin-bottom: 15px; font-size: 14px; color:#64748b;">
                            📍 {row['state']} | 👤 {row['owner']} | 🏷️ <b>{row['status']}</b> | 🏷️ <i>{row.get('tags','')}</i>
                        </div>
                        <div>
                            <a href="tel:{c_cell}" class="action-link">📞 {c_cell}</a>
                            <a href="rcmobile://call?number={c_cell}" class="action-link">RC Cell</a>
                            <a href="rcmobile://call?number={c_work}" class="action-link">🏢 Work Call</a>
                        </div>
                        <div style="margin-top:5px;">
                            <a href="rcmobile://sms?number={c_cell}" class="action-link">💬 SMS</a>
                            <a href="mailto:{row['email']}" class="action-link">✉️ Email</a>
                            <a href="https://calendar.google.com/calendar/r/eventedit?text=Meeting_{urllib.parse.quote(str(row['name']))}" target="_blank" class="action-link">📅 Calendar</a>
                        </div>
                    </div>
                    <div style="flex: 5; border-left: 1px solid #e2e8f0; padding-left: 20px;">
                        <div style="font-size: 12px; font-weight: 700; color: #94a3b8; margin-bottom: 8px;">LỊCH SỬ TƯƠNG TÁC</div>
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
                # NÚT SỬA ĐÃ ĐƯỢC FIX LỖI ĐÈ CHỮ
                with st.popover("⚙️ SỬA", use_container_width=True):
                    with st.form(f"f_ed_{u_key}"):
                        st.markdown("<div class='section-tag'>HỒ SƠ CHÍNH</div>", unsafe_allow_html=True)
                        un = st.text_input("Họ tên", row['name'])
                        col_e1, col_e2 = st.columns(2)
                        ui = col_e1.text_input("CRM ID", row['crm_id'])
                        ul = col_e2.text_input("CRM Link", row['crm_link'])
                        
                        st.markdown("<div class='section-tag'>LIÊN LẠC</div>", unsafe_allow_html=True)
                        col_e3, col_e4 = st.columns(2)
                        uc = col_e3.text_input("Số Cell", row['cell'])
                        uw = col_e4.text_input("Số Work", row.get('work',''))
                        ue = st.text_input("Email", row.get('email',''))
                        
                        st.markdown("<div class='section-tag'>PHÂN LOẠI & QUẢN TRỊ</div>", unsafe_allow_html=True)
                        col_e5, col_e6 = st.columns(2)
                        us = col_e5.text_input("Bang (State)", row.get('state',''))
                        uo = col_e6.text_input("Owner", row['owner'])
                        utg = st.text_input("Tags", row.get('tags',''))
                        st_list = ["New", "Contacted", "Following", "Closed"]
                        ust = st.selectbox("Status", st_list, index=st_list.index(row['status']) if row['status'] in st_list else 0)
                        
                        if st.form_submit_button("CẬP NHẬT", use_container_width=True):
                            conn.execute("UPDATE leads SET name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=?, status=?, last_updated=? WHERE id=?", 
                                         (un, ui, ul, uc, uw, ue, us, uo, utg, ust, datetime.now(NY_TZ).isoformat(), row['id']))
                            conn.commit(); st.rerun()

    with tab_add:
        # (Phần thêm hồ sơ 10 trường giữ nguyên bố cục sạch sẽ)
        pass
    conn.close()
# (Các phần khác giữ nguyên)
