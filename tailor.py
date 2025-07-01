import anthropic
import gradio as gr
from config import get_config
from openai import OpenAI
from dotenv import load_dotenv
from fpdf import FPDF
import os
import traceback


"""
def get_AI_client():
    config = get_config()
    print("DEBUG API KEY:", config.OPENAI_API_KEY)
    return OpenAI(api_key=config.OPENAI_API_KEY)
"""

def get_AI_client():
    config = get_config()
    print("DEBUG API KEY:", config.ANTHROPIC_API_KEY)
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

def tailor_resume(position_name, resume_content, polish_prompt=""):

    client = get_AI_client()

    if polish_prompt and polish_prompt.strip():
        prompt_use = f"Given the resume content: '{resume_content}', tailor it based on the following instructions: {polish_prompt} for the {position_name} position."
    else:
        prompt_use = f"Suggest improvements for the following resume content: '{resume_content}' to better align with the requirements and expectations of a {position_name} position. Return the tailored version, highlighting necessary adjustments for clarity, relevance, and impact in relation to the targeted role."

    try:
        
        anth_response = client.messages.create(
            model="claude-3-5-haiku-20241022", 
            messages=[
                {"role": "user", "content": prompt_use}
            ],
            temperature = 0.1,
            max_tokens=1000
        )

        response_text = anth_response.content[0].text
        return response_text

    except Exception as e:
        traceback.print_exc()  # Print full stack trace
        return f"An error occurred while processing your request: {str(e)}"



def resume_handler(position_name, resume_text, pdf_file, polish_prompt=""):
    if pdf_file is not None:
        resume_content = extract_text_from_pdf(pdf_file)
    elif resume_text.strip():
        resume_content = resume_text
    else:
        return "Please enter resume text or upload a PDF file."

    polished_text = tailor_resume(position_name, resume_content, polish_prompt)
    
    # Save to PDF
    output_pdf_path = "polished_resume.pdf"
    save_text_to_pdf(polished_text, output_pdf_path)

    return polished_text, output_pdf_path

    
def extract_text_from_pdf(pdf_file_path):
    """Extract text from PDF file"""
    try:
        with open(pdf_file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
                
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
                
            return text.strip()
    except Exception as e:
        return f"Error reading PDF: {str(e)}"
    
def save_text_to_pdf(text: str, output_path: str = "output.pdf"):
    """
    Saves the given text to a PDF.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(output_path)

    return output_path


resume_polish_application = gr.Interface(
    fn = resume_handler,
   
    inputs=[
        gr.Textbox(label="Position Name", placeholder="Enter the name of the position..."),
        gr.Textbox(label="Resume Content", placeholder="Paste your resume content here...", lines=20),
        gr.File(label="Or Upload Resume PDF", file_types=[".pdf"]),
        gr.Textbox(label="Polish Instruction (Optional)", placeholder="Enter specific instructions or areas for improvement (optional)...", lines=2),
    ],

    outputs=[
        gr.Textbox(label="Polished Content"), 
        gr.File(label="Download Polished Resume PDF")
    ],
    
    title="Resume Polish Application",
    description="This application helps you polish your resume. Enter the position your want to apply, your resume content, and specific instructions or areas for improvement (optional), then get a polished version of your content."
)
# Launch the application
resume_polish_application.launch()





