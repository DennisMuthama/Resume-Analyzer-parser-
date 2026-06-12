import re
import pdfplumber
import docx
from datetime import datetime
import pandas as pd
import os
from dateutil.relativedelta import relativedelta

# ------------------------------------------------------------
# 1. Extract raw text
# ------------------------------------------------------------
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs]).strip()

def get_raw_text(uploaded_file, pasted_text=None):
    if pasted_text:
        return pasted_text.strip()
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.pdf'):
            return extract_text_from_pdf(uploaded_file)
        elif uploaded_file.name.endswith('.docx'):
            return extract_text_from_docx(uploaded_file)
        else:
            return uploaded_file.read().decode('utf-8', errors='ignore').strip()
    return ""

# ------------------------------------------------------------
# 2. Extraction functions (original)
# ------------------------------------------------------------
def extract_email(text):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group(0) if match else ""

def extract_phone(text):
    pattern = r'[\+\(]?\d{1,3}[-.\s]?\)?\s?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{0,4}'
    full_matches = re.findall(pattern, text)
    if full_matches:
        return max(full_matches, key=len).strip()
    return ""

def extract_linkedin(text):
    pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0) if match else ""

def extract_name(text):
    lines = text.split('\n')
    for line in lines:
        if re.search(r'^name\s*:\s*', line, re.IGNORECASE):
            return re.sub(r'^name\s*:\s*', '', line, flags=re.IGNORECASE).strip()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if (re.search(r'@', line) or
            re.search(r'^(\+?\d|[\(\)\d]){3,}', line) or
            re.search(r'linkedin\.com', line, re.IGNORECASE) or
            re.search(r'address|phone|email|mobile|objective|summary|experience|education|skills', line, re.IGNORECASE)):
            continue
        words = line.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w.isalpha()):
            return line
    return ""

