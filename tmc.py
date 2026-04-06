import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import urllib.parse

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

# Load CSS
try:
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except: pass

def clean_phone(p):
    return str(p).replace(".0", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Khởi tạo bảng Leads với đầy đủ 10 trường dữ liệu
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, crm_id TEXT, crm_link TEXT,
                    cell TEXT UNIQUE, work TEXT, email TEXT,
                    state TEXT, owner TEXT, tags TEXT,
                    status TEXT DEFAULT 'New', note TEXT DEFAULT '', 
                    last_updated TIMESTAMP)''')
    
    # Bảng Profile lưu cấu hình trang chủ
    c.execute('''CREATE TABLE IF NOT EXISTS profile (
                    id INTEGER PRIMARY KEY, slogan TEXT, 
                    logo_app TEXT, img_national TEXT, img_iul TEXT)''')
    
    # Kiểm tra và bổ sung cột nếu thiếu (tránh lỗi database cũ)
    check_cols = [('crm_id', 'TEXT'), ('crm_link', 'TEXT'), ('work', 'TEXT'), 
                  ('email', 'TEXT'), ('tags', 'TEXT'), ('state', 'TEXT')]
    for col, ctype in check_cols:
        try: c.execute(f"ALTER TABLE leads ADD COLUMN {col} {ctype}")
        except: pass

    c.execute("SELECT count(*) FROM profile")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO profile (id, slogan) VALUES (1, 'Sâu sắc - Tận tâm - Chuyên nghiệp')")
    conn.commit()
    conn.close()

init_db()

def get_profile():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    res = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()
    return dict(res) if res else {}

prof = get_profile()

# --- 2. SIDEBAR & ĐIỀU HƯỚNG ---
with st.sidebar:
    logo = prof.get('logo_app')
    if logo and os.path.exists(logo): st.image(logo, use_container_width=True)
    else: st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    
    st.divider()
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        from streamlit_option_menu import option_menu
        selected = option_menu(
            menu_title=None,
            options=["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"],
            styles={"nav-link-selected": {"background-color": "#00263e"}}
        )
        if st.sidebar.button("ĐĂNG XUẤT", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    else:
        selected = "Trang Chủ"

# --- 3. LOGIC HIỂN THỊ CÁC PHÂN HỆ ---

# PHÂN HỆ: TRANG CHỦ
if selected == "Trang Chủ":
    st.markdown('<div class="hero-banner"><h1>NATIONAL LIFE GROUP</h1><p>Experience the Peace of Mind Since 1848</p></div>', unsafe_allow_html=True)
    
    col_left, col_right = st.columns(2, gap="small")
    with col_left:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<p class="section-header">Tập Đoàn National Life Group</p>', unsafe_allow_html=True)
        img_n = prof.get('img_national')
        if img_n and os.path.exists(img_n): st.image(img_n, use_container_width=True)
        else: st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
        st.write("Biểu tượng tài chính uy tín tại Hoa Kỳ. Chúng tôi cam kết mang lại sự bảo vệ vững chắc cho mọi gia đình.")
        st.markdown("- **Kinh nghiệm:** 170+ năm.\n- **Sứ mệnh:** Giữ trọn lời hứa.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<p class="section-header">Giải Pháp Tài Chính IUL</p>', unsafe_allow_html=True)
        img_i = prof.get('img_iul')
        if img_i and os.path.exists(img_i): st.image(img_i, use_container_width=True)
        else: st.info("Vui lòng upload ảnh minh họa IUL trong phần Cấu Hình.")
        st.write(f"**{prof.get('slogan')}**")
        st.write("Giải pháp kết hợp bảo vệ sinh mạng và tích lũy hưu trí không thuế, bảo đảm an toàn vốn tuyệt đối.")
        st.markdown("- **Lợi nhuận:** Theo chỉ số thị trường.\n- **Ưu điểm:** Rút tiền không thuế thu nhập.")
        st.markdown('</div>', unsafe_allow_html=True)

    if not st.session_state.authenticated:
        with st.expander("🔐 TRUY CẬP HỆ THỐNG QUẢN TRỊ"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("XÁC NHẬN"):
                if u == "Cong" and p == "admin123":
                    st.session_state.authenticated = True
                    st.rerun()

# PHÂN HỆ: VẬN HÀNH (10 TRƯỜNG & THANH ĐỘ TRỄ)
elif selected == "Vận Hành":
    st.markdown("<div class='main-card'><h2>HỆ THỐNG VẬN HÀNH DỮ LIỆU</h2></div>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    df_m = pd.read_sql("SELECT * FROM leads", conn)
    n_ny = datetime.now(NY_TZ)

    tab_list, tab_add = st.tabs(["DANH SÁCH HỒ SƠ", "THÊM MỚI HỒ SƠ"])

    with tab_list:
        # Dashboard chỉ số
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f"<div class='db-card'><p style='margin:0; font-weight:1000;'>TỔNG LEAD</p><div class='db-num-capsule'>{len(df_m)}</div></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='db-card'><p style='margin:0; font-weight:1000; color:green;'>MỚI</p><div class='db-num-capsule'>{len(df_m[df_m['status'] == 'New'])}</div></div>", unsafe_allow_html=True)
        with m3:
            def get_days(last_up):
                try:
                    dt = datetime.fromisoformat(last_up)
                    if dt.tzinfo is None: dt = NY_TZ.localize(dt)
                    return (n_ny - dt).days
                except: return 0
            df_m['days_diff'] = df_m['last_updated'].apply(get_days)
            late_leads = len(df_m[df_m['days_diff'] > 7])
            st.markdown(f"<div class='db-card'><p style='margin:0; font-weight:1000; color:red;'>TRỄ (>7D)</p><div class='db-num-capsule' style='color:red;'>{late_leads}</div></div>", unsafe_allow_html=True)
        with m4: st.markdown(f"<div class='db-card'><p style='margin:0; font-weight:1000; color:blue;'>CHỐT</p><div class='db-num-capsule' style='color:blue;'>{len(df_m[df_m['status'] == 'Closed'])}</div></div>", unsafe_allow_html=True)

        st.divider()
        # Lọc và Tìm kiếm
        c_sch, c_sld = st.columns([6, 4])
        q_s = c_sch.text_input("TÌM KIẾM THEO TÊN, SỐ ĐIỆN THOẠI...", key="q_search").lower().strip()
        days_limit = c_sld.slider("LỌC THEO SỐ NGÀY CHƯA TƯƠNG TÁC", 0, 90, 90)

        # Apply Filter
        filtered = df_m[(df_m.apply(lambda r: q_s in str(r).lower(), axis=1)) & (df_m['days_diff'] <= days_limit)]

        for idx, row in filtered.iterrows():
            c_cell = clean_phone(row['cell'])
            with st.container(border=True):
                ci, ce = st.columns([9.3, 0.7])
                with ci:
                    st.markdown(f"<span class='client-title'>{row['name']}</span> | <a href='{row['crm_link']}' target='_blank'>ID: {row['crm_id']}</a>", unsafe_allow_html=True)
                    st.markdown(f"BANG: {row['state']} | OWNER: {row['owner']} | STATUS: **{row['status']}**")
                    st.markdown(f"CELL: {c_cell} | EMAIL: {row['email']} | TAGS: {row['tags']}")
                    st.caption(f"Cập nhật lần cuối: {row['last_updated']}")
                    
                    st.markdown(f"<a href='rcmobile://sms?number={c_cell}'>SMS</a> | <a href='mailto:{row['email']}'>EMAIL</a>", unsafe_allow_html=True)

                with ce:
                    with st.popover("SỬA"):
                        with st.form(f"f_ed_{row['id']}"):
                            # 10 TRƯỜNG CẬP NHẬT
                            un = st.text_input("Tên", row['name'])
                            ui = st.text_input("CRM ID", row['crm_id'])
                            ul = st.text_input("CRM Link", row['crm_link'])
                            uc = st.text_input("Cell (SĐT chính)", row['cell'])
                            uw = st.text_input("Work (SĐT phụ)", row['work'])
                            ue = st.text_input("Email", row['email'])
                            us = st.text_input("Tiểu bang", row['state'])
                            uo = st.text_input("Người phụ trách", row['owner'])
                            utg = st.text_input("Thẻ (Tags)", row['tags'])
                            status_opts = ["New", "Contacted", "Following", "Closed"]
                            ust = st.selectbox("Trạng thái", status_opts, index=status_opts.index(row['status']) if row['status'] in status_opts else 0)
                            
                            if st.form_submit_button("CẬP NHẬT HỒ SƠ"):
                                conn.execute("""UPDATE leads SET 
                                    name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=?, status=?, last_updated=?
                                    WHERE id=?""", (un, ui, ul, uc, uw, ue, us, uo, utg, ust, datetime.now(NY_TZ).isoformat(), row['id']))
                                conn.commit(); st.rerun()

    with tab_add:
        st.markdown("### NHẬP HỒ SƠ KHÁCH HÀNG MỚI (10 TRƯỜNG)")
        with st.form("add_new_full_form", clear_on_submit=True):
            r1c1, r1c2, r1c3 = st.columns(3)
            an_name = r1c1.text_input("Họ và Tên")
            an_id = r1c2.text_input("CRM ID")
            an_link = r1c3.text_input("CRM Link")
            
            r2c1, r2c2, r2c3 = st.columns(3)
            an_cell = r2c1.text_input("Số điện thoại (Cell)")
            an_work = r2c2.text_input("Số làm việc (Work)")
            an_email = r2c3.text_input("Địa chỉ Email")
            
            r3c1, r3c2, r3c3 = st.columns(3)
            an_state = r3c1.text_input("Tiểu bang (State)")
            an_owner = r3c2.text_input("Người phụ trách", value="Cong")
            an_tags = r3c3.text_input("Thẻ phân loại (Tags)")
            
            # Trường thứ 10: Status
            an_status = st.selectbox("Trạng thái ban đầu", ["New", "Contacted", "Following", "Closed"])
            
            if st.form_submit_button("LƯU HỒ SƠ MỚI", use_container_width=True):
                if an_name and an_cell:
                    try:
                        conn.execute("""INSERT INTO leads (name, crm_id, crm_link, cell, work, email, state, owner, tags, status, last_updated) 
                                        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                                     (an_name, an_id, an_link, an_cell, an_work, an_email, an_state, an_owner, an_tags, an_status, datetime.now(NY_TZ).isoformat()))
                        conn.commit()
                        st.success(f"Đã lưu hồ sơ cho {an_name} thành công!"); st.rerun()
                    except: st.error("Lỗi: Số điện thoại này đã có trong hệ thống!")
                else: st.warning("Vui lòng nhập ít nhất Tên và Số điện thoại Cell.")
    conn.close()

# PHÂN HỆ: MẮT THẦN (THEO DÕI)
elif selected == "Mắt Thần":
    st.markdown("<div class='main-card'><h2>THEO DÕI TRUY CẬP REAL-TIME</h2></div>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    df_eye = pd.read_sql("SELECT * FROM leads WHERE note LIKE '%KHÁCH ĐANG XEM%' ORDER BY last_updated DESC", conn)
    if not df_eye.empty:
        for idx, row in df_eye.iterrows():
            with st.container(border=True):
                st.write(f"Khách hàng: **{row['name']}** ({row['cell']})")
                st.caption(f"Lịch sử truy cập: {row['note']}")
    else: st.info("Chưa có ghi nhận truy cập từ khách hàng.")
    conn.close()

# PHÂN HỆ: CẤU HÌNH (THIẾT LẬP GIAO DIỆN)
elif selected == "Cấu Hình":
    st.markdown("<div class='main-card'><h2>CÀI ĐẶT HỆ THỐNG</h2></div>", unsafe_allow_html=True)
    with st.form("config_form"):
        new_slogan = st.text_input("Slogan dòng IUL", value=prof.get('slogan'))
        c1, c2, c3 = st.columns(3)
        up_l = c1.file_uploader("Logo Sidebar", type=["png", "jpg"])
        up_n = c2.file_uploader("Ảnh National Life", type=["png", "jpg"])
        up_i = c3.file_uploader("Ảnh dòng IUL", type=["png", "jpg"])
        
        if st.form_submit_button("LƯU TẤT CẢ THAY ĐỔI"):
            conn = sqlite3.connect(DB_NAME)
            if up_l:
                with open("logo_app.png", "wb") as f: f.write(up_l.getbuffer())
                conn.execute("UPDATE profile SET logo_app='logo_app.png' WHERE id=1")
            if up_n:
                with open("img_nat.jpg", "wb") as f: f.write(up_n.getbuffer())
                conn.execute("UPDATE profile SET img_national='img_nat.jpg' WHERE id=1")
            if up_i:
                with open("img_iul.jpg", "wb") as f: f.write(up_i.getbuffer())
                conn.execute("UPDATE profile SET img_iul='img_iul.jpg' WHERE id=1")
            conn.execute("UPDATE profile SET slogan=? WHERE id=1", (new_slogan,))
            conn.commit(); conn.close(); st.success("Đã cập nhật cấu hình!"); st.rerun()
