import os
import tempfile
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables and initialize OpenAI client
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)


def extract_pdf_text(path):
    """Extract all text from a PDF file."""
    reader = PdfReader(path)
    texts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            texts.append(text)
    return "\n".join(texts)


def tailor_resume(resume_text, job_title, job_desc):
    """
    Call OpenAI to tailor only the key experience sections of a resume.
    Focus on sections like Work Experience, Internships, Leadership Experiences,
    Projects & Certifications, and similar.
    Output each entry in the format:

    <section title: Section Name>
    Old content:
    <original entry>

    New content:
    <revised entry>

    Only process these experience-related sections; skip all others.
    """
    prompt = (
        "You are an expert resume coach. "
        "Given a resume, job title, and description, extract and revise only the main experience-related sections. "
        "These include Work Experience, Internships, Leadership Experiences, Projects & Certifications, and similar. "
        "For each bullet or entry, output exactly in this format:\n"
        "<section title: Section Name>\n"
        "Old content:\n"
        "<original entry text>\n\n"
        "New content:\n"
        "<revised entry text>\n\n"
        "Do not include any other sections or extraneous details.\n\n"
        "=== RESUME ===\n"
        f"{resume_text}\n\n"
        "=== JOB TITLE ===\n"
        f"{job_title}\n\n"
        "=== JOB DESCRIPTION ===\n"
        f"{job_desc}\n\n"
        "Begin now."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()


@app.route("/", methods=["GET"])
def index():
    return render_template("upload.html")


@app.route("/upload", methods=["POST"])
def upload():
    # Get form fields
    job_title = request.form["job_title"]
    job_desc = request.form["job_desc"]

    # Save uploaded PDF
    f = request.files["resume"]
    filename = secure_filename(f.filename)
    tmp_path = os.path.join(tempfile.gettempdir(), filename)
    f.save(tmp_path)

    # Extract text
    resume_text = extract_pdf_text(tmp_path)

    # Get tailored experience suggestions
    suggestions = tailor_resume(resume_text, job_title, job_desc)

    # Render results
    return render_template("result.html", suggestions=suggestions)


if __name__ == "__main__":
    app.run(debug=True)
