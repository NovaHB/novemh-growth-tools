import streamlit as st
import pandas as pd
import anthropic
import smtplib
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

# ============================================
# CONFIG
# ============================================
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

# ============================================
# CUSTOM CSS — Blue, Beige, Brown
# ============================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --blue:    #1B3A5C;
    --blue-mid: #2D5F8A;
    --blue-light: #E8EFF6;
    --beige:   #F5F0E8;
    --beige-dark: #E8DFD0;
    --brown:   #6B4C35;
    --brown-light: #9C7A5E;
    --text:    #1A1A1A;
    --muted:   #6B6B6B;
    --white:   #FFFFFF;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--beige) !important;
    color: var(--text);
}

/* Header */
.app-header {
    background: linear-gradient(135deg, var(--blue) 0%, var(--blue-mid) 100%);
    padding: 2.5rem 2rem 2rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    border-bottom: 4px solid var(--brown);
}
.app-header h1 {
    font-family: 'Playfair Display', serif;
    color: var(--white);
    font-size: 2.2rem;
    margin: 0 0 0.4rem 0;
    letter-spacing: -0.5px;
}
.app-header p {
    color: rgba(255,255,255,0.75);
    font-size: 0.95rem;
    margin: 0;
    font-weight: 300;
}

/* Upload zone */
.upload-zone {
    background: var(--white);
    border: 2px dashed var(--beige-dark);
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    transition: border-color 0.2s;
}

/* Section headers */
.section-label {
    font-family: 'Playfair Display', serif;
    color: var(--blue);
    font-size: 1.3rem;
    font-weight: 600;
    margin-bottom: 1rem;
    padding-bottom: 0.4rem;
    border-bottom: 2px solid var(--beige-dark);
}

