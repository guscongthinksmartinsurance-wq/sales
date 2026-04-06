# tmc.py - MODERN LIGHT & BLUE INTERFACE
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import io
import urllib.parse

# --- 1. CẤU HÌNH & DATABASE ---
st.set_page_config(page_title="TMC Financial - Leader System", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT UNIQUE,
                    crm_id TEXT,
                    state TEXT,
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

# --- 2. LOGIC MẮT THẦN (GIAO DIỆN SẠCH CHÚC KHÁCH) ---
query_params = st.query_params
customer_id = query_params.get("id")

if customer_id:
    conn = sqlite3.connect(DB_NAME)
    # Lọc DB để tìm đúng khách
    df_check = pd.read_sql(f"SELECT * FROM leads WHERE phone = '{customer_id}'", conn)
    
    if not df_check.empty:
        row = df_check.iloc[0]
        # Ghi log Mắt Thần vào Note
        t_now = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
        view_log = f"<div class='history-entry'><span class='note-time'>{t_now}</span> <span class='customer-view-log'>🔥 KHÁCH VỪA XEM LINK</span></div>"
        
        # Cập nhật DB: Chèn log vào đầu Note
        if "KHÁCH VỪA XEM LINK" not in str(row['note'])[:150]: # Tránh spam log khi load lại
            new_note = view_log + str(row['note'])
            conn.execute("UPDATE leads SET note = ?, last_updated = ? WHERE phone = ?", 
                         (new_note, datetime.now(NY_TZ).isoformat(), customer_id))
            conn.commit()
        
        # --- GIAO DIỆN CHO KHÁCH (HIỆN ĐẠI, SẠCH SẼ) ---
        st.markdown(f"<h1 class='tmc-title'>🛡️ Chào {row['name']}</h1>", unsafe_allow_html=True)
        st.divider()
        st.markdown("""
        ### Giải Pháp Tài Chính IUL Của Bạn
        National Life Group - NATIONAL LIFE SOLUTIONS.
        
        Tài liệu cá nhân hóa của bạn đang được hiển thị an toàn. Em Công sẽ sớm liên hệ để giải đáp thắc mắc của chị.
        """)
        # Anh có thể dùng st.image hoặc st.download_button để đưa Illustration ở đây
        if st.button("Kết nối với em Công"):
            st.write("📞 Số điện thoại của em: **(Số của anh ở đây)**")

    else:
        st.error("Liên kết không tồn tại hoặc hồ sơ đang được cập nhật.")
    conn.close()
    st.stop() # Dừng lại, không cho khách thấy phần Admin

# --- 3. ĐĂNG NHẬP & PHÂN QUYỀN (ADMIN/STAFF) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 class='tmc-title'>🔐 TMC Leader System</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Đăng nhập hệ thống")
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Đăng nhập"):
            # Logic check user của anh
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

# --- 4. GIAO DIỆN QUẢN LÝ LEADS (LỘT XÁC SẠCH ĐẸP) ---
st.markdown(f"<h1 class='tmc-title'>🚀 QUẢN LÝ LEADS - {st.session_state.username}</h1>", unsafe_allow_html=True)

conn = sqlite3.connect(DB_NAME)
# Đọc DB
df_m = pd.read_sql("SELECT * FROM leads", conn)

# Phân quyền: Người đó chỉ thấy khách hàng của họ
if st.session_state.role == "Admin":
    filtered_df = df_m
else:
    filtered_df = df_m[df_m['owner'] == st.session_state.username]

# Thống kê sạch sẽ
st.markdown("---")
m1, m2, m3 = st.columns(3)
m1.metric("Tổng Leads", len(filtered_df))
m2.metric("Mới", len(filtered_df[filtered_df['status'] == 'New']))
# Đếm khách đang xem bằng cách check keyword trong Note
count_viewing = len(filtered_df[filtered_df['note'].str.contains("KHÁCH VỪA XEM LINK", na=False)])
m3.metric("Khách đang xem 🔥", count_viewing)

# Tìm kiếm sạch sẽ
q_s = st.text_input("🔍 Tìm tên hoặc số điện thoại...", placeholder="Nhập tên khách hàng...").lower()

# HIỂN THỊ DANH SÁCH LEADS (MODERN CARD STYLE)
for idx, row in filtered_df.iterrows():
    if q_s in row['name'].lower() or q_s in str(row['phone']):
        # Cấu trúc Container với bo góc và đổ bóng
        with st.container():
            col_info, col_history, col_action = st.columns([3.5, 5, 1.5])
            
            with col_info:
                st.markdown(f"<h3 style='margin:0;'>{row['name']}</h3>", unsafe_allow_html=True)
                st.caption(f"📍 {row['state']} | CRM ID: {row['crm_id']}")
                st.markdown(f"**🏷️ {row['status']}**")
                
                # Action Icons Tel/SMS (dùng style mới)
                c_a1, c_a2, c_a3, c_a4 = st.columns(4)
                c_a1.link_button("📞 Tel", f"tel:{row['phone']}")
                c_a2.link_button("📱 RC", f"rcmobile://sms?number={row['phone']}")
                c_a3.link_button("💬 SMS", f"sms:{row['phone']}")
                c_a4.link_button("✉️ Mail", f"mailto:{row['email'] if 'email' in filtered_df.columns else ''}")

                # Tracking Link
                tracking_link = f"https://your-app-url.streamlit.app/?id={row['phone']}"
                st.code(tracking_link, language=None)
                st.caption("Copy link này gửi RingCentral")
                
            with col_history:
                st.markdown("**History / Mắt Thần:**")
                st.markdown(f"<div class='history-container'>{row['note']}</div>", unsafe_allow_html=True)
            
            with col_action:
                # Cập nhật nhanh Note
                new_msg = st.text_input("Ghi chú...", label_visibility="collapsed", key=f"in_{row['id']}", placeholder="Ghi chú nhanh...")
                if st.button("Lưu", key=f"btn_{row['id']}", use_container_width=True):
                    t_str = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
                    updated_note = f"<div class='history-entry'><span class='note-time'>{t_str}</span> {new_msg}</div>" + row['note']
                    conn.execute("UPDATE leads SET note = ? WHERE id = ?", (updated_note, row['id']))
                    conn.commit()
                    st.rerun()
                st.markdown("---")
                # Nút Edit/⚙️ như cũ
                with st.popover("⚙️ Settings"):
                    st.write("Chỉnh sửa Lead...")
                    # ... (Phần form edit dữ liệu anh giữ nguyên như file cũ nhé)

# --- 5. NÚT BACKUP EXCEL ---
st.divider()
if st.button("📊 XUẤT FILE EXCEL BACKUP (VIP)"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name='Leads_Backup')
    st.download_button(
        label="📥 Tải file Backup về máy",
        data=output.getvalue(),
        file_name=f"TMC_Backup_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

conn.close()
