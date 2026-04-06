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

# Load CSS từ file style.css
try:
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except: pass

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Bảng Leads với đầy đủ 10 trường dữ liệu anh yêu cầu
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, crm_id TEXT, crm_link TEXT,
                    cell TEXT UNIQUE, work TEXT, email TEXT,
                    state TEXT, owner TEXT, tags TEXT,
                    status TEXT DEFAULT 'New', note TEXT DEFAULT '', 
                    last_updated TIMESTAMP)''')
    
    # Bảng Profile
    c.execute('''CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY, slogan TEXT)''')
    
    # Cơ chế tự động thêm cột để tránh lỗi KeyError khi nâng cấp
    cols = [('logo_app', 'TEXT'), ('img_national', 'TEXT'), ('img_iul', 'TEXT')]
    for col_name, col_type in cols:
        try: c.execute(f"ALTER TABLE profile ADD COLUMN {col_name} {col_type}")
        except: pass
            
    c.execute("SELECT count(*) FROM profile")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO profile (id, slogan) VALUES (1, 'Mang lại sự bình yên và thịnh vượng cho mọi gia đình')")
    conn.commit()
    conn.close()

init_db()

def get_profile():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    res = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()
    return dict(res) if res else {}

# --- 2. SIDEBAR & ĐIỀU HƯỚNG ---
prof = get_profile()

with st.sidebar:
    logo_app = prof.get('logo_app')
    if logo_app and os.path.exists(logo_app):
        st.image(logo_app, use_container_width=True)
    else:
        st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
    
    st.divider()
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        selected = option_menu(
            menu_title=None,
            options=["Trang Chủ", "Mắt Thần", "Vận Hành", "Cấu Hình"],
            icons=["house", "eye", "gear", "person-badge"],
            styles={"nav-link-selected": {"background-color": "#00263e"}}
        )
        if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    else:
        selected = "Trang Chủ"

# --- 3. TẦNG KHÁCH HÀNG (Nhận diện qua link ?id=...) ---
query_params = st.query_params
id_khach = query_params.get("id")

if id_khach:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM leads WHERE cell = ?", (id_khach,)).fetchone()
    if row:
        t_now = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
        view_log = f"<div class='history-entry'><span class='note-time'>{t_now}</span> <span style='color:#f57c00; font-weight:bold;'>🔥 KHÁCH ĐANG XEM</span></div>"
        if "KHÁCH ĐANG XEM" not in str(row['note'])[:150]:
            new_note = view_log + str(row['note'])
            conn.execute("UPDATE leads SET note = ?, last_updated = ? WHERE cell = ?", 
                         (new_note, datetime.now(NY_TZ).isoformat(), id_khach))
            conn.commit()

        st.markdown(f"<h1 style='color:#00263e;'>🛡️ Chào {row['name']}</h1>", unsafe_allow_html=True)
        img_i = prof.get('img_iul')
        if img_i and os.path.exists(img_i): st.image(img_i, use_container_width=True)
        st.info("Kế hoạch tài chính cá nhân hóa của bạn từ National Life Group.")
    conn.close()
    st.stop()

# --- 4. CÁC HÀM HIỂN THỊ TỪNG PHẦN ---

def show_home_page():
    st.markdown("""
        <style>
        [data-testid="column"] { width: 100% !important; flex: 1 1 calc(50% - 1rem) !important; }
        .main-card img { width: 100% !important; border-radius: 10px; }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="hero-banner"><h1>NATIONAL LIFE GROUP</h1><p>Experience the Peace of Mind Since 1848</p></div>', unsafe_allow_html=True)
    
    col_left, col_right = st.columns(2, gap="small")

    with col_left:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<p class="section-header">Tập Đoàn National Life Group</p>', unsafe_allow_html=True)
        img_n = prof.get('img_national')
        if img_n and os.path.exists(img_n):
            st.image(img_n, use_container_width=True)
        else:
            st.image("https://www.nationallife.com/img/Logo-National-Life-Group.png", use_container_width=True)
        st.write("National Life Group là biểu tượng tin cậy tại Hoa Kỳ từ năm 1848.")
        st.markdown("- **Uy tín:** 170+ năm.\n- **Cam kết:** Giữ trọn lời hứa.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<p class="section-header">Giải Pháp Tài Chính IUL</p>', unsafe_allow_html=True)
        img_i = prof.get('img_iul')
        if img_i and os.path.exists(img_i):
            st.image(img_i, use_container_width=True)
        else:
            st.info("Vào mục Cấu Hình để upload ảnh IUL.")
        st.write(f"**{prof.get('slogan')}**")
        st.write("IUL kết hợp bảo vệ và tích lũy hưu trí không thuế.")
        st.markdown("- **An toàn:** 0% sàn.\n- **Linh hoạt:** Rút tiền không thuế.")
        st.markdown('</div>', unsafe_allow_html=True)

    if not st.session_state.authenticated:
        st.write("<br>", unsafe_allow_html=True)
        with st.expander("🔐 QUẢN TRỊ HỆ THỐNG"):
            u = st.text_input("Username", key="login_u")
            p = st.text_input("Password", type="password", key="login_p")
            if st.button("XÁC NHẬN"):
                if u == "Cong" and p == "admin123":
                    st.session_state.authenticated, st.session_state.role, st.session_state.username = True, "Admin", "Cong"
                    st.rerun()

# --- 5. ĐIỀU HƯỚNG MENU CHÍNH ---

if selected == "Trang Chủ":
    show_home_page()

elif selected == "Mắt Thần":
    st.markdown("<div class='main-card'><h2 style='color:#00263e;'>👁️ THEO DÕI REAL-TIME</h2></div>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    df = pd.read_sql("SELECT * FROM leads WHERE note LIKE '%KHÁCH ĐANG XEM%' ORDER BY last_updated DESC", conn)
    if not df.empty:
        for idx, row in df.iterrows():
            with st.container(border=True):
                st.write(f"🔥 **{row['name']}** ({row['cell']})")
                st.caption(f"Trạng thái: {row['status']} | Owner: {row['owner']}")
                st.markdown(row['note'], unsafe_allow_html=True)
    else:
        st.info("Hiện chưa có khách hàng nào truy cập link.")
    conn.close()

elif selected == "Vận Hành":
    st.markdown("<div class='main-card'><h2 style='color:#00263e;'>⚙️ HỆ THỐNG VẬN HÀNH DỮ LIỆU</h2></div>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_NAME)
    
    # Lấy dữ liệu từ DB
    df_m = pd.read_sql("SELECT * FROM leads", conn)
    n_ny = datetime.now(NY_TZ)

    tab_list, tab_add = st.tabs(["📊 Danh sách Lead", "➕ Thêm mới"])

    with tab_list:
        # --- 1. DASHBOARD CHỈ SỐ ---
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f"<div class='db-card'><p style='margin:0; font-weight:1000;'>TỔNG LEAD</p><div class='db-num-capsule'>{len(df_m)}</div></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='db-card'><p style='margin:0; font-weight:1000; color:green;'>MỚI</p><div class='db-num-capsule'>{len(df_m[df_m['status'] == 'New'])}</div></div>", unsafe_allow_html=True)
        with m3:
            def is_late(r):
                try: 
                    last_i = r.get('last_updated')
                    if not last_i: return False
                    dt = datetime.fromisoformat(last_i)
                    if dt.tzinfo is None: dt = NY_TZ.localize(dt)
                    return (n_ny - dt).days > 7
                except: return False
            late_count = len(df_m[df_m.apply(is_late, axis=1)])
            st.markdown(f"<div class='db-card'><p style='margin:0; font-weight:1000; color:red;'>TRỄ (>7D)</p><div class='db-num-capsule' style='color:red;'>{late_count}</div></div>", unsafe_allow_html=True)
        with m4: st.markdown(f"<div class='db-card'><p style='margin:0; font-weight:1000; color:blue;'>CHỐT</p><div class='db-num-capsule' style='color:blue;'>{len(df_m[df_m['status'] == 'Closed'])}</div></div>", unsafe_allow_html=True)

        st.divider()

        # --- 2. BỘ LỌC TÌM KIẾM ---
        c_sch, c_sld = st.columns([7, 3])
        q_s = c_sch.text_input("🔍 Tìm kiếm lead...", key="q_s_leader_final").lower().strip()
        days_limit = c_sld.slider("⏳ Lọc khách trễ (ngày)", 0, 90, 90, key="sld_leader_final") 

        # Filter dữ liệu
        filtered = df_m[df_m.apply(lambda r: q_s in str(r).lower(), axis=1)]

        # --- 3. DANH SÁCH CARD KHÁCH HÀNG ---
        for idx, row in filtered.iterrows():
            u_key = f"ld_{row['id']}"
            c_cell = clean_phone(row['cell'])
            c_work = clean_phone(row.get('work', ''))
            
            with st.container(border=True):
                ci, cn, ce = st.columns([4.5, 5, 0.5])
                
                # Cột 1: Thông tin & Actions
                with ci:
                    st.markdown(f"<span class='client-title'>{row['name']}</span> | <a href='{row.get('crm_link','#')}' target='_blank'>🆔 {row.get('crm_id','N/A')}</a>", unsafe_allow_html=True)
                    st.markdown(f"📍 {row.get('state','')} | 👤 {row['owner']} | 🏷️ **{row['status']}** | 🏷️ *{row.get('tags', '')}*")
                    st.markdown(f"📱 <a href='tel:{c_cell}'>{c_cell}</a> | 🏢 <a href='tel:{c_work}'>{c_work}</a>", unsafe_allow_html=True)
                    
                    # Nút bấm nhanh SMS, Email...
                    a1, a2, a3 = st.columns([1,1,8])
                    a1.markdown(f"<a href='rcmobile://sms?number={c_cell}' style='text-decoration:none; font-size:20px;'>💬</a>", unsafe_allow_html=True)
                    a2.markdown(f"<a href='mailto:{row.get('email','')}' style='text-decoration:none; font-size:20px;'>✉️</a>", unsafe_allow_html=True)

                # Cột 2: Lịch sử & Ghi chú
                with cn:
                    st.markdown(f'<div class="history-container">{row["note"]}</div>', unsafe_allow_html=True)
                    c_n1, c_n2 = st.columns([8, 2])
                    with c_n1:
                        with st.form(key=f"f_nt_{u_key}", clear_on_submit=True):
                            ni = st.text_input("Ghi nhanh...", label_visibility="collapsed", key=f"in_{u_key}")
                            if st.form_submit_button("Lưu"):
                                t_str = datetime.now(NY_TZ).strftime('[%m/%d %H:%M]')
                                new_entry = f"<div class='history-entry'><span class='note-time'>{t_str}</span> {ni}</div>"
                                updated_note = new_entry + str(row['note'])
                                conn.execute("UPDATE leads SET note=?, last_updated=? WHERE id=?", 
                                             (updated_note, datetime.now(NY_TZ).isoformat(), row['id']))
                                conn.commit()
                                st.rerun()
                    with c_n2:
                        with st.popover("📝"):
                            en = st.text_area("Sửa History", value=format_note_for_edit(row['note']), height=250, key=f"area_{u_key}")
                            if st.button("Lưu lại", key=f"ed_note_{u_key}"):
                                fmt = "".join([f"<div class='history-entry'>{line.strip()}</div>" for line in en.split('\n') if line.strip()])
                                conn.execute("UPDATE leads SET note=? WHERE id=?", (fmt, row['id']))
                                conn.commit()
                                st.rerun()

                # Cột 3: Cài đặt (Sửa chi tiết)
                with ce:
                    with st.popover("⚙️"):
                        with st.form(f"f_ed_{u_key}"):
                            un = st.text_input("Tên", row['name'])
                            ui = st.text_input("ID", row.get('crm_id', ''))
                            ul = st.text_input("Link", row.get('crm_link', ''))
                            uc = st.text_input("Cell", row['cell'])
                            uw = st.text_input("Work", row.get('work', ''))
                            ue = st.text_input("Email", row.get('email', ''))
                            us = st.text_input("State", row.get('state', ''))
                            uo = st.text_input("Owner", row.get('owner', ''))
                            utg = st.text_input("Tags", row.get('tags', ''))
                            st_list = ["New", "Contacted", "Following", "Closed"]
                            ust = st.selectbox("Status", st_list, index=st_list.index(row['status']) if row['status'] in st_list else 0)
                            
                            if st.form_submit_button("CẬP NHẬT"):
                                conn.execute("""UPDATE leads SET 
                                    name=?, crm_id=?, crm_link=?, cell=?, work=?, email=?, state=?, owner=?, tags=?, status=?, last_updated=?
                                    WHERE id=?""", (un, ui, ul, uc, uw, ue, us, uo, utg, ust, datetime.now(NY_TZ).isoformat(), row['id']))
                                conn.commit()
                                st.success("Đã cập nhật!")
                                st.rerun()
    conn.close()

elif selected == "Cấu Hình":
    st.markdown("<div class='main-card'><h2 style='color:#00263e;'>👤 CÀI ĐẶT HỆ THỐNG</h2></div>", unsafe_allow_html=True)
    with st.form("config_form"):
        st.markdown("### 📝 Thay đổi Slogan")
        new_slogan = st.text_input("Slogan dòng IUL", value=prof.get('slogan'), label_visibility="collapsed")
        st.write("---")
        st.markdown("### 🖼️ Cập nhật Hình ảnh (Nhỏ gọn)")
        c1, c2, c3 = st.columns(3)
        with c1: up_logo = st.file_uploader("Logo Sidebar", type=["png", "jpg"], key="up_l")
        with c2: up_nat = st.file_uploader("Ảnh National Life", type=["png", "jpg"], key="up_n")
        with c3: up_iul = st.file_uploader("Ảnh dòng IUL", type=["png", "jpg"], key="up_i")
        
        if st.form_submit_button("💾 LƯU TẤT CẢ THAY ĐỔI", use_container_width=True):
            conn = sqlite3.connect(DB_NAME)
            if up_logo:
                with open("logo_app.png", "wb") as f: f.write(up_logo.getbuffer())
                conn.execute("UPDATE profile SET logo_app='logo_app.png' WHERE id=1")
            if up_nat:
                with open("img_nat.jpg", "wb") as f: f.write(up_nat.getbuffer())
                conn.execute("UPDATE profile SET img_national='img_nat.jpg' WHERE id=1")
            if up_iul:
                with open("img_iul.jpg", "wb") as f: f.write(up_iul.getbuffer())
                conn.execute("UPDATE profile SET img_iul='img_iul.jpg' WHERE id=1")
            conn.execute("UPDATE profile SET slogan=? WHERE id=1", (new_slogan,))
            conn.commit()
            conn.close()
            st.success("Đã lưu thành công!"); st.rerun()
