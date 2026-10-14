import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import hashlib
import secrets
import json
import os
from datetime import date, timedelta
from utils import add_indicators

# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================
st.set_page_config(
    page_title="Stock Analyzer | Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

USERS_FILE = "users.json"

# =====================================================
# 2. PREMIUM THEME
# =====================================================
st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(ellipse at 8% 82%, #06333b 0%, transparent 42%),
        radial-gradient(ellipse at 90% 10%, #172650 0%, transparent 42%),
        #030a15;
    color: #f4f7ff;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1500px;
    padding: 1.5rem 2.5rem 3rem;
}

#MainMenu, footer {
    visibility: hidden;
}

.brand {
    font-size: 29px;
    font-weight: 850;
    letter-spacing: -1px;
    margin-bottom: 32px;
}

.brand span, .accent {
    color: #28e8b0;
}

.eyebrow {
    display: inline-block;
    padding: 9px 15px;
    background: rgba(18, 43, 48, .85);
    border: 1px solid #3b625e;
    border-radius: 30px;
    color: #e8f7f7;
    font-size: 14px;
}

.hero-title {
    font-size: clamp(38px, 4vw, 61px);
    font-weight: 850;
    line-height: 1.08;
    letter-spacing: -2px;
    margin: 24px 0 18px;
}

.gradient-text {
    background: linear-gradient(90deg, #40efa4, #278cff);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.hero-description {
    color: #b4c5d9;
    font-size: 17px;
    line-height: 1.7;
}

.mini-stats {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin: 24px 0;
}

.mini-stat {
    flex: 1;
    min-width: 95px;
    padding: 15px 8px;
    text-align: center;
    background: rgba(9, 24, 40, .8);
    border: 1px solid #28506a;
    border-radius: 13px;
    transition: .2s ease;
}

.mini-stat:hover {
    transform: translateY(-4px);
    border-color: #28e8b0;
}

.stat-icon {
    font-size: 27px;
    margin-bottom: 5px;
}

.stat-label {
    font-size: 13px;
    color: #e0eafa;
}

.feature-card {
    background: linear-gradient(
        110deg, rgba(10, 34, 54, .94), rgba(9, 22, 40, .8)
    );
    border: 1px solid #28516c;
    border-radius: 14px;
    padding: 16px 18px;
    margin: 12px 0;
    transition: .2s ease;
}

.feature-card:hover {
    border-color: #28e8b0;
    transform: translateY(-2px);
}

.feature-card h3 {
    font-size: 17px;
    color: #f2f8ff;
    margin: 0 0 7px;
}

.feature-card p {
    color: #aec2d7;
    font-size: 13px;
    margin: 0;
}

.login-panel {
    background: linear-gradient(
        145deg, rgba(14, 34, 57, .96), rgba(6, 15, 30, .98)
    );
    border: 1px solid #386c91;
    border-radius: 23px;
    padding: 25px 25px 15px;
    box-shadow: 0 15px 55px rgba(0, 0, 0, .28);
}

.login-heading {
    text-align: center;
    padding: 8px 0 18px;
}

.login-logo {
    font-size: 48px;
}

.login-title {
    font-size: 31px;
    font-weight: 850;
    margin: 4px 0;
}

.login-subtitle {
    color: #9fb3cc;
    margin-bottom: 10px;
}

div[data-testid="stTextInput"] input {
    background: #081625;
    border: 1px solid #39546f;
    border-radius: 10px;
    color: white;
    min-height: 44px;
}

div[data-testid="stTextInput"] input:focus {
    border-color: #2be7ac;
    box-shadow: 0 0 0 1px #2be7ac;
}

div.stButton > button {
    width: 100%;
    min-height: 47px;
    border-radius: 11px;
    border: 1px solid #28dcb5;
    color: white !important;
    background: linear-gradient(100deg, #15dca8, #2867ff) !important;
    font-weight: 750;
    transition: .2s ease;
}

div.stButton > button p {
    color: white !important;
}

div.stButton > button:hover {
    filter: brightness(1.12);
    box-shadow: 0 5px 22px rgba(28, 170, 220, .25);
}

div[data-testid="stRadio"] label {
    color: #edf5ff;
}

.login-footer {
    text-align: center;
    color: #9aafc9;
    font-size: 13px;
    line-height: 1.7;
    padding: 18px 0 5px;
}

@media (max-width: 768px) {
    .block-container {
        padding: 1rem;
    }
    .brand {
        margin-bottom: 18px;
    }
    .hero-title {
        font-size: 38px;
    }
    .login-panel {
        padding: 17px;
    }
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. USER STORAGE AND PASSWORD SECURITY
# =====================================================
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=2)


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        300000
    ).hex()

    return {"salt": salt, "hash": hashed}


def verify_password(password, stored):
    # Supports previously saved plaintext accounts for migration.
    # New accounts are always stored as salted password hashes.
    if isinstance(stored, str):
        return secrets.compare_digest(password, stored)

    if not isinstance(stored, dict):
        return False

    salt = stored.get("salt", "")
    expected = stored.get("hash", "")

    if not salt or not expected:
        return False

    actual = hash_password(password, salt)["hash"]
    return secrets.compare_digest(actual, expected)


# =====================================================
# 4. SESSION STATE
# =====================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "auth_option" not in st.session_state:
    st.session_state.auth_option = "Login"


# =====================================================
# 5. PREMIUM LOGIN / SIGNUP PAGE
# =====================================================
if not st.session_state.logged_in:

    left, right = st.columns([1.05, 1], gap="large")

    # LEFT: LANDING PAGE
    with left:
        st.html("""
        <div class="brand">📈 Stock <span>Analyzer</span></div>

        <div style="margin-top:20px">
            <span class="eyebrow">
                🟢 &nbsp; Real-time Market Insights
            </span>

            <div class="hero-title">
                Analyze Stocks<br>
                <span class="gradient-text">Smarter, Faster.</span>
            </div>

            <p class="hero-description">
                A powerful stock market dashboard to explore financial
                time-series data, analyze market trends using technical
                indicators, and understand price movements through
                interactive visualizations.
            </p>
        </div>

        <div class="mini-stats">
            <div class="mini-stat">
                <div class="stat-icon">📈</div>
                <div class="stat-label">Market Data</div>
            </div>
            <div class="mini-stat">
                <div class="stat-icon">🕯️</div>
                <div class="stat-label">Indicators</div>
            </div>
            <div class="mini-stat">
                <div class="stat-icon">📊</div>
                <div class="stat-label">Charts</div>
            </div>
            <div class="mini-stat">
                <div class="stat-icon">⚡</div>
                <div class="stat-label">Analytics</div>
            </div>
        </div>

        <div class="feature-card">
            <h3>📈 Market Analytics</h3>
            <p>Explore historical prices and the latest available market data.</p>
        </div>

        <div class="feature-card">
            <h3>📉 Technical Indicators</h3>
            <p>Analyze MA50, MA200 and RSI to study market momentum.</p>
        </div>

        <div class="feature-card">
            <h3>⚡ Interactive Visualization</h3>
            <p>Explore candlestick charts, price movements and trends.</p>
        </div>

        <p style="color:#8fa9c2;font-size:12px;margin-top:20px">
            Built with Python • Pandas • Plotly • Streamlit • yfinance
        </p>
        """)

    # RIGHT: AUTHENTICATION CARD
    with right:
        st.markdown('<div class="login-panel">', unsafe_allow_html=True)

        st.html("""
        <div class="login-heading">
            <div class="login-logo">📈</div>
            <div class="login-title">
                Stock <span class="accent">Analyzer</span>
            </div>
            <div class="login-subtitle">
                Your Personal Market Companion
            </div>
        </div>
        """)

        option = st.radio(
            "Account",
            ["Login", "Sign Up"],
            horizontal=True,
            label_visibility="collapsed",
            key="auth_option"
        )

        username = st.text_input(
            "Username",
            placeholder="Enter your username",
            key="auth_username"
        ).strip()

        password = st.text_input(
            "Password",
            placeholder="Enter your password",
            type="password",
            key="auth_password"
        )

        confirm_password = ""

        if option == "Sign Up":
            confirm_password = st.text_input(
                "Confirm Password",
                placeholder="Re-enter your password",
                type="password",
                key="confirm_password"
            )

        remember = st.checkbox("Remember me for this session")

        if option == "Login":
            if st.button("Login  →", key="login_button"):
                users = load_users()
                stored = users.get(username)

                if not username or not password:
                    st.error("Please enter your username and password.")

                elif stored is not None and verify_password(password, stored):
                    # Upgrade a legacy plaintext password to a hash.
                    if isinstance(stored, str):
                        users[username] = hash_password(password)
                        save_users(users)

                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.remember_session = remember
                    st.rerun()

                else:
                    st.error("Invalid username or password.")

        else:
            if st.button("Create Account  →", key="signup_button"):
                users = load_users()

                if not username or not password:
                    st.error("Username and password are required.")

                elif len(username) < 3:
                    st.error("Username must contain at least 3 characters.")

                elif len(password) < 8:
                    st.error("Password must contain at least 8 characters.")

                elif password != confirm_password:
                    st.error("Passwords do not match.")

                elif username in users:
                    st.error("Username already exists.")

                else:
                    users[username] = hash_password(password)
                    save_users(users)
                    st.success("Account created! Select Login to continue.")

        st.html("""
        <div class="login-footer">
            ✦ &nbsp; Analyze trends. Explore insights.<br>
            Make informed decisions.
        </div>
        """)

        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()


# =====================================================
# 6. AUTHENTICATED STOCK DASHBOARD
# =====================================================
header_left, header_right = st.columns([4, 1])

with header_left:
    st.markdown(
        "<h1>📈 Stock Market Dashboard</h1>",
        unsafe_allow_html=True
    )
    st.caption(f"Welcome back, {st.session_state.username}!")

with header_right:
    if st.button("🚪 Logout", key="logout_button"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()


# =====================================================
# 7. STOCK INPUTS
# =====================================================
col1, col2, col3 = st.columns(3)

with col1:
    ticker = st.text_input("Stock Symbol", "AAPL").strip().upper()

with col2:
    start_date = st.date_input(
        "Start Date",
        value=date.today() - timedelta(days=30)
    )

with col3:
    end_date = st.date_input(
        "End Date",
        value=date.today()
    )

refresh = st.checkbox("Enable Live Refresh (30 seconds)")

if start_date > end_date:
    st.error("Start date must be on or before end date.")
    st.stop()

if end_date > date.today():
    st.error("End date cannot be in the future.")
    st.stop()

days = (end_date - start_date).days

# Yahoo Finance generally restricts 1-minute history to recent periods.
interval = "1m" if days <= 7 else "1d"

st.caption(
    f"Data interval: {interval} | Source: Yahoo Finance | "
    "Market data may be delayed."
)


# =====================================================
# 8. LOAD AND ANALYZE STOCK DATA
# =====================================================
@st.cache_data(ttl=30, show_spinner=False)
def load_data(symbol, start, end, data_interval):
    # yfinance end dates are exclusive.
    data = yf.download(
        symbol,
        start=start,
        end=end + timedelta(days=1),
        interval=data_interval,
        auto_adjust=True,
        progress=False,
        threads=False
    )

    if data.empty:
        return data

    # Flatten yfinance's MultiIndex columns when present.
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    return data


analyze = st.button("🔍 Analyze Stock", key="analyze_button")

if analyze:
    if not ticker:
        st.error("Enter a stock symbol.")
        st.stop()

    try:
        with st.spinner("Fetching market data and calculating indicators..."):
            data = load_data(
                ticker,
                start_date,
                end_date,
                interval
            )

        if data.empty:
            st.warning(
                "No data found. Check the stock symbol, date range, "
                "market trading hours, or data provider availability."
            )
            st.stop()

        required = {"Open", "High", "Low", "Close"}
        if not required.issubset(data.columns):
            st.error("The returned dataset is missing required price columns.")
            st.stop()

        data = add_indicators(data)

        close = pd.to_numeric(data["Close"], errors="coerce").dropna()

        if close.empty:
            st.error("No valid closing prices were returned.")
            st.stop()

        latest_price = float(close.iloc[-1])
        previous_price = (
            float(close.iloc[-2]) if len(close) > 1 else latest_price
        )
        change = latest_price - previous_price
        percent_change = (
            (change / previous_price) * 100 if previous_price else 0
        )

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric(
            "Latest Available Price",
            f"${latest_price:,.2f}",
            f"{change:+.2f} ({percent_change:+.2f}%)"
        )

        metric2.metric("Data Points", f"{len(data):,}")
        metric3.metric("Selected Interval", interval)

        # Candlestick chart
        st.subheader(f"📊 {ticker} Price Trend")

        fig = go.Figure()

        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name=ticker
        ))

        for column, label in [
            ("MA50", "MA50"),
            ("MA200", "MA200")
        ]:
            if column in data.columns:
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data[column],
                    mode="lines",
                    name=label
                ))

        fig.update_layout(
            template="plotly_dark",
            height=550,
            xaxis_rangeslider_visible=False,
            margin=dict(l=15, r=15, t=30, b=15),
            legend=dict(orientation="h", y=1.02)
        )

        st.plotly_chart(fig, use_container_width=True)

        # RSI
        if "RSI" in data.columns:
            st.subheader("📉 Relative Strength Index (RSI)")
            st.line_chart(data["RSI"].dropna())

            rsi_values = data["RSI"].dropna()

            if not rsi_values.empty:
                rsi_value = float(rsi_values.iloc[-1])
                st.metric("Latest RSI", f"{rsi_value:.2f}")

                if rsi_value > 70:
                    st.warning("RSI indicates potentially overbought conditions.")
                elif rsi_value < 30:
                    st.success("RSI indicates potentially oversold conditions.")
                else:
                    st.info("RSI is within the neutral range.")

        # Trend summary
        st.subheader("🧠 Trend Summary")

        ma50_values = data["MA50"].dropna()
        ma200_values = data["MA200"].dropna()

        if ma50_values.empty or ma200_values.empty:
            st.warning("Unable to calculate moving averages. Check stock data.")
        else:
            ma50 = float(ma50_values.iloc[-1])
            ma200 = float(ma200_values.iloc[-1])

            col1, col2 = st.columns(2)
            col1.metric("MA50", f"{ma50:.2f}")
            col2.metric("MA200", f"{ma200:.2f}")

            if ma50 > ma200:
                st.success(
                    "📈 Positive trend: MA50 is above MA200."
                )
            elif ma50 < ma200:
                st.warning(
                    "📉 Negative trend: MA50 is below MA200."
                )
            else:
                st.info("➡️ Neutral trend: Both averages are equal.")

            if len(data) < 200:
                st.caption(
                    "Note: Fewer than 200 records are available. "
                    "The moving averages may use limited history."
                )

        st.caption(
            "Educational analysis only. Not financial advice."
        )
                
        # Download data
        csv = data.to_csv().encode("utf-8")
        st.download_button(
            "⬇️ Download Analysis CSV",
            data=csv,
            file_name=f"{ticker}_stock_analysis.csv",
            mime="text/csv"
        )

    except Exception as exc:
        st.error(
            "Unable to analyze this stock. Verify the symbol, date range, "
            "internet connection, and data provider availability."
        )
        st.exception(exc)


# =====================================================
# 9. PERIODIC REFRESH
# =====================================================
if refresh:
    import time
    time.sleep(30)
    st.rerun()