def extract_age(text):
    age_pattern = r'age\s*:\s*(\d{1,3})'
    match = re.search(age_pattern, text, re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r'(\d{1,3})\s*years?\s*old', text, re.IGNORECASE)
    if match:
        return match.group(1)
    dob_patterns = [
        r'(?:DOB|Date\s*of\s*Birth)\s*:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(?:Born)\s*:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    ]
    for pat in dob_patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            dob_str = match.group(1)
            for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y"):
                try:
                    dob = datetime.strptime(dob_str, fmt)
                    today = datetime.today()
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                    return str(age)
                except ValueError:
                    continue
    return ""

def extract_location(text):
    loc_pattern = r'(?:Location|Address)\s*:\s*(.*)'
    match = re.search(loc_pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if re.search(r'\d{1,6}\s*,?\s*[A-Za-z\s]+', line) and not re.search(r'phone|email|linkedin', line, re.IGNORECASE):
            return line
    return ""

def extract_experience_paragraph(text):
    exp_start = re.search(r'(?:EXPERIENCE|WORK\s*EXPERIENCE|PROFESSIONAL\s*EXPERIENCE|EMPLOYMENT)', text, re.IGNORECASE)
    if not exp_start:
        return ""
    start_idx = exp_start.end()
    exp_end = re.search(r'(?:EDUCATION|SKILLS|PROJECTS|CERTIFICATIONS|REFERENCE)\s*\n', text[start_idx:], re.IGNORECASE)
    if exp_end:
        end_idx = start_idx + exp_end.start()
    else:
        end_idx = len(text)
    section = text[start_idx:end_idx].strip()
    cleaned = re.sub(r'\n\s*\n', '\n', section)
    cleaned = cleaned.replace('\n', ' | ')
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    return cleaned[:3000]

# ------------------------------------------------------------
# 3. NEW: Education extraction
# ------------------------------------------------------------
def extract_education(text):
    """
    Extract the highest degree, university, and graduation year.
    Looks for common degree patterns and nearby university/year.
    """
    degree = ""
    university = ""
    grad_year = ""

    # List of degree patterns (case‑insensitive)
    degree_patterns = [
        r'(Ph\.?D\.?|Doctor of Philosophy)',
        r'(Master\s?of\s?[A-Za-z]+|M\.?[A-Za-z]\.?)',
        r'(M\.?Sc\.?|M\.?A\.?|M\.?B\.?A\.?|M\.?Eng\.?|M\.?Tech\.?)',
        r'(Bachelor\s?of\s?[A-Za-z]+|B\.?[A-Za-z]\.?)',
        r'(B\.?Sc\.?|B\.?A\.?|B\.?Tech\.?|B\.?E\.?|B\.?Com\.?)',
        r'(Associate\s?of\s?[A-Za-z]+)',
        r'(High\s?School Diploma|GED)',
    ]

    # Try to find the highest degree in the whole text
    found_degrees = []
    for pat in degree_patterns:
        matches = re.findall(pat, text, re.IGNORECASE)
        found_degrees.extend(matches)

    if found_degrees:
        # Pick the highest ranking degree (rough priority)
        priority = []
        for d in found_degrees:
            if re.search(r'Ph\.?D|Doctor', d, re.IGNORECASE):
                priority.append((1, d))
            elif re.search(r'Master|M\.?Sc|M\.?A|M\.?B\.?A|M\.?Eng|M\.?Tech', d, re.IGNORECASE):
                priority.append((2, d))
            elif re.search(r'Bachelor|B\.?Sc|B\.?A|B\.?Tech|B\.?E|B\.?Com', d, re.IGNORECASE):
                priority.append((3, d))
            else:
                priority.append((4, d))
        if priority:
            # Sort by priority (lowest number = highest degree)
            priority.sort(key=lambda x: x[0])
            degree = priority[0][1].strip()

    # University extraction: look for "University of ..." or "... University"
    uni_pattern = r'((?:[A-Z][a-z]+\s)?(?:University|College|Institute)\s?(?:of\s)?[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)'
    uni_matches = re.findall(uni_pattern, text)
    if uni_matches:
        university = uni_matches[0].strip()
    else:
        # Fallback: line after "Education" header that looks like a school
        edu_section_start = re.search(r'EDUCATION', text, re.IGNORECASE)
        if edu_section_start:
            start = edu_section_start.end()
            end = re.search(r'(?:EXPERIENCE|SKILLS|PROJECTS)', text[start:], re.IGNORECASE)
            section = text[start:start+end.start()] if end else text[start:]
            for line in section.split('\n'):
                line = line.strip()
                if len(line) > 5 and not re.search(r'degree|major|minor|gpa', line, re.IGNORECASE):
                    university = line
                    break

    # Graduation year: look for a four‑digit year near the degree or university
    year_pattern = r'((?:19|20)\d{2})'
    # Try to get year from line that also contains degree/university
    if degree or university:
        # Search lines containing those
        for line in text.split('\n'):
            if (degree and degree.lower() in line.lower()) or (university and university.lower() in line.lower()):
                year_match = re.search(year_pattern, line)
                if year_match:
                    grad_year = year_match.group(1)
                    break
    if not grad_year:
        # Fallback: any four‑digit year near education section
        edu_section_start = re.search(r'EDUCATION', text, re.IGNORECASE)
        if edu_section_start:
            start = edu_section_start.end()
            end = re.search(r'(?:EXPERIENCE|SKILLS|PROJECTS)', text[start:], re.IGNORECASE)
            section = text[start:start+end.start()] if end else text[start:]
            year_match = re.search(year_pattern, section)
            if year_match:
                grad_year = year_match.group(1)

    return degree, university, grad_year

# ------------------------------------------------------------
# 4. NEW: Years of experience extraction
# ------------------------------------------------------------
def extract_years_experience(exp_paragraph):
    """
    Estimate total years of professional experience from date ranges.
    Parses patterns like '2018 - 2021', 'Jan 2020 – Present', '2018-2021'.
    Returns a rounded number as string, or empty if no data.
    """
    if not exp_paragraph:
        return ""
    # Replace separator variations
    exp = exp_paragraph.replace(' – ', '-').replace('–', '-').replace(' to ', '-')
    # Patterns that capture start and end years/month years
    # Pattern 1: "2018 - 2021" or "Jan 2018 - Dec 2021"
    date_range = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s*)?(\d{4})\s*[-–]\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s*)?(\d{4}|Present|present)'
    ranges = re.findall(date_range, exp)
    total_months = 0
    for m1, y1, m2, y2 in ranges:
        try:
            start_year = int(y1)
            if y2.lower() == 'present':
                end_date = datetime.today()
            else:
                end_year = int(y2)
                # If no month given, assume July (mid year)
                start_month = 7
                end_month = 7
                # If months provided, parse them
                if m1.strip():
                    start_month = datetime.strptime(m1.strip()[:3], '%b').month
                if m2.strip():
                    end_month = datetime.strptime(m2.strip()[:3], '%b').month
                end_date = datetime(end_year, end_month, 1)
            start_date = datetime(start_year, 1, 1)  # approximate
            if m1.strip():
                start_date = datetime(start_year, start_month, 1)
            # Calculate difference in months
            delta = relativedelta.relativedelta(end_date, start_date)
            total_months += delta.years * 12 + delta.months
        except:
            continue
    if total_months > 0:
        years = total_months / 12
        return str(round(years, 1))
    return ""

