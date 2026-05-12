import streamlit as st
import pandas as pd
import anthropic
import smtplib
import plotly.express as px
import os
from dotenv import load_dotenv
load_dotenv()
import plotly.graph_objects as go
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ============================================
# CONFIG
# ============================================
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")
# ============================================
# APP UI
# ============================================
st.set_page_config(page_title="Growth Acquisition Agent", page_icon="📊", layout="wide")
st.title("📊 Acquisition Report Agent")
st.caption("Upload your acquisition data and get a full AI-generated report delivered to your inbox.")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

# ============================================
# AUTO-DETECT COLUMNS
# ============================================
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()

    # Auto detect date column
    date_col = None
    for col in df.columns:
        if 'date' in col.lower() or 'time' in col.lower():
            date_col = col
            break

    # Auto detect total column
    total_col = None
    for col in df.columns:
        if 'total' in col.lower():
            total_col = col
            break

    # Auto detect channel columns (everything except date and total)
    exclude = [date_col, total_col]
    channel_cols = [col for col in df.columns if col not in exclude and col is not None]

    if date_col:
        df[date_col] = pd.to_datetime(df[date_col])

    st.success(f"✅ Detected {len(channel_cols)} channels: {', '.join(channel_cols)}")

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

    # ============================================
    # DASHBOARD
    # ============================================
    st.divider()
    st.subheader("📈 Dashboard")

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total New Users", f"{total_this_week:,.0f}", f"{wow_change:+.1f}% WoW")
    col2.metric("Daily Average", f"{daily_avg_this:,.0f}", f"{((daily_avg_this - daily_avg_last) / daily_avg_last * 100):+.1f}% WoW")
    col3.metric("Top Channel", top_channel.replace('_', ' '), f"{int(channel_this_week[top_channel]):,} users")
    col4.metric("Lowest Channel", bottom_channel.replace('_', ' '), f"{int(channel_this_week[bottom_channel]):,} users")

    st.divider()

    # Row 1 — Trend + Channel Share
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("**Daily Acquisition Trend**")
        if total_col:
            trend_data = df[[date_col, total_col]].tail(30)
            fig1 = px.line(trend_data, x=date_col, y=total_col, markers=True)
        else:
            trend_data = df[[date_col] + channel_cols].tail(30).copy()
            trend_data['Total'] = trend_data[channel_cols].sum(axis=1)
            fig1 = px.line(trend_data, x=date_col, y='Total', markers=True)
        fig1.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=300)
        st.plotly_chart(fig1, use_container_width=True)

    with chart_col2:
        st.markdown("**Channel Share This Week**")
        fig2 = px.pie(
            values=channel_this_week.values,
            names=[c.replace('_', ' ') for c in channel_this_week.index],
            hole=0.4
        )
        fig2.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=300)
        st.plotly_chart(fig2, use_container_width=True)

    # Row 2 — Channel WoW + Channel Trend
    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        st.markdown("**Channel WoW Change (%)**")
        wow_df = pd.DataFrame({
            'Channel': [c.replace('_', ' ') for c in channel_wow.index],
            'WoW Change': channel_wow.values
        }).sort_values('WoW Change')
        fig3 = px.bar(
            wow_df, x='WoW Change', y='Channel',
            orientation='h',
            color='WoW Change',
            color_continuous_scale=['red', 'gray', 'green'],
            color_continuous_midpoint=0
        )
        fig3.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=300)
        st.plotly_chart(fig3, use_container_width=True)

    with chart_col4:
        st.markdown("**Channel Trend (Last 30 Days)**")
        trend_channels = df[[date_col] + channel_cols].tail(30)
        fig4 = px.line(trend_channels, x=date_col, y=channel_cols, markers=False)
        fig4.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=300, legend=dict(font=dict(size=9)))
        st.plotly_chart(fig4, use_container_width=True)

    # ============================================
    # REPORT GENERATION
    # ============================================
    st.divider()

    receiver_email = st.text_input("Your email address")
    run_button = st.button("Generate & Send Report", type="primary")

    if run_button:
        if not receiver_email:
            st.error("Please enter your email address.")
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

            with st.spinner("Generating report with Claude..."):
                client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                message = client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=1500,
                    messages=[
                        {
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
                        }
                    ]
                )
                report = message.content[0].text
                st.success("✅ Report generated")
                st.markdown(report)

            with st.spinner("Sending to your inbox..."):
                msg = MIMEMultipart()
                msg['From'] = SENDER_EMAIL
                msg['To'] = receiver_email
                msg['Subject'] = f"📊 Weekly Acquisition Report — {last_7[date_col].iloc[-1].strftime('%b %d, %Y')}"
                msg.attach(MIMEText(report, 'plain'))

                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(SENDER_EMAIL, APP_PASSWORD)
                    smtp.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())

                st.success(f"✅ Report delivered to {receiver_email}")
                st.balloons()