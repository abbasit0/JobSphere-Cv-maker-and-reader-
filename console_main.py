import os
import time
import webbrowser
import utils
import re


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    clear_screen()
    print("      JOBSPHERE - CONSOLE EDITION")

def recruiter_mode():
    print_header()
    print("\n RECRUITER MODE: BATCH PROCESSOR ")
    
    default_path = "Resumes" 
    if not os.path.exists(default_path):
        if os.path.exists(os.path.join("static", "generated_cvs")):
            default_path = os.path.join("static", "generated_cvs")
        else:
            os.makedirs(default_path)

    print(f"Scanning Folder: {default_path}")
    
    skills_input = input("1. Enter Required Skills (comma separated): ").lower()
    required_skills = [s.strip() for s in skills_input.split(',') if s.strip()]
    
    try:
        min_cgpa = float(input("2. Minimum CGPA (Enter 0 to ignore): "))
    except: min_cgpa = 0.0
    
    try:
        min_exp = float(input("3. Minimum Experience Years (Enter 0 to ignore): "))
    except: min_exp = 0.0

    files = [f for f in os.listdir(default_path) if f.endswith(('.pdf', '.html'))]
    all_candidates = []

    print(f"\n--- SCANNING {len(files)} FILES ---")
    print("-" * 75)
    
    for filename in files:
        filepath = os.path.join(default_path, filename)
        content = utils.get_resume_content(filepath)
        
        if len(content) < 10: continue

        gpa = utils.find_cgpa(content)
        exp = utils.find_experience(content)
        has_skills, missing_skill = utils.check_skills(content, required_skills)
        status = "Rejected"
        reason = "Met Requirements"
        
        if not has_skills:
            reason = f"Missing Skill: {missing_skill.title()}"
        elif min_cgpa > 0 and gpa < min_cgpa:
            reason = f"Low CGPA ({gpa})"
        elif min_exp > 0 and exp < min_exp:
            reason = f"Low Exp ({exp} yrs)"
        else:
            status = "Shortlisted"
        
        icon = "✅" if status == "Shortlisted" else "❌"
        
        print(f"{icon} {filename[:20]:<20} | GPA: {gpa:<4} | Exp: {exp:<4} | {reason}")
        time.sleep(0.2)
        
        all_candidates.append({
            "Name": filename, "Status": status, "Reason": reason,
            "CGPA": gpa, "Experience": exp
        })

    # Summary
    shortlisted = [c for c in all_candidates if c['Status'] == "Shortlisted"]
    print("-" * 75)
    print(f"SUMMARY: {len(shortlisted)} Candidates Shortlisted out of {len(all_candidates)}")
    
    import csv
    with open("recruitment_report.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Name", "Status", "Reason", "CGPA", "Experience"])
        writer.writeheader()
        writer.writerows(all_candidates)
        
    print(f"\n✔ Report saved to: recruitment_report.csv")
    try:
        os.startfile("recruitment_report.csv")
    except: pass
    input("\nPress Enter to return...")

def candidate_mode():
    print_header()
    print(f"\n--- CANDIDATE MODE: CV BUILDER ---")
    
    user_data = {}
    
    while True:
        full_name = input("Enter Your Full Name : ").strip()
        if re.fullmatch(r"[A-Za-z\. ]+", full_name) and len(full_name) > 0:
            user_data["name"] = full_name.title()
            break
        print(f"Invalid Name! Letters only.")

    # Profile Pic
    pic_input = input("Enter Image Path (e.g. 'me.jpg' or leave empty): ").strip()
    if pic_input and os.path.exists(pic_input):
        user_data["filename"] = os.path.abspath(pic_input).replace("\\", "/") 
        user_data["profile_pic"] = user_data["filename"] 
    else:
        user_data["filename"] = "" 

    # Contact Info
    while True:
        phone = input("Enter Valid Phone : ").strip()
        if utils.validate_phone(phone):
            user_data["phone"] = phone
            break
        print(f"Invalid Phone!")

    while True:
        email = input("Enter Valid Email : ").strip()
        if utils.validate_email(email):
            user_data["email"] = email
            break
        print(f"Invalid Email!")

    user_data["city"] = input("Enter City/Country : ").strip() or "Lahore, Pakistan"
    user_data["job_title"] = input("Enter Job Title : ").strip().title() or "Fresh Graduate"
    
    # Skills
    skills_in = input("Enter Skills (comma separated) : ").strip()
    user_data["skills"] = utils.process_skills(skills_in)
    
    # Experience
    while True:
        try:
            exp_in = input("Enter Years of Experience : ").strip()
            user_data["years_exp"] = float(exp_in)
            user_data["level"] = utils.calculate_level(user_data["years_exp"])
            break
        except: print("Enter a number.")

    user_data["current_date"] = input("Current Role Date (e.g. 2022-Present) : ").strip() or "Present"
    
    # Previous Job
    print("\n--- Previous Job (Optional - Press Enter to skip) ---")
    user_data["prev_title"] = input("Prev Job Title : ").strip().title() or "Intern"
    user_data["prev_company"] = input("Prev Company : ").strip().title() or "Software House"
    user_data["prev_date"] = input("Prev Date : ").strip() or "2021"
    user_data["prev_desc"] = input("Prev Description : ").strip() or "Assisted senior developers."

    # Education
    print("\n--- Education ---")
    user_data["degree"] = input("Degree Name : ").strip() or "BS Computer Science"
    user_data["university"] = input("University : ").strip() or "UET Lahore"
    user_data["gpa"] = input("CGPA : ").strip() or "3.5"

    # Summaries
    user_data["summary"] = input("Professional Summary : ").strip() or f"A dedicated {user_data['job_title']}."
    user_data["about"] = input("About Me : ").strip() or "Passionate about coding."

    # 2. Template Selection
    print(f"\n-- CHOOSE YOUR DESIGN --")
    print("1. Grid Modern Blue")
    print("2. The Executive")
    print("3. The Elegant")
    print("4. The Tech Creative")
    print("5. The Classic")
    
    templates = {
        1: "Grid_Modern.html", 2: "Executive.html", 
        3: "Elegant.html", 4: "Tech_Creative.html", 5: "classic.html"
    }
    
    while True:
        try:
            choice = int(input("> Enter Choice (1-5): "))
            if 1 <= choice <= 5:
                selected_template = templates[choice]
                break
        except: pass
        print("Invalid choice.")

    # 3. Render
    print(f"\nGenerating Resume...")
    file_path = utils.render_console_cv(user_data, selected_template)
    
    if file_path:
        print(f"✔ Resume Saved: {file_path}")
        webbrowser.open("file://" + os.path.abspath(file_path))
    else:
        print(f"Error generating file.")
    
    input("\nPress Enter to return...")

while True:
    print_header()
    print("1. Recruiter Mode (Batch Scan)")
    print("2. Candidate Mode (CV Builder)")
    print("3. Launch Web Server")
    print("4. Exit")
    
    choice = input("\nSelect Option (1-4): ")
    
    if choice == '1': recruiter_mode()
    elif choice == '2': candidate_mode()
    elif choice == '3':
        print(f"\nStarting Web Server...")
        os.system("python app.py")
    elif choice == '4': break