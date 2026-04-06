import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import io

# --- 1. CẤU HÌNH & GIAO DIỆN HIỆN ĐẠI ---
st.set_page_config(page_title="TMC System", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

# Đọc CSS từ file style.css
try:
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except:
    pass

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

# --- ĐIỀU HƯỚNG 3 PHẦN ---
query_params = st.query_params
customer_id = query_params.get("id")

# ==========================================
# PHẦN 1: DÀNH CHO KHÁCH HÀNG (MẮT THẦN)
# ==========================================
if customer_id:
    conn = sqlite3.connect(DB_NAME)
    df_check = pd.read_sql(f"SELECT * FROM leads WHERE phone = '{customer_id}'", conn)
    
    if not df_check.empty:
        row = df_check.iloc[0]
        # Ghi log Mắt Thần vào Note
        t_now = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
        view_log = f"<div class='history-entry'><span class='note-time'>{t_now}</span> <span style='color:#f57c00; font-weight:bold;'>🔥 KHÁCH VỪA XEM LINK</span></div>"
        
        if "KHÁCH VỪA XEM LINK" not in str(row['note'])[:150]:
            new_note = view_log + str(row['note'])
            conn.execute("UPDATE leads SET note = ?, last_updated = ? WHERE phone = ?", 
                         (new_note, datetime.now(NY_TZ).isoformat(), customer_id))
            conn.commit()
        
        st.markdown(f"<h1 style='color:#0056D2;'>🛡️ Chào {row['name']}</h1>", unsafe_allow_html=True)
        st.divider()
        st.markdown("### Giải Pháp Tài Chính IUL Của Bạn")
        st.info("Tài liệu cá nhân hóa của bạn đang được hiển thị. Em Công sẽ sớm liên hệ chị.")
    else:
        st.error("Liên kết không tồn tại.")
    conn.close()
    st.stop()

# ==========================================
# PHẦN 2: TRANG CHỦ GIỚI THIỆU (CHO MỌI NGƯỜI)
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align:center; color:#0056D2;'>TMC FINANCIAL SYSTEM</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Giải pháp quản lý và tư vấn bảo hiểm nhân thọ chuyên nghiệp</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        with st.container(border=True):
            st.subheader("🔑 Đăng nhập hệ thống")
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            if st.button("Đăng nhập", use_container_width=True):
                if user == "Cong" and pw == "admin123":
                    st.session_state.authenticated = True
                    st.session_state.role = "Admin"
                    st.session_state.username = "Cong"
                    st.rerun()
                # Thêm Staff ở đây...
    st.stop()

# ==========================================
# PHẦN 3: DÀNH CHO ADMIN (QUẢN LÝ LEADS)
# ==========================================
st.markdown(f"<h1 style='color:#0056D2;'>🚀 QUẢN LÝ LEADS - {st.session_state.username}</h1>", unsafe_allow_html=True)

conn = sqlite3.connect(DB_NAME)

# --- NÚT THÊM LEAD MỚI (PHẢI CÓ CÁI NÀY) ---
with st.expander("➕ THÊM KHÁCH HÀNG MỚI (LEAD)", expanded=False):
    with st.form("add_lead_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        f_name = c1.text_input("Họ tên khách")
        f_phone = c2.text_input("Số điện thoại (ID)")
        f_state = c3.text_input("Tiểu bang")
        f_owner = st.selectbox("Người quản lý", ["Cong", "Sale1", "Sale2"])
        if st.form_submit_button("LƯU KHÁCH HÀNG"):
            if f_name and f_phone:
                try:
                    conn.execute("INSERT INTO leads (name, phone, state, owner) VALUES (?,?,?,?)", 
                                 (f_name, f_phone, f_state, f_owner))
                    conn.commit()
                    st.success("Đã thêm khách hàng thành công!")
                    st.rerun()
                except:
                    st.error("Số điện thoại này đã tồn tại!")

# Đọc dữ liệu
df_m = pd.read_sql("SELECT * FROM leads", conn)
if st.session_state.role != "Admin":
    df_m = df_m[df_m['owner'] == st.session_state.username]

# Thống kê & Tìm kiếm
m1, m2 = st.columns([2, 8])
m1.metric("Tổng Lead", len(df_m))
q_s = m2.text_input("🔍 Tìm kiếm khách hàng...", placeholder="Nhập tên hoặc số điện thoại")

# Hiển thị danh sách Card
for idx, row in df_m.iterrows():
    if q_s.lower() in row['name'].lower() or q_s in str(row['phone']):
        with st.container(border=True):
            col_info, col_history, col_action = st.columns([4, 4, 2])
            with col_info:
                st.markdown(f"### {row['name']}")
                st.write(f"📞 {row['phone']} | 📍 {row['state']}")
                # Link Mắt Thần
                # LƯU Ý: Thay link này bằng link thật của anh trên Streamlit
                t_link = f"https://the-nexus.streamlit.app/?id={row['phone']}"
                st.code(t_link, language=None)
            with col_history:
                st.markdown(f"<div style='height:100px; overflow-y:auto; background:#f1f3f6; padding:10px; border-radius:10px;'>{row['note']}</div>", unsafe_allow_html=True)
            with col_action:
                new_msg = st.text_input("Ghi chú", key=f"in_{row['id']}", label_visibility="collapsed")
                if st.button("Lưu", key=f"btn_{row['id']}", use_container_width=True):
                    t_str = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
                    updated_note = f"<div class='history-entry'><span class='note-time'>{t_str}</span> {new_msg}</div>" + row['note']
                    conn.execute("UPDATE leads SET note = ? WHERE id = ?", (updated_note, row['id']))
                    conn.commit()
                    st.rerun()
                if st.button("🗑️ Xóa", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM leads WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.rerun()

# Nút Backup
st.divider()
if st.button("📊 BACKUP EXCEL"):
    output = io.BytesIO()
    df_m.to_excel(output, index=False)
    st.download_button(label="📥 Tải file về máy", data=output.getvalue(), file_name="TMC_Backup.xlsx")

conn.close()