# ------------------------------------------------------------
# 5. NEW: Skills extraction (500+ curated list)
# ------------------------------------------------------------
SKILLS_LIST = [
    "Python", "Java", "JavaScript", "C++", "C#", "Ruby", "PHP", "Swift", "Kotlin", "TypeScript",
    "R", "Scala", "Go", "Rust", "Perl", "MATLAB", "Dart", "Lua", "Groovy", "Objective-C",
    "HTML", "CSS", "SQL", "NoSQL", "GraphQL", "REST API", "JSON", "XML", "YAML",
    "React", "Angular", "Vue.js", "Node.js", "Express.js", "Django", "Flask", "Spring Boot",
    "ASP.NET", "Laravel", "Ruby on Rails", "FastAPI", "Next.js", "Nuxt.js", "Svelte",
    "Git", "GitHub", "GitLab", "Bitbucket", "SVN", "Mercurial",
    "Docker", "Kubernetes", "Jenkins", "CircleCI", "Travis CI", "GitHub Actions", "Ansible", "Terraform", "Puppet", "Chef",
    "AWS", "Azure", "Google Cloud", "IBM Cloud", "Oracle Cloud", "DigitalOcean", "Heroku", "Netlify", "Vercel",
    "Machine Learning", "Deep Learning", "Natural Language Processing", "Computer Vision", "Data Science", "Big Data",
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly",
    "Hadoop", "Spark", "Kafka", "Airflow", "Tableau", "Power BI", "Excel", "Google Analytics",
    "Agile", "Scrum", "Kanban", "Waterfall", "JIRA", "Trello", "Asana", "Confluence", "Slack", "Microsoft Teams",
    "Linux", "Unix", "Windows", "macOS", "Shell Scripting", "Bash", "PowerShell",
    "Cybersecurity", "Penetration Testing", "Ethical Hacking", "Firewalls", "VPN", "IDS/IPS",
    "DevOps", "CI/CD", "Microservices", "Serverless", "RESTful", "SOAP",
    "MySQL", "PostgreSQL", "MongoDB", "SQLite", "Oracle DB", "SQL Server", "Redis", "Elasticsearch", "Cassandra", "DynamoDB",
    "UI/UX Design", "Figma", "Sketch", "Adobe XD", "Photoshop", "Illustrator", "InDesign",
    "Project Management", "Product Management", "Business Analysis", "Data Analysis", "Data Engineering", "ETL",
    "Communication", "Leadership", "Teamwork", "Problem Solving", "Critical Thinking", "Time Management", "Adaptability", "Creativity",
    "Customer Service", "Sales", "Marketing", "Digital Marketing", "SEO", "SEM", "Content Management", "CRM", "Salesforce",
    "Financial Modeling", "Accounting", "QuickBooks", "SAP", "Microsoft Dynamics",
    "AutoCAD", "SolidWorks", "MATLAB", "Simulink", "Revit",
    "Networking", "TCP/IP", "DNS", "DHCP", "LAN/WAN", "MPLS", "BGP", "OSPF",
    "Embedded Systems", "Arduino", "Raspberry Pi", "PCB Design", "VHDL", "Verilog",
    "Game Development", "Unity", "Unreal Engine", "Blender", "Maya", "3D Modeling",
    "Video Editing", "Final Cut Pro", "Premiere Pro", "After Effects",
    "Photography", "Lightroom", "Capture One",
    "Writing", "Technical Writing", "Copywriting", "Editing", "Proofreading",
    "Public Speaking", "Presentation Skills", "Negotiation", "Conflict Resolution",
    "Research", "Data Visualization", "Statistics", "Mathematics", "Physics",
    "Chemistry", "Biology", "Medicine", "Healthcare", "Nursing",
    "Legal Research", "Contract Negotiation", "Intellectual Property",
    "Supply Chain Management", "Logistics", "Procurement", "Inventory Management",
    "Quality Assurance", "Testing", "Selenium", "JUnit", "TestNG", "Cucumber",
    "Mobile Development", "iOS Development", "Android Development", "Flutter", "React Native", "Xamarin",
    "Ionic", "Cordova",
    "Blockchain", "Cryptocurrency", "Smart Contracts", "Solidity", "Web3",
    "Quantum Computing",
    "A/B Testing", "Growth Hacking", "Social Media Marketing", "Content Creation",
    "Bootstrap", "Tailwind CSS", "SASS", "LESS",
    "Web Security", "OWASP", "Encryption", "Authentication", "Authorization",
    "API Development", "API Integration",
    "System Administration", "Network Administration",
    "Data Warehousing", "Data Mining", "Hadoop", "Hive", "Pig",
    "SQL", "T-SQL", "PL/SQL", "PostgreSQL", "Oracle SQL",
    "Git", "Mercurial", "SVN",
    "Agile Methodologies", "Scrum Master", "Product Owner",
    "Cloud Computing", "SaaS", "PaaS", "IaaS",
    "Virtualization", "VMware", "Hyper-V", "VirtualBox",
    "Operating Systems", "Linux", "Windows Server", "Unix",
    "Customer Relationship Management", "CRM", "Salesforce", "HubSpot",
    "Enterprise Resource Planning", "ERP", "SAP", "Oracle EBS",
    "Business Intelligence", "BI", "Data Warehousing", "OLAP",
    "Machine Learning Algorithms", "Regression", "Classification", "Clustering",
    "Deep Learning Frameworks", "CNN", "RNN", "LSTM",
    "Natural Language Toolkit", "NLTK", "spaCy", "TextBlob",
    "Robotics", "ROS", "SLAM",
    "Control Systems", "PLC", "SCADA",
    "RFID", "IoT", "Embedded AI",
    "UI Design", "Interaction Design", "Wireframing", "Prototyping",
    "Accessibility", "WCAG", "ARIA",
    "Graphic Design", "Typography", "Color Theory",
    "Video Production", "Animation", "Motion Graphics",
    "Scripting", "Bash", "Perl", "Python", "Ruby",
    "Unit Testing", "Integration Testing", "System Testing",
    "Performance Testing", "JMeter", "LoadRunner",
    "Security Testing", "Penetration Testing", "Vulnerability Assessment",
    "Compliance", "GDPR", "HIPAA", "PCI-DSS",
    "Auditing", "Forensics",
    "Legal", "Contract Law", "Corporate Law", "Intellectual Property Law",
    "Academic Research", "Statistical Analysis", "SPSS", "Stata",
    "Econometrics", "Microeconomics", "Macroeconomics",
    "Journalism", "Reporting", "Investigative Journalism",
    "Healthcare Administration", "Patient Care", "EMR", "EHR",
    "Pharmaceutical", "Drug Development", "Clinical Trials",
    "Construction", "Project Planning", "Blueprint Reading",
    "Aviation", "Aerospace", "Flight Mechanics",
    "Logistics", "Supply Chain Optimization", "Shipping",
    "Hospitality", "Hotel Management", "Event Planning",
    "Real Estate", "Property Management", "Lease Administration",
    "Finance", "Accounting", "Bookkeeping", "Tax Preparation",
    "Investment Banking", "Portfolio Management", "Risk Management",
    "Insurance", "Claims Processing", "Underwriting",
    "Telecommunications", "VoIP", "5G",
    "Pharmaceuticals", "Good Manufacturing Practice", "GMP",
    "Food Safety", "HACCP", "ISO 22000",
    "Environmental Science", "Sustainability", "Renewable Energy",
    "GIS", "Remote Sensing", "ArcGIS", "QGIS",
    "Surveying", "Cartography",
    "Animation", "VFX", "Compositing",
    "Sound Design", "Audio Engineering", "Pro Tools",
    "Podcasting", "Live Streaming",
    "Customer Support", "Help Desk", "Ticketing Systems",
    "Database Administration", "Backup and Recovery",
    "Network Security", "Firewall Configuration", "Intrusion Detection",
    "Cloud Architecture", "Serverless Architecture", "Microservices",
    "Game Design", "Level Design", "Character Design",
    "Music Production", "Audio Mixing", "Mastering",
    "Digital Painting", "Concept Art", "Illustration",
    "Photography", "Portrait Photography", "Landscape Photography",
    "Fashion Design", "Textile Design", "Pattern Making",
    "Culinary Arts", "Baking", "Pastry",
    "Event Management", "Conference Planning", "Wedding Planning",
    "Travel Planning", "Tourism", "Hospitality Management",
    "Social Work", "Counseling", "Therapy",
    "Psychology", "Psychiatry", "Behavioral Health",
    "Nursing", "Clinical Care", "Phlebotomy",
    "Physical Therapy", "Occupational Therapy", "Speech Therapy",
    "Veterinary", "Animal Care", "Pet Grooming",
    "Automotive", "Mechanical Engineering", "Automotive Repair",
    "HVAC", "Plumbing", "Electrical",
    "Carpentry", "Welding", "Masonry",
    "Painting", "Home Renovation", "Interior Design",
    "Landscaping", "Gardening", "Horticulture",
    "Pest Control", "Pesticide Application",
    "Security Guard", "Surveillance", "CCTV",
    "Military", "Defense", "Combat Training",
    "Law Enforcement", "Criminology", "Forensic Science",
    "Firefighting", "Emergency Medical Services", "Paramedic",
    "Piloting", "Aircraft Maintenance", "Air Traffic Control",
    "Maritime", "Navigation", "Ship Handling",
    "Farming", "Agriculture", "Crop Management",
    "Livestock", "Animal Husbandry",
    "Beekeeping", "Aquaculture",
    "Mining", "Oil & Gas", "Petroleum Engineering",
    "Renewable Energy", "Solar Power", "Wind Energy",
    "Nuclear Engineering", "Radiation Safety",
    "Quality Control", "Six Sigma", "Lean Manufacturing",
    "Supply Chain", "Procurement", "Sourcing",
    "Warehouse Management", "Inventory Control",
    "Transportation", "Fleet Management", "Dispatch",
    "Logistics Software", "SAP", "Oracle Transportation Management",
    "E-commerce", "Drop Shipping", "Online Retail",
    "Retail Management", "Merchandising", "Visual Merchandising",
    "Point of Sale", "POS Systems",
    "Cash Management", "Bank Reconciliation",
    "Credit Analysis", "Loan Origination",
    "Mortgage", "Underwriting", "Title Insurance",
    "Wealth Management", "Financial Planning",
    "Tax Law", "Corporate Tax", "International Tax",
    "Audit", "Internal Audit", "External Audit",
    "Forensic Accounting", "Fraud Examination",
    "Corporate Finance", "M&A", "Valuation",
    "Venture Capital", "Private Equity",
    "Hedge Funds", "Derivatives",
    "Commodities Trading", "Futures", "Options",
    "Stock Market", "Equity Research",
    "Fixed Income", "Bonds",
    "Foreign Exchange", "FX Trading",
    "Risk Analytics", "Credit Risk", "Market Risk",
    "Operational Risk", "Compliance Risk",
    "Actuarial Science", "Pension", "Annuities",
    "Insurance Underwriting", "Claims Management",
    "Reinsurance",
    "Public Relations", "Corporate Communications",
    "Brand Management", "Product Marketing",
    "Market Research", "Consumer Insights",
    "Advertising", "Media Buying",
    "Creative Direction", "Art Direction",
    "Copywriting", "Scriptwriting",
    "Content Strategy", "Information Architecture",
    "UX Research", "Usability Testing",
    "Service Design", "Design Thinking",
    "Business Strategy", "Competitive Analysis",
    "Change Management", "Organizational Development",
    "Talent Acquisition", "Recruitment", "Onboarding",
    "Compensation & Benefits", "Payroll",
    "Employee Relations", "Labor Law",
    "Diversity & Inclusion", "Culture Building",
    "Training & Development", "Instructional Design",
    "E-Learning", "LMS Administration",
    "Performance Management", "360-Degree Feedback",
    "Succession Planning",
    "Coaching", "Mentoring",
    "Mediation", "Dispute Resolution",
    "Corporate Governance", "Board Relations",
    "Sustainability Reporting", "ESG",
    "Impact Investing", "Social Enterprise",
    "Nonprofit Management", "Fundraising",
    "Grant Writing", "Donor Relations",
    "Philanthropy", "Corporate Social Responsibility",
    "Policy Analysis", "Government Relations",
    "Lobbying", "Legislative Affairs",
    "International Relations", "Diplomacy",
    "Translation", "Interpretation",
    "Language Teaching", "ESL", "Foreign Languages",
    "Curriculum Development", "Educational Technology",
    "Special Education", "Gifted Education",
    "Early Childhood Education", "Montessori",
    "Higher Education Administration",
    "Library Science", "Archives Management",
    "Museum Studies", "Curatorship",
    "Anthropology", "Archaeology",
    "Sociology", "Political Science",
    "History", "Philosophy",
    "Literature", "Linguistics",
    "Fine Arts", "Performing Arts",
    "Music", "Dance", "Theater",
    "Film Production", "Screenwriting",
    "Cinematography", "Film Editing",
    "Art History", "Curatorial Practice"
]

