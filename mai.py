import re
import os
import shutil
import PyPDF2
from groq import Groq
from pathlib import Path
from docx import Document
from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("API_KEY")

client = Groq(api_key=api_key)

# User input for Job Description
job_description = input("Enter the Job Description: ")

# Input folder (where all CVs are)
input_folder = Path("artifact")

# Output folder (to store matched CVs)
matched_folder = Path("matched_cvs")
matched_folder.mkdir(exist_ok=True)

allowed_formats = ['.txt', '.pdf', '.docx']

# Loop through all text/PDF files
for file_path in input_folder.iterdir():
    if file_path.is_file() and file_path.suffix.lower() in allowed_formats:
        print(f"\nProcessing: {file_path.name}")

        # 🔹 Step 1: Read CV content
        try:
            if file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    cv_text = f.read()
            elif file_path.suffix.lower() == '.docx':
                doc = Document(file_path)
                cv_text = "\n".join([para.text for para in doc.paragraphs])
            elif file_path.suffix.lower() == '.pdf':
                # Optional: use PyPDF2 for PDFs
                
                cv_text = ""
                with open(file_path, 'rb') as pdf:
                    reader = PyPDF2.PdfReader(pdf)
                    for page in reader.pages:
                        cv_text += page.extract_text()
        except Exception as e:
            print(f"Error reading file {file_path.name}: {e}")
            continue

        # 🔹 Step 2: Send CV + JD to Groq for evaluation
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

        # 🔹 Step 3: Extract match score number
        try:
            match = re.search(r'(\d+)\s*(?:/|out of)\s*10', result)
            match = re.search(r'(\d+)/10', result)
            if match:
                score = int(match.group(1))
                # If score >= 7, treat as matched
                if score >= 7:
                    print(f"Match found ({score}/10)! Moving file...")
                    shutil.copy(file_path, matched_folder / file_path.name)
                else:
                    print(f"Not a good match ({score}/10). Skipping.")
            else:
                print("No valid score found.")
        except Exception as e:
            print(f"Error parsing match score: {e}")

print("\nProcess completed! Check your 'matched_cvs' folder for selected resumes.")
