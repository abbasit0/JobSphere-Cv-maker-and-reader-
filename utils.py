import os
import re
import json
import csv
from datetime import datetime
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

try:
    from pypdf import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("WARNING: pypdf not installed.")

CSV_FILE = 'Recruitment_Report.csv'
JSON_FILE = 'Candidates_Data.json'
USERS_FILE = 'users.csv'

def get_current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def process_skills(skills_string):
    if not skills_string: return []
    return [s.strip() for s in skills_string.split(',') if s.strip()]

def calculate_level(years_str):
    try:
        years = float(str(years_str).strip().split()[0])
        if years < 2: return "Junior"
        elif 2 <= years <= 5: return "Mid Level"
        else: return "Senior"
    except: return "Junior"

def save_user(name, email, password, role):
    file_exists = os.path.isfile(USERS_FILE)
    try:
        with open(USERS_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists: writer.writerow(['Name', 'Email', 'Password', 'Role'])
            writer.writerow([name.strip(), email.strip(), password.strip(), role.strip()])
        return True
    except: return False

def check_user_login(email, password):
    if not os.path.exists(USERS_FILE): return None
    try:
        with open(USERS_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row.get('Email', '').strip() == email.strip() and row.get('Password', '').strip() == password.strip():
                    return row
    except: return None
    return None

def save_cv_json(data, user_email):
    all_cvs = {}
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                all_cvs = json.load(f)
        except: all_cvs = {}
    
    if user_email not in all_cvs: all_cvs[user_email] = []
    all_cvs[user_email].insert(0, data)
    
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_cvs, f, indent=4, default=str)
    return True

def get_user_cvs(user_email):
    if not os.path.exists(JSON_FILE): return []
    try:
        with open(JSON_FILE, 'r') as f:
            all_cvs = json.load(f)
        return all_cvs.get(user_email, [])
    except: return []

def get_cv_by_id(cv_id, user_email):
    cvs = get_user_cvs(user_email)
    for cv in cvs:
        if cv.get('cv_id') == cv_id: return cv
    return None

# to validate Email
def validate_email(email):
    if len(email) < 5:
        return False
    
    pattern = re.compile(r"[A-Za-z0-9._%+-]+@[a-z]+\.com") # pattern to check the valid Email

    if pattern.fullmatch(email):
        print("Valid Email")
        return True
    else:
        print("Invalid Email")
        return False

# To validate Phone Number
def validate_phone(phone):
    pattern = re.compile(r'([0-9]{11}|[\+0-9]{13})')  # phone number check pattern 
    if pattern.fullmatch(phone):
        print("Valid Phone Number!")
        return True
    else:
        print("Invalid Phone Number!")
        return False
    
def get_resume_content(filepath):
    try:
        if filepath.endswith(".html"):
            with open(filepath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
                return soup.get_text(" ", strip=True).lower()
        elif filepath.endswith(".pdf") and PDF_SUPPORT:
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + " "
            return text.lower()
    except: return ""
    return ""

def find_cgpa(text):
    match = re.search(r'(cgpa|gpa)[\s:]*(\d+(\.\d+)?)', text)
    if match:
        try:
            val = float(match.group(2))
            if 0.0 < val <= 4.0: return val
        except: pass
    return 0.0

def find_experience(text):
    match = re.search(r'(\d+(\.\d+)?)\s(years?|y*rs?|exp)', text)
    if match:
        try: return float(match.group(1))
        except: pass
    return 0.0

def check_skills(text, required_skills):
    if isinstance(required_skills, str):
        required_skills = process_skills(required_skills)
    
    for skill in required_skills:
        if skill.lower() not in text:
            return False, skill 
    return True, None

def evaluate_candidate(content, min_cgpa, min_exp, req_skills):
 
    gpa = find_cgpa(content)
    exp = find_experience(content)
    has_skills, missing_skill = check_skills(content, req_skills)

    status = "Rejected"
    reason = "Met Requirements"

    if not has_skills:
        reason = f"Missing Skill: {missing_skill.title()}"
    elif min_cgpa > 0 and gpa < min_cgpa:
        reason = f"Low CGPA ({gpa})"
    elif min_exp > 0 and exp < min_exp:
        reason = f"Low Experience ({exp} yrs)"
    else:
        status = "Shortlisted"
        reason = "Met Requirements"

    return {
        "status": status,
        "reason": reason,
        "gpa": gpa,
        "exp": exp
    }


def process_resume_batch(batch_id, criteria, base_folder):
    batch_folder = os.path.join(base_folder, 'batches', batch_id)
    results = []
    
    print(f"\n--- PROCESSING BATCH with Criteria: {criteria} ---")

    if not os.path.exists(batch_folder): return []
    
    for filename in os.listdir(batch_folder):
        filepath = os.path.join(batch_folder, filename)
        
        content = get_resume_content(filepath)
        if len(content) < 10: continue

        req_skills_list = criteria.get('req_skill', '')
        
        evaluation = evaluate_candidate(
            content, 
            criteria.get('min_cgpa', 0), 
            criteria.get('min_exp', 0), 
            req_skills_list
        )

        results.append({
            'Name': filename,
            'Status': evaluation['status'],
            'Reason': evaluation['reason'],
            'CGPA': evaluation['gpa'],
            'Experience': evaluation['exp'],
            'File Type': 'PDF' if filename.endswith('.pdf') else 'HTML'
        })
        
    return results

def save_shortlist_report(results, batch_id):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        fieldnames = ['Name', 'Status', 'Reason', 'CGPA', 'Experience', 'File Type']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists: writer.writeheader()
        for row in results:
            writer.writerow(row)

def get_all_reports():
    data = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Name'): 
                    data.append(row)
    return list(reversed(data))


def render_console_cv(user_data, template_filename):
    output_folder = os.path.join("static", "generated_cvs")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    try:
        file_loader = FileSystemLoader(os.path.join("templates", "cv_designs"))
        env = Environment(loader=file_loader)
        template = env.get_template(template_filename)
        
        output_html = template.render(user_data)
        
        clean_name = user_data['name'].replace(' ', '_')
        filename = f"{clean_name}_{template_filename}"
        save_path = os.path.join(output_folder, filename)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(output_html)
            
        return save_path
    except Exception as e:
        print(f"Error generating CV: {e}")
        return None