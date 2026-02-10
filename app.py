import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import random
from datetime import datetime

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG & GIAO DIỆN (UI/UX)
# ==========================================
st.set_page_config(
    page_title="Travel AI Pro CRM",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS TÙY CHỈNH: GIAO DIỆN DARK MODE CAO CẤP (CHUYÊN NGHIỆP)
st.markdown("""
<style>
    /* Nền tối chủ đạo */
    .stApp { background-color: #0f172a; color: #e2e8f0; }
    
    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #1e293b; border-right: 1px solid #334155; }
    
    /* Card/Box chứa thông tin */
    .css-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    
    /* Metric Box */
    div[data-testid="stMetric"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 15px;
    }
    label[data-testid="stMetricLabel"] { color: #94a3b8; }
    div[data-testid="stMetricValue"] { color: #38bdf8; }
    
    /* Tiêu đề & Text */
    h1, h2, h3 { color: #38bdf8 !important; font-family: 'Segoe UI', sans-serif; }
    .highlight { color: #facc15; font-weight: bold; }
    
    /* Chat Zalo Styles */
    .msg-user { background-color: #334155; color: white; padding: 10px 15px; border-radius: 15px 15px 5px 15px; margin: 5px 0; float: right; clear: both; max-width: 80%; }
    .msg-ai { background-color: #0284c7; color: white; padding: 10px 15px; border-radius: 15px 15px 15px 5px; margin: 5px 0; float: left; clear: both; max-width: 80%; }
    
    /* Ẩn header mặc định */
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. XỬ LÝ DỮ LIỆU (DATA ENGINE)
# ==========================================

# Khởi tạo Session State (Lưu trạng thái chat & form)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "ai", "content": "Chào anh/chị, em là trợ lý ảo Tour AI. Em có thể giúp gì cho anh/chị hôm nay?"}
    ]
if "form_data" not in st.session_state:
    st.session_state.form_data = {"name": "", "tour": "", "budget": "", "note": ""}

# Hàm tải dữ liệu (Thay thế phần này bằng pd.read_csv('LINK_GOOGLE_SHEET') khi dùng thật)
@st.cache_data
def load_data():
    # 1. Dữ liệu Hiệu suất Kênh (Theo ảnh biểu đồ bạn gửi)
    df_kenh = pd.DataFrame({
        'Kênh': ['Sảnh Trụ sở', 'Chi nhánh', 'Tổng đài', 'Đại lý/CTV', 'VPBL', 'Chat Zalo', 'FIT Vũng Tàu', 'Web Organic', 'Web Digital', 'App'],
        'Lượt khách': [213, 193, 136, 122, 54, 32, 29, 27, 31, 24],
        'Doanh thu (Tỷ)': [3.6, 3.7, 1.7, 2.3, 0.99, 0.53, 0.52, 0.46, 0.42, 0.18]
    })
    
    # 2. Dữ liệu Nhân viên (Leaderboard)
    df_sale = pd.DataFrame({
        'Sale': ['Nguyễn Văn A', 'Trần Thị B', 'Lê Văn C', 'Phạm Thị D', 'Hoàng Văn E'],
        'Khách hỏi': [100, 50, 80, 120, 60],
        'Chốt đơn': [10, 25, 15, 8, 30]
    })
    df_sale['Tỷ lệ (%)'] = (df_sale['Chốt đơn'] / df_sale['Khách hỏi'] * 100).round(1)
    
    return df_kenh, df_sale

df_kenh, df_sale = load_data()

# Hàm Logic AI Chatbot
def get_ai_response(text):
    text = text.lower()
    if "giá" in text or "bao nhiêu" in text:
        return "Dạ tour Thái Lan 5N4Đ trọn gói bên em đang có giá ưu đãi **7.990.000đ** (Bay Vietnam Airlines). Giá này đã bao gồm thuế phí và 23kg hành lý ạ."
    elif "visa" in text:
        return "Đi Thái Lan được miễn Visa anh/chị nhé! Chỉ cần Hộ chiếu còn hạn trên 6 tháng là bay được ngay ạ."
    elif "lịch trình" in text:
        return "Lịch trình đi Bangkok - Pattaya - Đảo Coral. Tặng vé Massage Thái và Buffet 86 tầng Baiyoke Sky ạ."
    else:
        return "Dạ em đã ghi nhận thông tin. Anh/Chị chờ xíu em kiểm tra lịch trống rồi báo lại ngay nhé!"

# ==========================================
# 3. SIDEBAR NAVIGATION (MENU PHÂN HỆ)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/201/201623.png", width=60)
    st.markdown("## TRAVEL AI PRO")
    st.caption("Phiên bản: Enterprise v2.0")
    st.markdown("---")
    
    # Menu chọn chức năng
    menu = st.radio("PHÂN HỆ QUẢN LÝ", 
        ["📊 Dashboard Quản trị", 
         "🎙️ Nhập liệu (Zero-Touch)", 
         "🤖 Trợ lý AI (Coaching)", 
         "💬 Zalo Chat AI"])
    
    st.markdown("---")
    st.info("🟢 AI Engine: **Online**")
    st.info("🟢 Tổng đài: **Connected**")

# ==========================================
# 4. NỘI DUNG TỪNG TRANG (MAIN CONTENT)
# ==========================================

# --- TRANG 1: DASHBOARD QUẢN TRỊ (BƯỚC 3) ---
if menu == "📊 Dashboard Quản trị":
    st.title("📊 Real-time Executive Dashboard")
    st.caption(f"Cập nhật lần cuối: {datetime.now().strftime('%H:%M %d/%m/%Y')}")

    # 1. KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng Doanh Thu", "14.3 Tỷ", "+12%", border=True)
    k2.metric("Lượt Khách", "855", "+48", border=True)
    k3.metric("Tỷ lệ Chốt TB", "24.5%", "-2%", border=True)
    k4.metric("Dòng tiền Pipeline", "2.1 Tỷ", "Hot", border=True)
    
    # 2. Charts Row 1 (Khách & Doanh thu - Giống hình bạn gửi)
    st.markdown("### 1. Hiệu suất Kinh doanh theo Kênh")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.caption("Lượt khách đăng ký")
        fig1 = px.bar(df_kenh.sort_values('Lượt khách'), x='Lượt khách', y='Kênh', orientation='h', 
                      text='Lượt khách', color_discrete_sequence=['#38bdf8'])
        fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c2:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.caption("Doanh thu (Tỷ VNĐ)")
        fig2 = px.bar(df_kenh.sort_values('Doanh thu (Tỷ)'), x='Doanh thu (Tỷ)', y='Kênh', orientation='h', 
                      text='Doanh thu (Tỷ)', color_discrete_sequence=['#f97316'])
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 3. Charts Row 2 (Pie & Leaderboard)
    st.markdown("### 2. Phân tích Tỷ trọng & Nhân sự")
    c3, c4 = st.columns(2)
    
    with c3:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.caption("Tỷ trọng Doanh thu (%)")
        fig3 = px.pie(df_kenh, values='Doanh thu (Tỷ)', names='Kênh', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c4:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.caption("Bảng xếp hạng Sale (Conversion Rate)")
        st.dataframe(
            df_sale.sort_values('Tỷ lệ (%)', ascending=False).style.background_gradient(cmap="Greens", subset=['Tỷ lệ (%)']),
            use_container_width=True, height=300
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # 4. Pipeline
    st.markdown("### 3. Dự báo Dòng tiền (Cashflow Pipeline)")
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    pipe_data = pd.DataFrame({'Giai đoạn': ['Tiềm năng', 'Báo giá', 'Chờ thanh toán', 'Tiền về két'], 'Giá trị': [10.5, 5.2, 2.3, 13.4]})
    fig4 = px.funnel(pipe_data, x='Giá trị', y='Giai đoạn', color='Giá trị', color_continuous_scale='Teal')
    fig4.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    st.plotly_chart(fig4, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- TRANG 2: NHẬP LIỆU (BƯỚC 1) ---
elif menu == "🎙️ Nhập liệu (Zero-Touch)":
    st.title("🎙️ Nhập liệu Thông minh (Omni-channel)")
    st.caption("AI tự động lắng nghe và bóc tách dữ liệu từ cuộc gọi/tin nhắn.")

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("1. Nguồn dữ liệu")
        source = st.selectbox("Chọn kênh:", ["📞 Tổng đài Stringee", "💬 Zalo OA Webhook", "🎤 Ghi âm tại quầy"])
        
        if st.button("🔴 Bắt đầu Ghi nhận (Simulate)"):
            with st.spinner("AI đang chuyển giọng nói thành văn bản..."):
                time.sleep(1.5)
            st.success("Đã nhận tín hiệu!")
            raw_text = "Alo em, anh là Nam. Anh muốn tìm tour Thái Lan tháng 6 này cho gia đình 5 người. Ngân sách tầm 8 triệu một người. Lưu ý nhà có bà già cần xe lăn nhé."
            st.text_area("Văn bản gốc (Speech-to-Text):", raw_text, height=100)
            
            # Giả lập AI bóc tách
            st.session_state.form_data = {
                "name": "Anh Nam", "tour": "Thái Lan 5N4Đ", "budget": "8.000.000 VNĐ", "note": "Có người già, cần xe lăn. Đi tháng 6."
            }
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("2. AI Auto-Fill Form")
        with st.form("lead_form"):
            c_a, c_b = st.columns(2)
            name = c_a.text_input("Họ tên", value=st.session_state.form_data["name"])
            tour = c_b.text_input("Nhu cầu", value=st.session_state.form_data["tour"])
            budget = c_a.text_input("Ngân sách", value=st.session_state.form_data["budget"])
            time_trip = c_b.text_input("Thời gian", "Tháng 6")
            note = st.text_area("Ghi chú đặc biệt", value=st.session_state.form_data["note"])
            
            if st.form_submit_button("✅ Lưu Lead vào Hệ thống"):
                st.toast("Đã lưu khách hàng thành công!", icon="🚀")
        st.markdown('</div>', unsafe_allow_html=True)

# --- TRANG 3: TRỢ LÝ AI (BƯỚC 2) ---
elif menu == "🤖 Trợ lý AI (Coaching)":
    st.title("🤖 Trợ lý Sale & Lead Scoring")
    
    c_left, c_right = st.columns([1, 1.5])
    
    with c_left:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("🔥 Lead Scoring")
        st.metric("Điểm tiềm năng", "85/100", "HOT LEAD")
        st.progress(85)
        st.markdown("""
        **Phân tích hành vi:**
        - ✅ Đã hỏi số tài khoản
        - ✅ Đã hỏi thủ tục Visa
        - ⚠️ **Cảnh báo:** Chưa gọi lại quá 2h
        """)
        st.button("📞 Gọi ngay")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c_right:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("💡 Live Coaching (Nhắc bài)")
        st.info("🗣️ Khách đang hỏi: **'Sao giá bên em cao hơn bên A thế?'**")
        
        st.markdown("""
        <div style="background-color: #422006; border-left: 4px solid #f97316; padding: 15px; color: #ffedd5; border-radius: 5px;">
            <b>🤖 KỊCH BẢN TRẢ LỜI GỢI Ý:</b><br><br>
            "Dạ, sở dĩ bên A rẻ hơn vì họ bay <b>Vietjet (không hành lý)</b> và khách sạn xa trung tâm.<br>
            Tour mình bay <b>Vietnam Airlines (có 23kg hành lý)</b> + Khách sạn 4 sao ngay trung tâm + Ăn đủ 5 bữa chính (Họ chỉ 3 bữa).<br>
            Tính ra bên mình còn tiết kiệm hơn nếu anh mua thêm hành lý bên kia ạ."
        </div>
        """, unsafe_allow_html=True)
        st.text_area("Ghi chú cuộc gọi:", placeholder="Nhập kết quả...")
        st.button("Lưu lịch sử")
        st.markdown('</div>', unsafe_allow_html=True)

# --- TRANG 4: ZALO CHAT AI (TÍCH HỢP) ---
elif menu == "💬 Zalo Chat AI":
    st.title("💬 Zalo Chat Integration")
    
    col_list, col_chat = st.columns([1, 2])
    
    with col_list:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("Tin nhắn mới")
        st.markdown("""
        - **Anh Nam** <span style='color:#4ade80; float:right'>Vừa xong</span><br>
          <small style='color:gray'>Giá tour bao nhiêu...</small><hr>
        - **Chị Lan** <span style='color:gray; float:right'>5p trước</span><br>
          <small style='color:gray'>Gửi mình lịch trình...</small><hr>
        """, unsafe_allow_html=True)
        
        st.markdown("**🛠️ Tool Test (Giả lập khách):**")
        if st.button("Simulate: Hỏi Giá"):
            st.session_state.chat_history.append({"role": "user", "content": "Tour này giá bao nhiêu shop?"})
            # AI Reply
            reply = get_ai_response("giá")
            st.session_state.chat_history.append({"role": "ai", "content": reply})
            st.rerun()
            
        if st.button("Simulate: Hỏi Visa"):
            st.session_state.chat_history.append({"role": "user", "content": "Có cần làm visa không?"})
            # AI Reply
            reply = get_ai_response("visa")
            st.session_state.chat_history.append({"role": "ai", "content": reply})
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_chat:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("Hội thoại: Anh Nam")
        
        # Chat container
        chat_container = st.container(height=400)
        with chat_container:
            for msg in st.session_state.chat_history:
                if msg["role"] == "ai":
                    st.markdown(f'<div class="msg-ai"><b>🤖 AI Gợi ý:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
        
        # Chat Input
        with st.form("chat_input", clear_on_submit=True):
            cols = st.columns([4, 1])
            inp = cols[0].text_input("Nhập tin nhắn...", placeholder="Nhập nội dung hoặc copy gợi ý AI...")
            btn = cols[1].form_submit_button("Gửi 🚀")
            
            if btn and inp:
                st.session_state.chat_history.append({"role": "user", "content": inp}) # Demo nên user là Sale
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)