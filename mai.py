import re
import os
import csv
import shutil
import PyPDF2
from groq import Groq
from pathlib import Path
from docx import Document
from dotenv import load_dotenv

# Load API key
load_dotenv()
api_key = os.getenv("API_KEY")
client = Groq(api_key=api_key)

# Input from user
job_description = input("Enter the Job Description: ")

# Input & output folders
input_folder = Path("artifact")
matched_folder = Path("matched_cvs")
matched_folder.mkdir(exist_ok=True)

# CSV file to store shortlisted candidates
output_csv = Path("shortlisted_candidates.csv")

# Allowed file formats
allowed_formats = ['.txt', '.pdf', '.docx']

# Function to save shortlisted candidate details
def save_shortlisted_candidate(name, email, phone, reason):
    file_exists = output_csv.exists()
    with open(output_csv, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Name", "Email", "Phone", "Reason"])
        writer.writerow([name, email, phone, reason])

# Loop through all CVs
for file_path in input_folder.iterdir():
    if file_path.is_file() and file_path.suffix.lower() in allowed_formats:
        print(f"\nProcessing: {file_path.name}")

        # Step 1: Read CV
        try:
            if file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    cv_text = f.read()
            elif file_path.suffix.lower() == '.docx':
                doc = Document(file_path)
                cv_text = "\n".join([para.text for para in doc.paragraphs])
            elif file_path.suffix.lower() == '.pdf':
                cv_text = ""
                with open(file_path, 'rb') as pdf:
                    reader = PyPDF2.PdfReader(pdf)
                    for page in reader.pages:
                        cv_text += page.extract_text()
        except Exception as e:
            print(f"Error reading file {file_path.name}: {e}")
            continue

        # Step 2: Send CV + JD to Groq
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": f"""
You are an expert HR recruiter.
Compare the Job Description and the Candidate CV, and output ONLY this single line of CSV exactly in this format:
Candidate Name, Candidate Email, Candidate Phone, Match Score (as X/10), Reason

Example:
John Doe, john.doe@gmail.com, +1-234-567-8901, 8/10, Candidate has strong communication skills but limited sales experience.

Job Description: {job_description}
Candidate CV: {cv_text[:4000]}
"""
                }
            ],
            temperature=0.7,
            max_completion_tokens=512,
            top_p=1,
        )

        result = completion.choices[0].message.content.strip()
        # print(result)

        # Step 3: Extract match score
        try:
            match = re.search(r'(\d+)/10', result)
            if match:
                score = int(match.group(1))
                if score >= 7:
                    print(f"Match found ({score}/10)! Moving file...")

                    # Extract name, email, phone, and reason
                    parts = [p.strip() for p in result.split(',')]
                    name = parts[0] if len(parts) > 0 else "Unknown"
                    email = parts[1] if len(parts) > 1 else "Unknown"
                    phone = parts[2] if len(parts) > 2 else "Unknown"
                    reason = parts[4] if len(parts) > 4 else "No reason provided"

                    # Save to CSV
                    save_shortlisted_candidate(name, email, phone, reason)

                    # Move file to matched folder
                    shutil.copy(file_path, matched_folder / file_path.name)
                else:
                    print(f"Not a good match ({score}/10). Skipping.")
            else:
                print("No valid score found in result.")
        except Exception as e:
            print(f"Error parsing match score: {e}")

print("\nProcess completed! Check your 'matched_cvs' folder and 'shortlisted_candidates.csv' file for selected resumes.")
