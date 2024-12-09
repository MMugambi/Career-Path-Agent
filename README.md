# Career-Path-Agent
This application is designed to simplify the job application resume, finding relevant job opportunities, and offering skill enhancement recommendations

## Features

1. **Resume Parsing**  
   Extracts content from uploaded resumes (PDF or DOCX) and identifies skills, experience, and education using an AI-powered language model.

2. **Job Matching**  
   Finds job listings relevant to the extracted skills using the Adzuna API.

3. **Skill Extraction**  
   Extracts key skills from job descriptions for better matching and analysis.

4. **Job Ranking**  
   Ranks job listings based on the relevance of their required skills to those on your resume using Jaccard similarity.

5. **Skill Gap Analysis**  
   Identifies gaps between the skills in job descriptions and those on your resume, helping you focus on areas for improvement.

6. **Course Recommendations**  
   Suggests online courses from platforms like Coursera to address the identified skill gaps.

## Getting Started

### Prerequisites
- Python 3.7 or higher
- Required Python libraries (see `requirements.txt`):
  - `requests`
  - `sentence_transformers`
  - `langchain`
  - `PyPDF2`
  - `docx`
  - `bs4`
  - `streamlit`

### Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Streamlit app:
   ```bash
   streamlit run streamlit_autonomy.py
   ```

### Usage
1. **Upload Resume**  
   Upload your resume in PDF or DOCX format.

2. **View Parsed Content**  
   Review the extracted text and JSON-parsed details from your resume.

3. **Explore Job Listings**  
   View job opportunities tailored to your skills.

4. **Skill Gap Analysis**  
   Understand which skills you need to develop.

5. **Course Recommendations**  
   Find courses to bridge skill gaps and improve your profile.

## Configuration

### Environment Variables
Replace the placeholders with your API credentials in the script:
- `ADZUNA_APP_ID`
- `ADZUNA_API_KEY`
- `ASTRA_DB_APPLICATION_TOKEN`
- `ASTRA_DB_ENDPOINT`
- `openai_api_key`

### Database Setup
This application connects to an Astra DB collection (`career_agent`) to store user and resume data. Ensure the specified database exists or is automatically created during runtime.

## Key Technologies
- **Streamlit**: Frontend framework for building interactive web apps.
- **Adzuna API**: Job search API for fetching job listings.
- **Astra DB**: Cloud database for storing resume and job data.
- **SentenceTransformer**: NLP model for embedding and skill matching.
- **OpenAI GPT**: Language model for natural language understanding.

## License
This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Contributing
Feel free to fork the repository and submit pull requests for enhancements or bug fixes.

## Contact
For any queries or support, please reach out via GitHub issues.

---

Enjoy smarter job searching and skill-building! 🎯


