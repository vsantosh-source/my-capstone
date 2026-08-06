"""Main UI for Capstone demo.

Run:
  streamlit run landing_page.py
"""

import base64
from pathlib import Path

from openai import base_url
import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
import json
import httpx

WORKDIR_CMD = "Capstone"
MODELS = ["gpt-4o-mini", "gpt-4o", "o3-mini"]


def build_payload(question: str, model: str, force_bad: bool) -> dict:
    return {
        "question": question,
        "model": model,
        "force_bad": force_bad,
    }


def render_curl(base_url: str, payload: dict) -> str:
    body = json.dumps(payload)
    return (
        f'curl -s -X POST {base_url.rstrip("/")}/ask '
        f'-H "Content-Type: application/json" '
        f"-d '{body}'"
    )


def call_json(method: str, url: str, payload: dict | None = None) -> tuple[int, dict | str]:
    try:
        if method == "POST":
            response = httpx.post(url, json=payload, timeout=120.0)
        else:
            response = httpx.get(url, timeout=5.0)

        try:
            return response.status_code, response.json()
        except json.JSONDecodeError:
            return response.status_code, response.text
    except httpx.ConnectError:
        return 0, {"error": f"Cannot reach {url}. Start the API server first."}
    except httpx.HTTPError as exc:
        return 0, {"error": str(exc)}


def render_attempts(data: dict | str) -> None:
    if not isinstance(data, dict):
        return

    attempts = data.get("attempts", [])
    if not attempts:
        return

    st.markdown("### Attempts")
    for attempt in attempts:
        status = "passed" if attempt.get("ok") else "failed"
        title = f"Attempt {attempt.get('attempt')}: {attempt.get('step')} ({status})"
        with st.expander(title, expanded=True):
            st.write(attempt.get("message"))
            if attempt.get("raw_output"):
                st.markdown("**Raw model output**")
                st.code(attempt["raw_output"], language="json")
            if attempt.get("validation_error"):
                st.markdown("**Validation error**")
                st.code(attempt["validation_error"], language="text")


def render_response_summary(data: dict | str) -> None:
    if not isinstance(data, dict) or "error" in data:
        return

    answer = data.get("answer")
    if isinstance(answer, dict):
        st.markdown("### Answer")
        st.write(answer.get("answer", ""))
        #st.caption(
        #    f"confidence: {answer.get('confidence')} | "
        #    f"sources_needed: {answer.get('sources_needed')}"
        #)

    #metric_cols = st.columns(4)
    #metric_cols[0].metric("Model", str(data.get("model", "-")))
    #metric_cols[1].metric("Tokens", str(data.get("tokens_used", "-")))
    #metric_cols[2].metric("Latency", f"{data.get('latency_ms', '-')} ms")
    #metric_cols[3].metric("Cost", f"${data.get('cost_usd', '-')}")

# Enable the opaque theme globally
alt.theme.enable('opaque')

# Initialize session state for plan selection
if 'selected_plan' not in st.session_state:
    st.session_state.selected_plan = None

# Helper function to trigger scroll via JavaScript
def scroll_to_section():
    st.components.v1.html("""
        <script>
            (function() {
                var target = window.parent.document.getElementById('signup-section');
                if (target) {
                    target.scrollIntoView({behavior: 'smooth', block: 'start'});
                } else {
                    setTimeout(function() {
                        var t = window.parent.document.getElementById('signup-section');
                        if(t) t.scrollIntoView({behavior: 'smooth', block: 'start'});
                    }, 100);
                }
            })();
        </script>
    """, height=0)

# Callback function to set the selected plan and trigger scroll
def select_plan(plan_name):
    st.session_state.selected_plan = plan_name
    scroll_to_section()

# Page configuration
st.set_page_config(page_title="Social Alpha", layout="wide")



