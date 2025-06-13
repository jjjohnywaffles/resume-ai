"""
File: gui.py
Author: Jonathan Hu
Date Created: 6/12/25
Last Modified: 6/12/25
Description: Tkinter-based desktop GUI for the Resume Analyzer.
             Note: This file is replaced by the Flask web interface and is
             no longer needed for the web application version.
Status: DEPRECATED - Use Flask app.py instead
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import os
from main import ResumeAnalyzer

class ResumeAnalyzerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Resume Analyzer")
        self.root.geometry("900x750")  # Increased height for new fields
        self.root.configure(bg='#f0f0f0')
        
        # Initialize analyzer as None first
        self.analyzer = None
        self.current_result = None  # Store current analysis result for explanation feature
        
        try:
            self.analyzer = ResumeAnalyzer()
        except Exception as e:
            messagebox.showerror(
                "Configuration Error", 
                f"Failed to initialize Resume Analyzer:\n\n{str(e)}\n\nPlease check:\n1. Your .env file exists\n2. OPENAI_API_KEY is set correctly\n3. Internet connection is available"
            )
            self.root.destroy()
            return
            
        self.resume_path = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main title
        title_label = tk.Label(
            self.root, 
            text="Resume Analyzer", 
            font=("Arial", 24, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        title_label.pack(pady=20)
        
        # Create main container
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
        
        # Candidate name
        name_frame = tk.Frame(input_frame, bg='#f0f0f0')
        name_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(
            name_frame, 
            text="Candidate Name:", 
            font=("Arial", 12, "bold"), 
            bg='#f0f0f0'
        ).pack(anchor='w', pady=(0, 5))
        
        self.name_entry = tk.Entry(
            name_frame, 
            font=("Arial", 12), 
            relief='solid',
            bd=1
        )
        self.name_entry.pack(fill='x')
        
        # NEW: Job title and company in a horizontal layout
        job_info_frame = tk.Frame(input_frame, bg='#f0f0f0')
        job_info_frame.pack(fill='x', pady=(0, 15))
        
        # Job title (left side)
        job_title_frame = tk.Frame(job_info_frame, bg='#f0f0f0')
        job_title_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        tk.Label(
            job_title_frame, 
            text="Job Title:", 
            font=("Arial", 12, "bold"), 
            bg='#f0f0f0'
        ).pack(anchor='w', pady=(0, 5))
        
        self.job_title_entry = tk.Entry(
            job_title_frame, 
            font=("Arial", 12), 
            relief='solid',
            bd=1
        )
        self.job_title_entry.pack(fill='x')
        
        # Company (right side)
        company_frame = tk.Frame(job_info_frame, bg='#f0f0f0')
        company_frame.pack(side='left', fill='both', expand=True, padx=(10, 0))
        
        tk.Label(
            company_frame, 
            text="Company:", 
            font=("Arial", 12, "bold"), 
            bg='#f0f0f0'
        ).pack(anchor='w', pady=(0, 5))
        
        self.company_entry = tk.Entry(
            company_frame, 
            font=("Arial", 12), 
            relief='solid',
            bd=1
        )
        self.company_entry.pack(fill='x')
        
        # Resume upload section
        resume_frame = tk.Frame(input_frame, bg='#f0f0f0')
        resume_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(
            resume_frame, 
            text="Resume (PDF):", 
            font=("Arial", 12, "bold"), 
            bg='#f0f0f0'
        ).pack(anchor='w', pady=(0, 5))
        
        # File selection frame
        file_frame = tk.Frame(resume_frame, bg='#f0f0f0')
        file_frame.pack(fill='x')
        
        self.browse_button = tk.Button(
            file_frame,
            text="📁 Browse for PDF",
            font=("Arial", 11),
            bg='#3498db',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            command=self.browse_file,
            cursor='hand2'
        )
        self.browse_button.pack(side='left')
        
        self.file_label = tk.Label(
            file_frame, 
            text="No file selected", 
            font=("Arial", 10), 
            bg='#f0f0f0', 
            fg='#7f8c8d'
        )
        self.file_label.pack(side='left', padx=(15, 0))
        
        # Job description section
        job_frame = tk.Frame(input_frame, bg='#f0f0f0')
        job_frame.pack(fill='both', expand=True)
        
        tk.Label(
            job_frame, 
            text="Job Description:", 
            font=("Arial", 12, "bold"), 
            bg='#f0f0f0'
        ).pack(anchor='w', pady=(0, 5))
        
        # Job description text area with placeholder
        self.job_text = scrolledtext.ScrolledText(
            job_frame,
            font=("Arial", 11),
            wrap=tk.WORD,
            height=10,  # Reduced height slightly to accommodate new fields
            relief='solid',
            bd=1
        )
        self.job_text.pack(fill='both', expand=True)
        
        # Add placeholder text
        placeholder_text = "Paste the job description here...\n\nExample:\nWe are looking for a Software Engineer with 3+ years of experience.\n\nRequired Skills:\n- Python\n- JavaScript\n- SQL\n\nResponsibilities:\n- Develop web applications\n- Work with databases"
        self.job_text.insert("1.0", placeholder_text)
        self.job_text.bind('<FocusIn>', self.clear_placeholder)
        self.job_text.bind('<FocusOut>', self.add_placeholder)
        self.placeholder_active = True
        
        # Control buttons
        button_frame = tk.Frame(container, bg='#f0f0f0')
        button_frame.pack(fill='x', pady=20)
        
        self.analyze_button = tk.Button(
            button_frame,
            text="🔍 Analyze Resume",
            font=("Arial", 14, "bold"),
            bg='#27ae60',
            fg='white',
            relief='flat',
            padx=40,
            pady=12,
            command=self.start_analysis,
            cursor='hand2'
        )
        self.analyze_button.pack(side='left')
        
        self.clear_button = tk.Button(
            button_frame,
            text="🗑️ Clear All",
            font=("Arial", 12),
            bg='#e74c3c',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            command=self.clear_all,
            cursor='hand2'
        )
        self.clear_button.pack(side='left', padx=(15, 0))
        
        # NEW: Detailed explanation button
        self.explain_button = tk.Button(
            button_frame,
            text="📝 View Detailed Explanation",
            font=("Arial", 12),
            bg='#f39c12',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            command=self.show_detailed_explanation,
            cursor='hand2'
        )
        self.explain_button.pack(side='left', padx=(15, 0))
        self.explain_button.config(state='disabled')  # Initially disabled
        
        self.history_button = tk.Button(
            button_frame,
            text="📊 View History",
            font=("Arial", 12),
            bg='#9b59b6',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            command=self.show_all_analyses,
            cursor='hand2'
        )
        self.history_button.pack(side='right')
        
        # Progress bar (initially hidden)
        self.progress_frame = tk.Frame(container, bg='#f0f0f0')
        self.progress = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            length=400
        )
        self.status_label = tk.Label(
            self.progress_frame,
            text="",
            font=("Arial", 11),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        
        # Results frame (initially hidden)
        self.results_frame = tk.LabelFrame(
            container,
            text="Analysis Results",
            font=("Arial", 14, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50',
            padx=20,
            pady=15
        )
        
    def clear_placeholder(self, event):
        """Clear placeholder text when focused"""
        if self.placeholder_active:
            self.job_text.delete("1.0", tk.END)
            self.job_text.config(fg='black')
            self.placeholder_active = False
    
    def add_placeholder(self, event):
        """Add placeholder text if empty"""
        if not self.job_text.get("1.0", tk.END).strip():
            placeholder_text = "Paste the job description here...\n\nExample:\nWe are looking for a Software Engineer with 3+ years of experience.\n\nRequired Skills:\n- Python\n- JavaScript\n- SQL\n\nResponsibilities:\n- Develop web applications\n- Work with databases"
            self.job_text.insert("1.0", placeholder_text)
            self.job_text.config(fg='gray')
            self.placeholder_active = True
    
    def browse_file(self):
        """Browse for PDF file"""
        file_path = filedialog.askopenfilename(
            title="Select Resume PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if file_path:
            self.resume_path = file_path
            filename = os.path.basename(file_path)
            self.file_label.config(
                text=f"✓ {filename}", 
                fg='#27ae60'
            )
            self.browse_button.config(text="📁 Change PDF")
    
    def clear_all(self):
        """Clear all inputs and results"""
        self.name_entry.delete(0, tk.END)
        self.job_title_entry.delete(0, tk.END)  # Clear job title
        self.company_entry.delete(0, tk.END)    # Clear company
        self.job_text.delete("1.0", tk.END)
        self.add_placeholder(None)
        self.resume_path = None
        self.file_label.config(text="No file selected", fg='#7f8c8d')
        self.browse_button.config(text="📁 Browse for PDF")
        self.results_frame.pack_forget()
        self.progress_frame.pack_forget()
        
        # Clear current result and disable explanation button
        self.current_result = None
        self.explain_button.config(state='disabled')
    
    def start_analysis(self):
        """Start the analysis in a separate thread"""
        name = self.name_entry.get().strip()
        job_title = self.job_title_entry.get().strip()  # Get job title
        company = self.company_entry.get().strip()      # Get company
        
        # Get job description, handling placeholder
        if self.placeholder_active:
            job_description = ""
        else:
            job_description = self.job_text.get("1.0", tk.END).strip()
        
        # Validation
        if not name:
            messagebox.showerror("Missing Information", "Please enter the candidate's name")
            return
        
        if not job_title:
            messagebox.showerror("Missing Information", "Please enter the job title")
            return
        
        if not company:
            messagebox.showerror("Missing Information", "Please enter the company name")
            return
        
        if not self.resume_path:
            messagebox.showerror("Missing File", "Please select a resume PDF file")
            return
        
        if not job_description:
            messagebox.showerror("Missing Information", "Please enter a job description")
            return
        
        # Hide results and show progress
        self.results_frame.pack_forget()
        self.progress_frame.pack(fill='x', pady=20)
        self.progress.pack()
        self.status_label.pack(pady=(10, 0))
        
        # Disable controls
        self.analyze_button.config(state='disabled', text='🔄 Analyzing...')
        self.browse_button.config(state='disabled')
        self.clear_button.config(state='disabled')
        self.explain_button.config(state='disabled')
        
        self.progress.start()
        self.status_label.config(text="Processing resume and job description...")
        
        # Start analysis in separate thread
        thread = threading.Thread(
            target=self.run_analysis,
            args=(name, job_title, company, self.resume_path, job_description)
        )
        thread.daemon = True
        thread.start()
    
    def run_analysis(self, name, job_title, company, resume_path, job_description):
        """Run the analysis"""
        try:
            # Extract text from resume PDF
            resume_text = self.analyzer.pdf_reader.extract_text_from_pdf(resume_path)
            
            if resume_text.startswith("Error"):
                self.root.after(0, self.show_error, resume_text)
                return
            
            # Extract structured data from resume and job
            resume_data = self.analyzer.ai_analyzer.extract_resume_data(resume_text)
            job_requirements = self.analyzer.ai_analyzer.extract_job_requirements(job_description)
            
            # Get detailed explanation AND score in one call (no duplicate API calls)
            explanation_result = self.analyzer.ai_analyzer.explain_match_score(resume_data, job_requirements)
            match_score = explanation_result["score"]
            cached_explanation = explanation_result["explanation"]
            
            # Save to database with new fields
            self.analyzer.db_manager.save_analysis(
                name, resume_data, job_requirements, match_score, 
                cached_explanation, job_title, company
            )
            
            # Build result with cached explanation
            result = {
                "name": name,
                "job_title": job_title,
                "company": company,
                "resume_data": resume_data,
                "job_requirements": job_requirements,
                "match_score": match_score,
                "cached_explanation": cached_explanation  # Store explanation for later use
            }
            
            self.root.after(0, self.show_results, result)
        except Exception as e:
            self.root.after(0, self.show_error, str(e))
    
    def show_results(self, result):
        """Display analysis results"""
        # Stop progress and re-enable controls
        self.progress.stop()
        self.progress_frame.pack_forget()
        self.analyze_button.config(state='normal', text='🔍 Analyze Resume')
        self.browse_button.config(state='normal')
        self.clear_button.config(state='normal')
        
        if 'error' in result:
            messagebox.showerror("Analysis Error", result['error'])
            return
        
        # Store current result for explanation feature
        self.current_result = result
        
        # Enable explanation button
        self.explain_button.config(state='normal')
        
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # Show results frame
        self.results_frame.pack(fill='both', expand=True, pady=(20, 0))
        
        # Score display
        score_frame = tk.Frame(self.results_frame, bg='#f0f0f0')
        score_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(
            score_frame,
            text="Compatibility Score:",
            font=("Arial", 14, "bold"),
            bg='#f0f0f0'
        ).pack(side='left')
        
        score = result['match_score']
        if score >= 80:
            score_color = '#27ae60'
            score_text = "Excellent Match"
        elif score >= 60:
            score_color = '#f39c12'
            score_text = "Good Match"
        else:
            score_color = '#e74c3c'
            score_text = "Needs Improvement"
        
        score_label = tk.Label(
            score_frame,
            text=f"{score}/100",
            font=("Arial", 24, "bold"),
            bg='#f0f0f0',
            fg=score_color
        )
        score_label.pack(side='left', padx=(20, 10))
        
        tk.Label(
            score_frame,
            text=f"({score_text})",
            font=("Arial", 12),
            bg='#f0f0f0',
            fg=score_color
        ).pack(side='left')
        
        # Create notebook for detailed results
        notebook = ttk.Notebook(self.results_frame)
        notebook.pack(fill='both', expand=True)
        
        # Resume analysis tab
        resume_frame = tk.Frame(notebook, bg='white')
        notebook.add(resume_frame, text='📄 Resume Analysis')
        
        resume_text = scrolledtext.ScrolledText(
            resume_frame, 
            font=("Arial", 11), 
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        resume_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Format resume content with job info
        resume_content = f"CANDIDATE: {result['name']}\n"
        resume_content += f"POSITION: {result['job_title']} at {result['company']}\n\n"
        resume_content += "🔧 EXTRACTED SKILLS:\n"
        for skill in result['resume_data'].get('skills', []):
            resume_content += f"  • {skill}\n"
        
        resume_content += "\n💼 WORK EXPERIENCE:\n"
        for exp in result['resume_data'].get('experience', []):
            role = exp.get('role', 'Unknown Role')
            company = exp.get('company', 'Unknown Company')
            duration = exp.get('duration', 'Unknown Duration')
            resume_content += f"  • {role} at {company} ({duration})\n"
        
        resume_content += "\n🎓 EDUCATION:\n"
        for edu in result['resume_data'].get('education', []):
            degree = edu.get('degree', 'Unknown Degree')
            institution = edu.get('institution', 'Unknown Institution')
            year = edu.get('year', 'Unknown Year')
            resume_content += f"  • {degree} from {institution} ({year})\n"
        
        resume_text.insert("1.0", resume_content)
        resume_text.config(state='disabled')
        
        # Job requirements tab
        job_frame = tk.Frame(notebook, bg='white')
        notebook.add(job_frame, text='📋 Job Requirements')
        
        job_text = scrolledtext.ScrolledText(
            job_frame, 
            font=("Arial", 11), 
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        job_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Format job content
        job_content = "✅ REQUIRED SKILLS:\n"
        for skill in result['job_requirements'].get('required_skills', []):
            job_content += f"  • {skill}\n"
        
        job_content += "\n⭐ PREFERRED SKILLS:\n"
        for skill in result['job_requirements'].get('preferred_skills', []):
            job_content += f"  • {skill}\n"
        
        job_content += f"\n⏱️ EXPERIENCE REQUIRED:\n  • {result['job_requirements'].get('experience_required', 'Not specified')}\n"
        job_content += f"\n🎓 EDUCATION REQUIRED:\n  • {result['job_requirements'].get('education_required', 'Not specified')}\n"
        
        job_content += "\n📝 KEY RESPONSIBILITIES:\n"
        for resp in result['job_requirements'].get('responsibilities', []):
            job_content += f"  • {resp}\n"
        
        job_text.insert("1.0", job_content)
        job_text.config(state='disabled')
        
        # Success message
        messagebox.showinfo(
            "Analysis Complete", 
            f"Analysis completed successfully!\nCandidate: {result['name']}\nPosition: {result['job_title']} at {result['company']}\nMatch Score: {score}/100\n\nResults saved to database.\n\nClick 'View Detailed Explanation' to see the scoring breakdown."
        )
    
    def show_error(self, error_message):
        """Show error message"""
        self.progress.stop()
        self.progress_frame.pack_forget()
        self.analyze_button.config(state='normal', text='🔍 Analyze Resume')
        self.browse_button.config(state='normal')
        self.clear_button.config(state='normal')
        messagebox.showerror("Analysis Error", f"Error during analysis:\n\n{error_message}")
    
    def show_detailed_explanation(self):
        """Show detailed explanation for the current analysis"""
        if not self.current_result:
            messagebox.showwarning("No Analysis", "Please run an analysis first.")
            return
        
        # Check if we have a cached explanation
        if "cached_explanation" in self.current_result:
            # Use the cached explanation (no API call needed)
            self.display_explanation(self.current_result["cached_explanation"])
        else:
            # Fallback: generate explanation if not cached (shouldn't happen with new flow)
            try:
                # Disable button and show loading state
                self.explain_button.config(state='disabled', text='🔄 Generating...')
                
                def get_explanation():
                    try:
                        result = self.analyzer.ai_analyzer.explain_match_score(
                            self.current_result['resume_data'],
                            self.current_result['job_requirements']
                        )
                        self.root.after(0, self.display_explanation, result["explanation"])
                    except Exception as e:
                        self.root.after(0, self.show_explanation_error, str(e))
                
                # Run in separate thread
                thread = threading.Thread(target=get_explanation)
                thread.daemon = True
                thread.start()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate explanation:\n{str(e)}")
                self.explain_button.config(state='normal', text='📝 Get Detailed Explanation')

    def display_explanation(self, explanation):
        """Display the detailed explanation in a new window"""
        # Re-enable button (no loading state needed for cached explanations)
        self.explain_button.config(state='normal', text='📝 View Detailed Explanation')
        
        # Create new window
        window = tk.Toplevel(self.root)
        window.title("Detailed Score Explanation")
        window.geometry("900x700")
        window.configure(bg='#f0f0f0')
        
        # Make window modal
        window.transient(self.root)
        window.grab_set()
        
        # Title
        title_frame = tk.Frame(window, bg='#f0f0f0')
        title_frame.pack(fill='x', pady=20)
        
        tk.Label(
            title_frame,
            text="📊 Compatibility Score Breakdown",
            font=("Arial", 18, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        ).pack()
        
        # Updated to show job title and company
        tk.Label(
            title_frame,
            text=f"Analysis for: {self.current_result['name']} | {self.current_result['job_title']} at {self.current_result['company']}",
            font=("Arial", 12),
            bg='#f0f0f0',
            fg='#7f8c8d'
        ).pack()
        
        # Explanation text
        text_frame = tk.Frame(window, bg='#f0f0f0')
        text_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        explanation_text = scrolledtext.ScrolledText(
            text_frame,
            font=("Arial", 11),
            wrap=tk.WORD,
            padx=15,
            pady=15,
            relief='solid',
            bd=1
        )
        explanation_text.pack(fill='both', expand=True)
        
        explanation_text.insert("1.0", explanation)
        explanation_text.config(state='disabled')
        
        # Button frame
        button_frame = tk.Frame(window, bg='#f0f0f0')
        button_frame.pack(fill='x', pady=(0, 20))
        
        # Close button
        tk.Button(
            button_frame,
            text="Close",
            font=("Arial", 12),
            bg='#95a5a6',
            fg='white',
            relief='flat',
            padx=30,
            pady=8,
            command=window.destroy,
            cursor='hand2'
        ).pack()

    def show_explanation_error(self, error_message):
        """Show error when explanation generation fails"""
        self.explain_button.config(state='normal', text='📝 View Detailed Explanation')
        messagebox.showerror("Explanation Error", f"Failed to generate detailed explanation:\n\n{error_message}")
    
    def show_all_analyses(self):
        """Show all previous analyses"""
        try:
            analyses = self.analyzer.get_all_analyses()
            
            if not analyses:
                messagebox.showinfo("No Data", "No previous analyses found in the database.")
                return
            
            # Create new window
            window = tk.Toplevel(self.root)
            window.title("Analysis History")
            window.geometry("1000x500")  # Increased width for new columns
            window.configure(bg='#f0f0f0')
            
            # Title
            tk.Label(
                window,
                text="Previous Resume Analyses",
                font=("Arial", 16, "bold"),
                bg='#f0f0f0',
                fg='#2c3e50'
            ).pack(pady=20)
            
            # Create frame for treeview
            tree_frame = tk.Frame(window, bg='#f0f0f0')
            tree_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
            
            # Create treeview with new columns
            columns = ('Name', 'Job Title', 'Company', 'Score', 'Date')
            tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
            
            tree.heading('Name', text='Candidate Name')
            tree.heading('Job Title', text='Job Title')
            tree.heading('Company', text='Company')
            tree.heading('Score', text='Match Score')
            tree.heading('Date', text='Analysis Date')
            
            tree.column('Name', width=200)
            tree.column('Job Title', width=200)
            tree.column('Company', width=150)
            tree.column('Score', width=100)
            tree.column('Date', width=150)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Insert data
            for analysis in sorted(analyses, key=lambda x: x.get('timestamp', ''), reverse=True):
                date_str = analysis['timestamp'].strftime('%Y-%m-%d %H:%M') if 'timestamp' in analysis else 'Unknown'
                score_display = f"{analysis['match_score']}/100"
                
                # Handle missing job_title and company fields (for backward compatibility)
                job_title = analysis.get('job_title', 'N/A')
                company = analysis.get('company', 'N/A')
                
                tree.insert('', 'end', values=(
                    analysis['name'],
                    job_title,
                    company,
                    score_display,
                    date_str
                ))
            
            tree.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
            
            # Add close button
            tk.Button(
                window,
                text="Close",
                font=("Arial", 12),
                bg='#95a5a6',
                fg='white',
                relief='flat',
                padx=30,
                pady=8,
                command=window.destroy
            ).pack(pady=(0, 20))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve analyses:\n{str(e)}")
    
    def run(self):
        """Start the GUI"""
        try:
            self.root.mainloop()
        finally:
            # Only try to close analyzer if it was successfully created
            if hasattr(self, 'analyzer') and self.analyzer is not None:
                self.analyzer.close()

def main():
    app = ResumeAnalyzerGUI()
    app.run()

if __name__ == "__main__":
    main()