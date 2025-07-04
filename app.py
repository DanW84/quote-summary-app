# updated-app-script-optimized-for-streamlit-playground

import streamlit as st
import os
import pdfplumber
import pandas as pd
from docx import Document
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import tempfile
from openai import OpenAI

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# Extract text from uploaded file
def extract_text(file, filetype):
    if filetype == "pdf":
        with pdfplumber.open(file) as pdf:
            return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    elif filetype == "docx":
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    elif filetype == "xlsx":
        df = pd.read_excel(file)
        return df.to_string(index=False)
    elif filetype == "html":
        soup = BeautifulSoup(file.read(), 'html.parser')
        return soup.get_text(separator="\n", strip=True)
    else:
        return "Unsupported file type"

# Generate summary using OpenAI or dummy data
def generate_summary(text, mode):
    if mode == "Test (Offline)":
        return (
            "📝 **Mock Summary (Offline Mode)**\n\n"
            "1. Contractor proposes general repairs.\n"
            "2. Labour: $1,000 | Materials: $800\n"
            "3. Risk Rating: Low (Likelihood: Low, Severity: Low)\n"
            "4. ✅ Final Recommendation: Approved\n\n"
            "*This is a mock summary.*"
        )
    else:
        prompt = f"""
You are a benchmarking assistant. Analyze the contractor quote below and generate a benchmarking quote summary including:

1. A plain English summary of the work proposed  
2. Labour and material cost checks  
3. Risk rating (severity and likelihood)  
4. Final recommendation (Approved / Request More Info / Declined)

Quote:
{text}
"""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

# Streamlit UI setup
st.set_page_config(page_title="Benchmarking Quote Summary", layout="centered")
st.title("📄 Benchmarking Quote Summary Generator")

mode = st.radio("Select mode:", ["Real (OpenAI)", "Test (Offline)"])
uploaded_file = st.file_uploader("Upload a quote file (HTML, PDF, Word, Excel)", type=["pdf", "docx", "xlsx", "html"])

if uploaded_file is not None:
    with st.spinner("Extracting and analyzing quote..."):
        ext = uploaded_file.name.split(".")[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_path = tmp_file.name

        extracted_text = extract_text(open(tmp_path, 'rb'), ext)
        os.remove(tmp_path)

        if len(extracted_text.strip()) == 0:
            st.error("❌ Could not extract any text from the file.")
        else:
            try:
                summary = generate_summary(extracted_text, mode)
                st.success("✅ Summary generated")
                st.text_area("Generated Summary", summary, height=400)
                st.download_button("Download Summary as TXT", summary, file_name="benchmarking_summary.txt")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
