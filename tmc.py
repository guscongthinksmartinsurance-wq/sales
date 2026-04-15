import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import urllib.parse
import base64

# --- 1. CẤU HÌNH & CSS ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f1f5f9; }
    
    /* Card Khách hàng */
    .client-card {
        background: white; padding: 20px; border-radius: 12px;
        border: 1px solid #e2e8f0; margin-bottom: 5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .name-link { font-size: 20px; font-weight: 800; color: #00263e !important; text-decoration: none; }
    .id-link { color: #0ea5e9 !important; font-weight: 700; text-decoration: none; }
    
    /* Tabs nội bộ sạch sẽ */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #f8fafc; border-radius: 5px; padding: 5px 15px; border: 1px solid #e2e8f0; font-weight: 600;
    }
    
    /* Nút Copy Link chuyên nghiệp */
    .copy-btn {
        background-color: #10b981; color: white !important; border: none;
        padding: 8px 15px; border-radius: 6px; font-weight: 700; cursor: pointer;
        display: inline-block; font-size: 13px; margin-top: 10px;
    }
    .copy-btn:hover { background-color: #059669; }

    /* Home Card */
    .home-card {
        background: white; border-radius: 20px; overflow: hidden;
        border: 1px solid #e2e8f0; min-height: 520px; text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    .home-img-container { height: 320px; width: 100%; overflow: hidden; }
    .home-img-container img { width: 100%; height: 100%; object-fit: cover; }
    </style>
    
    <script>
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(function() {
            alert('Đã copy đường link PDF! Anh hãy dán vào tin nhắn gửi cho khách nhé.');
        }, function(err) {
            console.error('Không thể copy: ', err);
        });
    }
    </script>
""", unsafe_allow_html=True)

# --- 2. HÀM DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, crm_id TEXT, crm_link TEXT, cell TEXT, work TEXT, email TEXT, state TEXT, owner TEXT, tags TEXT, status TEXT DEFAULT 'New', note TEXT DEFAULT '', last_updated TIMESTAMP, pdf_file BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY, slogan TEXT, logo_app TEXT, img_national TEXT, img_iul TEXT)''')
    c.execute("INSERT OR IGNORE INTO profile (id, slogan) VALUES (1, 'Sâu sắc - Tận tâm - Chuyên nghiệp')")
    conn.commit(); conn.close()

init_db()

@st.cache_data(ttl=300)
def get_prof():
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
    res = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()
    return dict(res) if res else {'slogan': 'Sâu sắc - Tận tâm - Chuyên nghiệp'}

def to_b64(path):
    if path and os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return ""

prof = get_prof()

# --- 3. TẦNG KHÁCH HÀNG (DÀNH CHO KHÁCH NHẬN LINK) ---
id_khach = st.query_params.get("id")
if id_khach:
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM leads WHERE cell = ?", (id_khach,)).fetchone()
    if row:
        t_now = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
        new_n = f"<div>{t_now} 🔥 KHÁCH ĐANG XEM PDF TRỰC TUYẾN</div>" + str(row['note'])
        conn.execute("UPDATE leads SET note=?, last_updated=? WHERE cell=?", (new_n, datetime.now(NY_TZ).isoformat(), id_khach))
        conn.commit()
        if row['pdf_file']:
            st.markdown(f"<h2 style='text-align:center;'>Hồ sơ của: {row['name']}</h2>", unsafe_allow_html=True)
            st.download_button("📂 BẤM ĐỂ MỞ/TẢI FILE PDF MINH HỌA", data=row['pdf_file'], file_name=f"MinhHoa_{row['name']}.pdf", mime="application/pdf", use_container_width=True)
    conn.close(); st.stop()

# --- 4. SIDEBAR QUẢN TRỊ ---
if 'auth' not in st.session_state: st.session_state.auth = False
with st.sidebar:
    logo = prof.get('logo_app')
    st.image(logo if logo and os.path.exists(logo) else "https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    if st.session_state.auth:
        selected = st.radio("QUẢN LÝ", ["Trang Chủ", "Vận Hành", "Mắt Thần", "Cấu Hình"])
        if st.button("🚪 Đăng xuất"): st.session_state.auth = False; st.rerun()
    else: selected = "Trang Chủ"

# --- 5. VẬN HÀNH (BẢN TABS SIÊU SẠCH) ---
if selected == "Vận Hành":
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    t_main1, t_main2 = st.tabs(["📊 DANH SÁCH KHÁCH", "➕ THÊM HỒ SƠ"])
    
    with t_main1:
        for idx, row in df.iterrows():
            with st.container():
                # Thông tin nhúng link trực tiếp
                st.markdown(f"""
                <div class="client-card">
                    <a href="tel:{row['cell']}" class="name-link">👤 {row['name']}</a> <br>
                    <div style="margin-top:8px; font-size:14px; color:#64748b;">
                        Mã CRM: <a href="{row['crm_link']}" target="_blank" class="id-link">{row['crm_id']}</a> | 
                        Cell: <b>{row['cell']}</b> | 
                        Work: <a href="tel:{row['work']}" style="color:#64748b; text-decoration:none;"><b>{row['work']}</b></a>
                    </div>
                    <div style="margin-top:10px; display:flex; gap:20px;">
                        <a href="rcmobile://sms?number={row['cell']}" style="text-decoration:none; font-size:24px;">💬</a>
                        <a href="mailto:{row['email']}" style="text-decoration:none; font-size:24px;">✉️</a>
                        <a href="https://calendar.google.com/calendar/r/eventedit?text=Meeting_{row['name']}" target="_blank" style="text-decoration:none; font-size:24px;">📅</a>
                    </div>
                </div>""", unsafe_allow_html=True)
                
                # HỆ THỐNG TABS KHÔNG CHỒNG CHỮ
                sub_t1, sub_t2, sub_t3 = st.tabs(["📝 GHI CHÚ", "🔗 GỬI PDF CHO KHÁCH", "⚙️ SỬA HỒ SƠ"])
                
                with sub_t1:
                    with st.form(f"nt_{row['id']}", clear_on_submit=True):
                        ni = st.text_input("Ghi chú mới", placeholder="Khách vừa trao đổi gì...")
                        if st.form_submit_button("LƯU"):
                            n_n = f"<div>{datetime.now(NY_TZ).strftime('%H:%M')} {ni}</div>" + str(row['note'])
                            conn.execute("UPDATE leads SET note=? WHERE id=?", (n_n, row['id'])); conn.commit(); st.rerun()
                    st.write(row['note'], unsafe_allow_html=True)
                
                with sub_t2:
                    col_info, col_up = st.columns(2)
                    with col_info:
                        if row['pdf_file']:
                            st.success("✅ ĐÃ CÓ PDF")
                            st.download_button("👁️ XEM FILE (Dành cho anh)", data=row['pdf_file'], file_name=f"Check_{row['name']}.pdf", key=f"v_{row['id']}")
                            # NÚT COPY THỰC THỤ ĐỂ GỬI KHÁCH
                            link_khach = f"https://tmc-elite.streamlit.app/?id={row['cell']}"
                            st.markdown(f"""
                                <button class="copy-btn" onclick="copyToClipboard('{link_khach}')">
                                    🚀 SAO CHÉP LINK GỬI KHÁCH
                                </button>
                                <div style='font-size:11px; color:#94a3b8; margin-top:5px;'>Link: {link_khach}</div>
                            """, unsafe_allow_html=True)
                        else:
                            st.warning("⚠️ CHƯA CÓ FILE")
                    with col_up:
                        f = st.file_uploader("Upload PDF mới", type="pdf", key=f"up_{row['id']}")
                        if st.button("LƯU VÀO DATABASE", key=f"btn_{row['id']}"):
                            if f: conn.execute("UPDATE leads SET pdf_file=? WHERE id=?", (f.read(), row['id'])); conn.commit(); st.success("Xong!"); st.rerun()
                
                with sub_t3:
                    with st.form(f"e_{row['id']}"):
                        ca, cb, cc = st.columns(3)
                        un = ca.text_input("Tên", row['name']); ui = cb.text_input("ID", row['crm_id']); ul = cc.text_input("Link CRM", row['crm_link'])
                        uc = ca.text_input("Cell", row['cell']); uw = cb.text_input("Work", row['work']); ue = cc.text_input("Email", row['email'])
                        us = ca.text_input("State", row['state']); uo = cb.text_input("Owner", row['owner']); ut = cc.text_input("Tags", row['tags'])
                        if st.form_submit_button("CẬP NHẬT 10 TRƯỜNG"):
                            conn.execute("UPDATE leads SET name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=? WHERE id=?", (un, ui, ul, uc, uw, ue, us, uo, ut, row['id'])); conn.commit(); st.rerun()
                st.markdown("---")

    with t_main2:
        with st.form("add"):
            st.markdown("### ➕ THIẾT LẬP HỒ SƠ (10 TRƯỜNG)")
            c1, c2, c3 = st.columns(3)
            an = c1.text_input("Tên"); ai = c2.text_input("ID"); al = c3.text_input("Link")
            ac = c1.text_input("Cell"); aw = c2.text_input("Work"); ae = c3.text_input("Email")
            as_ = c1.text_input("State"); ao = c2.text_input("Owner", value="Cong"); at = c3.text_input("Tags")
            if st.form_submit_button("LƯU MỚI"):
                conn.execute("INSERT INTO leads (name, crm_id, crm_link, cell, work, email, state, owner, tags, last_updated) VALUES (?,?,?,?,?,?,?,?,?,?)", (an, ai, al, ac, aw, ae, as_, ao, at, datetime.now(NY_TZ).isoformat()))
                conn.commit(); st.success("Đã thêm!"); st.rerun()
    conn.close()

# --- TRANG CHỦ & CẤU HÌNH ---
elif selected == "Trang Chủ":
    st.markdown(f"<h1 style='text-align:center; padding:30px;'>{prof.get('slogan')}</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    b_nat = to_b64(prof.get('img_national'))
    b_iul = to_b64(prof.get('img_iul'))
    with c1:
        st.markdown(f"<div class='home-card'><div class='home-img-container'><img src='data:image/jpeg;base64,{b_nat}' onerror='this.src=\"https://via.placeholder.com/600x300\"'></div><div style='padding:25px;'><h3>National Life Group</h3><p>Uy tín từ 1848.</p></div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='home-card'><div class='home-img-container'><img src='data:image/jpeg;base64,{b_iul}' onerror='this.src=\"https://via.placeholder.com/600x300\"'></div><div style='padding:25px;'><h3>Giải pháp IUL</h3><p>{prof.get('slogan')}</p></div></div>", unsafe_allow_html=True)
    if not st.session_state.auth:
        with st.expander("🔐 LOGIN"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.button("OK"):
                if u == "Cong" and p == "admin123": st.session_state.auth = True; st.rerun()

elif selected == "Cấu Hình":
    with st.form("conf"):
        sl = st.text_input("Slogan", value=prof.get('slogan'))
        c1, c2, c3 = st.columns(3); ul = c1.file_uploader("Logo"); un = c2.file_uploader("Ảnh Nat"); ui = c3.file_uploader("Ảnh IUL")
        if st.form_submit_button("LƯU"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("UPDATE profile SET slogan=? WHERE id=1", (sl,))
            if ul: 
                with open("logo_app.png", "wb") as f: f.write(ul.getbuffer())
                conn.execute("UPDATE profile SET logo_app='logo_app.png' WHERE id=1")
            if un: 
                with open("img_nat.jpg", "wb") as f: f.write(un.getbuffer())
                conn.execute("UPDATE profile SET img_national='img_nat.jpg' WHERE id=1")
            if ui: 
                with open("img_iul.jpg", "wb") as f: f.write(ui.getbuffer())
                conn.execute("UPDATE profile SET img_iul='img_iul.jpg' WHERE id=1")
            conn.commit(); conn.close(); st.cache_data.clear(); st.rerun()

elif selected == "Mắt Thần":
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql("SELECT * FROM leads WHERE note LIKE '%ĐANG XEM%' ORDER BY last_updated DESC LIMIT 15", conn)
    for _, row in df.iterrows():
        st.error(f"🔥 Khách {row['name']} đang xem hồ sơ!")
    conn.close()
