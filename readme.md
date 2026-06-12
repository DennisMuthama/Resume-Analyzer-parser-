# 📄 Resume Parser

> Upload a resume. Get the important stuff — instantly.

A smart, multi-format resume parsing web app built with **Python** and **Streamlit**. Paste your resume text or upload a PDF/DOCX file and the parser pulls out the key details in seconds — no manual reading required.

---

## 📸 Screenshots

<!-- Add your screenshots here -->

### Upload Screen
> _Screenshot: The main upload interface_

![Upload Screen](screenshots/upload_screen.png)

### Parsed Results
> _Screenshot: Extracted resume data displayed on screen_

![Parsed Results](screenshots/parsed_results.png)

### Text Paste Mode
> _Screenshot: Pasting raw resume text directly into the app_

![Paste Mode](screenshots/paste_mode.png)

---

## ✨ Features

- 📤 **Multi-format support** — Upload PDF, DOCX, TXT, or simply paste raw resume text
- 👤 **Contact extraction** — Pulls name, email, location, LinkedIn URL, and other relevant links
- 💼 **Job title detection** — Identifies the candidate's current or most recent occupation title
- 🏢 **Work experience parsing** — Extracts work history including companies, roles, and durations
- ⚡ **Instant results** — Clean, structured output displayed right in the browser
- 🧠 **Hybrid parsing engine** — Combines regex patterns, NLP (spaCy/NLTK), and AI-based extraction for higher accuracy

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| UI / Frontend | Streamlit |
| Language | Python 3.x |
| PDF Parsing | PyMuPDF / pdfplumber |
| DOCX Parsing | python-docx |
| NLP | spaCy, NLTK |
| AI Extraction | Gemini / OpenAI API |
| Pattern Matching | Regex |

---

## 🚀 Getting Started

### Prerequisites

Make sure you have Python 3.8+ installed.

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/resume-parser.git
cd resume-parser

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the App

```bash
streamlit run app.py
```

Then open your browser and go to `http://localhost:8501`.

---

## 📂 Project Structure

```
resume-parser/
│
├── app.py                  # Main Streamlit app
├── parser/
│   ├── extractor.py        # Core extraction logic
│   ├── file_handler.py     # PDF, DOCX, and text processing
│   └── utils.py            # Helper functions
├── requirements.txt
└── README.md
```

> _Adjust the structure above to match your actual project layout._

---

## 🧪 How It Works

1. **Input** — User uploads a resume file (PDF/DOCX/TXT) or pastes text directly
2. **Text extraction** — Raw text is pulled from the file using the appropriate parser
3. **NLP + Regex pipeline** — Sections are identified and key fields are located using a combination of pattern matching and NLP models
4. **AI refinement** — Where needed, an AI model cleans up ambiguous or complex extractions
5. **Output** — Structured data is displayed cleanly in the Streamlit UI

---

## 📌 Extracted Fields

| Field | Description |
|---|---|
| Full Name | Candidate's full name |
| Email | Primary email address |
| Location | City, country or region |
| LinkedIn | LinkedIn profile URL |
| Other Links | GitHub, portfolio, or other URLs |
| Job Title | Current or most recent occupation title |
| Work Experience | Company names, roles, and time periods |

---

## 🔮 Future Improvements

- [ ] Skills extraction (technical + soft skills)
- [ ] Education history parsing
- [ ] Export parsed data as JSON or CSV
- [ ] Support for more file formats (RTF, image-based resumes via OCR)
- [ ] Resume scoring / ATS compatibility check

---

## 👨‍💻 Author

Built solo by **[Your Name]**  
📧 [your-email@example.com]  
🔗 [LinkedIn](https://linkedin.com/in/your-profile) | [GitHub](https://github.com/your-username)

---

## 📝 License

This project is open source and available under the [MIT License](LICENSE).