def extract_skills(text):
    """Find skills from the curated list in the text. Returns comma-separated string."""
    found = []
    text_lower = text.lower()
    for skill in SKILLS_LIST:
        # Build pattern with word boundaries to avoid substring matches (e.g., "Java" matching "JavaScript")
        # Use re.escape to handle special characters
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower, re.IGNORECASE):
            found.append(skill)
    # Remove duplicates and sort
    found = sorted(set(found))
    return ", ".join(found[:30])  # limit to 30 most relevant

# ------------------------------------------------------------
# Master function: parse_resume – now returns enhanced dict
# ------------------------------------------------------------
def parse_resume(text):
    # Extract original fields
    name = extract_name(text)
    email = extract_email(text)
    linkedin = extract_linkedin(text)
    phone = extract_phone(text)
    age = extract_age(text)
    location = extract_location(text)
    experience_text = extract_experience_paragraph(text)

    # New extractions
    degree, university, grad_year = extract_education(text)
    years_exp = extract_years_experience(experience_text)  # using exp paragraph, but could also use full text
    skills = extract_skills(text)

    return {
        "Name": name,
        "Email": email,
        "LinkedIn": linkedin,
        "Phone": phone,
        "Age": age,
        "Location": location,
        "Degree": degree,
        "University": university,
        "Graduation_Year": grad_year,
        "Skills": skills,
        "Years_Experience": years_exp,
        "Experience_Text": experience_text
    }

