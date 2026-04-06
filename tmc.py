import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import io
import plotly.express as px

# --- 1. CẤU HÌNH & DATABASE ---
st.set_page_config(page_title="TMC LEADER SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT UNIQUE,
                    crm_link TEXT,
                    status TEXT DEFAULT 'New',
                    owner TEXT,
                    note TEXT DEFAULT '',
                    last_updated TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# Load CSS
with open("style.css") as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# --- 2. LOGIC MẮT THẦN (CHO KHÁCH HÀNG) ---
query_params = st.query_params
customer_id = query_params.get("id")

if customer_id:
    conn = sqlite3.connect(DB_NAME)
    # Tìm khách hàng theo số điện thoại (ID)
    df_check = pd.read_sql(f"SELECT * FROM leads WHERE phone = '{customer_id}'", conn)
    
    if not df_all.empty if 'df_all' in locals() else not df_check.empty:
        row = df_check.iloc[0]
        # Ghi log Mắt Thần vào History (Note)
        t_now = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
        view_log = f"<div class='history-entry'><span class='note-time'>{t_now}</span> 🔥 KHÁCH ĐANG XEM LINK</div>"
        
        # Cập nhật DB: Chèn log vào đầu Note
        new_note = view_log + str(row['note'])
        conn.execute("UPDATE leads SET note = ?, last_updated = ? WHERE phone = ?", 
                     (new_note, datetime.now(NY_TZ).isoformat(), customer_id))
        conn.commit()
        
        # Giao diện cho khách xem
        st.title(f"Chào {row['name']}!")
        st.divider()
        st.subheader("Bảng Minh Họa Giải Pháp IUL")
        st.info("Tài liệu cá nhân hóa của bạn đang được hiển thị an toàn.")
        # Anh có thể chèn link PDF/Ảnh ở đây
    else:
        st.error("Liên kết không tồn tại hoặc đã hết hạn.")
    conn.close()
    st.stop()

# --- 3. ĐĂNG NHẬP & PHÂN QUYỀN (CHO ADMIN/STAFF) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 TMC Leader Login")
    col1, col2 = st.columns([1, 2])
    with col1:
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Đăng nhập"):
            # Anh có thể sửa logic check user ở đây
            if user == "Cong" and pw == "admin123":
                st.session_state.authenticated = True
                st.session_state.role = "Admin"
                st.session_state.username = "Cong"
                st.rerun()
            elif user == "Sale1" and pw == "123":
                st.session_state.authenticated = True
                st.session_state.role = "Staff"
                st.session_state.username = "Sale1"
                st.rerun()
    st.stop()

# --- 4. GIAO DIỆN QUẢN LÝ ---
st.title(f"🚀 QUẢN LÝ LEADS - {st.session_state.username}")

conn = sqlite3.connect(DB_NAME)
df_m = pd.read_sql("SELECT * FROM leads", conn)

# Phân quyền: Staff chỉ thấy khách mình quản lý
if st.session_state.role == "Admin":
    filtered_df = df_m
else:
    filtered_df = df_m[df_m['owner'] == st.session_state.username]

# Thống kê nhanh
m1, m2, m3 = st.columns(3)
m1.metric("Tổng Leads", len(filtered_df))
m2.metric("Khách đang xem", len(filtered_df[filtered_df['note'].str.contains("KHÁCH ĐANG XEM", na=False)]))

# Tìm kiếm & Hiển thị
q_s = st.text_input("🔍 Tìm tên hoặc số điện thoại...").lower()

for idx, row in filtered_df.iterrows():
    if q_s in row['name'].lower() or q_s in str(row['phone']):
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 5, 2])
            with c1:
                st.markdown(f"### {row['name']}")
                st.write(f"📞 {row['phone']}")
                tracking_link = f"https://your-app-url.streamlit.app/?id={row['phone']}"
                st.code(tracking_link, language=None)
                st.caption("Copy link này gửi RingCentral")
                
            with c2:
                st.markdown("**History / Mắt Thần:**")
                st.markdown(f"<div style='height:120px; overflow-y:auto; background:#111; padding:10px;'>{row['note']}</div>", unsafe_allow_html=True)
            
            with c3:
                new_msg = st.text_input("Ghi chú nhanh", key=f"in_{row['id']}")
                if st.button("Lưu", key=f"btn_{row['id']}"):
                    t_str = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
                    updated_note = f"<div class='history-entry'><span class='note-time'>{t_str}</span> {new_msg}</div>" + row['note']
                    conn.execute("UPDATE leads SET note = ? WHERE id = ?", (updated_note, row['id']))
                    conn.commit()
                    st.rerun()

# --- 5. NÚT BACKUP EXCEL (GIẢI QUYẾT NỖI LO MẤT DATA) ---
st.divider()
if st.button("✨ XUẤT FILE EXCEL BACKUP (VIP)"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name='Leads_Backup')
    st.download_button(
        label="📥 Tải file Backup về máy",
        data=output.getvalue(),
        file_name=f"TMC_Backup_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

conn.close()
