# Novemh Growth Tools 🚀

A collection of AI-powered growth analytics tools built for analysts and consultants.

---

## Tools

### 📊 Acquisition Report Agent
Upload your acquisition data and get a full AI-generated weekly growth report delivered to your inbox.

**Features:**
- Auto-detects channels from any CSV structure
- Computes WoW performance automatically
- Visual dashboard (trend, channel share, WoW change)
- Claude AI writes the full analyst report
- Delivers report to any email address

### 🧹 Data Cleaner Tool
Upload a dirty CSV, choose your cleaning options, and download a clean dataset.

**Features:**
- Remove duplicates
- Trim whitespace
- Fix text casing
- Handle missing values (5 options)
- Standardize date formats
- Convert text to numeric
- Remove outliers (3σ rule)
- Before vs After comparison

---

## Stack
- Python
- Streamlit
- Claude API (Anthropic)
- Pandas & Plotly

---

## Setup

1. Clone the repo
2. Install dependencies:
pip install streamlit pandas plotly anthropic python-dotenv
3. Create a `.env` file:
ANTHROPIC_API_KEY=your-key
SENDER_EMAIL=your-email
APP_PASSWORD=your-app-password

Run either tool:
python -m streamlit run acquisition_agent_app.py
python -m streamlit run data_cleaner_app.py

---

Built by [@SuperNovemh](https://x.com/SuperNovemh)
