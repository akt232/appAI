import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import gspread
import json
import os

from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime


# =====================================================
# CONFIG
# =====================================================

CONFIG_FILE = "config.json"

DEFAULT_SHEET = "YOUR_ORDER_SHEET_LINK"
DEFAULT_TOUR_SHEET = ""

LOGO_URL = "https://travel.com.vn/Content/images/logo.png"

st.set_page_config(
    page_title="Vietravel Sales Hub",
    page_icon="🌍",
    layout="wide"
)


# =====================================================
# LOAD CONFIG
# =====================================================

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)

    return {
        "sheet_url": DEFAULT_SHEET,
        "tour_sheet_url": DEFAULT_TOUR_SHEET
    }


def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)


config = load_config()


# =====================================================
# SESSION
# =====================================================

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


# =====================================================
# CSS
# =====================================================

st.markdown("""
<style>
.stApp {background:#0f172a;color:#e2e8f0;}
.stButton>button {background:#1d4ed8;color:white;border-radius:6px;border:none;height:40px;}
.chat-box {background:#020617;border:1px solid #1e293b;border-radius:10px;height:60vh;display:flex;flex-direction:column;}
.chat-area {flex-grow:1;overflow-y:auto;padding:15px;}
.msg {background:#334155;padding:10px;border-radius:8px;margin-bottom:10px;}
</style>
""", unsafe_allow_html=True)


# =====================================================
# AI
# =====================================================

def ask_gemini(prompt):

    if not st.session_state.api_key:
        return "Chưa nhập API Key"

    try:
        genai.configure(api_key=st.session_state.api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content(prompt).text
    except Exception as e:
        return str(e)


# =====================================================
# GOOGLE SHEET CONNECT
# =====================================================

def connect_sheet(url):

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials.json", scope)

    client = gspread.authorize(creds)

    sheet = client.open_by_url(url).sheet1

    return sheet


def load_sheet():

    try:
        sheet = connect_sheet(st.session_state.sheet_url)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()


def load_tour_sheet():

    try:
        if not st.session_state.tour_sheet_url:
            return pd.DataFrame()

        sheet = connect_sheet(st.session_state.tour_sheet_url)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()


def save_to_sheet(row):

    try:
        sheet = connect_sheet(st.session_state.sheet_url)
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(e)
        return False


def delete_row(row_number):

    try:
        sheet = connect_sheet(st.session_state.sheet_url)
        sheet.delete_rows(row_number)
        return True
    except:
        return False


# =====================================================
# TOUR SUGGEST LOGIC (NO AI)
# =====================================================

def suggest_tour(message):

    df = load_tour_sheet()

    if df.empty:
        return pd.DataFrame()

    msg = message.lower()

    results = []

    for _, row in df.iterrows():

        text = " ".join([
            str(row.get("Tour", "")),
            str(row.get("Điểm đến", "")),
            str(row.get("Thời gian", ""))
        ]).lower()

        if any(word in msg for word in text.split()):
            results.append(row)

    return pd.DataFrame(results)


# =====================================================
# DASHBOARD
# =====================================================

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

    route_df = df.groupby("Tour").agg({
        "Tên": "count",
        "Giá": "sum"
    }).reset_index()

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(route_df, x="Tên", y="Tour", orientation="h")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(route_df, x="Giá", y="Tour", orientation="h")
        st.plotly_chart(fig, use_container_width=True)


# =====================================================
# SALES CENTER
# =====================================================

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
                    <div class="msg">{cust["msg"]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ===== TOUR SUGGEST =====

            st.subheader("🎯 Tour phù hợp (từ dữ liệu)")

            suggest_df = suggest_tour(cust["msg"])

            if suggest_df.empty:
                st.info("Không tìm thấy tour phù hợp")
            else:
                st.dataframe(suggest_df)

            # ===== STATUS =====

            status = st.selectbox(
                "Trạng thái",
                ["Đang theo dõi", "Đã chốt đơn", "Không chốt"]
            )

            if status == "Đã chốt đơn":

                with st.form("deal"):

                    name = st.text_input("Tên", cust["name"])
                    tour = st.text_input("Tour")
                    price = st.text_input("Giá")
                    note = st.text_area("Note")

                    sale = st.text_input("Sale")

                    channel = st.selectbox(
                        "Kênh",
                        ["Online", "Facebook", "Zalo", "Chi nhánh"]
                    )

                    ok = st.form_submit_button("Xác nhận")

                    if ok:

                        saved = save_to_sheet([
                            datetime.now().strftime("%Y-%m-%d"),
                            name,
                            tour,
                            price,
                            note,
                            channel,
                            sale
                        ])

                        if saved:
                            st.success("Đã lưu Sheet")

    # ===== AI CHAT =====

    with col_right:

        st.subheader("AI Hỏi Tour")

        user_q = st.text_input("Hỏi AI")

        if st.button("Gửi"):

            prompt = f"Bạn là chuyên gia du lịch. Trả lời: {user_q}"

            res = ask_gemini(prompt)

            st.session_state.chat_history.append(("Bạn", user_q))
            st.session_state.chat_history.append(("AI", res))

        for role, msg in st.session_state.chat_history:
            st.write(f"**{role}:** {msg}")


# =====================================================
# CUSTOMERS & ORDERS
# =====================================================

def render_customer_orders():

    st.title("Customers & Orders")

    st.subheader("Danh sách khách")
    st.dataframe(pd.DataFrame(st.session_state.customer_list))

    st.divider()

    df = load_sheet()

    st.subheader("Đơn đã chốt")

    if df.empty:
        st.info("Chưa có dữ liệu")
        return

    for idx, row in df.iterrows():

        col1, col2, col3, col4, col5, col6 = st.columns([2,2,2,2,2,1])

        with col1:
            st.write(row.get('Ngày',''))

        with col2:
            st.write(row.get('Tên',''))

        with col3:
            st.write(row.get('Tour',''))

        with col4:
            st.write(row.get('Giá',''))

        with col5:
            st.write(row.get('Kênh',''))

        with col6:

            if st.button("❌", key=f"del_{idx}"):

                ok = delete_row(idx + 2)

                if ok:
                    st.success("Đã xóa")
                    st.rerun()


# =====================================================
# SETTINGS
# =====================================================

def render_settings():

    st.title("Settings")

    key = st.text_input("Gemini API Key", value=st.session_state.api_key)

    if st.button("Save API"):
        st.session_state.api_key = key
        st.success("Saved")

    st.divider()

    st.subheader("Sheet Đơn Hàng")

    sheet_link = st.text_input(
        "Link Sheet Orders",
        value=st.session_state.sheet_url
    )

    st.subheader("Sheet Data Tour")

    tour_link = st.text_input(
        "Link Sheet Tour",
        value=st.session_state.tour_sheet_url
    )

    if st.button("Lưu cấu hình"):

        st.session_state.sheet_url = sheet_link
        st.session_state.tour_sheet_url = tour_link

        save_config({
            "sheet_url": sheet_link,
            "tour_sheet_url": tour_link
        })

        st.success("Đã lưu vĩnh viễn")


# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.image(LOGO_URL, width=150)

menu = st.sidebar.radio(
    "MENU",
    ["Dashboard", "Sales Center", "Customers & Orders", "Settings"]
)


# =====================================================
# ROUTER
# =====================================================

if menu == "Dashboard":
    render_dashboard()

elif menu == "Sales Center":
    render_sales_center()

elif menu == "Customers & Orders":
    render_customer_orders()

elif menu == "Settings":
    render_settings()
