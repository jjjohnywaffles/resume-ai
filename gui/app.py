"""
File: gui.py
Author: Jonathan Hu
Date Created: 6/12/25
Last Modified: 6/15/25
Description: Tkinter-based desktop GUI for the Resume Analyzer.
             Note: This file is replaced by the Flask web interface and is
             no longer needed for the web application version.
Status: DEPRECATED - Use Flask app.py instead
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import os

# Import from core modules
from core.analyzer import ResumeAnalyzer
from core.database import DatabaseManager
from core.pdf_reader import PDFReader

class ResumeAnalyzerGUI:
    """Desktop GUI for resume analysis"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Resume Analyzer")
        self.root.geometry("900x750")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize components
        self.current_result = None
        
        try:
            self.ai_analyzer = ResumeAnalyzer()
            self.db_manager = DatabaseManager()
            self.pdf_reader = PDFReader()
        except Exception as e:
            messagebox.showerror(
                "Configuration Error", 
                f"Failed to initialize Resume Analyzer:\n\n{str(e)}"
            )
            self.root.destroy()
            return
            
        self.resume_path = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Title
        title_label = tk.Label(
            self.root, 
            text="Resume Analyzer", 
            font=("Arial", 24, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        title_label.pack(pady=20)
        
        # Main container
        container = tk.Frame(self.root, bg='#f0f0f0')
        container.pack(expand=True, fill='both', padx=30, pady=20)
        
        # Input section
        input_frame = tk.LabelFrame(
            container, 
            text="Resume Analysis Input", 
            font=("Arial", 14, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50',
            padx=20,
            pady=15
        )
        input_frame.pack(fill='x', pady=(0, 20))
        
        # Name input
        name_frame = tk.Frame(input_frame, bg='#f0f0f0')
        name_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(name_frame, text="Candidate Name:", font=("Arial", 12, "bold"), bg='#f0f0f0').pack(anchor='w', pady=(0, 5))
        self.name_entry = tk.Entry(name_frame, font=("Arial", 12), relief='solid', bd=1)
        self.name_entry.pack(fill='x')
        
        # Job info
        job_info_frame = tk.Frame(input_frame, bg='#f0f0f0')
        job_info_frame.pack(fill='x', pady=(0, 15))
        
        # Job title
        job_title_frame = tk.Frame(job_info_frame, bg='#f0f0f0')
        job_title_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        tk.Label(job_title_frame, text="Job Title:", font=("Arial", 12, "bold"), bg='#f0f0f0').pack(anchor='w', pady=(0, 5))
        self.job_title_entry = tk.Entry(job_title_frame, font=("Arial", 12), relief='solid', bd=1)
        self.job_title_entry.pack(fill='x')
        
        # Company
        company_frame = tk.Frame(job_info_frame, bg='#f0f0f0')
        company_frame.pack(side='left', fill='both', expand=True, padx=(10, 0))
        
        tk.Label(company_frame, text="Company:", font=("Arial", 12, "bold"), bg='#f0f0f0').pack(anchor='w', pady=(0, 5))
        self.company_entry = tk.Entry(company_frame, font=("Arial", 12), relief='solid', bd=1)
        self.company_entry.pack(fill='x')
        
        # File selection
        resume_frame = tk.Frame(input_frame, bg='#f0f0f0')
        resume_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(resume_frame, text="Resume (PDF):", font=("Arial", 12, "bold"), bg='#f0f0f0').pack(anchor='w', pady=(0, 5))
        
        file_frame = tk.Frame(resume_frame, bg='#f0f0f0')
        file_frame.pack(fill='x')
        
        self.browse_button = tk.Button(
            file_frame, text="Browse for PDF", font=("Arial", 11),
            bg='#3498db', fg='white', relief='flat', padx=20, pady=8,
            command=self.browse_file, cursor='hand2'
        )
        self.browse_button.pack(side='left')
        
        self.file_label = tk.Label(
            file_frame, text="No file selected", font=("Arial", 10), 
            bg='#f0f0f0', fg='#7f8c8d'
        )
        self.file_label.pack(side='left', padx=(15, 0))
        
        # Job description
        job_frame = tk.Frame(input_frame, bg='#f0f0f0')
        job_frame.pack(fill='both', expand=True)
        
        tk.Label(job_frame, text="Job Description:", font=("Arial", 12, "bold"), bg='#f0f0f0').pack(anchor='w', pady=(0, 5))
        
        self.job_text = scrolledtext.ScrolledText(
            job_frame, font=("Arial", 11), wrap=tk.WORD, height=10, relief='solid', bd=1
        )
        self.job_text.pack(fill='both', expand=True)
        
        # Buttons
        button_frame = tk.Frame(container, bg='#f0f0f0')
        button_frame.pack(fill='x', pady=20)
        
        self.analyze_button = tk.Button(
            button_frame, text="Analyze Resume", font=("Arial", 14, "bold"),
            bg='#27ae60', fg='white', relief='flat', padx=40, pady=12,
            command=self.start_analysis, cursor='hand2'
        )
        self.analyze_button.pack(side='left')
        
        tk.Button(
            button_frame, text="Clear All", font=("Arial", 12),
            bg='#e74c3c', fg='white', relief='flat', padx=20, pady=8,
            command=self.clear_all, cursor='hand2'
        ).pack(side='left', padx=(15, 0))
        
        tk.Button(
            button_frame, text="View History", font=("Arial", 12),
            bg='#9b59b6', fg='white', relief='flat', padx=20, pady=8,
            command=self.show_history, cursor='hand2'
        ).pack(side='right')
        
        # Results area
        self.results_text = scrolledtext.ScrolledText(container, height=15)
        self.results_text.pack(fill='both', expand=True, pady=(20, 0))
    
    def browse_file(self):
        """Browse for PDF file"""
        file_path = filedialog.askopenfilename(
            title="Select Resume PDF",
            filetypes=[("PDF files", "*.pdf")]
        )
        if file_path:
            self.resume_path = file_path
            filename = os.path.basename(file_path)
            self.file_label.config(text=f"Selected: {filename}", fg='#27ae60')
    
    def clear_all(self):
        """Clear all inputs"""
        self.name_entry.delete(0, tk.END)
        self.job_title_entry.delete(0, tk.END)
        self.company_entry.delete(0, tk.END)
        self.job_text.delete("1.0", tk.END)
        self.results_text.delete("1.0", tk.END)
        self.resume_path = None
        self.file_label.config(text="No file selected", fg='#7f8c8d')
    
    def start_analysis(self):
        """Start analysis in thread"""
        # Validation
        name = self.name_entry.get().strip()
        job_title = self.job_title_entry.get().strip()
        company = self.company_entry.get().strip()
        job_desc = self.job_text.get("1.0", tk.END).strip()
        
        if not all([name, job_title, company, job_desc, self.resume_path]):
            messagebox.showerror("Error", "Please fill all fields and select a PDF")
            return
        
        self.analyze_button.config(state='disabled', text='Analyzing...')
        
        thread = threading.Thread(
            target=self.run_analysis,
            args=(name, job_title, company, job_desc)
        )
        thread.daemon = True
        thread.start()
    
    def run_analysis(self, name, job_title, company, job_desc):
        """Run analysis in background"""
        try:
            # Extract PDF text
            resume_text = self.pdf_reader.extract_text_from_pdf(self.resume_path)
            
            if resume_text.startswith("Error"):
                self.root.after(0, self._show_error, resume_text)
                return
            
            # Analyze
            resume_data = self.ai_analyzer.extract_resume_data(resume_text)
            job_requirements = self.ai_analyzer.extract_job_requirements(job_desc)
            explanation_result = self.ai_analyzer.explain_match_score(resume_data, job_requirements)
            
            match_score = explanation_result["score"]
            
            # Save to database
            self.db_manager.save_analysis(
                name, resume_data, job_requirements, match_score, 
                explanation_result["explanation"], job_title, company
            )
            
            # Show results
            self.root.after(0, self._show_results, {
                'name': name, 'job_title': job_title, 'company': company,
                'match_score': match_score, 'resume_data': resume_data,
                'job_requirements': job_requirements
            })
            
        except Exception as e:
            self.root.after(0, self._show_error, str(e))
    
    def _show_results(self, result):
        """Display results"""
        self.analyze_button.config(state='normal', text='Analyze Resume')
        
        score = result['match_score']
        results_text = f"""ANALYSIS COMPLETE

Candidate: {result['name']}
Position: {result['job_title']} at {result['company']}
Match Score: {score}/100

SKILLS FOUND:
{chr(10).join(f"• {skill}" for skill in result['resume_data'].get('skills', []))}

EXPERIENCE:
{chr(10).join(f"• {exp.get('role', 'N/A')} at {exp.get('company', 'N/A')}" 
              for exp in result['resume_data'].get('experience', []))}

REQUIRED SKILLS:
{chr(10).join(f"• {skill}" for skill in result['job_requirements'].get('required_skills', []))}
"""
        
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert("1.0", results_text)
        
        messagebox.showinfo("Complete", f"Analysis complete! Score: {score}/100")
    
    def _show_error(self, error):
        """Show error"""
        self.analyze_button.config(state='normal', text='Analyze Resume')
        messagebox.showerror("Error", f"Analysis failed: {error}")
    
    def show_history(self):
        """Show analysis history"""
        try:
            analyses = self.db_manager.get_all_analyses()
            if not analyses:
                messagebox.showinfo("History", "No previous analyses found.")
                return
            
            # Create history window
            history_window = tk.Toplevel(self.root)
            history_window.title("Analysis History")
            history_window.geometry("600x400")
            
            history_text = scrolledtext.ScrolledText(history_window)
            history_text.pack(fill='both', expand=True, padx=10, pady=10)
            
            history_content = "ANALYSIS HISTORY\n" + "="*50 + "\n\n"
            for analysis in sorted(analyses, key=lambda x: x.get('timestamp', ''), reverse=True):
                date_str = analysis.get('timestamp', 'Unknown').strftime('%Y-%m-%d %H:%M') if hasattr(analysis.get('timestamp', ''), 'strftime') else 'Unknown'
                history_content += f"""Name: {analysis.get('name', 'N/A')}
Job: {analysis.get('job_title', 'N/A')} at {analysis.get('company', 'N/A')}
Score: {analysis.get('match_score', 0)}/100
Date: {date_str}

{'-'*40}

"""
            
            history_text.insert("1.0", history_content)
            history_text.config(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load history: {e}")
    
    def run(self):
        """Start the GUI"""
        try:
            self.root.mainloop()
        finally:
            if hasattr(self, 'db_manager'):
                self.db_manager.close_connection()

def main():
    """Main function for GUI"""
    app = ResumeAnalyzerGUI()
    app.run()

if __name__ == "__main__":
    main()
