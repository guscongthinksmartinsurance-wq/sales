import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import io
import os
from streamlit_option_menu import option_menu

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

# Load CSS (Giữ nguyên giao diện anh đã ưng ý)
try:
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except: pass

def init_db():
    conn = sqlite3.connect(DB_NAME)
    # Bảng Leads
    conn.execute('''CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, phone TEXT UNIQUE, state TEXT,
                    status TEXT DEFAULT 'New', owner TEXT,
                    note TEXT DEFAULT '', last_updated TIMESTAMP)''')
    # Bảng Profile (Lưu Logo và Slogan)
    conn.execute('''CREATE TABLE IF NOT EXISTS profile (
                    id INTEGER PRIMARY KEY,
                    slogan TEXT, logo_path TEXT)''')
    # Khởi tạo profile mặc định nếu chưa có
    c = conn.cursor()
    c.execute("SELECT count(*) FROM profile")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO profile (id, slogan) VALUES (1, 'Sâu sắc - Tận tâm - Chuyên nghiệp')")
    conn.commit()
    conn.close()

init_db()

# --- 2. XỬ LÝ ẢNH LOGO & PROFILE ---
def get_profile():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM profile WHERE id=1", conn)
    conn.close()
    return df.iloc[0]

prof = get_profile()

# --- 3. SIDEBAR MENU ---
with st.sidebar:
    # Hiển thị Logo từ Profile
    if prof['logo_path'] and os.path.exists(prof['logo_path']):
        st.image(prof['logo_path'], use_container_width=True)
    else:
        st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    
    st.markdown(f"<p style='text-align:center; font-style:italic; font-size:0.8em;'>{prof['slogan']}</p>", unsafe_allow_html=True)
    st.divider()
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        selected = option_menu(
            menu_title=None,
            options=["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"],
            icons=["house", "eye", "gear", "person-badge"],
            styles={
                "nav-link-selected": {"background-color": "#0056D2"},
            }
        )
        if st.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    else:
        selected = "Trang Chủ"
        st.info("🔓 Đăng nhập để quản lý")

# --- 4. ĐIỀU HƯỚNG TẦNG ---
query_params = st.query_params
id_khach = query_params.get("id")

# TẦNG KHÁCH HÀNG (Khi khách bấm vào link)
if id_khach:
    conn = sqlite3.connect(DB_NAME)
    df_k = pd.read_sql(f"SELECT * FROM leads WHERE phone = '{id_khach}'", conn)
    if not df_k.empty:
        row = df_k.iloc[0]
        # Ghi log Mắt Thần
        t_now = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
        view_log = f"<div class='history-entry'><span class='note-time'>{t_now}</span> <span style='color:#f57c00; font-weight:bold;'>🔥 KHÁCH VỪA XEM LINK</span></div>"
        if "KHÁCH VỪA XEM LINK" not in str(row['note'])[:150]:
            new_note = view_log + str(row['note'])
            conn.execute("UPDATE leads SET note = ?, last_updated = ? WHERE phone = ?", 
                         (new_note, datetime.now(NY_TZ).isoformat(), id_khach))
            conn.commit()
        
        st.markdown(f"<div class='main-card'><h1 class='tmc-title'>Chào {row['name']}</h1></div>", unsafe_allow_html=True)
        st.image("https://www.nationallife.com/img/National-Life-Group-Foundation.jpg", use_container_width=True)
        st.info("Kế hoạch tài chính IUL cá nhân hóa của bạn đang được hiển thị.")
    conn.close()
    st.stop()

