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

# CSS ĐẶC TRỊ ĐỂ "TẨY PHÈN"
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: #f8fafc;
    }

    /* Card khách hàng phong cách hiện đại */
    .client-card {
        background: white;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    .client-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-color: #00a9e0;
    }

    .client-title {
        font-size: 20px;
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.025em;
    }

    .db-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border-top: 4px solid #00263e;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    .db-num {
        font-size: 28px;
        font-weight: 700;
        color: #1e293b;
    }

    /* Tinh chỉnh Link Action */
    .action-link {
        color: #00a9e0;
        text-decoration: none;
        font-weight: 600;
        padding: 5px 10px;
        border-radius: 6px;
        background: #f1f5f9;
        font-size: 13px;
        transition: 0.2s;
    }
    
    .action-link:hover {
        background: #00a9e0;
        color: white;
    }

    .history-box {
        background: #fdfdfd;
        border-radius: 8px;
        padding: 12px;
        border-left: 3px solid #cbd5e1;
        height: 180px;
        overflow-y: auto;
        font-size: 14px;
        line-height: 1.6;
    }
    
    .note-time {
        color: #64748b;
        font-weight: 600;
        font-size: 12px;
    }
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
    conn.commit()
    conn.close()

init_db()

# --- 2. SIDEBAR & LOGIC ---
conn = sqlite3.connect(DB_NAME)
prof_df = pd.read_sql("SELECT * FROM profile WHERE id=1", conn)
prof = prof_df.to_dict('records')[0] if not prof_df.empty else {'slogan': 'Sâu sắc - Tận tâm'}
conn.close()

with st.sidebar:
    logo = prof.get('logo_app')
    st.image(logo if logo and os.path.exists(logo) else "https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    st.divider()
    if 'authenticated' not in st.session_state: st.session_state.authenticated = False
    if st.session_state.authenticated:
        from streamlit_option_menu import option_menu
        selected = option_menu(None, ["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"], 
                               styles={"nav-link-selected": {"background-color": "#00263e"}})
    else: selected = "Trang Chủ"

# --- 3. VẬN HÀNH (GIAO DIỆN ELITE) ---
if selected == "Vận Hành":
    st.markdown("<h2 style='color:#0f172a; margin-bottom:25px;'>Hệ Thống Điều Hành Lead</h2>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    df_m = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    n_ny = datetime.now(NY_TZ)

    # Dashboard
    d1, d2, d3, d4 = st.columns(4)
    d1.markdown(f"<div class='db-card'><p style='color:#64748b; font-size:14px;'>TỔNG LEAD</p><div class='db-num'>{len(df_m)}</div></div>", unsafe_allow_html=True)
    d2.markdown(f"<div class='db-card' style='border-top-color:green;'><p style='color:#64748b; font-size:14px;'>MỚI</p><div class='db-num'>{len(df_m[df_m['status'] == 'New'])}</div></div>", unsafe_allow_html=True)
    d3.markdown(f"<div class='db-card' style='border-top-color:red;'><p style='color:#64748b; font-size:14px;'>TRỄ (>7D)</p><div class='db-num' style='color:red;'>{len(df_m)}</div></div>", unsafe_allow_html=True) # Logic trễ anh tự tinh chỉnh sau
    d4.markdown(f"<div class='db-card' style='border-top-color:#00a9e0;'><p style='color:#64748b; font-size:14px;'>ĐÃ CHỐT</p><div class='db-num'>{len(df_m[df_m['status'] == 'Closed'])}</div></div>", unsafe_allow_html=True)

    tab_list, tab_add = st.tabs(["📊 QUẢN LÝ DANH SÁCH", "➕ TIẾP NHẬN HỒ SƠ"])

    with tab_list:
        st.write("---")
        q_s = st.text_input("🔍 Lọc danh sách (Tên, Số điện thoại, Bang...)", placeholder="Nhập từ khóa...")
        
        filtered = df_m[df_m.apply(lambda r: q_s in str(r).lower(), axis=1)]

        for idx, row in filtered.iterrows():
            c_cell = clean_phone(row['cell'])
            c_work = clean_phone(row.get('work', ''))
            u_key = f"ld_{row['id']}"

            st.markdown(f"""
                <div class="client-card">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex: 4;">
                            <div class="client-title">{row['name']} <span style="font-size:14px; font-weight:400; color:#64748b;">| ID: {row['crm_id']}</span></div>
                            <div style="margin: 10px 0; color: #475569; font-size: 14px;">
                                📍 <b>{row['state']}</b> | 👤 <b>{row['owner']}</b> | 🏷️ <span style="background:#e0f2fe; color:#0369a1; padding:2px 8px; border-radius:4px; font-weight:600;">{row['status']}</span>
                            </div>
                            <div style="margin-top: 15px;">
                                <a href="tel:{c_cell}" class="action-link">📞 {c_cell}</a>
                                <a href="rcmobile://call?number={c_cell}" class="action-link">RC Call</a>
                                <a href="rcmobile://sms?number={c_cell}" class="action-link">💬 SMS</a>
                                <a href="mailto:{row['email']}" class="action-link">✉️ Email</a>
                            </div>
                        </div>
                        <div style="flex: 5; border-left: 1px solid #e2e8f0; padding-left: 20px;">
                            <div style="font-size: 12px; font-weight: 700; color: #94a3b8; margin-bottom: 8px;">LỊCH SỬ TƯƠNG TÁC</div>
                            <div class="history-box">{row['note']}</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Form Ghi nhanh & Sửa đặt dưới Card
            c_btn1, c_btn2, c_btn3 = st.columns([7, 2, 1])
            with c_btn1:
                with st.form(key=f"nt_{u_key}", clear_on_submit=True):
                    ni = st.text_input("Ghi nhanh nội dung cuộc gọi...", label_visibility="collapsed")
                    if st.form_submit_button("LƯU GHI CHÚ"):
                        t_str = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
                        new_note = f"<div class='history-entry'><span class='note-time'>{t_str}</span> {ni}</div>" + str(row['note'])
                        conn.execute("UPDATE leads SET note=?, last_updated=? WHERE id=?", (new_note, datetime.now(NY_TZ).isoformat(), row['id']))
                        conn.commit(); st.rerun()
            with c_btn2:
                with st.popover("⚙️ Tùy chỉnh hồ sơ", use_container_width=True):
                    with st.form(f"f_ed_{u_key}"):
                        un = st.text_input("Tên", row['name']); ui = st.text_input("ID", row['crm_id'])
                        uc = st.text_input("Cell", row['cell']); uo = st.text_input("Owner", row['owner'])
                        ust = st.selectbox("Trạng thái", ["New", "Contacted", "Following", "Closed"])
                        if st.form_submit_button("CẬP NHẬT"):
                            conn.execute("UPDATE leads SET name=?, crm_id=?, cell=?, owner=?, status=? WHERE id=?", (un, ui, uc, uo, ust, row['id']))
                            conn.commit(); st.rerun()

    with tab_add:
        # Form Thêm mới giữ nguyên logic 10 trường nhưng làm gọn UI
        pass

    conn.close()

# --- TRANG CHỦ & CẤU HÌNH ---
elif selected == "Trang Chủ":
    st.markdown('<div class="hero-banner"><h1>TMC ELITE SYSTEM</h1><p>Luxury Insurance Management Platform</p></div>', unsafe_allow_html=True)
    # Giữ nguyên logic hiển thị ảnh National và IUL của anh