# ------------------------------------------------------------
# 6. Save to CSV (updated column order)
# ------------------------------------------------------------
def save_to_csv(data_dict, csv_path="data/extracted_resumes.csv"):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    new_row = pd.DataFrame([data_dict])

    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        try:
            existing_df = pd.read_csv(csv_path)
            if not existing_df.empty:
                df = pd.concat([existing_df, new_row], ignore_index=True)
            else:
                df = new_row
        except pd.errors.EmptyDataError:
            df = new_row
    else:
        df = new_row

    # Desired column order (important for consistency)
    col_order = [
        "Name", "Email", "LinkedIn", "Phone", "Age", "Location",
        "Degree", "University", "Graduation_Year", "Skills",
        "Years_Experience", "Experience_Text"
    ]
    # Keep only columns that exist (in case some are missing)
    existing_cols = [col for col in col_order if col in df.columns]
    df = df[existing_cols]
    df.to_csv(csv_path, index=False)
    return csv_path


# import re
# import pdfplumber
# import docx
# from datetime import datetime
# import pandas as pd
# import os

# # ------------------------------------------------------------
# # 1. Extract raw text from PDF, DOCX, or plain text
# # ------------------------------------------------------------
# def extract_text_from_pdf(file):
#     text = ""
#     with pdfplumber.open(file) as pdf:
#         for page in pdf.pages:
#             page_text = page.extract_text()
#             if page_text:
#                 text += page_text + "\n"
#     return text.strip()

