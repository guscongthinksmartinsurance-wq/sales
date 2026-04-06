import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import os
import urllib.parse

# --- 1. CẤU HÌNH & CSS ---
st.set_page_config(page_title="TMC ELITE SYSTEM", layout="wide")
NY_TZ = pytz.timezone('America/New_York')
DB_NAME = "tmc_database.db"

# CSS Elite: Tách bạch các ô nhập liệu
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .client-card {
        background: white; padding: 24px; border-radius: 16px;
        border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .action-link {
        color: #0369a1; text-decoration: none; font-weight: 600;
        padding: 8px 15px; border-radius: 8px; background: #f1f5f9;
        font-size: 13px; display: inline-block; margin-right: 5px; margin-bottom: 5px;
    }
    .action-link:hover { background: #0ea5e9; color: white; }
    
    /* Fix dính chữ trong Popover */
    [data-testid="stForm"] {
        border: none !important;
        padding: 0px !important;
    }
    .stTextInput, .stSelectbox {
        margin-bottom: 15px !important; /* Tạo khoảng cách giữa các ô nhập liệu */
    }
    </style>
""", unsafe_allow_html=True)

# (Hàm clean_phone và init_db giữ nguyên như cũ)

# --- 3. VẬN HÀNH ---
# ... (Phần Dashboard giữ nguyên)

# Phần hiển thị Card khách hàng
with tab_list:
    # ... (Phần Search và Slider giữ nguyên)
    for idx, row in filtered.iterrows():
        u_key = f"ld_{row['id']}"
        c_cell = clean_phone(row['cell'])
        c_work = clean_phone(row.get('work', ''))
        
        with st.container():
            st.markdown(f"""
            <div class="client-card">
                <div style="display: flex; justify-content: space-between;">
                    <div style="flex: 5;">
                        <div style="font-size: 20px; font-weight: 700; color: #0f172a; margin-bottom:10px;">{row['name']} | <a href="{row['crm_link']}" target="_blank" style="text-decoration:none; color:#0ea5e9;">ID: {row['crm_id']}</a></div>
                        <div style="margin-bottom: 15px; font-size: 14px; color:#64748b;">
                            📍 {row['state']} | 👤 {row['owner']} | 🏷️ <b>{row['status']}</b>
                        </div>
                        <div>
                            <a href="tel:{c_cell}" class="action-link">📞 {c_cell}</a>
                            <a href="rcmobile://call?number={c_cell}" class="action-link">📞 RC Cell</a>
                            <a href="rcmobile://call?number={c_work}" class="action-link">🏢 RC Work: {c_work}</a>
                        </div>
                        <div style="margin-top:5px;">
                            <a href="rcmobile://sms?number={c_cell}" class="action-link">💬 SMS</a>
                            <a href="mailto:{row['email']}" class="action-link">✉️ Email</a>
                            <a href="https://calendar.google.com/calendar/r/eventedit?text=Meeting_{urllib.parse.quote(row['name'])}" target="_blank" class="action-link">📅 Calendar</a>
                        </div>
                    </div>
                    <div style="flex: 5; border-left: 1px solid #e2e8f0; padding-left: 20px;">
                        <div style="font-size: 12px; font-weight: 700; color: #94a3b8; margin-bottom: 8px;">LỊCH SỬ TƯƠNG TÁC</div>
                        <div style="height: 150px; overflow-y: auto; font-size: 14px; line-height: 1.6;">{row['note']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # PHẦN TÙY CHỈNH ĐÃ FIX DÍNH CHỮ
            c_act1, c_act2 = st.columns([8.5, 1.5])
            with c_act1:
                # Form ghi nhanh...
                pass
            with c_act2:
                with st.popover("⚙️ SỬA HỒ SƠ", use_container_width=True):
                    with st.form(f"f_ed_{u_key}"):
                        st.markdown("**Thông tin cơ bản**")
                        e1, e2 = st.columns(2)
                        un = e1.text_input("Tên khách", row['name'])
                        ui = e2.text_input("CRM ID", row['crm_id'])
                        
                        ul = st.text_input("CRM Link", row['crm_link'])
                        
                        st.markdown("**Liên lạc**")
                        e3, e4 = st.columns(2)
                        uc = e3.text_input("Cell Phone", row['cell'])
                        uw = e4.text_input("Work Phone", row.get('work',''))
                        
                        ue = st.text_input("Email", row.get('email',''))
                        
                        st.markdown("**Quản lý**")
                        e5, e6 = st.columns(2)
                        us = e5.text_input("State", row.get('state',''))
                        uo = e6.text_input("Owner", row['owner'])
                        
                        utg = st.text_input("Tags", row.get('tags',''))
                        
                        st_list = ["New", "Contacted", "Following", "Closed"]
                        ust = st.selectbox("Status", st_list, index=st_list.index(row['status']) if row['status'] in st_list else 0)
                        
                        if st.form_submit_button("LƯU THAY ĐỔI", use_container_width=True):
                            # Code UPDATE giữ nguyên
                            pass

# (Phần tab_add 10 trường giữ nguyên bố cục 3 cột)
