import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import io

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="TMC Financial System", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

# Kết nối CSS
try:
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except:
    pass

# Khởi tạo Database SQLite
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT UNIQUE,
                    state TEXT,
                    status TEXT DEFAULT 'New',
                    owner TEXT,
                    note TEXT DEFAULT '',
                    last_updated TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# =========================================================
# TẦNG 2: TRANG KHÁCH HÀNG (Nhận diện qua ?id=...)
# =========================================================
def show_customer_page(phone_id):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql(f"SELECT * FROM leads WHERE phone = '{phone_id}'", conn)
    
    if not df.empty:
        row = df.iloc[0]
        # MẮT THẦN: Ghi log khi khách xem
        t_now = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
        view_log = f"<div class='history-entry'><span class='note-time'>{t_now}</span> <span style='color:#f57c00; font-weight:bold;'>🔥 KHÁCH VỪA XEM LINK</span></div>"
        
        if "KHÁCH VỪA XEM LINK" not in str(row['note'])[:150]:
            new_note = view_log + str(row['note'])
            conn.execute("UPDATE leads SET note = ?, last_updated = ? WHERE phone = ?", 
                         (new_note, datetime.now(NY_TZ).isoformat(), phone_id))
            conn.commit()

        # Giao diện sạch đẹp cho khách
        st.markdown(f"<h1 style='color:#0056D2;'>🛡️ Chào {row['name']}</h1>", unsafe_allow_html=True)
        st.divider()
        st.subheader("Giải Pháp Bảo Vệ Tài Chính IUL")
        st.info("Kế hoạch tài chính của chị đang được hiển thị an toàn. Em Công sẽ gọi lại hỗ trợ chị sớm.")
        # Chỗ này anh có thể thêm ảnh minh họa (Illustration)
    else:
        st.error("Liên kết không đúng hoặc đã hết hạn.")
    conn.close()

# =========================================================
# TẦNG 3: TRANG ADMIN & STAFF (Quản lý nội bộ)
# =========================================================
def show_admin_page():
    st.markdown(f"<h1 style='color:#0056D2;'>🚀 QUẢN TRỊ HỆ THỐNG - {st.session_state.username}</h1>", unsafe_allow_html=True)
    
    conn = sqlite3.connect(DB_NAME)
    
    # --- FORM THÊM LEAD MỚI ---
    with st.expander("➕ THÊM KHÁCH HÀNG MỚI", expanded=False):
        with st.form("add_lead"):
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("Tên khách")
            p = c2.text_input("Số điện thoại (ID)")
            s = c3.text_input("Tiểu bang")
            ow = st.selectbox("Người quản lý", ["Cong", "Sale1", "Sale2"])
            if st.form_submit_button("LƯU HỒ SƠ"):
                if n and p:
                    try:
                        conn.execute("INSERT INTO leads (name, phone, state, owner) VALUES (?,?,?,?)", (n,p,s,ow))
                        conn.commit()
                        st.success("Đã thêm thành công!")
                        st.rerun()
                    except: st.error("Số điện thoại này đã có trong hệ thống!")

    # --- DANH SÁCH LEADS ---
    df = pd.read_sql("SELECT * FROM leads", conn)
    if st.session_state.role != "Admin":
        df = df[df['owner'] == st.session_state.username]

    q = st.text_input("🔍 Tìm kiếm nhanh...", placeholder="Nhập tên hoặc số điện thoại")
    
    for idx, row in df.iterrows():
        if q.lower() in row['name'].lower() or q in str(row['phone']):
            with st.container(border=True):
                col1, col2, col3 = st.columns([4, 4, 2])
                with col1:
                    st.markdown(f"### {row['name']}")
                    st.write(f"📞 {row['phone']} | 📍 {row['state']}")
                    t_link = f"https://the-nexus.streamlit.app/?id={row['phone']}"
                    st.code(t_link, language=None)
                with col2:
                    st.markdown(f"<div style='height:100px; overflow-y:auto; background:#f8fafd; padding:10px; border-radius:10px; border:1px solid #ddd;'>{row['note']}</div>", unsafe_allow_html=True)
                with col3:
                    msg = st.text_input("Ghi chú", key=f"m_{row['id']}", label_visibility="collapsed")
                    if st.button("Lưu", key=f"b_{row['id']}", use_container_width=True):
                        t_str = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
                        up_note = f"<div class='history-entry'><span class='note-time'>{t_str}</span> {msg}</div>" + row['note']
                        conn.execute("UPDATE leads SET note = ? WHERE id = ?", (up_note, row['id']))
                        conn.commit()
                        st.rerun()
                    if st.button("🗑️", key=f"d_{row['id']}"):
                        conn.execute("DELETE FROM leads WHERE id = ?", (row['id'],))
                        conn.commit()
                        st.rerun()
    conn.close()

# =========================================================
# TẦNG 1: TRANG CHỦ (GIỚI THIỆU & ĐĂNG NHẬP)
# =========================================================
def show_home_page():
    st.markdown("<h1 style='text-align:center; color:#0056D2; margin-top:50px;'>TMC FINANCIAL SYSTEM</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:1.2em;'>Giải pháp bảo vệ tài chính thông minh của National Life Group</p>", unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.subheader("🔑 Đăng nhập")
        u = st.text_input("Tên đăng nhập")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("VÀO HỆ THỐNG", use_container_width=True):
            if u == "Cong" and p == "admin123":
                st.session_state.authenticated = True
                st.session_state.role = "Admin"
                st.session_state.username = "Cong"
                st.rerun()
            elif u == "Sale1" and p == "123":
                st.session_state.authenticated = True
                st.session_state.role = "Staff"
                st.session_state.username = "Sale1"
                st.rerun()
            else:
                st.error("Sai thông tin đăng nhập!")

# --- LOGIC ĐIỀU HƯỚNG CHÍNH ---
query_params = st.query_params
id_khach = query_params.get("id")

if id_khach:
    show_customer_page(id_khach)
elif st.session_state.get('authenticated'):
    show_admin_page()
else:
    show_home_page()
