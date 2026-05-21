import streamlit as st
import pandas as pd
import anthropic
import os
import json
import base64
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TRACKER_FILE = "leads_data.json"

# ============================================
# CUSTOM CSS — Khaki, White, Black
# ============================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --khaki:        #C3B091;
    --khaki-light:  #EDE3D3;
    --khaki-dark:   #A0896A;
    --black:        #111111;
    --white:        #FFFFFF;
    --gray:         #6B6B6B;
    --gray-light:   #F4F1EC;
    --border:       #DDD5C5;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--gray-light) !important;
    color: var(--black);
}

.app-header {
    background: var(--black);
    padding: 2.5rem 2rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    border-bottom: 4px solid var(--khaki);
}
.app-header h1 {
    font-family: 'Playfair Display', serif;
    color: var(--white);
    font-size: 2.2rem;
    margin: 0 0 0.4rem 0;
}
.app-header p {
    color: rgba(255,255,255,0.6);
    font-size: 0.9rem;
    margin: 0;
    font-weight: 300;
}

.section-label {
    font-family: 'Playfair Display', serif;
    color: var(--black);
    font-size: 1.2rem;
    font-weight: 600;
    margin: 1.5rem 0 1rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 2px solid var(--khaki);
}

.kpi-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
.kpi-card {
    background: var(--white);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    border-top: 4px solid var(--khaki);
    flex: 1;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.kpi-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color: var(--gray); margin-bottom: 0.3rem; }
.kpi-value { font-family: 'Playfair Display', serif; font-size: 2rem; color: var(--black); line-height: 1; }

