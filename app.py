import streamlit as st
from extractor import get_raw_text, parse_resume, save_to_csv
import pandas as pd
import os

st.set_page_config(page_title="Resume Analyzer Pro", layout="wide", initial_sidebar_state="expanded")

# ------------------------------------------------------------
# Warm, light & accessible theme – embedded CSS (no external file needed)
# ------------------------------------------------------------
st.markdown("""
<style>
/* ── Import modern fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@300;400;500;600;700&family=Source+Code+Pro:wght@400;500&display=swap');

/* ── Root variables ── */
:root {
  --bg:           #f4f1ec;      /* warm cream */
  --bg2:          #efe9e1;      /* slightly darker cream */
  --surface:      #ffffff;
  --surface2:     #faf8f5;
  --border:       #d6cec5;
  --border2:      #c4bbb0;
  --accent:       #3b6cb4;      /* warm blue */
  --accent2:      #4f8ef7;
  --accent3:      #2d8a6e;      /* warm green */
  --text:         #2e2a28;
  --text2:        #5c554f;
  --text3:        #8a8078;
  --font-display: 'Instrument Serif', Georgia, serif;
  --font-body:    'Inter', sans-serif;
  --font-mono:    'Source Code Pro', monospace;
  --radius:       14px;
  --radius-lg:    20px;
  --shadow:       0 8px 30px rgba(0,0,0,0.05);
  --shadow-hover: 0 12px 36px rgba(0,0,0,0.08);
}

/* ── Global reset ── */
html, body, [class*="css"] {
  font-family: var(--font-body) !important;
  color: var(--text) !important;
  background: var(--bg);
}

.stApp {
  background: var(--bg);
}

/* ── Main content area ── */
.block-container {
  padding-top: 3rem;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: var(--bg2);
  border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] .stMarkdown h2 {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--text3);
  margin-bottom: 12px;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
  background: var(--surface);
  border: 1px dashed var(--border2);
  border-radius: var(--radius);
  padding: 1rem !important;
  transition: border-color 0.2s, background 0.2s;
}

[data-testid="stFileUploader"]:hover {
  border-color: var(--accent);
  background: #f0f5ff;
}

/* ── Text area (paste resume) ── */
[data-testid="stSidebar"] textarea,
textarea {
  background: var(--surface) !important;
  border: 1px solid var(--border2) !important;
  border-radius: var(--radius) !important;
  color: var(--text) !important;
  font-family: var(--font-mono) !important;
  font-size: 13px !important;
  padding: 12px !important;
  resize: none !important;
  transition: border-color 0.2s !important;
}

[data-testid="stSidebar"] textarea:focus,
textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(59,108,180,0.15) !important;
  outline: none !important;
}

/* ── Divider ── */
[data-testid="stSidebar"] hr {
  border-color: var(--border);
  margin: 1.25rem 0;
}

/* ── Main header ── */
h1[style*="text-align: center"] {
  font-family: var(--font-display) !important;
  font-size: clamp(2.6rem, 6vw, 3.8rem) !important;
  font-weight: 400 !important;
  font-style: italic !important;
  color: #2c3e50 !important;
  letter-spacing: -1px !important;
  margin-bottom: 0.5rem !important;
  animation: fade-up 0.7s ease-out both;
}

p[style*="text-align: center"] {
  font-family: var(--font-mono) !important;
  font-size: 12px !important;
  letter-spacing: 3px !important;
  text-transform: uppercase !important;
  color: var(--text3) !important;
  margin-bottom: 2.5rem !important;
  animation: fade-up 0.7s 0.1s ease-out both;
}

@keyframes fade-up {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── Cards ── */
.main-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 2rem;
  margin-bottom: 1.5rem;
  box-shadow: var(--shadow);
  animation: card-in 0.5s ease-out both;
  transition: box-shadow 0.2s;
}

.main-card:hover {
  box-shadow: var(--shadow-hover);
}

@keyframes card-in {
  from { opacity: 0; transform: translateY(16px) scale(0.99); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* ── Metric boxes ── */
.metric-box {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.4rem 1.25rem;
  text-align: left;
  box-shadow: 0 2px 10px rgba(0,0,0,0.02);
  margin-bottom: 0.85rem;
  transition: transform 0.22s, border-color 0.22s, box-shadow 0.22s;
}

.metric-box:hover {
  transform: translateY(-4px);
  border-color: var(--accent);
  box-shadow: 0 8px 24px rgba(0,0,0,0.06);
}

.metric-label {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: var(--text3);
  margin-bottom: 0.6rem;
  display: flex;
  align-items: center;
  gap: 6px;
}

.metric-value {
  font-family: var(--font-body);
  font-size: 1.05rem;
  font-weight: 500;
  color: var(--text);
  word-break: break-word;
  line-height: 1.4;
}

/* ── Buttons ── */
.stButton > button {
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  color: #fff;
  border: none;
  border-radius: var(--radius);
  padding: 0.7rem 1.8rem;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.2px;
  box-shadow: 0 4px 14px rgba(59,108,180,0.25);
  transition: transform 0.18s, box-shadow 0.18s;
  cursor: pointer;
}

.stButton > button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(59,108,180,0.35);
}

.stButton > button:active {
  transform: scale(0.98);
}

/* ── Download button ── */
.stDownloadButton > button {
  background: var(--surface);
  color: var(--accent3);
  border: 1px solid var(--accent3);
  border-radius: var(--radius);
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 500;
  transition: all 0.18s;
  padding: 0.6rem 1.5rem;
}

.stDownloadButton > button:hover {
  background: rgba(45,138,110,0.08);
  border-color: var(--accent3);
  transform: translateY(-1px);
}

/* ── Dataframe table ── */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

[data-testid="stDataFrame"] th {
  background: #f0ede7;
  color: var(--text3);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  border-bottom: 1px solid var(--border);
  padding: 10px 14px;
}

[data-testid="stDataFrame"] td {
  color: var(--text2);
  border-bottom: 1px solid var(--border);
  padding: 10px 14px;
  background: var(--surface);
}

[data-testid="stDataFrame"] tr:hover td {
  background: #f5f9ff;
  color: var(--text);
}

/* ── Experience text ── */
.exp-text {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--text2);
  line-height: 1.8;
  font-weight: 400;
  white-space: pre-wrap;
  border-left: 3px solid var(--accent);
  padding-left: 1rem;
  margin-top: 0.5rem;
  background: #fafbfd;
  border-radius: 0 6px 6px 0;
}

/* ── Database header ── */
.db-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 1rem;
}

.db-pill {
  font-family: var(--font-mono);
  font-size: 10px;
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(59,108,180,0.1);
  border: 1px solid rgba(59,108,180,0.25);
  color: var(--accent);
  letter-spacing: 1px;
  text-transform: uppercase;
}

/* ── Welcome page ── */
.welcome-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  display: block;
  animation: pulse-icon 3s ease-in-out infinite;
}

@keyframes pulse-icon {
  0%, 100% { transform: scale(1); opacity: 1; }
  50%       { transform: scale(1.06); opacity: 0.85; }
}

.welcome-title {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 400;
  font-style: italic;
  color: var(--text);
  margin-bottom: 0.75rem;
  letter-spacing: -0.5px;
}

.welcome-sub {
  font-family: var(--font-body);
  font-size: 15px;
  color: var(--text2);
  font-weight: 300;
  line-height: 1.7;
}

.step-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 1.1rem;
  padding: 12px 16px;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 10px;
  transition: border-color 0.2s;
}

.step-row:hover {
  border-color: var(--accent);
}

.step-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  flex-shrink: 0;
}

.step-text {
  font-size: 14px;
  color: var(--text2);
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: #c4bbb0; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #a89f96; }

/* ── Hide Streamlit branding ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Expandable sections (expander) ── */
[data-testid="stExpander"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

[data-testid="stExpander"] summary {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text2);
  padding: 0.85rem 1rem;
}

[data-testid="stExpander"] summary:hover {
  color: var(--text);
}

/* ── Spinner ── */
[data-testid="stSpinner"] > div {
  border-color: var(--accent) !important;
}

/* ── Alert boxes ── */
[data-testid="stAlert"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-family: var(--font-body);
  color: var(--text2);
}

[data-baseweb="notification"][kind="positive"] {
  background: #e6f7f0;
  border: 1px solid var(--accent3);
  border-radius: var(--radius);
  color: var(--accent3);
  font-family: var(--font-mono);
  font-size: 13px;
}

/* ── Input fields (non‑sidebar) ── */
input, select, .stTextInput > div > div > input {
  background: var(--surface) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
}

input:focus, select:focus, .stTextInput > div > div > input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(59,108,180,0.15) !important;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# App Header
# ------------------------------------------------------------
st.markdown("<h1 style='text-align: center;'>📄 Resume Analyzer Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Upload · Extract · Save to CSV</p>", unsafe_allow_html=True)

# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## Upload Resume")
    uploaded_file = st.file_uploader("Drag & drop a PDF, DOCX, or TXT file", type=["pdf", "docx", "txt"])
    st.markdown("---")
    st.markdown("## Or Paste Resume Text")
    pasted_text = st.text_area("Paste full resume content here", height=200)

# ------------------------------------------------------------
# Main Logic
# ------------------------------------------------------------
if uploaded_file is not None or pasted_text:
    raw_text = get_raw_text(uploaded_file, pasted_text)
    if raw_text:
        # Raw text expander
        with st.container():
            st.markdown("<div class='main-card'>", unsafe_allow_html=True)
            with st.expander("📜 Raw Extracted Text (Preview)"):
                st.text(raw_text[:2000])
            st.markdown("</div>", unsafe_allow_html=True)

        with st.spinner("Analyzing resume…"):
            extracted = parse_resume(raw_text)

        # Extracted fields in cards
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #2c3e50;'>📋 Extracted Details</h3>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">👤 Name</div>
                <div class="metric-value">{extracted['Name'] or '–'}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">📧 Email</div>
                <div class="metric-value">{extracted['Email'] or '–'}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">🔗 LinkedIn</div>
                <div class="metric-value">{extracted['LinkedIn'] or '–'}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">📞 Phone</div>
                <div class="metric-value">{extracted['Phone'] or '–'}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">🎂 Age</div>
                <div class="metric-value">{extracted['Age'] or '–'}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">📍 Location</div>
                <div class="metric-value">{extracted['Location'] or '–'}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Experience
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #2c3e50;'>💼 Professional Experience</h4>", unsafe_allow_html=True)
        exp_text = extracted['Experience_Text']
        if exp_text:
            st.markdown(f"<div class='exp-text'>{exp_text[:2000]}</div>", unsafe_allow_html=True)
        else:
            st.info("No experience section detected.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Save to CSV & view database
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        col_save, col_download = st.columns([2, 1])

        with col_save:
            if st.button("💾 Save to CSV & Update Table"):
                csv_path = save_to_csv(extracted)
                st.success(f"✅ Appended to `{csv_path}`")

        csv_file = "data/extracted_resumes.csv"
        if os.path.exists(csv_file) and os.path.getsize(csv_file) > 0:
            df = pd.read_csv(csv_file)
            st.markdown("""
            <div class="db-header">
                <span style="font-family: 'Instrument Serif', serif; font-size:1.2rem; color: #2c3e50;">📊 Resume Database</span>
                <span class="db-pill">LIVE</span>
            </div>
            """, unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            with col_download:
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv,
                    file_name="extracted_resumes.csv",
                    mime="text/csv"
                )
        else:
            st.info("No records yet. Click 'Save to CSV' to add the first entry.")
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.warning("⚠️ Could not extract text. Please check the file or pasted content.")
else:
    # Welcome screen
    st.markdown("<div class='main-card' style='text-align: center;'>", unsafe_allow_html=True)
    st.markdown('<span class="welcome-icon">📊</span>', unsafe_allow_html=True)
    st.markdown('<div class="welcome-title">Welcome to Resume Analyzer Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="welcome-sub">Upload a resume or paste its text to instantly extract key fields – saved to a live CSV.</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="step-row">
        <div class="step-num">1</div>
        <div class="step-text">📤 Upload a PDF, DOCX, or paste raw text</div>
    </div>
    <div class="step-row">
        <div class="step-num">2</div>
        <div class="step-text">🔍 AI extracts name, email, phone, LinkedIn, experience…</div>
    </div>
    <div class="step-row">
        <div class="step-num">3</div>
        <div class="step-text">💾 Append to CSV & download for screening</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    
    # import streamlit as st
# from extractor import get_raw_text, parse_resume, save_to_csv
# import pandas as pd
# import os
# import base64
# from pathlib import Path

# st.set_page_config(page_title="Resume Analyzer Pro", layout="wide", initial_sidebar_state="expanded")

# # ------------------------------------------------------------
# # Custom CSS — 2025 Premium UI: Obsidian Dark, Bento Grid,
# # Soft glow accents, Editorial typography, Fluid micro-interactions
# # ------------------------------------------------------------
# st.markdown("""
# <style>
#     @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@300;400;500&display=swap');

#     /* ── Design tokens ── */
#     :root {
#         --bg:           #080a0f;
#         --bg2:          #0d1017;
#         --bg3:          #121620;
#         --surface:      #161b26;
#         --surface2:     #1c2233;
#         --border:       rgba(255,255,255,0.06);
#         --border2:      rgba(255,255,255,0.11);
#         --accent:       #4f8ef7;
#         --accent2:      #7c6af5;
#         --accent3:      #3ecfa3;
#         --glow:         rgba(79,142,247,0.18);
#         --glow2:        rgba(124,106,245,0.12);
#         --text:         #eef0f6;
#         --text2:        #8b91a8;
#         --text3:        #474f68;
#         --font-display: 'Instrument Serif', Georgia, serif;
#         --font-body:    'Geist', sans-serif;
#         --font-mono:    'Geist Mono', monospace;
#         --radius:       14px;
#         --radius-lg:    20px;
#         --shadow:       0 24px 64px rgba(0,0,0,0.55);
#     }

#     /* ── Global reset ── */
#     html, body, [class*="css"] {
#         font-family: var(--font-body) !important;
#         color: var(--text) !important;
#     }

#     /* ── App background ── */
#     .stApp {
#         background: var(--bg) !important;
#         position: relative;
#         overflow-x: hidden;
#     }

#     /* Noise texture overlay */
#     .stApp::before {
#         content: '';
#         position: fixed;
#         inset: 0;
#         background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
#         pointer-events: none;
#         z-index: 0;
#         opacity: 0.4;
#     }

#     /* Ambient glow orbs */
#     .stApp::after {
#         content: '';
#         position: fixed;
#         width: 700px;
#         height: 700px;
#         background: radial-gradient(circle, rgba(79,142,247,0.07) 0%, transparent 70%);
#         top: -200px;
#         left: -100px;
#         pointer-events: none;
#         z-index: 0;
#         animation: orb-drift 18s ease-in-out infinite alternate;
#     }

#     @keyframes orb-drift {
#         from { transform: translate(0, 0) scale(1); }
#         to   { transform: translate(60px, 40px) scale(1.08); }
#     }

#     /* Grid lines background */
#     .stApp > div {
#         background-image:
#             linear-gradient(rgba(79,142,247,0.025) 1px, transparent 1px),
#             linear-gradient(90deg, rgba(79,142,247,0.025) 1px, transparent 1px);
#         background-size: 48px 48px;
#         background-position: center top;
#     }

#     /* ── Sidebar ── */
#     [data-testid="stSidebar"] {
#         background: var(--bg2) !important;
#         border-right: 1px solid var(--border2) !important;
#         padding-top: 0 !important;
#     }

#     [data-testid="stSidebar"] > div:first-child {
#         padding-top: 2rem;
#     }

#     [data-testid="stSidebar"] .stMarkdown h2 {
#         font-family: var(--font-mono) !important;
#         font-size: 11px !important;
#         font-weight: 500 !important;
#         letter-spacing: 2px !important;
#         text-transform: uppercase !important;
#         color: var(--text3) !important;
#         margin-bottom: 12px !important;
#     }

#     /* Sidebar file uploader */
#     [data-testid="stSidebar"] [data-testid="stFileUploader"] {
#         background: var(--surface) !important;
#         border: 1px dashed var(--border2) !important;
#         border-radius: var(--radius) !important;
#         transition: border-color 0.2s, background 0.2s !important;
#     }

#     [data-testid="stSidebar"] [data-testid="stFileUploader"]:hover {
#         border-color: var(--accent) !important;
#         background: rgba(79,142,247,0.05) !important;
#     }

#     /* Sidebar textarea */
#     [data-testid="stSidebar"] textarea {
#         background: var(--surface) !important;
#         border: 1px solid var(--border2) !important;
#         border-radius: var(--radius) !important;
#         color: var(--text) !important;
#         font-family: var(--font-mono) !important;
#         font-size: 13px !important;
#         resize: none !important;
#         transition: border-color 0.2s !important;
#     }

#     [data-testid="stSidebar"] textarea:focus {
#         border-color: var(--accent) !important;
#         box-shadow: 0 0 0 3px rgba(79,142,247,0.12) !important;
#         outline: none !important;
#     }

#     /* Sidebar divider */
#     [data-testid="stSidebar"] hr {
#         border-color: var(--border) !important;
#         margin: 1.25rem 0 !important;
#     }

#     /* ── Main header ── */
#     h1[style*="text-align: center"] {
#         font-family: var(--font-display) !important;
#         font-size: clamp(2.4rem, 5vw, 3.6rem) !important;
#         font-weight: 400 !important;
#         font-style: italic !important;
#         letter-spacing: -1px !important;
#         background: linear-gradient(135deg, #eef0f6 30%, var(--accent) 70%, var(--accent3) 100%) !important;
#         -webkit-background-clip: text !important;
#         -webkit-text-fill-color: transparent !important;
#         background-clip: text !important;
#         line-height: 1.1 !important;
#         padding: 2rem 0 0.5rem !important;
#         animation: fade-up 0.7s ease-out both !important;
#     }

#     p[style*="text-align: center"] {
#         font-family: var(--font-mono) !important;
#         font-size: 12px !important;
#         letter-spacing: 3px !important;
#         text-transform: uppercase !important;
#         color: var(--text3) !important;
#         margin-bottom: 2.5rem !important;
#         animation: fade-up 0.7s 0.1s ease-out both !important;
#     }

#     @keyframes fade-up {
#         from { opacity: 0; transform: translateY(20px); }
#         to   { opacity: 1; transform: translateY(0); }
#     }

#     /* ── Cards ── */
#     .main-card {
#         background: var(--surface) !important;
#         border: 1px solid var(--border2) !important;
#         border-radius: var(--radius-lg) !important;
#         padding: 2rem !important;
#         margin-bottom: 1.25rem !important;
#         box-shadow: var(--shadow), inset 0 1px 0 rgba(255,255,255,0.05) !important;
#         position: relative !important;
#         overflow: hidden !important;
#         animation: card-in 0.5s ease-out both !important;
#         transition: border-color 0.3s !important;
#     }

#     .main-card::before {
#         content: '' !important;
#         position: absolute !important;
#         top: 0 !important; left: 0 !important; right: 0 !important;
#         height: 1px !important;
#         background: linear-gradient(90deg, transparent, rgba(79,142,247,0.4), transparent) !important;
#     }

#     @keyframes card-in {
#         from { opacity: 0; transform: translateY(16px) scale(0.99); }
#         to   { opacity: 1; transform: translateY(0) scale(1); }
#     }

#     /* ── Bento metric boxes ── */
#     .metric-box {
#         background: var(--bg3) !important;
#         border: 1px solid var(--border2) !important;
#         border-radius: var(--radius) !important;
#         padding: 1.4rem 1.25rem !important;
#         text-align: left !important;
#         position: relative !important;
#         overflow: hidden !important;
#         transition: transform 0.22s cubic-bezier(.22,.68,0,1.2),
#                     border-color 0.22s,
#                     box-shadow 0.22s !important;
#         margin-bottom: 0.85rem !important;
#     }

#     .metric-box::after {
#         content: '' !important;
#         position: absolute !important;
#         inset: 0 !important;
#         background: radial-gradient(circle at 80% 20%, var(--glow), transparent 65%) !important;
#         opacity: 0 !important;
#         transition: opacity 0.3s !important;
#     }

#     .metric-box:hover {
#         transform: translateY(-4px) !important;
#         border-color: rgba(79,142,247,0.35) !important;
#         box-shadow: 0 12px 32px rgba(0,0,0,0.4), 0 0 0 1px rgba(79,142,247,0.12) !important;
#     }

#     .metric-box:hover::after {
#         opacity: 1 !important;
#     }

#     .metric-label {
#         font-family: var(--font-mono) !important;
#         font-size: 10px !important;
#         font-weight: 500 !important;
#         text-transform: uppercase !important;
#         letter-spacing: 2px !important;
#         color: var(--text3) !important;
#         margin-bottom: 0.6rem !important;
#         display: flex !important;
#         align-items: center !important;
#         gap: 6px !important;
#     }

#     .metric-value {
#         font-family: var(--font-body) !important;
#         font-size: 1.05rem !important;
#         font-weight: 500 !important;
#         color: var(--text) !important;
#         word-break: break-word !important;
#         line-height: 1.4 !important;
#     }

#     /* ── Section headings inside cards ── */
#     h3[style*="text-align: center"],
#     h4[style*="color: #1a2b4c"] {
#         font-family: var(--font-display) !important;
#         font-size: 1.45rem !important;
#         font-weight: 400 !important;
#         font-style: italic !important;
#         color: var(--text) !important;
#         letter-spacing: -0.3px !important;
#         margin-bottom: 1.25rem !important;
#     }

#     /* ── Expander ── */
#     [data-testid="stExpander"] {
#         background: var(--bg3) !important;
#         border: 1px solid var(--border2) !important;
#         border-radius: var(--radius) !important;
#         overflow: hidden !important;
#     }

#     [data-testid="stExpander"] summary {
#         font-family: var(--font-mono) !important;
#         font-size: 13px !important;
#         color: var(--text2) !important;
#         padding: 0.85rem 1rem !important;
#     }

#     [data-testid="stExpander"] summary:hover {
#         color: var(--text) !important;
#     }

#     /* ── Spinner ── */
#     [data-testid="stSpinner"] {
#         color: var(--accent) !important;
#     }

#     /* ── Primary button ── */
#     .stButton > button {
#         background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
#         color: #fff !important;
#         border: none !important;
#         border-radius: var(--radius) !important;
#         padding: 0.65rem 1.5rem !important;
#         font-family: var(--font-body) !important;
#         font-size: 14px !important;
#         font-weight: 500 !important;
#         letter-spacing: 0.2px !important;
#         box-shadow: 0 4px 20px rgba(79,142,247,0.28), inset 0 1px 0 rgba(255,255,255,0.12) !important;
#         transition: transform 0.18s cubic-bezier(.22,.68,0,1.2),
#                     box-shadow 0.18s,
#                     opacity 0.18s !important;
#         cursor: pointer !important;
#     }

#     .stButton > button:hover {
#         transform: translateY(-2px) scale(1.02) !important;
#         box-shadow: 0 8px 32px rgba(79,142,247,0.42), inset 0 1px 0 rgba(255,255,255,0.15) !important;
#         opacity: 0.95 !important;
#     }

#     .stButton > button:active {
#         transform: scale(0.98) !important;
#     }

#     /* ── Download button ── */
#     .stDownloadButton > button {
#         background: var(--surface2) !important;
#         color: var(--accent3) !important;
#         border: 1px solid rgba(62,207,163,0.3) !important;
#         border-radius: var(--radius) !important;
#         font-family: var(--font-mono) !important;
#         font-size: 13px !important;
#         font-weight: 500 !important;
#         transition: all 0.18s !important;
#         box-shadow: none !important;
#     }

#     .stDownloadButton > button:hover {
#         background: rgba(62,207,163,0.1) !important;
#         border-color: var(--accent3) !important;
#         transform: translateY(-1px) !important;
#         box-shadow: 0 4px 16px rgba(62,207,163,0.15) !important;
#     }

#     /* ── Dataframe / table ── */
#     [data-testid="stDataFrame"] {
#         border: 1px solid var(--border2) !important;
#         border-radius: var(--radius) !important;
#         overflow: hidden !important;
#     }

#     [data-testid="stDataFrame"] table {
#         background: var(--bg3) !important;
#         font-family: var(--font-mono) !important;
#         font-size: 13px !important;
#     }

#     [data-testid="stDataFrame"] th {
#         background: var(--surface2) !important;
#         color: var(--text3) !important;
#         font-size: 10px !important;
#         text-transform: uppercase !important;
#         letter-spacing: 1.5px !important;
#         border-bottom: 1px solid var(--border2) !important;
#         padding: 10px 14px !important;
#     }

#     [data-testid="stDataFrame"] td {
#         color: var(--text2) !important;
#         border-bottom: 1px solid var(--border) !important;
#         padding: 10px 14px !important;
#     }

#     [data-testid="stDataFrame"] tr:hover td {
#         background: rgba(79,142,247,0.04) !important;
#         color: var(--text) !important;
#     }

#     /* ── Subheader ── */
#     .stMarkdown h3,
#     h3 {
#         font-family: var(--font-display) !important;
#         font-weight: 400 !important;
#         font-style: italic !important;
#         font-size: 1.3rem !important;
#         color: var(--text) !important;
#         letter-spacing: -0.2px !important;
#     }

#     /* ── Info / warning / success alerts ── */
#     [data-testid="stAlert"] {
#         background: var(--surface) !important;
#         border: 1px solid var(--border2) !important;
#         border-radius: var(--radius) !important;
#         font-family: var(--font-body) !important;
#         font-size: 14px !important;
#         color: var(--text2) !important;
#     }

#     /* ── Success alert ── */
#     [data-baseweb="notification"][kind="positive"] {
#         background: rgba(62,207,163,0.08) !important;
#         border: 1px solid rgba(62,207,163,0.25) !important;
#         border-radius: var(--radius) !important;
#         color: var(--accent3) !important;
#         font-family: var(--font-mono) !important;
#         font-size: 13px !important;
#     }

#     /* ── Scrollbar ── */
#     ::-webkit-scrollbar { width: 6px; height: 6px; }
#     ::-webkit-scrollbar-track { background: var(--bg); }
#     ::-webkit-scrollbar-thumb {
#         background: var(--surface2);
#         border-radius: 3px;
#     }
#     ::-webkit-scrollbar-thumb:hover { background: var(--text3); }

#     /* ── Column gaps ── */
#     [data-testid="column"] {
#         padding: 0 0.4rem !important;
#     }

#     /* ── Hide Streamlit branding ── */
#     #MainMenu, footer, header { visibility: hidden !important; }

#     /* ── Welcome screen ── */
#     .welcome-icon {
#         font-size: 3rem;
#         margin-bottom: 1rem;
#         display: block;
#         animation: pulse-icon 3s ease-in-out infinite;
#     }

#     @keyframes pulse-icon {
#         0%, 100% { transform: scale(1); opacity: 1; }
#         50%       { transform: scale(1.06); opacity: 0.85; }
#     }

#     .welcome-title {
#         font-family: var(--font-display) !important;
#         font-size: 2rem !important;
#         font-weight: 400 !important;
#         font-style: italic !important;
#         color: var(--text) !important;
#         margin-bottom: 0.75rem !important;
#         letter-spacing: -0.5px !important;
#     }

#     .welcome-sub {
#         font-family: var(--font-body) !important;
#         font-size: 15px !important;
#         color: var(--text2) !important;
#         font-weight: 300 !important;
#         line-height: 1.7 !important;
#     }

#     .step-row {
#         display: flex;
#         align-items: center;
#         gap: 14px;
#         margin-top: 1.1rem;
#         padding: 12px 16px;
#         background: var(--bg3);
#         border: 1px solid var(--border);
#         border-radius: 10px;
#         transition: border-color 0.2s;
#     }
#     .step-row:hover { border-color: var(--border2); }

#     .step-num {
#         width: 28px;
#         height: 28px;
#         border-radius: 50%;
#         background: linear-gradient(135deg, var(--accent), var(--accent2));
#         display: flex;
#         align-items: center;
#         justify-content: center;
#         font-family: var(--font-mono);
#         font-size: 12px;
#         font-weight: 600;
#         color: #fff;
#         flex-shrink: 0;
#     }

#     .step-text {
#         font-size: 14px;
#         color: var(--text2);
#     }

#     /* ── Experience section ── */
#     .exp-text {
#         font-family: var(--font-body) !important;
#         font-size: 14px !important;
#         color: var(--text2) !important;
#         line-height: 1.8 !important;
#         font-weight: 300 !important;
#         white-space: pre-wrap !important;
#         border-left: 2px solid rgba(79,142,247,0.3) !important;
#         padding-left: 1rem !important;
#         margin-top: 0.5rem !important;
#     }

#     /* ── Raw text expander content ── */
#     .stTextContent, pre {
#         font-family: var(--font-mono) !important;
#         font-size: 12.5px !important;
#         color: var(--text2) !important;
#         background: var(--bg) !important;
#         border-radius: 8px !important;
#         padding: 1rem !important;
#         line-height: 1.7 !important;
#     }

#     /* ── DB subheader ── */
#     .db-header {
#         display: flex;
#         align-items: center;
#         gap: 10px;
#         margin-bottom: 1rem;
#     }

#     .db-pill {
#         font-family: var(--font-mono);
#         font-size: 10px;
#         padding: 3px 10px;
#         border-radius: 20px;
#         background: rgba(79,142,247,0.1);
#         border: 1px solid rgba(79,142,247,0.25);
#         color: var(--accent);
#         letter-spacing: 1px;
#         text-transform: uppercase;
#     }
# </style>
# """, unsafe_allow_html=True)

# # ------------------------------------------------------------
# # UI
# # ------------------------------------------------------------
# st.markdown("<h1 style='text-align: center; color: white; padding-top: 1rem;'>Resume Analyzer Pro</h1>", unsafe_allow_html=True)
# st.markdown("<p style='text-align: center; color: #d0dfff;'>Upload · Extract · Save to CSV</p>", unsafe_allow_html=True)

# # Sidebar
# with st.sidebar:
#     st.markdown("## 📤 Upload Resume")
#     uploaded_file = st.file_uploader("PDF, DOCX, or TXT", type=["pdf", "docx", "txt"])
#     st.markdown("---")
#     st.markdown("## ✍️ Or Paste Text")
#     pasted_text = st.text_area("Paste resume content here", height=200)
#     st.markdown("---")
#     st.image("https://img.icons8.com/clouds/200/resume.png", width=100)

# # Main container
# if uploaded_file is not None or pasted_text:
#     raw_text = get_raw_text(uploaded_file, pasted_text)
#     if raw_text:
#         with st.container():
#             st.markdown("<div class='main-card'>", unsafe_allow_html=True)
#             with st.expander("📜 Raw Extracted Text (Preview)"):
#                 st.text(raw_text[:2000])
#             st.markdown("</div>", unsafe_allow_html=True)

#         with st.spinner("🔍 Extracting fields using AI smarts..."):
#             extracted = parse_resume(raw_text)

#         # Display extracted info in metric boxes
#         st.markdown("<div class='main-card' style='padding: 1.5rem;'>", unsafe_allow_html=True)
#         st.markdown("<h3 style='text-align: center; color: #1a2b4c;'>📋 Extracted Details</h3>", unsafe_allow_html=True)
#         col1, col2, col3 = st.columns(3)
#         with col1:
#             st.markdown(f"""
#             <div class="metric-box">
#                 <div class="metric-label">👤 &nbsp;Name</div>
#                 <div class="metric-value">{extracted['Name'] or '–'}</div>
#             </div>
#             """, unsafe_allow_html=True)
#             st.markdown(f"""
#             <div class="metric-box">
#                 <div class="metric-label">📧 &nbsp;Email</div>
#                 <div class="metric-value">{extracted['Email'] or '–'}</div>
#             </div>
#             """, unsafe_allow_html=True)
#         with col2:
#             st.markdown(f"""
#             <div class="metric-box">
#                 <div class="metric-label">🔗 &nbsp;LinkedIn</div>
#                 <div class="metric-value">{extracted['LinkedIn'] or '–'}</div>
#             </div>
#             """, unsafe_allow_html=True)
#             st.markdown(f"""
#             <div class="metric-box">
#                 <div class="metric-label">📞 &nbsp;Phone</div>
#                 <div class="metric-value">{extracted['Phone'] or '–'}</div>
#             </div>
#             """, unsafe_allow_html=True)
#         with col3:
#             st.markdown(f"""
#             <div class="metric-box">
#                 <div class="metric-label">🎂 &nbsp;Age</div>
#                 <div class="metric-value">{extracted['Age'] or '–'}</div>
#             </div>
#             """, unsafe_allow_html=True)
#             st.markdown(f"""
#             <div class="metric-box">
#                 <div class="metric-label">📍 &nbsp;Location</div>
#                 <div class="metric-value">{extracted['Location'] or '–'}</div>
#             </div>
#             """, unsafe_allow_html=True)
#         st.markdown("</div>", unsafe_allow_html=True)

#         # Experience paragraph
#         st.markdown("<div class='main-card' style='padding: 1.5rem;'>", unsafe_allow_html=True)
#         st.markdown("<h4 style='color: #1a2b4c;'>💼 Professional Experience</h4>", unsafe_allow_html=True)
#         exp_text = extracted['Experience_Text']
#         if exp_text:
#             st.markdown(f"<div class='exp-text'>{exp_text[:2000]}</div>", unsafe_allow_html=True)
#         else:
#             st.info("No experience section detected.")
#         st.markdown("</div>", unsafe_allow_html=True)

#         # Save to CSV
#         st.markdown("<div class='main-card' style='padding: 1.5rem;'>", unsafe_allow_html=True)
#         col_save, col_download = st.columns([2, 1])
#         with col_save:
#             if st.button("💾 Save to CSV & Update Table"):
#                 csv_path = save_to_csv(extracted)
#                 st.success(f"✅ Data appended to `{csv_path}`")
#         # Show current CSV
#         csv_file = "data/extracted_resumes.csv"
#         if os.path.exists(csv_file) and os.path.getsize(csv_file) > 0:
#             df = pd.read_csv(csv_file)
#             st.markdown("""
#             <div class='db-header'>
#                 <h3 style='margin:0;font-style:italic;'>Resume Database</h3>
#                 <span class='db-pill'>Live</span>
#             </div>
#             """, unsafe_allow_html=True)
#             st.dataframe(df, use_container_width=True)
#             csv = df.to_csv(index=False).encode('utf-8')
#             with col_download:
#                 st.download_button(
#                     label="⬇️ Download CSV",
#                     data=csv,
#                     file_name="extracted_resumes.csv",
#                     mime="text/csv"
#                 )
#         else:
#             st.info("No records yet. Click 'Save to CSV' to add the first entry.")
#         st.markdown("</div>", unsafe_allow_html=True)
#     else:
#         st.warning("⚠️ Could not extract text. Please check your file or pasted content.")
# else:
#     # Welcome screen
#     st.markdown("""
#     <div class='main-card' style='text-align: center; padding: 3rem 2rem;'>
#         <span class='welcome-icon'>📄</span>
#         <div class='welcome-title'>Welcome to Resume Analyzer Pro</div>
#         <p class='welcome-sub'>Upload a resume or paste its text using the sidebar<br>to instantly extract key fields.</p>
#         <div style='max-width: 400px; margin: 2rem auto 0; text-align: left;'>
#             <div class='step-row'>
#                 <div class='step-num'>1</div>
#                 <div class='step-text'>Upload a PDF, DOCX, or TXT file — or paste raw text</div>
#             </div>
#             <div class='step-row'>
#                 <div class='step-num'>2</div>
#                 <div class='step-text'>AI extracts name, email, phone, LinkedIn & experience</div>
#             </div>
#             <div class='step-row'>
#                 <div class='step-num'>3</div>
#                 <div class='step-text'>Save all records to a shareable, downloadable CSV</div>
#             </div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)
    
    # import streamlit as st
# from extractor import get_raw_text, parse_resume, save_to_csv
# import pandas as pd
# import os

# st.set_page_config(page_title="Resume Analyzer Dashboard", layout="wide")
# st.title("📄 Resume Analyzer Dashboard")
# st.markdown("Upload a resume (PDF, DOCX) or paste the text. Extracted fields are saved to a CSV file.")

# # Sidebar - upload or paste
# st.sidebar.header("1. Upload Resume")
# uploaded_file = st.sidebar.file_uploader("Choose a file", type=["pdf", "docx", "txt"])

# st.sidebar.markdown("---")
# st.sidebar.header("2. Or Paste Resume Text")
# pasted_text = st.sidebar.text_area("Paste the full resume text here", height=200)

# # Main area
# if uploaded_file is not None or pasted_text:
#     raw_text = get_raw_text(uploaded_file, pasted_text)
#     if raw_text:
#         st.subheader("📝 Raw Extracted Text")
#         with st.expander("Show raw text"):
#             st.text(raw_text[:2000])  # preview first 2000 chars

#         with st.spinner("🔍 Analyzing resume..."):
#             extracted = parse_resume(raw_text)

#         st.subheader("✅ Extracted Information")
#         col1, col2 = st.columns(2)
#         with col1:
#             st.metric("Name", extracted["Name"] or "N/A")
#             st.metric("Email", extracted["Email"] or "N/A")
#             st.metric("Phone", extracted["Phone"] or "N/A")
#         with col2:
#             st.metric("Age", extracted["Age"] or "N/A")
#             st.metric("Location", extracted["Location"] or "N/A")
#             st.metric("LinkedIn", extracted["LinkedIn"] or "N/A")

#         st.subheader("💼 Professional Experience (Organizations)")
#         st.write(extracted["Experience_Organizations"] if extracted["Experience_Organizations"] else "None detected")

#         if st.button("💾 Save to CSV"):
#             csv_path = save_to_csv(extracted)
#             st.success(f"Saved to `{csv_path}`")
#             # Show current CSV content
#             if os.path.exists(csv_path):
#                 df = pd.read_csv(csv_path)
#                 st.dataframe(df)
#                 csv = df.to_csv(index=False).encode('utf-8')
#                 st.download_button(
#                     label="⬇️ Download CSV",
#                     data=csv,
#                     file_name="extracted_resumes.csv",
#                     mime="text/csv"
#                 )
#     else:
#         st.warning("No text could be extracted. Please check your file or pasted content.")
# else:
#     st.info("👈 Upload a resume file or paste text in the sidebar to begin.")