/* KPI cards */
.kpi-card {
    background: var(--white);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    border-left: 4px solid var(--blue);
    box-shadow: 0 2px 8px rgba(27,58,92,0.08);
}
.kpi-label {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--muted);
    font-weight: 500;
    margin-bottom: 0.3rem;
}
.kpi-value {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    color: var(--blue);
    line-height: 1;
    margin-bottom: 0.2rem;
}
.kpi-delta-pos { color: #2E7D32; font-size: 0.82rem; font-weight: 500; }
.kpi-delta-neg { color: #C62828; font-size: 0.82rem; font-weight: 500; }

/* Channel pill */
.channel-pill {
    background: var(--beige-dark);
    color: var(--brown);
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 500;
    display: inline-block;
    margin: 2px;
}

/* Report box */
.report-box {
    background: var(--white);
    border-radius: 12px;
    padding: 2rem;
    border-left: 4px solid var(--brown);
    box-shadow: 0 2px 12px rgba(107,76,53,0.1);
    margin-top: 1rem;
}

/* Alert boxes */
.alert-success {
    background: #E8F5E9;
    border-left: 4px solid #2E7D32;
    padding: 0.8rem 1rem;
    border-radius: 8px;
    color: #1B5E20;
    font-size: 0.9rem;
    margin: 0.5rem 0;
}
.alert-error {
    background: #FFEBEE;
    border-left: 4px solid #C62828;
    padding: 0.8rem 1rem;
    border-radius: 8px;
    color: #B71C1C;
    font-size: 0.9rem;
    margin: 0.5rem 0;
}
.alert-info {
    background: var(--blue-light);
    border-left: 4px solid var(--blue);
    padding: 0.8rem 1rem;
    border-radius: 8px;
    color: var(--blue);
    font-size: 0.9rem;
    margin: 0.5rem 0;
}

/* Streamlit overrides */
div[data-testid="stMetric"] {
    background: var(--white);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    border-left: 4px solid var(--blue);
    box-shadow: 0 2px 8px rgba(27,58,92,0.08);
}
div[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 1px; }
div[data-testid="stMetricValue"] { color: var(--blue) !important; font-family: 'Playfair Display', serif !important; }

.stButton > button {
    background: linear-gradient(135deg, var(--blue) 0%, var(--blue-mid) 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.8rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.3px !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

.stTextInput > div > div > input {
    border: 1.5px solid var(--beige-dark) !important;
    border-radius: 8px !important;
    background: var(--white) !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--blue-mid) !important;
    box-shadow: 0 0 0 2px rgba(45,95,138,0.15) !important;
}

[data-testid="stFileUploader"] {
    background: var(--white) !important;
    border: 2px dashed var(--beige-dark) !important;
    border-radius: 12px !important;
}

.stExpander {
    background: var(--white) !important;
    border-radius: 10px !important;
    border: 1px solid var(--beige-dark) !important;
}

hr { border-color: var(--beige-dark) !important; }

/* Footer */
.footer {
    text-align: center;
    color: var(--muted);
    font-size: 0.8rem;
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--beige-dark);
}
</style>
""", unsafe_allow_html=True)

# ============================================
# APP HEADER
# ============================================
st.set_page_config(page_title="Acquisition Report Agent", page_icon="📊", layout="wide")

st.markdown("""
<div class="app-header">
    <h1>📊 Acquisition Report Agent</h1>
    <p>Upload your acquisition data — get a full AI-generated growth report delivered to your inbox.</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# FILE UPLOAD
# ============================================
st.markdown('<div class="section-label">Upload Data</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx", "xls"], label_visibility="collapsed")

if uploaded_file:
    try:
        # Load file
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            excel_file = pd.ExcelFile(uploaded_file)
            if len(excel_file.sheet_names) > 1:
                sheet = st.selectbox("Select sheet", excel_file.sheet_names)
            else:
                sheet = excel_file.sheet_names[0]
            df = pd.read_excel(uploaded_file, sheet_name=sheet)

        df.columns = df.columns.str.strip()

        # Auto detect columns
        date_col = next((col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()), None)
        total_col = next((col for col in df.columns if 'total' in col.lower()), None)
        channel_cols = [col for col in df.columns if col not in [date_col, total_col] and col is not None]

        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])

        # Show detected channels
        channel_pills = " ".join([f'<span class="channel-pill">{c.replace("_", " ")}</span>' for c in channel_cols])
        st.markdown(f'<div class="alert-info">✅ {df.shape[0]:,} rows loaded &nbsp;|&nbsp; {len(channel_cols)} channels detected: {channel_pills}</div>', unsafe_allow_html=True)

        with st.expander("👀 Preview Raw Data"):
            st.dataframe(df.head(20), use_container_width=True)

        # ============================================
        # COMPUTE METRICS
        # ============================================
        last_7 = df.tail(7)
        prev_7 = df.iloc[-14:-7]

        if total_col:
            total_this_week = last_7[total_col].sum()
            total_last_week = prev_7[total_col].sum()
        else:
            total_this_week = last_7[channel_cols].sum().sum()
            total_last_week = prev_7[channel_cols].sum().sum()

        wow_change = ((total_this_week - total_last_week) / total_last_week) * 100
        channel_this_week = last_7[channel_cols].sum()
        channel_last_week = prev_7[channel_cols].sum()
        channel_wow = ((channel_this_week - channel_last_week) / channel_last_week * 100).round(1)
        channel_share = (channel_this_week / total_this_week * 100).round(1)
        top_channel = channel_this_week.idxmax()
        bottom_channel = channel_this_week.idxmin()
        daily_avg_this = last_7[channel_cols].sum(axis=1).mean() if not total_col else last_7[total_col].mean()
        daily_avg_last = prev_7[channel_cols].sum(axis=1).mean() if not total_col else prev_7[total_col].mean()
        daily_avg_wow = ((daily_avg_this - daily_avg_last) / daily_avg_last) * 100

        # ============================================
        # DASHBOARD
        # ============================================
        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">📈 Dashboard</div>', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total New Users", f"{total_this_week:,.0f}", f"{wow_change:+.1f}% WoW")
        col2.metric("Daily Average", f"{daily_avg_this:,.0f}", f"{daily_avg_wow:+.1f}% WoW")
        col3.metric("Top Channel", top_channel.replace('_', ' '), f"{int(channel_this_week[top_channel]):,} users")
        col4.metric("Weakest Channel", bottom_channel.replace('_', ' '), f"{int(channel_this_week[bottom_channel]):,} users")

        st.markdown('<br>', unsafe_allow_html=True)

        # Chart colors
        BLUE = "#1B3A5C"
        BROWN = "#6B4C35"
        BEIGE = "#F5F0E8"
        chart_bg = "rgba(0,0,0,0)"

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("**Daily Acquisition Trend**")
            if total_col:
                trend_data = df[[date_col, total_col]].tail(30)
                fig1 = px.line(trend_data, x=date_col, y=total_col, markers=True,
                               color_discrete_sequence=[BLUE])
            else:
                trend_data = df[[date_col] + channel_cols].tail(30).copy()
                trend_data['Total'] = trend_data[channel_cols].sum(axis=1)
                fig1 = px.line(trend_data, x=date_col, y='Total', markers=True,
                               color_discrete_sequence=[BLUE])
            fig1.update_layout(paper_bgcolor=chart_bg, plot_bgcolor=BEIGE,
                               margin=dict(l=0, r=0, t=10, b=0), height=300,
                               xaxis=dict(gridcolor="#E8DFD0"), yaxis=dict(gridcolor="#E8DFD0"))
            st.plotly_chart(fig1, use_container_width=True)

        with chart_col2:
            st.markdown("**Channel Share This Week**")
            fig2 = px.pie(
                values=channel_this_week.values,
                names=[c.replace('_', ' ') for c in channel_this_week.index],
                hole=0.45,
                color_discrete_sequence=["#1B3A5C", "#2D5F8A", "#6B4C35", "#9C7A5E",
                                         "#4A7FA5", "#C4A882", "#3D6B8C", "#8B6345"]
            )
            fig2.update_layout(paper_bgcolor=chart_bg, margin=dict(l=0, r=0, t=10, b=0), height=300)
            st.plotly_chart(fig2, use_container_width=True)

        chart_col3, chart_col4 = st.columns(2)

        with chart_col3:
            st.markdown("**Channel WoW Change (%)**")
            wow_df = pd.DataFrame({
                'Channel': [c.replace('_', ' ') for c in channel_wow.index],
                'WoW Change': channel_wow.values
            }).sort_values('WoW Change')
            fig3 = px.bar(wow_df, x='WoW Change', y='Channel', orientation='h',
                          color='WoW Change',
                          color_continuous_scale=["#C62828", "#E8DFD0", "#1B3A5C"],
                          color_continuous_midpoint=0)
            fig3.update_layout(paper_bgcolor=chart_bg, plot_bgcolor=BEIGE,
                               margin=dict(l=0, r=0, t=10, b=0), height=300,
                               xaxis=dict(gridcolor="#E8DFD0"), yaxis=dict(gridcolor="#E8DFD0"))
            st.plotly_chart(fig3, use_container_width=True)

        with chart_col4:
            st.markdown("**Channel Trend (Last 30 Days)**")
            trend_channels = df[[date_col] + channel_cols].tail(30)
            fig4 = px.line(trend_channels, x=date_col, y=channel_cols,
                           color_discrete_sequence=["#1B3A5C", "#2D5F8A", "#6B4C35", "#9C7A5E",
                                                    "#4A7FA5", "#C4A882", "#3D6B8C", "#8B6345"])
            fig4.update_layout(paper_bgcolor=chart_bg, plot_bgcolor=BEIGE,
                               margin=dict(l=0, r=0, t=10, b=0), height=300,
                               legend=dict(font=dict(size=9)),
                               xaxis=dict(gridcolor="#E8DFD0"), yaxis=dict(gridcolor="#E8DFD0"))
            st.plotly_chart(fig4, use_container_width=True)

        # ============================================
        # REPORT GENERATION
        # ============================================
        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">📬 Generate & Send Report</div>', unsafe_allow_html=True)

        receiver_email = st.text_input("Your email address", placeholder="you@example.com")
        run_button = st.button("Generate & Send Report")

        if run_button:
            if not receiver_email:
                st.markdown('<div class="alert-error">Please enter your email address.</div>', unsafe_allow_html=True)
            else:
                channel_breakdown = ""
                for ch in channel_cols:
                    channel_breakdown += f"\n  - {ch.replace('_', ' ')}: {int(channel_this_week[ch]):,} users ({channel_share[ch]}% share) | WoW: {channel_wow[ch]:+.1f}%"

                summary_stats = f"""
Reporting Period: {last_7[date_col].iloc[0].strftime('%b %d')} – {last_7[date_col].iloc[-1].strftime('%b %d, %Y')}

OVERALL ACQUISITION
- Total New Users (This Week): {total_this_week:,}
- Total New Users (Last Week): {total_last_week:,}
- Week-over-Week Change: {wow_change:+.1f}%
- Daily Average (This Week): {daily_avg_this:,.0f}
- Daily Average (Last Week): {daily_avg_last:,.0f}

CHANNEL BREAKDOWN:
{channel_breakdown}

TOP CHANNEL: {top_channel.replace('_', ' ')} ({int(channel_this_week[top_channel]):,} users)
LOWEST CHANNEL: {bottom_channel.replace('_', ' ')} ({int(channel_this_week[bottom_channel]):,} users)
"""
                try:
                    with st.spinner("Generating report with Claude..."):
                        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                        message = client.messages.create(
                            model="claude-opus-4-6",
                            max_tokens=1500,
                            messages=[{
                                "role": "user",
                                "content": f"""You are a senior growth analyst writing a weekly acquisition report.

Analyze the following data and write a structured weekly report:

{summary_stats}

Structure:
## Weekly Acquisition Report
**[Date Range]**

### Overview
### Key Metrics
### Channel Performance
### Insights & Patterns
### Recommendations

Be direct, data-driven, and concise."""
                            }]
                        )
                        report = message.content[0].text
                    st.markdown('<div class="alert-success">✅ Report generated successfully</div>', unsafe_allow_html=True)
                    st.markdown('<div class="report-box">', unsafe_allow_html=True)
                    st.markdown(report)
                    st.markdown('</div>', unsafe_allow_html=True)
                except Exception:
                    st.markdown('<div class="alert-error">Something went wrong generating the report. Please check your API key in settings and try again.</div>', unsafe_allow_html=True)
                    st.stop()

                try:
                    with st.spinner("Sending to your inbox..."):
                        msg = MIMEMultipart()
                        msg['From'] = SENDER_EMAIL
                        msg['To'] = receiver_email
                        msg['Subject'] = f"📊 Weekly Acquisition Report — {last_7[date_col].iloc[-1].strftime('%b %d, %Y')}"
                        msg.attach(MIMEText(report, 'plain'))
                        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                            smtp.login(SENDER_EMAIL, APP_PASSWORD)
                            smtp.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
                    st.markdown(f'<div class="alert-success">✅ Report delivered to {receiver_email}</div>', unsafe_allow_html=True)
                    st.balloons()
                except Exception:
                    st.markdown('<div class="alert-error">Report was generated but email delivery failed. Check your email settings and try again.</div>', unsafe_allow_html=True)

    except Exception:
        st.markdown('<div class="alert-error">Could not read your file. Make sure it is a valid CSV or Excel file and try again.</div>', unsafe_allow_html=True)

# Footer
st.markdown('<div class="footer">Built by <a href="https://x.com/SuperNovemh" target="_blank">@SuperNovemh</a> · Enneractlabs</div>', unsafe_allow_html=True)
