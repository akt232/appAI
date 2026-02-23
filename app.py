import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import gspread
import json
import os
import requests
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

CONFIG_FILE = "config.json"
DEFAULT_SHEET = ""
LOGO_URL = "https://travel.com.vn/Content/images/logo.png"

st.set_page_config(
    page_title="Vietravel Sales Hub",
    page_icon="🌍",
    layout="wide"
)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"sheet_url": DEFAULT_SHEET, "tour_sheet_url": ""}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

config = load_config()

if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "sheet_url" not in st.session_state:
    st.session_state.sheet_url = config.get("sheet_url", DEFAULT_SHEET)
if "tour_sheet_url" not in st.session_state:
    st.session_state.tour_sheet_url = config.get("tour_sheet_url", "")
if "selected_customer" not in st.session_state:
    st.session_state.selected_customer = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "customer_list" not in st.session_state:
    st.session_state.customer_list = [
        {"id": 1, "name": "Anh Hùng", "msg": "Anh muốn đi Nhật tháng 3 ngân sách 40000000", "time": "10:30"},
        {"id": 2, "name": "Chị Lan", "msg": "Tour Thái Lan bao nhiêu tiền em?", "time": "09:15"},
        {"id": 3, "name": "Khách Web", "msg": "Tư vấn giúp tour Đà Nẵng", "time": "08:00"},
    ]

st.markdown("""
<style>
.stApp {background:#0f172a;color:#e2e8f0;}
.card {background:#020617;padding:20px;border-radius:10px;border:1px solid #1e293b;margin-bottom:20px;}
.stButton>button {background:#1d4ed8;color:white;border-radius:6px;border:none;height:40px;}
.chat-box {background:#020617;border:1px solid #1e293b;border-radius:10px;height:60vh;display:flex;flex-direction:column;}
.chat-area {flex-grow:1;overflow-y:auto;padding:15px;}
.msg {background:#334155;padding:10px;border-radius:8px;margin-bottom:10px;}
</style>
""", unsafe_allow_html=True)

