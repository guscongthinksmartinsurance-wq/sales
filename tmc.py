import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import io

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="TMC Financial System", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

# Kết nối CSS để làm đẹp giao diện
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
                    state TEXT,
                    status TEXT DEFAULT 'New',
                    owner TEXT,
                    note TEXT DEFAULT '',
                    last_updated TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# --- XỬ LÝ ĐIỀU HƯỚNG ---
query_params = st.query_params
id_khach = query_params.get("id")

# =========================================================
# TẦNG 1: TRANG CHỦ (GIỚI THIỆU NATIONAL LIFE & IUL)
# =========================================================
def show_home_page():
    # Header sang trọng
    st.markdown("<div style='text-align: center; padding: 20px;'>", unsafe_allow_html=True)
    st.markdown("<h1 style='color:#0056D2; font-size: 3em;'>TMC FINANCIAL GROUP</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.2em; color: #555;'>Đối tác chiến lược của <b>National Life Group</b> tại cộng đồng Việt Nam</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # Chia cột giới thiệu IUL và National Life
    col_img, col_txt = st.columns([1, 1])
    
    with col_img:
        # Anh có thể thay link ảnh bằng logo National Life hoặc ảnh văn phòng
        st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", width=300)
        st.markdown("""
        ### Tại sao chọn National Life Group?
        * **Lịch sử lâu đời:** Hơn 170 năm kinh nghiệm tài chính.
        * **Cam kết:** Mang lại sự bình yên và thịnh vượng cho mọi gia đình.
        * **Sản phẩm:** Đứng đầu về dòng bảo hiểm chỉ số IUL.
        """)

    with col_txt:
        st.markdown("### Giải Pháp IUL (Indexed Universal Life)")
        st.write("""
        IUL không chỉ là bảo hiểm, mà là một công cụ tài chính linh hoạt giúp bạn:
        1. **Bảo vệ gia đình:** Quyền lợi tử vong cao.
        2. **Tích lũy hưu trí:** Tận dụng sức mạnh lãi kép từ thị trường chứng khoán (nhưng không lo lỗ vốn).
        3. **Rút tiền không thuế:** Sử dụng tiền mặt tích lũy cho mục đích cá nhân mà không phải đóng thuế thu nhập.
        """)
        
        # Nút bấm đăng nhập cho nhân viên (Để gọn gàng ở dưới)
        with st.popover("🔐 Đăng nhập cho Thành viên"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
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
                    st.error("Sai thông tin!")

# =========================================================
# TẦNG 2: TRANG KHÁCH HÀNG (Dành riêng cho khách)
# =========================================================
def show_customer_page(phone_id):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql(f"SELECT * FROM leads WHERE phone = '{phone_id}'", conn)
    
    if not df.empty:
        row = df.iloc[0]
        # MẮT THẦN: Ghi log
        t_now = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
        view_log = f"<div class='history-entry'><span class='note-time'>{t_now}</span> <span style='color:#f57c00; font-weight:bold;'>🔥 KHÁCH VỪA XEM LINK</span></div>"
        
        if "KHÁCH VỪA XEM LINK" not in str(row['note'])[:150]:
            new_note = view_log + str(row['note'])
            conn.execute("UPDATE leads SET note = ?, last_updated = ? WHERE phone = ?", (new_note, datetime.now(NY_TZ).isoformat(), phone_id))
            conn.commit()

        st.markdown(f"<h1 style='color:#0056D2;'>🛡️ Chào chị {row['name']}</h1>", unsafe_allow_html=True)
        st.divider()
        st.markdown("### Kế Hoạch Tài Chính Cá Nhân Hóa")
        st.info("Bảng minh họa IUL của chị đã sẵn sàng. Em Công sẽ sớm gọi điện để giải thích chi tiết cho chị.")
        # Link ảnh minh họa hoặc file
        st.image("https://www.nationallife.com/img/IUL-Infographic.jpg", caption="Giải pháp IUL thông minh")
    else:
        st.error("Liên kết không đúng.")
    conn.close()

# =========================================================
# TẦNG 3: QUẢN LÝ LEADS (Dành cho Anh & Staff)
# =========================================================
def show_admin_page():
    st.markdown(f"<h1 style='color:#0056D2;'>🚀 QUẢN TRỊ LEADS - {st.session_state.username}</h1>", unsafe_allow_html=True)
    
    # Nút Đăng xuất để quay về trang chủ
    if st.sidebar.button("🚪 Đăng xuất"):
        st.session_state.authenticated = False
        st.rerun()

    conn = sqlite3.connect(DB_NAME)
    
    with st.expander("➕ THÊM KHÁCH HÀNG MỚI"):
        with st.form("add"):
            n = st.text_input("Họ tên")
            p = st.text_input("Phone (ID)")
            o = st.selectbox("Sale phụ trách", ["Cong", "Sale1"])
            if st.form_submit_button("LƯU"):
                conn.execute("INSERT INTO leads (name, phone, owner) VALUES (?,?,?)", (n,p,o))
                conn.commit()
                st.rerun()

    df = pd.read_sql("SELECT * FROM leads", conn)
    if st.session_state.role != "Admin":
        df = df[df['owner'] == st.session_state.username]

    for idx, row in df.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([4, 4, 2])
            with c1:
                st.markdown(f"### {row['name']}")
                st.code(f"https://the-nexus.streamlit.app/?id={row['phone']}", language=None)
            with c2:
                st.markdown(f"<div class='history-container'>{row['note']}</div>", unsafe_allow_html=True)
            with c3:
                msg = st.text_input("Ghi chú", key=f"m_{row['id']}", label_visibility="collapsed")
                if st.button("Lưu", key=f"b_{row['id']}"):
                    t_str = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
                    up_note = f"<div class='history-entry'><span class='note-time'>{t_str}</span> {msg}</div>" + row['note']
                    conn.execute("UPDATE leads SET note = ? WHERE id = ?", (up_note, row['id']))
                    conn.commit()
                    st.rerun()
    conn.close()

# --- ĐIỀU HƯỚNG ---
if id_khach:
    show_customer_page(id_khach)
elif st.session_state.get('authenticated'):
    show_admin_page()
else:
    show_home_page()
