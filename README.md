# Job Screening AI Website

A Flask-based web application that automates job screening using a multi-agent AI system. The application processes CV uploads, matches them against job descriptions, and generates interview invitations for qualified candidates.

## Features

- CV upload and processing (PDF format)
- Job title selection from predefined descriptions
- Automated CV-Job matching with scoring
- Candidate shortlisting based on match score
- Interview invitation email generation for shortlisted candidates
- Responsive design with Bootstrap 5.3.0

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. Clone the repository or download the source code

2. Create a virtual environment (recommended):
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Download the spaCy model:
```bash
python -m spacy download en_core_web_lg
```

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Project Structure

```
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── job_descriptions.csv   # Sample job descriptions
├── static/
│   ├── css/
│   │   └── styles.css    # Custom CSS styles
│   └── js/
│       └── scripts.js    # Client-side JavaScript
├── templates/
│   ├── base.html         # Base template
│   ├── index.html        # Homepage template
│   └── results.html      # Results page template
└── uploads/              # Directory for uploaded CVs
```

## Usage

1. On the homepage, upload a PDF CV (max 16MB)
2. Select a job title from the dropdown menu
3. Submit the application
4. View the results, including:
   - Match score
   - Shortlisting status
   - Interview invitation (if shortlisted)

## Technical Details

- Backend: Flask (Python)
- Frontend: Bootstrap 5.3.0
- Database: SQLite
- NLP: spaCy (en_core_web_lg model)
- PDF Processing: PyMuPDF

## Security Features

- Secure file uploads with type checking
- File size limitations
- Input validation
- SQL injection prevention
- XSS protection

## License

MIT License