import os
import sqlite3
import pandas as pd
import fitz
import spacy
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create required directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database initialization
def init_db():
    conn = sqlite3.connect('recruitment.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            title TEXT PRIMARY KEY,
            summary TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            name TEXT,
            email TEXT,
            score REAL,
            job_title TEXT,
            shortlisted INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize spaCy
nlp = spacy.load('en_core_web_lg')

# Agent 1: JD Summarizer
def summarize_job_description(title, description):
    doc = nlp(description)
    skills = [token.text for token in doc if token.pos_ == 'NOUN']
    experience = [token.text for token in doc if token.like_num]
    qualifications = [token.text for token in doc if 'Bachelor' in token.text or 'Master' in token.text]
    return {
        'skills': skills,
        'experience': experience,
        'qualifications': qualifications
    }

# Agent 2: Recruiting Agent
def parse_cv(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ''
        for page in doc:
            try:
                # Extract text with encoding error handling
                page_text = page.get_text().encode('utf-8', errors='ignore').decode('utf-8')
                text += ' ' + page_text
            except Exception as e:
                print(f"Error extracting text from page: {str(e)}")
                continue
        
        # Clean and normalize text
        text = ' '.join(text.split())  # Remove extra whitespace
        text = text.lower()  # Convert to lowercase for better matching
        
        # Basic information extraction
        lines = text.split('\n')
        # Get first two lines for name, remove extra whitespace and join with space
        name_lines = [line.strip() for line in lines[:2] if line.strip()]
        name = ' '.join(name_lines) if name_lines else 'Unknown'
        # Limit name to first 50 characters
        name = name[:50]
        email = next((word for word in text.split() if '@' in word), 'unknown@email.com')
        
        return {
            'name': name,
            'email': email,
            'text': text
        }
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return {
            'name': 'Error',
            'email': 'error@parsing.com',
            'text': '',
            'has_job_title': lambda title: False
        }

# Agent 3: Shortlisting Agent
def calculate_match_score(cv_info, job_summary, job_title):
    # Get CV text from cv_info and preprocess
    cv_text = cv_info['text'].lower()
    cv_text = ' '.join(cv_text.split())  # Normalize whitespace
    
    # Normalize job title
    job_title_lower = job_title.lower()
    job_title_words = [word.strip() for word in job_title_lower.split() if word.strip()]
    
    # Expanded variations and abbreviations with more comprehensive mappings
    variations = {
        'software engineer': ['swe', 'software developer', 'software development engineer', 'software engineering', 'programmer', 'coder', 'application developer', 'software dev'],
        'frontend': ['front-end', 'front end', 'frontend developer', 'ui developer', 'web developer', 'client-side developer'],
        'backend': ['back-end', 'back end', 'backend developer', 'server-side developer', 'api developer'],
        'fullstack': ['full-stack', 'full stack', 'fullstack developer', 'full stack developer', 'end-to-end developer'],
        'devops': ['dev ops', 'dev-ops', 'devops engineer', 'site reliability engineer', 'sre', 'platform engineer', 'infrastructure engineer'],
        'machine learning': ['ml engineer', 'ml developer', 'ai engineer', 'machine learning engineer', 'deep learning engineer', 'ai/ml engineer'],
        'data scientist': ['data science engineer', 'data analytics', 'data analyst', 'analytics engineer', 'quantitative analyst', 'data science professional'],
        'mobile developer': ['android developer', 'ios developer', 'mobile app developer', 'react native developer', 'flutter developer'],
        'qa engineer': ['quality assurance', 'test engineer', 'sdet', 'quality engineer', 'automation engineer', 'test automation']
    }
    
    # Initialize score components
    exact_match_score = 0
    variation_match_score = 0
    partial_match_score = 0
    context_match_score = 0
    
    # Check for exact match first (with flexible word boundaries)
    cv_words = cv_text.split()
    for i in range(len(cv_words)):
        window = ' '.join(cv_words[i:i+len(job_title_words)])
        if job_title_lower in window:
            exact_match_score = 100
            break
    
    # Check for variations with weighted scoring
    for base_title, title_variations in variations.items():
        if any(word in base_title for word in job_title_words):
            for variation in title_variations:
                if variation in cv_text:
                    variation_match_score = max(variation_match_score, 90)
                    # Additional context matching
                    context_words = ['experience', 'worked as', 'role', 'position', 'title', 'job']
                    for context in context_words:
                        if context in cv_text[max(0, cv_text.find(variation)-30):cv_text.find(variation)+len(variation)+30]:
                            context_match_score = 5
                            break
    
    # Enhanced partial matching with position weighting
    if exact_match_score == 0 and variation_match_score == 0:
        matched_words = 0
        total_weight = len(job_title_words)
        for i, word in enumerate(job_title_words):
            if word in cv_text:
                # Words at the beginning of the title get higher weight
                position_weight = 1.0 if i == 0 else 0.8 if i == 1 else 0.6
                matched_words += position_weight
        
        if matched_words > 0:
            partial_match_score = (matched_words / total_weight) * 70
    
    # Calculate final score with weights
    score = max(
        exact_match_score,
        variation_match_score + context_match_score,
        partial_match_score
    )
    
    # Determine if the candidate is qualified based on the score
    has_job_title = score >= 50
    
    return {
        'score': round(score, 2),
        'has_job_title': has_job_title,
        'message': f'Match score: {round(score, 2)}%' if score > 0 else 'No relevant job title found in CV'
    }
    
    return {
        'score': score,
        'has_job_title': has_job_title,
        'message': f'Match score: {score}%' if score > 0 else 'No relevant job title found in CV'
    }

# Agent 4: Interview Scheduler
def generate_interview_email(name, job_title):
    return f"""Dear {name},

Thank you for applying for the {job_title} position. We are pleased to invite you for an interview.

Available slots:
1. April 15, 2025, 10:00 AM (Zoom)
2. April 16, 2025, 2:00 PM (In-person)

Please reply to recruitment@company.com with your preferred slot.

Best regards,
HR Team"""

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/history')
def history():
    # Fetch all candidates from the database
    conn = sqlite3.connect('recruitment.db')
    c = conn.cursor()
    c.execute('SELECT name, job_title, score, shortlisted, created_at FROM candidates ORDER BY created_at DESC')
    candidates_data = c.fetchall()
    conn.close()
    
    # Convert the data to a list of dictionaries for easier template rendering
    candidates = [{
        'name': row[0],
        'job_title': row[1],
        'score': row[2],
        'shortlisted': row[3],
        'created_at': datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S')
    } for row in candidates_data]
    
    return render_template('history.html', candidates=candidates)

@app.route('/', methods=['GET'])
def index():
    # Load job titles from CSV
    try:
        # Try different encodings to handle special characters
        try:
            df = pd.read_csv('job_descriptions.csv', skipinitialspace=True, encoding='utf-8-sig')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv('job_descriptions.csv', skipinitialspace=True, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv('job_descriptions.csv', skipinitialspace=True, encoding='latin-1')
        job_titles = df['Job Title'].dropna().tolist()
        if not job_titles:
            flash('No job titles found in the database', 'warning')
    except FileNotFoundError:
        job_titles = []
        flash('Job descriptions file not found', 'error')
    except Exception as e:
        job_titles = []
        flash(f'Error loading job titles: {str(e)}', 'error')
    
    return render_template('index.html', job_titles=job_titles)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'cv' not in request.files:
        flash('No file uploaded')
        return redirect(url_for('index'))
    
    file = request.files['cv']
    job_title = request.form.get('job_title')
    
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if not job_title:
        flash('Please select a job title')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process CV
        cv_info = parse_cv(filepath)
        
        # Calculate match score and check job title presence
        match_result = calculate_match_score(cv_info, {}, job_title)
        
        # Get results
        has_job_title = match_result['has_job_title']
        score = match_result['score']
        message = match_result['message']
        
        # Generate email draft for shortlisted candidates
        email_draft = generate_interview_email(cv_info['name'], job_title) if has_job_title else ''
        
        # Store in database
        conn = sqlite3.connect('recruitment.db')
        c = conn.cursor()
        c.execute('INSERT INTO candidates (name, email, score, job_title, shortlisted) VALUES (?, ?, ?, ?, ?)',
                  (cv_info['name'], cv_info['email'], score, job_title, has_job_title))
        conn.commit()
        conn.close()
        
        return render_template('results.html',
                             name=cv_info['name'],
                             email=cv_info['email'],
                             job_title=job_title,
                             score=score,
                             has_job_title=has_job_title,
                             message=message,
                             shortlisted=has_job_title,
                             email_draft=email_draft)
    
    flash('Invalid file type')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)