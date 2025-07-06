"""
File: pdf_reader.py
Author: Jonathan Hu
Date Created: 6/12/25
Last Modified: 7/5/25
Description: PDF processing module that extracts text content from resume PDF files.
             Handles both file path and byte stream inputs for flexibility and integration
             with web uploads and local file processing.

Classes:
    - PDFReader: Utility class for PDF text extraction with static methods for file and byte processing

Collections:
    - N/A (This module does not interact with database collections)

Methods:
    - extract_text_from_pdf(): Extract text from PDF file path with error handling
    - extract_text_from_pdf_bytes(): Extract text from PDF byte stream for uploaded files
"""

import PyPDF2
import io

class PDFReader:
    """PDF text extraction utility"""
    
    @staticmethod
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
    
    @staticmethod
    def extract_text_from_pdf_bytes(pdf_bytes):
        """Extract text from PDF bytes (for uploaded files)"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