# Custom CSS for styling
st.markdown("""
<style>
    .stApp {
        background-color: #FFFFFF;
        color: #1F2937;
    }
    header[data-testid="stHeader"] {
        background-color: #FFFFFF;          /* White background for header */
    }
        /* Target the Metric Label (e.g., "Best stock") */
    .stMetric label {
        font-family: "Courier New", Courier, monospace; /* Change font family */
        font-size: 16px;                                /* Change font size */
        font-weight: bold;                              /* Change weight */
        color: #333333;                                 /* Change color */
    }
    /* Target the Metric Value (e.g., the stock price) */
    .stMetric .value {
        font-family: "Georgia", serif;
        font-size: 24px;
        color: #0E1117;
    }
    /* Optional: Target the Delta (percentage change) */
    .stMetric .delta {
        font-family: "Arial", sans-serif;
        font-size: 14px;
    }
    .pricing-card {
        background: white;
        border-radius: 12px;
        padding: 30px;
        width: 100%;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .pricing-card.standard {
        background: #F3E8FF;
    }
    .price {
        font-size: 2.5em;
        font-weight: bold;
        margin: 20px 0;
    }
    .period {
        font-size: 0.4em;
        color: #6B7280;
    }
    .features {
        text-align: left;
        margin: 20px 0;
        font-size: 0.9em;
        flex-grow: 1;
    }
    .feature-item {
        padding: 8px 0;
        border-bottom: 1px solid rgba(0,0,0,0.1);
    }
    .stButton > button {
        background: #7C3AED;
        color: white;
        padding: 12px 30px;
        border: none;
        border-radius: 8px;
        font-size: 1em;
        font-weight: bold;
        width: 100%;
        margin-top: 20px;
        transition: background 0.3s ease;
    }
    .stButton > button:hover {
        background: #6D28D9;
        color: white;
        border: none;
    }
    .header-section {
        text-align: center;
        padding: 40px 0 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .header-content {
        display: flex;
        align-items: center;
        gap: 20px;
        justify-content: center;
        margin-bottom: 10px;
    }
    .header-logo {
        max-height: 90px;
        width: auto;
    }
    .header-section h1 {
        color: #1F2937;
        font-size: 2.5em;
        margin: 0;
    }
    .header-section p {
        color: #6B7280;
        font-size: 1.1em;
        max-width: 600px;
        margin: 10px auto 0;
    }
    .dynamic-content {
        background: #F9FAFB;
        border-left: 5px solid #7C3AED;
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
        animation: fadeIn 0.5s ease-in;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# Header section with Logo
logo_path = Path(__file__).parent / "social_alpha_logo.png"
logo_url = f"data:image/png;base64,{base64.b64encode(logo_path.read_bytes()).decode()}"

st.markdown(f"""
<div class="header-section">
    <div class="header-content">
        <img src="{logo_url}" alt="Company Logo" class="header-logo">
        <h1>Trending products. Due Diligence. Institutional-quality Research.</h1>
    </div>
    <p style="font-size: 24px;">Identify trending consumer products and services. Invest confidently.</p>

</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Pricing cards
cols = st.columns(3)

# Define pricing plans (Monthly only)
plans = [
    {
        "name": "Retail Investor",
        "price": 8.00,
        "features": [
            "No credit card required",
            "Daily trend signals",
            "Basic ticker tracking",
            "Monthly reports"
        ],
        "details": "Perfect for individuals starting their investment journey. Get access to daily signals and basic tracking tools without any commitment."
    },
    {
        "name": "Equity Analyst",
        "price": 48.00,
        "features": [
            "Daily trend signals",
            "Advanced planning tools",
            "Weekly & monthly reports",
            "Priority support"
        ],
        "details": "Designed for serious analysts. Unlock advanced planning tools, comprehensive reports, and priority support to deepen your market analysis."
    },
    {
        "name": "Portfolio Manager",
        "price": 89.00,
        "features": [
            "Product & company analysis",
            "Complete financial analysis",
            "Competitive dynamics",
            "24/7 dedicated support"
        ],
        "details": "The ultimate solution for professional portfolio management. Includes complete financial analysis, competitive dynamics, and dedicated 24/7 support for teams."
    }
]

# Render pricing cards
for idx, plan in enumerate(plans):
    card_class = "pricing-card standard"
    
    with cols[idx]:
        st.markdown(f"""
        <div class="{card_class}">
            <h3>{plan["name"]}</h3>
            <div class="price">
                ${plan["price"]:.2f}
                <span class="period">per month</span>
            </div>
            <div class="features">
                {''.join([f'<div class="feature-item">✓ {feature}</div>' for feature in plan["features"]])}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Get Started - {plan['name']}", key=f"btn_{plan['name']}"):
            select_plan(plan['name'])

# --- DYNAMIC CONTENT SECTION ---

#STOCKS = [
#    "AAPL",
#    "AMZN",
#    "AVGO",
#    "VZ",
#]
#DEFAULT_STOCKS = ["AAPL", "MSFT", "GOOGL", "NVDA", "META"]

STOCKS = []
DEFAULT_STOCKS = []

CATEGORIES = [
    "Apparel",
    "Home Goods",
    "Technology"
]

def stocks_to_str(stocks):
    return ",".join(stocks)
if "tickers_input" not in st.session_state:
    st.session_state.tickers_input = st.query_params.get(
        "stocks", stocks_to_str(DEFAULT_STOCKS)
    ).split(",")

# Callback to update query param when input changes
def update_query_param():
    if st.session_state.tickers_input:
        st.query_params["stocks"] = stocks_to_str(st.session_state.tickers_input)
    else:
        st.query_params.pop("stocks", None)

# This anchor is the target for the scroll function
st.markdown('<div id="signup-section"></div>', unsafe_allow_html=True)

st.markdown("---")

if st.session_state.selected_plan:
    selected_plan_data = next((p for p in plans if p["name"] == st.session_state.selected_plan), None)
    
    if selected_plan_data:
        st.markdown(f"""
        <div class="dynamic-content">
            <h2>Welcome: {selected_plan_data['name']}</h2>
            <p>{selected_plan_data['details']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('\n\n\n', unsafe_allow_html=True)
        st.markdown('<p style="font-size: 24px;"><strong></strong>  Select the industry you\'re interested in.</p>', unsafe_allow_html=True)

        # Display Logic for Retail Investor
        if selected_plan_data['name'] == "Retail Investor":
            selected_category = st.selectbox("Select Category", CATEGORIES, index=None, placeholder="Choose a category.") 
            #st.markdown(f"You Selected: {selected_category}", unsafe_allow_html=True)

            base_url = "http://127.0.0.1:8000"

            #question = f"Search the web for recent viral trends in the {selected_category} industry and brands seeing momentum in the last one week. I don't need any explanations, just output a comma separated list of stock tickers for any publicly traded {selected_category} companies associated with these trends.  Do not output company names, only stock tickers."
            question = (f"Search the web for recent viral trends in the {selected_category} industry and brands seeing momentum in the last one week. "
                        f"I don't need any explanations, just output a comma separated list of stock tickers for any publicly traded {selected_category} companies associated with these trends. "
                        f"Do not output company names, only stock tickers."
                        )
            model = MODELS[0]  # Default to the first model for simplicity
            force_bad = False  # No need for a bad response in this context
            submitted = st.button("Submit", type="primary", disabled=not selected_category)

            payload = build_payload(question, model, force_bad)

            #st.markdown("### Request")
            #st.code(render_curl(base_url, payload), language="bash")

            col1, col2 = st.columns(2)
            #with col1:
            #    if st.button("Check API health"):
            #        status, data = call_json("GET", f"{base_url.rstrip('/')}/health")
            #        st.markdown(f"**HTTP {status}**" if status else "**Not connected**")
            #        st.json(data)

            if submitted:
                with st.spinner(f"Building a list of trending {selected_category} stocks..."):
                    status, data = call_json("POST", f"{base_url.rstrip('/')}/ask", payload)
                #st.markdown("### Response")
                #st.markdown(f"**HTTP {status}**" if status else "**Request failed**")
                #render_response_summary(data)
                #render_attempts(data)
                #st.markdown("### Raw JSON")
                #st.json(data)

                answer = data.get("answer") if isinstance(data, dict) else None
                #if isinstance(answer, dict):
                #    st.markdown("### Answer")
                #    st.write(answer.get("answer", ""))

                if isinstance(answer, dict) and answer.get("answer"):
                    st.session_state.fetched_stocks = [
                        ticker.strip().upper() for ticker in answer["answer"].split(",") if ticker.strip()
                    ]
                    #st.markdown("### List of stocks from API response:")
                    #st.write(st.session_state.fetched_stocks)
                else:
                    error_message = data.get("error") if isinstance(data, dict) else None
                    st.error(error_message or "Failed to fetch trending stocks. Please try again.")

            if st.session_state.get("fetched_stocks"):
                st.markdown('\n\n', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 24px;"><strong></strong>  Here are the trending stocks in the {selected_category} industry.</p>', unsafe_allow_html=True)
                st.markdown('\n', unsafe_allow_html=True)

                cols = st.columns([1, 3])
                # Will declare right cell later to avoid showing it when no data.

                top_left_cell = cols[0].container(
                    border=True, height="stretch", vertical_alignment="center"
                )

                with top_left_cell:
                    # Display the fetched stock tickers
                    tickers = st.session_state.fetched_stocks
                    st.write(f"**Top {selected_category} stocks:** {', '.join(tickers)}" if tickers else "No tickers yet.")
                    # Time horizon selector
                    horizon_map = {
                        "1 Months": "1mo",
                        "3 Months": "3mo",
                        "6 Months": "6mo",
                        "1 Year": "1y",
                    }
                    # Buttons for picking time horizon
                    horizon = st.pills(
                        "Time horizon",
                        options=list(horizon_map.keys()),
                        default="6 Months",
                    )
                    tickers = [t.upper() for t in tickers]

                    # Update query param when text input changes
                    if tickers:
                        st.query_params["stocks"] = stocks_to_str(tickers)
                    else:
                        # Clear the param if input is empty
                        st.query_params.pop("stocks", None)

                    if not tickers:
                        top_left_cell.info("Pick some stocks to compare", icon=":material/info:")
                        st.stop()

                    right_cell = cols[1].container(
                        border=True, height="stretch", vertical_alignment="center"
                    )

                    @st.cache_resource(show_spinner=False, ttl="6h")
                    def load_data(tickers, period):
                        tickers_obj = yf.Tickers(tickers)
                        data = tickers_obj.history(period=period)
                        if data is None:
                            raise RuntimeError("YFinance returned no data.")
                        return data["Close"]

                    # Load the data
                    try:
                        data = load_data(tickers, horizon_map[horizon])
                    except yf.exceptions.YFRateLimitError as e:
                        st.warning("YFinance is rate-limiting us :(\nTry again later.")
                        load_data.clear()  # Remove the bad cache entry.
                        st.stop()

                    empty_columns = data.columns[data.isna().all()].tolist()

                    if empty_columns:
                        st.error(f"Ignoring tickers with no data available: {', '.join(empty_columns)}.")
                        data = data.drop(columns=empty_columns)
                        tickers = [t for t in tickers if t not in empty_columns]

                    if not tickers:
                        st.stop()

                    # Normalize prices (start at 1)
                    normalized = data.div(data.iloc[0])

                    latest_norm_values = {normalized[ticker].iat[-1]: ticker for ticker in tickers}
                    max_norm_value = max(latest_norm_values.items())
                    min_norm_value = min(latest_norm_values.items())

                    bottom_left_cell = cols[0].container(
                        border=True, height="stretch", vertical_alignment="center"
                    )

                    with bottom_left_cell:
                        cols = st.columns(2)
                        cols[0].metric(
                            "Best stock",
                            max_norm_value[1],
                            delta=f"{round(max_norm_value[0] * 100)}%",
                            width="content",
                        )
                        cols[1].metric(
                            "Worst stock",
                            min_norm_value[1],
                            delta=f"{round(min_norm_value[0] * 100)}%",
                            width="content",
                        )

                    # Plot normalized prices
                    with right_cell:
                        st.altair_chart(
                            alt.Chart(
                                normalized.reset_index().melt(
                                    id_vars=["Date"], var_name="Stock", value_name="Normalized price"
                                ),
                            )
                            .mark_line()
                            .encode(
                                alt.X("Date:T"),
                                alt.Y("Normalized price:Q").scale(zero=False),
                                alt.Color("Stock:N"),
                            )
                            .properties(height=400)
                        )

        elif selected_plan_data['name'] == "Equity Analyst":
            selected_option = st.selectbox("Select Category", CATEGORIES, index=None, placeholder="Choose a category.") 
        elif selected_plan_data['name'] == "Portfolio Manager":
            selected_option = st.selectbox("Select Category", CATEGORIES, index=None, placeholder="Choose a category.") 
else:
    # Placeholder content if nothing selected yet
    st.markdown("""
    <div style="text-align: center; padding: 40px 0; color: #9CA3AF;">
        <p>Select a plan above to view details here.</p>
    </div>
    """, unsafe_allow_html=True)

# c1, c2, _ = st.columns([1, 1, 3])
# with c1:
#     if st.button("Proceed to Signup", key="signup_btn"):
#         st.success("Redirecting to signup... (Action placeholder)")
# with c2:
#     if st.button("Clear Selection", key="clear_btn"):
#         st.session_state.selected_plan = None
#         st.rerun()

st.markdown("""
<div style="text-align: center; padding: 40px 0; color: #6B7280;">
    <h3>Additional Information</h3>
    <p>All plans include secure data encryption, regular backups, and cancel anytime policy.</p>
    <p>Need a custom solution? <a href="#" style="color: #7C3AED;">Contact our sales team</a></p>
</div>
""", unsafe_allow_html=True)