# --- NỘI DUNG CÁC TRANG QUẢN TRỊ ---
if selected == "Trang Chủ":
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.markdown("<h1 class='tmc-title'>TMC FINANCIAL GROUP</h1>", unsafe_allow_html=True)
    st.image("https://www.nationallife.com/img/National-Life-Group-Foundation.jpg", use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🛡️ National Life Group")
        st.write("Đồng hành cùng gia đình Việt tại Mỹ với hơn 170 năm uy tín.")
    with col2:
        if not st.session_state.authenticated:
            st.subheader("🔑 Đăng nhập")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Truy cập", use_container_width=True):
                if u == "Cong" and p == "admin123":
                    st.session_state.authenticated, st.session_state.role, st.session_state.username = True, "Admin", "Cong"
                    st.rerun()
        else:
            st.success(f"Chào anh {st.session_state.username}, hệ thống đã sẵn sàng.")
    st.markdown("</div>", unsafe_allow_html=True)

elif selected == "Mắt Thần":
    st.markdown("<div class='main-card'><h2 class='tmc-title'>👁️ KHÁCH ĐANG QUAN TÂM</h2></div>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM leads", conn)
    # Lọc khách có dấu hiệu đang xem
    viewing = df[df['note'].str.contains("KHÁCH VỪA XEM LINK", na=False)]
    
    if not viewing.empty:
        for idx, r in viewing.iterrows():
            with st.container():
                st.markdown(f"<div class='history-entry'><b>🔥 {r['name']}</b> ({r['phone']}) - Sale: {r['owner']}<br>{r['note'][:200]}...</div>", unsafe_allow_html=True)
    else:
        st.info("Hiện chưa có khách nào đang truy cập link.")
    conn.close()

elif selected == "Vận Hành":
    st.markdown("<div class='main-card'><h2 class='tmc-title'>⚙️ QUẢN LÝ DỮ LIỆU TỔNG</h2></div>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    
    tab1, tab2 = st.tabs(["➕ Thêm Lead Mới", "📊 Danh Sách & Backup"])
    
    with tab1:
        with st.form("add_lead"):
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("Tên khách")
            p = c2.text_input("Số điện thoại")
            s = c3.text_input("Tiểu bang")
            ow = st.selectbox("Người quản lý", ["Cong", "Sale1", "Sale2"])
            if st.form_submit_button("LƯU HỒ SƠ"):
                conn.execute("INSERT INTO leads (name, phone, state, owner) VALUES (?,?,?,?)", (n,p,s,ow))
                conn.commit()
                st.success("Đã thêm thành công!"); st.rerun()

    with tab2:
        df_all = pd.read_sql("SELECT id, name, phone, state, owner, status FROM leads", conn)
        # Cho phép sửa trực tiếp trên bảng
        edited_df = st.data_editor(df_all, use_container_width=True, num_rows="dynamic")
        if st.button("Xác nhận cập nhật bảng"):
            edited_df.to_sql("leads", conn, if_exists="replace", index=False)
            st.success("Đã lưu thay đổi!"); st.rerun()
            
        output = io.BytesIO()
        df_all.to_excel(output, index=False)
        st.download_button("📥 Tải file Backup Excel", output.getvalue(), "TMC_Leads.xlsx")
    conn.close()

elif selected == "Cấu Hình":
    st.markdown("<div class='main-card'><h2 class='tmc-title'>👤 CÀI ĐẶT HỆ THỐNG</h2></div>", unsafe_allow_html=True)
    with st.form("profile_form"):
        new_slogan = st.text_input("Slogan của anh", value=prof['slogan'])
        new_logo = st.file_uploader("Upload Logo mới (PNG/JPG)", type=["png", "jpg", "jpeg"])
        if st.form_submit_button("CẬP NHẬT"):
            conn = sqlite3.connect(DB_NAME)
            if new_logo:
                path = f"logo_{new_logo.name}"
                with open(path, "wb") as f:
                    f.write(new_logo.getbuffer())
                conn.execute("UPDATE profile SET slogan=?, logo_path=? WHERE id=1", (new_slogan, path))
            else:
                conn.execute("UPDATE profile SET slogan=? WHERE id=1", (new_slogan,))
            conn.commit()
            conn.close()
            st.success("Đã cập nhật Profile!"); st.rerun()