# def extract_text_from_docx(file):
#     doc = docx.Document(file)
#     return "\n".join([para.text for para in doc.paragraphs]).strip()

# def get_raw_text(uploaded_file, pasted_text=None):
#     """Returns cleaned text from any source."""
#     if pasted_text:
#         return pasted_text.strip()
#     if uploaded_file is not None:
#         if uploaded_file.name.endswith('.pdf'):
#             return extract_text_from_pdf(uploaded_file)
#         elif uploaded_file.name.endswith('.docx'):
#             return extract_text_from_docx(uploaded_file)
#         else:
#             # Assume plain text
#             return uploaded_file.read().decode('utf-8', errors='ignore').strip()
#     return ""

# # ------------------------------------------------------------
# # 2. Extraction functions for specific fields
# # ------------------------------------------------------------
# def extract_email(text):
#     pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
#     match = re.search(pattern, text)
#     return match.group(0) if match else ""

# def extract_phone(text):
#     # Match various international and local phone formats
#     pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
#     match = re.search(pattern, text)
#     return match.group(0).strip() if match else ""

# def extract_linkedin(text):
#     pattern = r'(https?://)?(www\.)?linkedin\.com/in/[A-Za-z0-9_-]+'
#     match = re.search(pattern, text, re.IGNORECASE)
#     return match.group(0) if match else ""

