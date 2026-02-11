import streamlit as st
import pandas as pd
import plotly.express as px
import time
import google.generativeai as genai  # <--- THƯ VIỆN AI CỦA GOOGLE

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG
# ==========================================
st.set_page_config(page_title="Real AI Travel CRM", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")

# CSS DARK MODE
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #e2e8f0; }
    section[data-testid="stSidebar"] { background-color: #1e293b; border-right: 1px solid #334155; }
    .css-card { background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; margin-bottom: 20px; }
    h1, h2, h3 { color: #38bdf8 !important; }
    .msg-user { background-color: #334155; color: white; padding: 10px; border-radius: 10px 10px 5px 10px; margin: 5px 0; float: right; clear: both; max-width: 80%; }
    .msg-ai { background-color: #0284c7; color: white; padding: 10px; border-radius: 10px 10px 10px 5px; margin: 5px 0; float: left; clear: both; max-width: 80%; }
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KẾT NỐI AI (THE BRAIN)
# ==========================================

# Sidebar nhập API Key (Để bảo mật)
with st.sidebar:
    st.title("🧠 CẤU HÌNH AI")
    api_key = st.text_input("Nhập Google Gemini API Key:", type="password")
    st.caption("Chưa có Key? Truy cập [aistudio.google.com](https://aistudio.google.com/app/apikey) để lấy miễn phí.")
    
    if api_key:
        genai.configure(api_key=api_key)
        st.success("Đã kết nối não bộ AI! 🟢")
    else:
        st.warning("Vui lòng nhập Key để AI hoạt động.")

# HÀM 1: AI TƯ VẤN KHÁCH HÀNG (ZALO CHAT)
def ask_gemini_chat(user_msg):
    if not api_key: return "⚠️ Vui lòng nhập API Key để tôi trả lời."
    
    # Kịch bản huấn luyện AI (System Prompt)
    prompt = f"""
    Bạn là một nhân viên Sale Tour du lịch xuất sắc, thân thiện và chốt sale giỏi của công ty 'Travel AI'.
    Sản phẩm chủ lực: Tour Thái Lan 5N4Đ, Bay Vietnam Airlines, Khách sạn 4 sao, Giá 7.990k.
    
    Khách hàng hỏi: "{user_msg}"
    
    Hãy trả lời ngắn gọn (dưới 3 câu), khéo léo, tập trung vào lợi ích (VD: Bay giờ đẹp, 23kg hành lý) và kêu gọi hành động.
    """
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Lỗi AI: {e}"

# HÀM 2: AI BÓC TÁCH DỮ LIỆU (ZERO-TOUCH)
def ask_gemini_extract(raw_text):
    if not api_key: return "Chưa có Key", "Chưa có Key", "Chưa có Key", "Chưa có Key"
    
    prompt = f"""
    Hãy trích xuất thông tin từ đoạn văn sau và trả về định dạng: Tên | Nhu cầu Tour | Ngân sách | Ghi chú.
    Nếu không có thông tin thì ghi "Không rõ".
    Đoạn văn: "{raw_text}"
    
    Chỉ trả về 1 dòng duy nhất ngăn cách bởi dấu |. Ví dụ: Anh Nam | Tour Nhật | 20 triệu | Ăn chay
    """
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        # Xử lý kết quả trả về
        parts = response.text.split('|')
        if len(parts) >= 4:
            return parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
        else:
            return parts[0], "Lỗi định dạng", "", ""
    except:
        return "Lỗi", "Lỗi", "Lỗi", "Lỗi"

# ==========================================
# 3. GIAO DIỆN & LOGIC
# ==========================================

# Dữ liệu mẫu & Session
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = {"name": "", "tour": "", "budget": "", "note": ""}

# Dữ liệu biểu đồ (Fake data để vẽ)
df_kenh = pd.DataFrame({'Kênh': ['Facebook', 'Zalo', 'Tổng đài', 'Website'], 'Doanh thu': [3.5, 2.1, 1.8, 4.2]})

# --- MENU CHÍNH ---
with st.sidebar:
    st.markdown("---")
    menu = st.radio("CHỨC NĂNG", ["🎙️ Nhập liệu AI (Thật)", "💬 Zalo Chat AI (Thật)", "📊 Dashboard"])

# --- TRANG 1: NHẬP LIỆU AI ---
if menu == "🎙️ Nhập liệu AI (Thật)":
    st.title("🎙️ AI Auto-Extraction (Bóc tách thật)")
    st.caption("AI sẽ đọc hiểu đoạn văn bất kỳ và điền vào form.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("1. Dữ liệu đầu vào")
        input_text = st.text_area("Nhập nội dung cuộc gọi/tin nhắn:", 
                                  value="Chị Lan cần tìm tour đi Hàn Quốc ngắm lá đỏ tháng 10 này. Nhà chị có 2 vợ chồng với 1 bé nhỏ 5 tuổi. Kinh phí tầm 15 triệu một người thôi em nhé.", height=150)
        
        if st.button("🚀 Yêu cầu AI Bóc tách"):
            with st.spinner("AI đang đọc hiểu..."):
                # GỌI HÀM AI THẬT
                n, t, b, no = ask_gemini_extract(input_text)
                st.session_state.extracted_data = {"name": n, "tour": t, "budget": b, "note": no}
            st.success("Đã xong!")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("2. Kết quả (Form tự động)")
        with st.form("result_form"):
            c_a, c_b = st.columns(2)
            st.text_input("Họ tên", value=st.session_state.extracted_data['name'])
            st.text_input("Nhu cầu", value=st.session_state.extracted_data['tour'])
            st.text_input("Ngân sách", value=st.session_state.extracted_data['budget'])
            st.text_area("Ghi chú", value=st.session_state.extracted_data['note'])
            st.form_submit_button("Lưu")
        st.markdown('</div>', unsafe_allow_html=True)

# --- TRANG 2: ZALO CHAT AI ---
elif menu == "💬 Zalo Chat AI (Thật)":
    st.title("💬 Zalo Chat với AI (Thông minh)")
    
    col_chat, col_tools = st.columns([2, 1])
    
    with col_tools:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("🛠️ Công cụ Test")
        st.info("Nhập câu hỏi bất kỳ, AI sẽ tự nghĩ câu trả lời chứ không theo mẫu.")
        test_msg = st.text_input("Giả lập khách hỏi:", "Tour này có đi đảo Coral không em?")
        if st.button("Gửi tin nhắn giả lập"):
            st.session_state.chat_history.append({"role": "user", "content": test_msg})
            # GỌI AI TRẢ LỜI
            ai_reply = ask_gemini_chat(test_msg)
            st.session_state.chat_history.append({"role": "ai", "content": ai_reply})
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_chat:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        chat_container = st.container(height=400)
        with chat_container:
            if not api_key:
                st.warning("⚠️ Hãy nhập API Key ở menu bên trái để Chatbot hoạt động!")
            
            for msg in st.session_state.chat_history:
                role_class = "msg-user" if msg['role'] == "user" else "msg-ai"
                prefix = "👤 Khách:" if msg['role'] == "user" else "🤖 AI:"
                st.markdown(f'<div class="{role_class}"><b>{prefix}</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
        
        # Ô nhập liệu thật
        if prompt := st.chat_input("Nhập tin nhắn trả lời khách..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            # Gọi AI trả lời
            response = ask_gemini_chat(prompt)
            st.session_state.chat_history.append({"role": "ai", "content": response})
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- TRANG 3: DASHBOARD ---
elif menu == "📊 Dashboard":
    st.title("📊 Báo cáo Doanh thu")
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    fig = px.bar(df_kenh, x='Doanh thu', y='Kênh', orientation='h', title="Doanh thu theo Kênh")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
