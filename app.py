import streamlit as st
from pathlib import Path
import zipfile
import tempfile
import os
import io
import shutil
import re
from groq import Groq
from docx import Document
import PyPDF2
from dotenv import load_dotenv

# Assuming you already have Groq client
# from your_groq_client_module import client  

st.title("CV Matcher - AI Powered")

load_dotenv()

api_key = os.getenv("API_KEY")

client = Groq(api_key=api_key)

job_description = st.text_area("Enter the Job Description:")


uploaded_zip = st.file_uploader("Upload folder containing CVs (zip)", type=["zip"])



if uploaded_zip and job_description:
    st.info("Processing uploaded CVs...")

    matched_cvs = []
    allowed_formats = ['.txt', '.pdf', '.docx']

    # Convert uploaded file to BytesIO
    uploaded_bytes = io.BytesIO(uploaded_zip.read())

    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract zip
        with zipfile.ZipFile(uploaded_bytes) as z:
            z.extractall(tmpdir)

        # Walk through all files (including subfolders)
        for root, dirs, files in os.walk(tmpdir):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                if Path(file_path).suffix.lower() in allowed_formats:
                    st.write(f"Processing: {file_name}")


                
                try:
                    suffix = Path(file_path).suffix.lower()
                    cv_text = ""
                    if suffix == '.txt':
                        with open(file_path, 'r', encoding='utf-8') as f:
                            cv_text = f.read()
                    elif suffix == '.docx':
                        doc = Document(file_path)
                        cv_text = "\n".join([para.text for para in doc.paragraphs])
                    elif suffix == '.pdf':
                        with open(file_path, 'rb') as pdf:
                            reader = PyPDF2.PdfReader(pdf)
                            for page in reader.pages:
                                cv_text += page.extract_text()
                except Exception as e:
                    st.error(f"Error reading file {file_name}: {e}")
                    continue

                
                try:
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "user",
                                "content": f"""
You are an expert HR recruiter. 
Compare the Job Description and the Candidate CV, and output ONLY this single line of CSV exactly in this format:
Candidate Name, Candidate Email, Candidate Phone, Match Score (as X/10), Reason

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
                    # Extract match score
                    match = re.search(r'(\d+)/10', result)
                    if match:
                        score = int(match.group(1))
                        if score >= 7:
                            matched_cvs.append({
                                "file_name": file_name,
                                "result": result,
                                "score": score,
                                "file_path": file_path
                            })
                            st.success(f"Match found ({score}/10) for {file_name}")
                        else:
                            st.warning(f"Not a good match ({score}/10) for {file_name}")
                    else:
                        st.error(f"No valid score found for {file_name}")
                except Exception as e:
                    st.error(f"Error processing {file_name}: {e}")


        if matched_cvs:
            st.subheader("Matched CVs")
            for cv in matched_cvs:
                st.markdown(f"**{cv['file_name']}** — Score: {cv['score']}/10")
                st.text(cv['result'])
                # Download button for each matched CV
                with open(cv['file_path'], 'rb') as f:
                    st.download_button(
                        label=f"Download {cv['file_name']}",
                        data=f,
                        file_name=cv['file_name']
                    )
        else:
            st.info("No CVs matched the criteria.")
