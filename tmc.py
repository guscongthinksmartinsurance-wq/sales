import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import sqlite3
import urllib.parse

# --- 1. CẤU HÌNH & KẾT NỐI ---
st.set_page_config(page_title="TMC LEADER SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')

# Giả sử anh dùng SQLite để lưu trữ cho nhanh và đồng bộ
DB_NAME = "tmc_leads_master.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Bảng Leads chính
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT UNIQUE,
                    crm_link TEXT,
                    status TEXT,
                    owner TEXT,
                    note TEXT,
                    last_interact TIMESTAMP)''')
    # Bảng Staff để phân quyền
    c.execute('''CREATE TABLE IF NOT EXISTS staff (
                    username TEXT PRIMARY KEY,
                    password TEXT,
                    role TEXT)''') # Role: 'Admin' hoặc 'Sale'
    conn.commit()
    conn.close()

init_db()

# --- 2. NHẬN DIỆN KHÁCH HÀNG (MẮT THẦN) ---
query_params = st.query_params
customer_id = query_params.get("id") # Link dạng: myapp.com/?id=714xxxx

if customer_id:
    conn = sqlite3.connect(DB_NAME)
    df_all = pd.read_sql(f"SELECT * FROM leads WHERE phone = '{customer_id}'", conn)
    
    if not df_all.empty:
        row = df_all.iloc[0]
        # Ghi log Mắt Thần vào History
        t_now = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
        new_log = f"<div style='color:gold;'>{t_now} 🔥 KHÁCH ĐANG XEM LINK</div>"
        updated_note = new_log + str(row['note'])
        
        conn.execute("UPDATE leads SET note = ?, last_interact = ? WHERE phone = ?", 
                     (updated_note, datetime.now(NY_TZ).isoformat(), customer_id))
        conn.commit()
        
        # HIỂN THỊ CHO KHÁCH
        st.title(f"Chào {row['name']}!")
        st.write("---")
        st.subheader("Bảng Minh Họa Quyền Lợi IUL")
        st.info("Đây là giải pháp được thiết kế riêng cho chị. Em Công sẽ sớm liên hệ để giải đáp thắc mắc.")
        # Anh có thể dùng st.image hoặc st.download_button để đưa Illustration ở đây
    else:
        st.error("Hồ sơ không tồn tại hoặc link đã hết hạn.")
    conn.close()
    st.stop() # Dừng lại, không cho khách thấy phần Admin bên dưới

# --- 3. HỆ THỐNG QUẢN TRỊ (ADMIN & STAFF) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    # Form đăng nhập đơn giản cho anh và Team
    with st.container():
        st.title("🔐 TMC Leader Login")
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Đăng nhập"):
            # Anh có thể check cứng ở đây cho nhanh hoặc check qua bảng staff
            if user == "Cong" and pw == "123": # Ví dụ Admin
                st.session_state.authenticated = True
                st.session_state.user_role = "Admin"
                st.session_state.username = "Cong"
                st.rerun()
            elif user == "Sale1" and pw == "123": # Ví dụ Staff
                st.session_state.authenticated = True
                st.session_state.user_role = "Sale"
                st.session_state.username = "Sale1"
                st.rerun()
    st.stop()

# --- 4. GIAO DIỆN QUẢN LÝ ---
st.title(f"🚀 Quản Lý Leads - {st.session_state.username}")

conn = sqlite3.connect(DB_NAME)
df_leads = pd.read_sql("SELECT * FROM leads", conn)

# PHÂN QUYỀN THÔNG MINH
if st.session_state.user_role == "Admin":
    display_df = df_leads # Anh thấy hết
else:
    display_df = df_leads[df_leads['owner'] == st.session_state.username] # Staff thấy khách của họ

# HIỂN THỊ DANH SÁCH (Dùng cấu trúc Container giống file cũ của anh)
q_search = st.text_input("🔍 Tìm tên hoặc số điện thoại...").lower()

for idx, row in display_df.iterrows():
    if q_search in row['name'].lower() or q_search in str(row['phone']):
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 5, 2])
            with c1:
                st.markdown(f"### {row['name']}")
                st.write(f"📞 {row['phone']}")
                st.caption(f"Trạng thái: {row['status']}")
                
                # Tạo link Mắt Thần để anh copy gửi RingCentral
                actual_url = "https://your-app-link.streamlit.app"
                tracking_link = f"{actual_url}/?id={row['phone']}"
                st.code(tracking_link, language=None)
                
            with c2:
                st.markdown("**Lịch sử chăm sóc (Mắt thần báo ở đây):**")
                st.markdown(f"<div style='height:100px; overflow-y:auto; border:1px solid #444; padding:5px;'>{row['note']}</div>", unsafe_allow_html=True)
            
            with c3:
                # Nút cập nhật nhanh Note
                new_note = st.text_input("Ghi chú nhanh", key=f"note_{row['phone']}")
                if st.button("Lưu", key=f"btn_{row['phone']}"):
                    t_str = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
                    updated_note = f"<div>{t_str} {new_note}</div>" + row['note']
                    conn.execute("UPDATE leads SET note = ? WHERE phone = ?", (updated_note, row['phone']))
                    conn.commit()
                    st.rerun()

conn.close()