.status-badge {
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-block;
}
.status-sent       { background: #E3F2FD; color: #1565C0; }
.status-replied    { background: #E8F5E9; color: #2E7D32; }
.status-follow-up  { background: #FFF3E0; color: #E65100; }
.status-interested { background: #F3E5F5; color: #6A1B9A; }
.status-closed     { background: #EFEBE9; color: #4E342E; }
.status-not-interested { background: #FFEBEE; color: #C62828; }
.status-no-reply   { background: #F5F5F5; color: #616161; }

.lead-card {
    background: var(--white);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.8rem;
    border-left: 4px solid var(--khaki);
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
.lead-name { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: var(--black); margin-bottom: 0.2rem; }
.lead-meta { font-size: 0.82rem; color: var(--gray); margin-bottom: 0.5rem; }
.lead-summary { font-size: 0.88rem; color: var(--black); line-height: 1.5; }
.lead-action { font-size: 0.82rem; color: var(--khaki-dark); font-weight: 600; margin-top: 0.4rem; }

.alert-success {
    background: #E8F5E9; border-left: 4px solid #2E7D32;
    padding: 0.8rem 1rem; border-radius: 8px; color: #1B5E20;
    font-size: 0.9rem; margin: 0.5rem 0;
}
.alert-error {
    background: #FFEBEE; border-left: 4px solid #C62828;
    padding: 0.8rem 1rem; border-radius: 8px; color: #B71C1C;
    font-size: 0.9rem; margin: 0.5rem 0;
}
.alert-info {
    background: var(--khaki-light); border-left: 4px solid var(--khaki-dark);
    padding: 0.8rem 1rem; border-radius: 8px; color: var(--black);
    font-size: 0.9rem; margin: 0.5rem 0;
}

.stButton > button {
    background: var(--black) !important;
    color: var(--white) !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.8rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.8 !important; }

div[data-testid="stMetric"] {
    background: var(--white) !important;
    border-radius: 12px !important;
    padding: 1rem 1.2rem !important;
    border-top: 4px solid var(--khaki) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
}

.footer {
    text-align: center; color: var(--gray);
    font-size: 0.8rem; margin-top: 3rem;
    padding-top: 1.5rem; border-top: 1px solid var(--border);
}
</style>
""", unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
st.set_page_config(page_title="Leads Tracker", page_icon="📬", layout="wide")

st.markdown("""
<div class="app-header">
    <h1>📬 Outreach Leads Tracker</h1>
    <p>AI-powered cold email tracker — scans your Gmail, extracts leads, tracks every conversation.</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# LOAD / SAVE LEADS
# ============================================
def load_leads():
    try:
        if os.path.exists(TRACKER_FILE):
            with open(TRACKER_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_leads(leads):
    try:
        with open(TRACKER_FILE, "w") as f:
            json.dump(leads, f, indent=2)
    except Exception:
        pass

def show_error(msg):
    st.markdown(f'<div class="alert-error">{msg}</div>', unsafe_allow_html=True)

def show_success(msg):
    st.markdown(f'<div class="alert-success">{msg}</div>', unsafe_allow_html=True)

def show_info(msg):
    st.markdown(f'<div class="alert-info">{msg}</div>', unsafe_allow_html=True)

# ============================================
# GMAIL AUTH
# ============================================
def get_gmail_service():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                return None
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

# ============================================
# FETCH EMAIL THREADS
# ============================================
def get_email_body(msg):
    body = ""
    try:
        if 'parts' in msg['payload']:
            for part in msg['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            data = msg['payload']['body'].get('data', '')
            body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    except Exception:
        pass
    return body[:2000]

def fetch_threads(service, max_threads=30):
    threads_data = []
    try:
        results = service.users().threads().list(
            userId='me',
            labelIds=['SENT'],
            maxResults=max_threads
        ).execute()
        threads = results.get('threads', [])

        for thread in threads:
            thread_detail = service.users().threads().get(
                userId='me', id=thread['id']
            ).execute()
            messages = thread_detail.get('messages', [])

            thread_info = {
                'thread_id': thread['id'],
                'messages': []
            }

            for msg in messages:
                headers = {h['name']: h['value'] for h in msg['payload']['headers']}
                thread_info['messages'].append({
                    'from': headers.get('From', ''),
                    'to': headers.get('To', ''),
                    'subject': headers.get('Subject', ''),
                    'date': headers.get('Date', ''),
                    'body': get_email_body(msg)
                })

            threads_data.append(thread_info)
    except Exception:
        pass
    return threads_data

# ============================================
# CLAUDE — EXTRACT LEAD DATA
# ============================================
def extract_lead_with_claude(thread):
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        thread_text = ""
        for msg in thread['messages']:
            thread_text += f"\nFrom: {msg['from']}\nTo: {msg['to']}\nDate: {msg['date']}\nSubject: {msg['subject']}\n{msg['body']}\n---"

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            messages=[{
                "role": "user",
                "content": f"""You are analyzing email threads to identify cold outreach and professional networking emails.

First, determine if this is a cold outreach, job application, business pitch, partnership request, or professional networking email.

If it is NOT outreach (e.g. customer support, receipts, newsletters, spam, personal emails, automated notifications), return exactly:
{{"skip": true}}

If it IS outreach, return ONLY this JSON:
{{
  "skip": false,
  "name": "contact full name or Unknown",
  "company": "company name or Unknown",
  "role": "their job title or Unknown",
  "email": "their email address",
  "subject": "email subject",
  "status": "one of: Sent, Replied, Follow-up Due, Interested, Closed, Not Interested, No Reply",
  "last_contact": "most recent date in YYYY-MM-DD format",
  "summary": "2 sentence summary of the conversation",
  "next_action": "recommended next step in one sentence",
  "message_count": {len(thread['messages'])}
}}

EMAIL THREAD:
{thread_text}

Return only the JSON, no other text."""
            }]
        )

        text = message.content[0].text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)

        if data.get("skip"):
            return None

        return data
    except Exception:
        return None

# ============================================
# MAIN APP
# ============================================
leads = load_leads()

# Tabs
tab1, tab2, tab3 = st.tabs(["📋 All Leads", "🔄 Sync Gmail", "➕ Add Manual Lead"])

# ============================================
# TAB 1 — ALL LEADS
# ============================================
with tab1:
    if not leads:
        show_info('No leads yet. Go to Sync Gmail or Add Manual Lead to get started.')
    else:
        # KPI row
        total = len(leads)
        replied = len([l for l in leads if l.get('status') == 'Replied'])
        interested = len([l for l in leads if l.get('status') == 'Interested'])
        follow_up = len([l for l in leads if l.get('status') == 'Follow-up Due'])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Leads", total)
        col2.metric("Replied", replied)
        col3.metric("Interested", interested)
        col4.metric("Follow-up Due", follow_up)

        st.markdown('<br>', unsafe_allow_html=True)

        # Filters
        filter_col1, filter_col2 = st.columns([2, 1])
        with filter_col1:
            search = st.text_input("Search leads", placeholder="Search by name, company, or role...")
        with filter_col2:
            status_filter = st.selectbox("Filter by status", ["All", "Sent", "Replied", "Follow-up Due", "Interested", "Closed", "Not Interested", "No Reply"])

        # Apply filters
        filtered = leads
        if search:
            filtered = [l for l in filtered if
                        search.lower() in l.get('name', '').lower() or
                        search.lower() in l.get('company', '').lower() or
                        search.lower() in l.get('role', '').lower()]
        if status_filter != "All":
            filtered = [l for l in filtered if l.get('status') == status_filter]

        show_info(f'Showing {len(filtered)} of {total} leads')
        st.markdown('<br>', unsafe_allow_html=True)

        # Lead cards
        status_class_map = {
            "Sent": "status-sent",
            "Replied": "status-replied",
            "Follow-up Due": "status-follow-up",
            "Interested": "status-interested",
            "Closed": "status-closed",
            "Not Interested": "status-not-interested",
            "No Reply": "status-no-reply"
        }

        for i, lead in enumerate(filtered):
            try:
                status = lead.get('status', 'Sent')
                status_cls = status_class_map.get(status, 'status-sent')

                with st.container():
                    col_info, col_action = st.columns([4, 1])

                    with col_info:
                        st.markdown(f"""
                        <div class="lead-card">
                            <div class="lead-name">{lead.get('name', 'Unknown')}</div>
                            <div class="lead-meta">
                                {lead.get('company', 'Unknown')} &nbsp;·&nbsp; {lead.get('role', 'Unknown')} &nbsp;·&nbsp; {lead.get('email', '')} &nbsp;·&nbsp; Last contact: {lead.get('last_contact', 'N/A')} &nbsp;·&nbsp; {lead.get('message_count', 1)} message(s)
                            </div>
                            <span class="status-badge {status_cls}">{status}</span>
                            <div class="lead-summary" style="margin-top:0.6rem">{lead.get('summary', '')}</div>
                            <div class="lead-action">→ {lead.get('next_action', '')}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_action:
                        st.markdown('<br><br>', unsafe_allow_html=True)
                        new_status = st.selectbox(
                            "Update",
                            ["Sent", "Replied", "Follow-up Due", "Interested", "Closed", "Not Interested", "No Reply"],
                            index=["Sent", "Replied", "Follow-up Due", "Interested", "Closed", "Not Interested", "No Reply"].index(status) if status in ["Sent", "Replied", "Follow-up Due", "Interested", "Closed", "Not Interested", "No Reply"] else 0,
                            key=f"lead_status_{i}"
                        )
                        if new_status != status:
                            leads[leads.index(lead)]['status'] = new_status
                            save_leads(leads)
                            st.rerun()
            except Exception:
                show_error(f"Could not display lead #{i+1}. The record may be corrupted.")

        # Export
        st.markdown('<br>', unsafe_allow_html=True)
        if st.button("⬇️ Export to CSV"):
            try:
                df = pd.DataFrame(leads)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", csv, "leads_tracker.csv", "text/csv")
            except Exception:
                show_error("Could not export leads. Please try again.")

# ============================================
# TAB 2 — SYNC GMAIL
# ============================================
with tab2:
    st.markdown('<div class="section-label">Sync Your Gmail</div>', unsafe_allow_html=True)
    show_info('This scans your Sent folder, reads threads, and uses Claude to extract lead data automatically.')
    st.markdown('<br>', unsafe_allow_html=True)

    st.markdown("""
    **Setup required (one time only):**
    1. Go to [Google Cloud Console](https://console.cloud.google.com)
    2. Create a project → Enable Gmail API
    3. Create OAuth credentials → Download as `credentials.json`
    4. Place `credentials.json` in your `novemh-growth-tools` folder
    """)

    max_threads = st.slider("How many threads to scan?", 5, 50, 20)
    sync_button = st.button("🔄 Sync Gmail Now")

    if sync_button:
        try:
            with st.spinner("Connecting to Gmail..."):
                service = get_gmail_service()

            if not service:
                show_error('credentials.json not found. Follow the setup steps above first.')
            else:
                with st.spinner(f"Fetching {max_threads} threads from Gmail..."):
                    threads = fetch_threads(service, max_threads)

                show_success(f'✅ Found {len(threads)} threads')

                progress = st.progress(0)
                existing_ids = [l.get('thread_id') for l in leads]
                new_count = 0

                for i, thread in enumerate(threads):
                    progress.progress((i + 1) / len(threads))
                    if thread['thread_id'] in existing_ids:
                        continue
                    with st.spinner(f"Analysing thread {i+1} of {len(threads)}..."):
                        lead = extract_lead_with_claude(thread)
                    if lead:
                        lead['thread_id'] = thread['thread_id']
                        lead['added_at'] = datetime.now().strftime('%Y-%m-%d')
                        leads.append(lead)
                        new_count += 1

                save_leads(leads)
                show_success(f'✅ {new_count} new leads added to your tracker')
                if new_count > 0:
                    st.rerun()

        except Exception:
            show_error('Something went wrong. Please check your setup and try again.')

# ============================================
# TAB 3 — MANUAL LEAD
# ============================================
with tab3:
    st.markdown('<div class="section-label">Add a Lead Manually</div>', unsafe_allow_html=True)

    # Show success message if lead was just added
    if st.session_state.get("lead_added"):
        show_success('✅ Lead added successfully')
        st.session_state["lead_added"] = False

    # Use session state keys to allow form clearing
    if "form_key" not in st.session_state:
        st.session_state["form_key"] = 0

    form_key = st.session_state["form_key"]

    col_a, col_b = st.columns(2)
    with col_a:
        m_name = st.text_input("Contact Name", key=f"name_{form_key}")
        m_company = st.text_input("Company", key=f"company_{form_key}")
        m_role = st.text_input("Role / Title", key=f"role_{form_key}")
        m_email = st.text_input("Email Address", key=f"email_{form_key}")
    with col_b:
        m_status = st.selectbox("Status", ["Sent", "Replied", "Follow-up Due", "Interested", "Closed", "Not Interested", "No Reply"], key=f"form_status_{form_key}")
        m_last_contact = st.date_input("Last Contact Date", key=f"date_{form_key}")
        m_next_action = st.text_input("Next Action", key=f"action_{form_key}")

    m_summary = st.text_area("Conversation Summary", height=100, key=f"summary_{form_key}")

    if st.button("Add Lead"):
        if not m_name:
            show_error('Please enter at least a contact name.')
        else:
            new_lead = {
                "thread_id": f"manual_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "name": m_name,
                "company": m_company,
                "role": m_role,
                "email": m_email,
                "status": m_status,
                "last_contact": str(m_last_contact),
                "summary": m_summary,
                "next_action": m_next_action,
                "message_count": 1,
                "added_at": datetime.now().strftime('%Y-%m-%d')
            }
            try:
                leads.append(new_lead)
                save_leads(leads)
                st.session_state["lead_added"] = True
                st.session_state["form_key"] += 1
                st.rerun()
            except Exception:
                show_error("Could not save lead. Please try again.")

# Footer
st.markdown('<div class="footer">Built by <a href="https://x.com/SuperNovemh" target="_blank">@SuperNovemh</a> · Enneractlabs</div>', unsafe_allow_html=True)
