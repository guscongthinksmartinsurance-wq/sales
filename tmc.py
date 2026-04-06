import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import io
from streamlit_option_menu import option_menu

# --- 1. SETUP ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

with open("style.css") as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# --- 2. MENU SIDEBAR CHUYÊN NGHIỆP ---
with st.sidebar:
    st.markdown("<h1 style='color:#0056D2; text-align:center;'>TMC ELITE</h1>", unsafe_allow_html=True)
    st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    st.divider()
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        selected = option_menu(
            menu_title=None,
            options=["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"],
            icons=["house", "eye", "gear", "person-badge"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "#0056D2", "font-size": "18px"}, 
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#0056D2"},
            }
        )
        if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    else:
        selected = "Trang Chủ"
        st.info("🔓 Đăng nhập để mở tính năng Quản lý")

# --- 3. ĐIỀU HƯỚNG TẦNG ---
query_params = st.query_params
id_khach = query_params.get("id")

if id_khach:
    # --- TẦNG KHÁCH HÀNG (TRANG TRÍ LẠI CỰC ĐẸP) ---
    st.markdown(f"<div class='main-card'><h1 class='tmc-title'>🛡️ Kế Hoạch Bảo Vệ Tài Chính</h1></div>", unsafe_allow_html=True)
    st.image("https://www.nationallife.com/img/National-Life-Group-Foundation.jpg", use_container_width=True)
    # Logic ghi mắt thần...
    st.stop()

if selected == "Trang Chủ":
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.markdown("<h1 class='tmc-title'>Chào mừng đến với TMC Financial Group</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", width=250)
        st.write("### Đối tác chiến lược National Life Group")
        st.write("Hơn 170 năm kinh nghiệm phục vụ cộng đồng.")
    with col2:
        if not st.session_state.authenticated:
            st.write("### Đăng nhập hệ thống")
            u = st.text_input("Tên đăng nhập")
            p = st.text_input("Mật khẩu", type="password")
            if st.button("Truy cập hệ thống", use_container_width=True):
                if u == "Cong" and p == "admin123":
                    st.session_state.authenticated, st.session_state.role, st.session_state.username = True, "Admin", "Cong"
                    st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif selected == "Mắt Thần":
    st.markdown("<div class='main-card'><h2 class='tmc-title'>👁️ THEO DÕI REAL-TIME</h2></div>", unsafe_allow_html=True)
    # Lấy data từ SQLite và hiện những khách đang xem link
    # Phân quyền cho Sale xem đúng khách mình quản lý

elif selected == "Vận Hành":
    st.markdown("<div class='main-card'><h2 class='tmc-title'>⚙️ QUẢN LÝ DỮ LIỆU TỔNG</h2></div>", unsafe_allow_html=True)
    # 1. Tab Thêm Lead
    # 2. Bảng DataFrame xịn (st.data_editor) cho phép sửa trực tiếp
    # 3. Nút Backup Excel

elif selected == "Cấu Hình":
    st.markdown("<div class='main-card'><h2 class='tmc-title'>👤 CẤU HÌNH PROFILE</h2></div>", unsafe_allow_html=True)
    st.text_input("Tiêu đề Web App", value="TMC FINANCIAL SYSTEM")
    st.text_area("Slogan của anh", value="Sâu sắc - Tận tâm - Chuyên nghiệp")
    st.button("Lưu thay đổi")
