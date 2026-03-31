import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import time
import json
import os
from utils import add_indicators

# Load users
def load_users():
    if not os.path.exists("users.json"):
        return {}
    with open("users.json", "r") as f:
        return json.load(f)

# Save users
def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f)

st.set_page_config(page_title="Stock Dashboard", layout="wide")

# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "users" not in st.session_state:
    st.session_state.users = {}

users = st.session_state.users

if not st.session_state.logged_in:

    st.title("🔐 Login / Signup")

    option = st.selectbox("Choose", ["Login", "Signup"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if option == "Signup":
        if st.button("Create Account"):
            if username in users:
                st.error("User already exists")
            else:
                users[username] = password
                save_users(users)
                st.success("Account created! Please login.")

    if option == "Login":
        if st.button("Login"):
            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()
    
    if st.button(". LOGOUT ."):
        st.session_state.logged_in = False
        st.success("Logged out")
        st.rerun()

# Title
st.markdown("<h1 style='text-align:center;'>📊 Stock Market Dashboard</h1>", unsafe_allow_html=True)

# Inputs
col1, col2, col3 = st.columns(3)

with col1:
    ticker = st.text_input("Stock", "AAPL")

with col2:
    start_date = st.date_input("Start Date")

with col3:
    end_date = st.date_input("End Date")

refresh = st.checkbox("Enable Live Refresh (5 sec)")

# Smart interval selection
days = (end_date - start_date).days
interval = "1m" if days <= 7 else "1d"

# Load data
def load_data():
    return yf.download(ticker, start=start_date, end=end_date, interval=interval)

if st.button("Analyze") or refresh:

    data = load_data()

    if data.empty:
        st.error("No data found. Try different date range.")
    else:
        # Indicators
        data = add_indicators(data)

        # Live Price
        latest_price = data['Close'].dropna().values[-1].item()
        st.metric("💰 Current Price", f"${latest_price:.2f}")

        # Chart
        fig = go.Figure(data=[go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close']
        )])

        fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], name="MA50"))
        fig.add_trace(go.Scatter(x=data.index, y=data['MA200'], name="MA200"))

        st.plotly_chart(fig, use_container_width=True)

        # RSI
        st.subheader("📉 RSI Indicator")
        st.line_chart(data['RSI'])

        # Insights
        st.subheader("🧠 Insights")

        rsi_value = data['RSI'].iloc[-1]

        if rsi_value > 70:
            st.warning("⚠️ Overbought (Sell)")
        elif rsi_value < 30:
            st.success("💡 Oversold (Buy)")
        else:
            st.info("Neutral Market")

        # Trading Signal
        st.subheader("🚨 Trading Signal")

        if data['MA50'].iloc[-1] > data['MA200'].iloc[-1]:
            st.success("🟢 BUY Signal (Golden Cross)")
        else:
            st.error("🔴 SELL Signal (Death Cross)")

# Auto refresh
if refresh:
    time.sleep(5)
    st.rerun()