# def extract_name(text):
#     """
#     Heuristic: first non-empty line that is not an email/phone/link.
#     Also look for a "Name:" label.
#     """
#     lines = text.split('\n')
#     # Try to find a line with "Name:"
#     for line in lines:
#         if re.search(r'^name\s*:\s*', line, re.IGNORECASE):
#             return re.sub(r'^name\s*:\s*', '', line, flags=re.IGNORECASE).strip()
#     # Fallback: first line that looks like a name (not email/phone/link)
#     for line in lines:
#         line = line.strip()
#         if not line:
#             continue
#         # Skip lines that are clearly not names
#         if (re.search(r'@', line) or
#             re.search(r'^(\+?\d|[\(\)\d]){3,}', line) or
#             re.search(r'linkedin\.com', line, re.IGNORECASE) or
#             re.search(r'address|phone|email|mobile|objective|summary|experience|education|skills', line, re.IGNORECASE)):
#             continue
#         # If line looks like a name (2-3 words, uppercase or proper case)
#         words = line.split()
#         if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w.isalpha()):
#             return line
#     return ""

# def extract_age(text):
#     """
#     Extract age if explicitly mentioned: "Age: 25", "25 years old"
#     or calculate from a Date of Birth.
#     """
#     # Pattern 1: "Age: XX"
#     age_pattern = r'age\s*:\s*(\d{1,3})'
#     match = re.search(age_pattern, text, re.IGNORECASE)
#     if match:
#         return match.group(1)
#     # Pattern 2: "XX years old"
#     match = re.search(r'(\d{1,3})\s*years?\s*old', text, re.IGNORECASE)
#     if match:
#         return match.group(1)
#     # Pattern 3: Date of Birth -> calculate age
#     dob_patterns = [
#         r'(?:DOB|Date\s*of\s*Birth)\s*:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
#         r'(?:Born)\s*:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
#         r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*(?:\((?:DOB|Date of Birth)\))?'
#     ]
#     for pat in dob_patterns:
#         match = re.search(pat, text, re.IGNORECASE)
#         if match:
#             dob_str = match.group(1)
#             # parse date
#             for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y"):
#                 try:
#                     dob = datetime.strptime(dob_str, fmt)
#                     today = datetime.today()
#                     age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
#                     return str(age)
#                 except ValueError:
#                     continue
#     return ""

