import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import urllib.parse
import base64

# --- 1. CẤU HÌNH HỆ THỐNG & CSS SẠCH ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
n_ny = datetime.now(NY_TZ)
DB_NAME = "tmc_database.db"

# CSS Elite: Sửa lỗi đè chữ, giữ Sidebar nguyên bản, hiện PDF chuyên nghiệp
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* Card trang chủ: Hình trên chữ dưới */
    .home-card { background: white; padding: 25px; border-radius: 15px; border-top: 5px solid #00263e; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; margin-bottom: 20px; }
    .slogan-text { color: #64748b; font-size: 15px; margin-top: 15px; }

    /* Card khách hàng Vận hành */
    .client-card { background: white; padding: 25px; border-radius: 16px; border: 1px solid #e2e8f0; margin-bottom: 15px; }
    .action-link { color: #0369a1; text-decoration: none; font-weight: 600; padding: 7px 12px; border-radius: 6px; background: #f1f5f9; font-size: 13px; display: inline-block; margin: 2px; }
    .history-box { background: #fdfdfd; border-radius: 8px; padding: 12px; border-left: 3px solid #cbd5e1; height: 165px; overflow-y: auto; font-size: 14px; line-height: 1.6; }
    
    /* Hiệu ứng nhấp nháy cho Mắt Thần */
    @keyframes blinker { 50% { opacity: 0; } }
    .blink { animation: blinker 1.5s linear infinite; color: #ef4444; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, crm_id TEXT, crm_link TEXT, cell TEXT, work TEXT, email TEXT, state TEXT, owner TEXT, tags TEXT, status TEXT DEFAULT 'New', note TEXT DEFAULT '', last_updated TIMESTAMP, pdf_file BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY, slogan TEXT, logo_app TEXT, img_national TEXT, img_iul TEXT)''')
    # Kiểm tra và thêm cột pdf_file nếu chưa có
    try: c.execute("ALTER TABLE leads ADD COLUMN pdf_file BLOB")
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

# --- 2. TẦNG KHÁCH HÀNG: SOY PDF REAL-TIME ---
id_khach = st.query_params.get("id")
if id_khach:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM leads WHERE cell = ?", (id_khach,)).fetchone()
    if row:
        # Ghi nhận Mắt Thần ngay lập tức
        t_str = n_ny.strftime('[%m/%d %H:%M]')
        new_n = f"<div style='color:red;'>{t_str} 🔥 KHÁCH ĐANG ĐỌC HỒ SƠ PDF</div>" + str(row['note'])
        conn.execute("UPDATE leads SET note=?, last_updated=? WHERE cell=?", (new_n, n_ny.isoformat(), id_khach))
        conn.commit()
        
        st.markdown(f"<h2 style='text-align:center;'>🛡️ Chào mừng {row['name']}</h2>", unsafe_allow_html=True)
        
        if row['pdf_file']:
            base64_pdf = base64.b64encode(row['pdf_file']).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="900" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            st.info("Hồ sơ của bạn đang được cập nhật. Vui lòng quay lại sau.")
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

if selected == "Trang Chủ":
    st.markdown(f"<h2 style='text-align:center; color:#00263e; margin-bottom:30px;'>{prof.get('slogan')}</h2>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("<div class='home-card'><h3>National Life Group</h3></div>", unsafe_allow_html=True)
        if prof.get('img_national'): st.image(prof['img_national'], use_container_width=True)
        st.markdown("<p class='slogan-text'>Uy tín từ 1848 - Giá trị bền vững cho cộng đồng.</p>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='home-card' style='border-top-color:#00a9e0;'><h3>Giải pháp IUL</h3></div>", unsafe_allow_html=True)
        if prof.get('img_iul'): st.image(prof['img_iul'], use_container_width=True)
        st.markdown(f"<p class='slogan-text'>{prof.get('slogan')}</p>", unsafe_allow_html=True)
    
    if not st.session_state.authenticated:
        with st.expander("🔐 QUẢN TRỊ"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.button("ĐĂNG NHẬP"):
                if u == "Cong" and p == "admin123": st.session_state.authenticated = True; st.rerun()

elif selected == "Vận Hành":
    conn = sqlite3.connect(DB_NAME)
    df_m = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    tab_list, tab_add = st.tabs(["📊 DANH SÁCH", "➕ THÊM MỚI"])
    
    with tab_list:
        for idx, row in df_m.iterrows():
            with st.container():
                st.markdown(f"""<div class="client-card">
                    <div style="display: flex; justify-content: space-between;">
                        <div style="flex: 4.8;">
                            <div style="font-size: 20px; font-weight: 700;">{row['name']} | ID: {row['crm_id']}</div>
                            <div style="margin: 10px 0; font-size: 14px; color:#64748b;">📍 {row['state']} | 👤 {row['owner']} | 🏷️ <b>{row['status']}</b></div>
                            <div>
                                <a href="tel:{row['cell']}" class="action-link">📞 Call Cell</a>
                                <a href="mailto:{row['email']}" class="action-link">✉️ Email</a>
                                <a href="https://tmc-elite.streamlit.app/?id={row['cell']}" target="_blank" class="action-link" style="background:#10b981; color:white;">🔗 Link Gửi Khách</a>
                            </div>
                        </div>
                        <div style="flex: 5.2; border-left: 1px solid #e2e8f0; padding-left: 20px;"><div class="history-box">{row['note']}</div></div>
                    </div>
                </div>""", unsafe_allow_html=True)
                
                c_n, c_up, c_s = st.columns([5, 3, 2])
                with c_n:
                    with st.form(key=f"nt_{row['id']}", clear_on_submit=True):
                        ni = st.text_input("Ghi nhanh...", label_visibility="collapsed")
                        if st.form_submit_button("LƯU GHI CHÚ"):
                            t_str = n_ny.strftime('[%m/%d %H:%M]')
                            new_n = f"<div>{t_str} {ni}</div>" + str(row['note'])
                            conn.execute("UPDATE leads SET note=?, last_updated=? WHERE id=?", (new_n, n_ny.isoformat(), row['id']))
                            conn.commit(); st.rerun()
                with c_up:
                    with st.popover("📁 UP MINH HỌA PDF", use_container_width=True):
                        up_pdf = st.file_uploader("Chọn PDF", type="pdf", key=f"f_{row['id']}")
                        if st.button("XÁC NHẬN UP", key=f"b_{row['id']}"):
                            if up_pdf:
                                conn.execute("UPDATE leads SET pdf_file=? WHERE id=?", (up_pdf.read(), row['id']))
                                conn.commit(); st.success("Đã lưu!"); st.rerun()
                with c_s:
                    with st.popover("⚙️ SỬA", use_container_width=True):
                        with st.form(f"ed_{row['id']}"):
                            un = st.text_input("Tên", row['name'])
                            uc = st.text_input("Cell", row['cell'])
                            ust = st.selectbox("Status", ["New", "Contacted", "Following", "Closed"])
                            if st.form_submit_button("CẬP NHẬT"):
                                conn.execute("UPDATE leads SET name=?, cell=?, status=? WHERE id=?", (un, uc, ust, row['id']))
                                conn.commit(); st.rerun()
    conn.close()

elif selected == "Mắt Thần":
    st.markdown("## 👁️ Mắt Thần Real-time")
    conn = sqlite3.connect(DB_NAME)
    df_eye = pd.read_sql("SELECT * FROM leads WHERE note LIKE '%ĐỌC HỒ SƠ PDF%' ORDER BY last_updated DESC", conn)
    for _, row in df_eye.iterrows():
        with st.container(border=True):
            st.markdown(f"Khách **{row['name']}** <span class='blink'>🔥 ĐANG XEM PDF</span>", unsafe_allow_html=True)
            st.write(f"SĐT: {row['cell']} | Owner: {row['owner']}")
            st.markdown(f"<div style='font-size:13px; color:#64748b;'>{row['note']}</div>", unsafe_allow_html=True)
    conn.close()

elif selected == "Cấu Hình":
    # Phần Cấu Hình giữ nguyên để anh Up Logo/Ảnh Hãng
    st.markdown("## ⚙️ Cấu Hình")
    with st.form("config"):
        new_sl = st.text_input("Slogan", value=prof.get('slogan'))
        if st.form_submit_button("LƯU"):
            conn = sqlite3.connect(DB_NAME); conn.execute("UPDATE profile SET slogan=? WHERE id=1", (new_sl,)); conn.commit(); st.rerun()