def ask_gemini(prompt):
    if not st.session_state.api_key:
        return "Chưa nhập API Key"
    try:
        genai.configure(api_key=st.session_state.api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content(prompt).text
    except Exception as e:
        return str(e)

def extract_data(text):
    prompt = f"""
    Trích xuất thông tin khách hàng từ nội dung:
    {text}
    Trả JSON:
    {{
    "name":"",
    "tour":"",
    "budget":"",
    "note":""
    }}
    """
    res = ask_gemini(prompt)
    try:
        start = res.find('{')
        end = res.rfind('}') + 1
        return json.loads(res[start:end])
    except:
        return None

def connect_sheet(url):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(url).sheet1
    return sheet

def save_to_sheet(data_row):
    try:
        sheet = connect_sheet(st.session_state.sheet_url)
        sheet.append_row(data_row)
        return True
    except Exception as e:
        st.error(e)
        return False

def load_sheet():
    try:
        sheet = connect_sheet(st.session_state.sheet_url)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

def delete_row(row_number):
    try:
        sheet = connect_sheet(st.session_state.sheet_url)
        sheet.delete_rows(row_number)
        return True
    except Exception as e:
        st.error(e)
        return False

def load_tour_sheet():
    if not st.session_state.tour_sheet_url:
        return pd.DataFrame()
    try:
        sheet = connect_sheet(st.session_state.tour_sheet_url)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

def suggest_tour_logic(customer_text):
    df_tours = load_tour_sheet()
    if df_tours.empty:
        return pd.DataFrame()
    
    customer_text_lower = customer_text.lower()
    
    # Danh sách các từ khóa cần bỏ qua (stop words) để tránh bắt nhầm
    ignored_words = ["anh", "chị", "em", "muốn", "đi", "tư", "vấn", "giúp", "tour", "bao", "nhiêu", "tiền", "tháng"]
    
    # Tách các từ trong câu chat của khách và lọc bỏ từ vô nghĩa
    words = [w for w in customer_text_lower.split() if w not in ignored_words and len(w) > 1]
    
    matches = []
    for _, row in df_tours.iterrows():
        # Lấy dữ liệu từ cột "Tour (Tên tour)" và "Mô tả" (theo file của bạn)
        tour_name = str(row.get('Tour (Tên tour)', '')).lower()
        description = str(row.get('Mô tả', '')).lower()
        
        # Chỉ giữ lại tour nếu có ít nhất một từ khóa quan trọng xuất hiện
        is_match = any(word in tour_name for word in words) or \
                   any(word in description for word in words)
        
        if is_match:
            matches.append(row)
            
    # Trả về DataFrame chứa các dòng khớp, nếu không có thì trả về DF trống
    return pd.DataFrame(matches) if matches else pd.DataFrame()

def render_dashboard():
    st.title("📊 Dashboard")
    df = load_sheet()
    if df.empty:
        st.warning("Chưa có dữ liệu")
        return

    df["Giá"] = pd.to_numeric(df["Giá"], errors="coerce").fillna(0)
    df["Ngày"] = pd.to_datetime(df["Ngày"], errors="coerce")

    today = datetime.now().date()
    today_df = df[df["Ngày"].dt.date == today]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Khách hôm nay", len(today_df))
    col2.metric("Doanh thu hôm nay", f"{today_df['Giá'].sum():,.0f} đ")
    col3.metric("Tổng khách", len(df))
    col4.metric("Tổng doanh thu", f"{df['Giá'].sum():,.0f} đ")

    route_df = df.groupby("Tour").agg({"Tên": "count", "Giá": "sum"}).reset_index()
    route_df.columns = ["Tuyến", "Khách", "Doanh thu"]

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(route_df, x="Khách", y="Tuyến", orientation="h")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(route_df, x="Doanh thu", y="Tuyến", orientation="h")
        st.plotly_chart(fig, use_container_width=True)

def render_sales_center():
    col_left, col_mid, col_right = st.columns([1, 2, 1])

    with col_left:
        st.subheader("Khách hàng")
        for cust in st.session_state.customer_list:
            if st.button(f"{cust['name']} - {cust['time']}", key=cust["id"]):
                st.session_state.selected_customer = cust

    with col_mid:
        cust = st.session_state.selected_customer
        if cust:
            st.subheader(f"Chat với {cust['name']}")
            st.markdown(f"""
            <div class="chat-box">
                <div class="chat-area">
                    <div class="msg">{cust['msg']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.divider()
            st.subheader("🎯 Tour gợi ý (Dựa trên dữ liệu Sheet)")
            suggested_df = suggest_tour_logic(cust["msg"])
            
            if suggested_df is not None and not suggested_df.empty:
                st.dataframe(suggested_df, use_container_width=True)
            else:
                st.info("Không tìm thấy tour khớp trực tiếp trong Sheet dữ liệu.")

            status = st.selectbox("Trạng thái", ["Đang theo dõi", "Đã chốt đơn", "Không chốt"])

            if status == "Đã chốt đơn":
                data = extract_data(cust["msg"])
                name = data.get("name", cust["name"]) if data else cust["name"]
                tour = data.get("tour", "") if data else ""
                budget = data.get("budget", "") if data else ""
                note = data.get("note", "") if data else ""

                with st.form("deal"):
                    name = st.text_input("Tên", name)
                    tour = st.text_input("Tour", tour)
                    budget = st.text_input("Giá", budget)
                    note = st.text_area("Note", note)
                    sale = st.text_input("Sale")
                    channel = st.selectbox("Kênh", ["Online", "Facebook", "Zalo", "Chi nhánh"])
                    if st.form_submit_button("Xác nhận"):
                        saved = save_to_sheet([datetime.now().strftime("%Y-%m-%d"), name, tour, budget, note, channel, sale])
                        if saved: st.success("Đã lưu Sheet")

    with col_right:
        st.subheader("AI Tư Vấn")
        user_q = st.text_input("Hỏi AI")
        if st.button("Gửi"):
            res = ask_gemini(f"Bạn là chuyên gia tư vấn tour Vietravel. Trả lời: {user_q}")
            st.session_state.chat_history.append(("Bạn", user_q))
            st.session_state.chat_history.append(("AI", res))
        for role, msg in st.session_state.chat_history:
            st.write(f"**{role}:** {msg}")

def render_customer_orders():
    st.title("Customers & Orders")
    st.dataframe(pd.DataFrame(st.session_state.customer_list))
    st.divider()
    df = load_sheet()
    if df.empty:
        st.info("Chưa có dữ liệu")
        return
    for idx, row in df.iterrows():
        c1, c2, c3, c4, c5, c6 = st.columns([2,2,2,2,2,1])
        c1.write(row.get('Ngày',''))
        c2.write(row.get('Tên',''))
        c3.write(row.get('Tour',''))
        c4.write(row.get('Giá',''))
        c5.write(row.get('Kênh',''))
        if c6.button("❌", key=f"del_{idx}"):
            if delete_row(idx + 2): st.rerun()

def render_settings():
    st.title("Settings")
    key = st.text_input("Gemini API Key", value=st.session_state.api_key, type="password")
    if st.button("Save API"):
        st.session_state.api_key = key
        st.success("Saved")
    st.divider()
    sheet_link = st.text_input("Link Sheet Đơn", value=st.session_state.sheet_url)
    if st.button("Lưu Link Đơn"):
        st.session_state.sheet_url = sheet_link
        save_config({"sheet_url": sheet_link, "tour_sheet_url": st.session_state.tour_sheet_url})
    st.divider()
    tour_link = st.text_input("Link Sheet Tour Data", value=st.session_state.tour_sheet_url)
    if st.button("Lưu Link Tour"):
        st.session_state.tour_sheet_url = tour_link
        save_config({"sheet_url": st.session_state.sheet_url, "tour_sheet_url": tour_link})

st.sidebar.image(LOGO_URL, width=150)
menu = st.sidebar.radio("MENU", ["Dashboard", "Sales Center", "Customers & Orders", "Settings"])

if menu == "Dashboard": render_dashboard()
elif menu == "Sales Center": render_sales_center()
elif menu == "Customers & Orders": render_customer_orders()
elif menu == "Settings": render_settings()