# def extract_location(text):
#     """
#     Look for location lines like "Location: City, Country" or city/state patterns.
#     This is a basic heuristic; you can replace with geotext or NER.
#     """
#     # Explicit "Location:" label
#     loc_pattern = r'(?:Location|Address)\s*:\s*(.*)'
#     match = re.search(loc_pattern, text, re.IGNORECASE)
#     if match:
#         return match.group(1).strip()
#     # Try to find a line with a city, state zip pattern (US style)
#     lines = text.split('\n')
#     for line in lines:
#         line = line.strip()
#         if re.search(r'\d{1,6}\s*,?\s*[A-Za-z\s]+', line) and not re.search(r'phone|email|linkedin', line, re.IGNORECASE):
#             # if line looks like address (has a number and city/state)
#             return line
#     return ""

# def extract_organizations(text):
#     """
#     Extract company names from "Experience" section.
#     Heuristic: after "Experience" / "Work History" header, look for lines
#     that are likely company names (often in all caps or following a date range).
#     Returns a comma-separated list.
#     """
#     exp_section = ""
#     # Find experience section
#     exp_start = re.search(r'(?:EXPERIENCE|WORK\s*EXPERIENCE|PROFESSIONAL\s*EXPERIENCE|EMPLOYMENT)', text, re.IGNORECASE)
#     exp_end = re.search(r'(?:EDUCATION|SKILLS|PROJECTS|CERTIFICATIONS|REFERENCE)', text, re.IGNORECASE)
#     if exp_start:
#         start_idx = exp_start.end()
#         end_idx = exp_end.start() if exp_end else len(text)
#         exp_section = text[start_idx:end_idx]
#     if not exp_section:
#         return ""

#     # Lines that might be company names: often standalone, may have "at" before, or line before a date range
#     company_patterns = [
#         r'(?:at|with)\s+([A-Z][A-Za-z\s&.,]+)',   # "at Microsoft"
#         r'^([A-Z][A-Za-z\s&.,]{3,})$'  # line that is only a capitalized phrase
#     ]
#     orgs = set()
#     lines = exp_section.split('\n')
#     for i, line in enumerate(lines):
#         line = line.strip()
#         # Skip empty/date-only lines
#         if not line or re.fullmatch(r'[\d\s–\-to/]+', line):
#             continue
#         # "at Company"
#         match = re.search(r'(?:at|with)\s+([A-Z][A-Za-z\s&.,]+)', line)
#         if match:
#             orgs.add(match.group(1).strip())
#         # If line is fully capitalized (common for company names in old formats)
#         elif line.upper() == line and len(line) > 3 and not line.isdigit():
#             # But skip if contains common non-company words
#             if not any(word in line.lower() for word in ['experience', 'intern', 'manager', 'developer', 'engineer']):
#                 orgs.add(line.title())
#     if not orgs:
#         # fallback: any line that doesn't have many lowercase words (looks like a title/company)
#         for line in lines:
#             words = line.split()
#             if len(words) <= 5 and sum(1 for w in words if w[0].isupper()) >= 1:
#                 orgs.add(line.strip())
#     return ", ".join(list(orgs)[:5])  # limit to 5 companies

# def parse_resume(text):
#     """Master function that extracts all fields from raw text."""
#     return {
#         "Name": extract_name(text),
#         "Age": extract_age(text),
#         "Location": extract_location(text),
#         "Phone": extract_phone(text),
#         "LinkedIn": extract_linkedin(text),
#         "Email": extract_email(text),
#         "Experience_Organizations": extract_organizations(text)
#     }

# # ------------------------------------------------------------
# # 3. Save to CSV
# # ------------------------------------------------------------
# def save_to_csv(data_dict, csv_path="data/extracted_resumes.csv"):
#     os.makedirs(os.path.dirname(csv_path), exist_ok=True)
#     new_row = pd.DataFrame([data_dict])

#     # If file exists and is not empty, load it; otherwise start fresh
#     if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
#         try:
#             existing_df = pd.read_csv(csv_path)
#             # Concatenate only if existing_df has data
#             if not existing_df.empty:
#                 df = pd.concat([existing_df, new_row], ignore_index=True)
#             else:
#                 df = new_row
#         except pd.errors.EmptyDataError:
#             # File exists but pandas couldn't parse (empty or malformed)
#             df = new_row
#     else:
#         df = new_row

#     df.to_csv(csv_path, index=False)
#     return csv_path