""" Team Members
1. George Kirangu
2. Anthony Kigen
3. Ken Mwaniki
4. Timothy Mugambi
""" 

# Import Libraries
import requests
import re
import tkinter as tk
from tkinter import filedialog
from sentence_transformers import SentenceTransformer, util
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from astrapy import DataAPIClient
from bs4 import BeautifulSoup
import json
from datetime import datetime
from PyPDF2 import PdfReader
import docx
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema.runnable import RunnableSequence
# from langchain.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
import openai
import streamlit as st

# API Integrations and Database Configuration
ADZUNA_APP_ID = "74e2ec41"
ADZUNA_API_KEY = "faec158c90b5e0652f6e5c8966ec2d7c"
ASTRA_DB_APPLICATION_TOKEN = "AstraCS:chtZrQZOAuGwmZZErQtRRicF:3f6ae3555e2e3a543ec7ff406afadf5717386cd2eb485311ce7a826502368d02"
ASTRA_DB_ENDPOINT = "https://4e5160dc-9ec1-4f56-8740-4d62a6ae7aed-us-east-2.apps.astra.datastax.com"

# Database Connection
client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
db = client.get_database_by_api_endpoint(ASTRA_DB_ENDPOINT)
collection_name = "career_agent"
if collection_name not in db.list_collection_names():
    db.create_collection(collection_name)
collection = db.get_collection(collection_name)
print(f"Connected to Astra DB: {db.list_collection_names()}")

# Embedding Model for NLP-Based Skill Matching
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize LLM (OpenAI GPT)
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0, openai_api_key='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')

# Helper Functions
def generate_user_id():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = f"user_{timestamp}"
    return unique_id

system_prompt = """
You are an AI agent tasked with assisting users in finding the best job opportunities based on their resume.
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop, you output an Answer
Use Thought to parse and understand the user's requestresume
Use Action to process the resume by running the actions available to you, then PAUSE
The AObservation will be the result of running those actions.

Your primary goals are:

Parse the user's resume to extract key information such as skills, experience, education, and job preferences.
Use this information to search the internet for job listings that closely match the user's qualifications and aspirations.
Rank the top 5 jobs that best align with the resume.
Identify the skills gap between the user's current qualifications and the requirements of each job.
Provide actionable insights about which skills the user needs to acquire before applying.

Your available actions are:

Action 1: Parse Resume:

Input: A resume in text or document form (e.g., PDF, DOCX, or plain text).
Task: Extract relevant information from the resume, including:
Skills: Programming languages, software, tools, frameworks, etc.
Experience: Job titles, companies, durations, responsibilities.
Education: Degrees, institutions, certifications.
Preferences: Desired job title, location, salary range (if available).
Observation: A structured summary of the parsed information should be output, such as:
Skills: JavaScript, Python, React, SQL, etc.
Experience: 3 years as a software engineer at XYZ Corp.
Education: B.Sc. in Computer Science from ABC University.

Action 2: Search for Jobs:

Input: The parsed resume data (skills, experience, etc.).
Task: Search job listings on popular platforms (e.g., LinkedIn, Indeed, Glassdoor, etc.) for roles that closely match the user's qualifications and preferences.
Observation: A list of 5 job listings, each with the following details:
Job title.
Company.
Location.
Required skills (both technical and soft skills).
Job description summary.

Action 3: Rank Job Listings:

Input: The list of job listings.
Task: Rank the jobs based on the match to the user's skills, experience, and preferences.
Observation: A ranked list of the top 5 jobs, showing the best match at the top, with relevant job details.

Action 4: Identify Skills Gap:

Input: The top 5 job listings and the user’s parsed resume.
Task: For each job, identify the skills gap. Compare the required skills in the job descriptions with the user’s current skills.
Observation: For each of the top 5 jobs, return the skills that the user lacks or needs to improve upon before applying. For example:
Job 1: Software Engineer at ABC Corp.
Missing skills: Machine Learning, Docker, Cloud Computing.
Job 2: Frontend Developer at XYZ Inc.
Missing skills: Vue.js, UX/UI design principles.

Action 5: Provide Recommendations:

Input: The identified skills gaps for the top 5 jobs.
Task: Suggest specific online courses, certifications, or resources that the user can use to acquire the missing skills.
Observation: A list of recommendations for each job’s skills gap:
Machine Learning: Coursera’s "Machine Learning by Stanford University."
Docker: Udemy's "Docker Mastery: The Complete Toolset."

Example session:
User: I need help finding a job
Assistant: Sure, please upload your resume.
User: My resume has been uploaded and shared as a path file called "file_path"
Assistant: Let me parse your resume.
Assistant: I found the following information:
Skills: Python, Java, SQL
Experience: 3 years as a software developer at XYZ Corp.
Education: B.Sc. in Computer Science from ABC University.
Assistant: Now, let me search for job listings.
Assistant: I found 5 jobs that match your qualifications.
Assistant: Here are the top 5 job listings:
1. Software Engineer at ABC Corp.
2. Data Analyst at XYZ Inc.
3. Web Developer at 123 Co.
4. Product Manager at QRS Corp.
5. UX Designer at UVW Inc.
Assistant: I will now identify the skills gap.
Assistant: For the Software Engineer position, you need to improve in Machine Learning and Cloud Computing.
Assistant: For the Data Analyst position, you need to improve in Data Visualization and Statistics.
Assistant: For the Web Developer position, you need to improve in React.js and Node.js.
Assistant: For the Product Manager position, you need to improve in Agile Methodologies and Product Strategy.
Assistant: For the UX Designer position, you need to improve in Wireframing and Prototyping.
Assistant: I will now provide recommendations.
Assistant: I recommend taking the following courses:
Machine Learning by Stanford University on Coursera for Machine Learning.
Docker Mastery: The Complete Toolset on Udemy for Docker.
React.js Essentials on Udemy for React.js.
Statistics for Data Science on edX for Data Visualization.
Product Management Fundamentals on LinkedIn Learning for Agile Methodologies.
UX Design Fundamentals on Coursera for Wireframing.
Assistant:I have completed the loop of Thought, Action, PAUSE, Observation.

Now it's your turn to assist the user in finding the best job opportunities based on their resume.
"""

# 1. Dialog box to select file for upload
def select_file():
    # print("Opening file selection dialog...")
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window
    file_path = filedialog.askopenfilename(
        title="Select Your Resume",
        filetypes=(("DOCX files", "*.docx"), ("PDF files", "*.pdf"))
    )
    if file_path:
        print(f"File selected: {file_path}")
    else:
        print("No file selected. Exiting...")
    return file_path

# 2. Exracting resume content

def extract_resume_context(uploaded_file):
    # print("Extracting text from the resume...")
    file_name = uploaded_file.name.lower() 
    if file_name.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        text = " ".join(page.extract_text() for page in reader.pages if page.extract_text())
        print("Text extracted from PDF.")
        return text
    elif file_name.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        print("Text extracted from DOCX.")
        return text
    else:
        st.error("Unsupported file format.")
        return None

#3. Parsing the resume and cleaning
def clean_json_output(raw_output):
    try:
        json_match = re.search(r"{.*}", raw_output, re.DOTALL)
        if not json_match:
            print("Could not locate JSON content in the output.")
            return None
        cleaned_output = json_match.group(0)
        return json.loads(cleaned_output)
    except json.JSONDecodeError as e:
        print(f"Failed to clean JSON: {e}")
        return None

def parse_resume(resume_text, llm):
    prompt_template = PromptTemplate(
        input_variables=["resume_text"],
        template=(
            "Extract the following details from the resume text and return them as a JSON object:\n"
            "{{\n"
            "  \"skills\": [\"list of skills\"],\n"
            "  \"experience\": [\"list of experiences\"],\n"
            "  \"education\": [\"list of education qualifications\"]\n"
            "}}\n\n"
            "Resume:\n{resume_text}"
        )
    )
    chain = LLMChain(prompt=prompt_template, llm=llm)

    # Pass the input as a dictionary
    result = chain.run({"resume_text": resume_text})
    # print(f"Raw LLM Output:\n{result}")

    # Validate and return JSON output
    parsed_result = clean_json_output(result)
    if parsed_result:
        print("Resume parsed successfully.")
        return parsed_result
    else:
        print("Returning raw result for debugging.")
        return result
    

# 4. Scraping jobs based on the skills extracted from the resume
def scrape_jobs(parsed_resume):
    if not isinstance(parsed_resume, dict):
        try:
            # Attempt to parse as JSON if it's a string
            parsed_resume = json.loads(parsed_resume)
        except json.JSONDecodeError:
            print("Error: Parsed resume is not in the correct format.")
            return []
    
    if "skills" not in parsed_resume or not parsed_resume["skills"]:
        print("No skills found in the parsed resume.")
        return []

    all_job_listings = []
    unique_urls = set()

    for skill in parsed_resume["skills"]:
        # print(f"\nSearching for jobs with skill: {skill}...")
        try:
            response = requests.get(
                f"https://api.adzuna.com/v1/api/jobs/us/search/1",
                params={
                    "app_id": ADZUNA_APP_ID,
                    "app_key": ADZUNA_API_KEY,
                    "what": skill,
                },
            )

            if response.status_code == 200:
                jobs = response.json().get("results", [])
                # print(f"Found {len(jobs)} job listings for skill: {skill}.")
                for job in jobs:
                    url = job.get("redirect_url", "No URL")
                    if url not in unique_urls: 
                        unique_urls.add(url)
                        all_job_listings.append({
                            "title": job.get("title", "No Title"),
                            "description": job.get("description", "No Description"),
                            "url": url,
                        })
            else:
                print(f"Error fetching job listings for skill: {skill}. Status Code: {response.status_code}")

        except requests.RequestException as e:
            print(f"An error occurred while fetching jobs for skill: {skill}. Error: {e}")
    
    print(f"\nTotal unique job listings found: {len(all_job_listings)}")
    return all_job_listings


# 5. Extracting the skills from the lob listings of the scraped data
def clean_and_validate_json(raw_output):
    cleaned_output = raw_output.strip()
    if cleaned_output.startswith("```") and cleaned_output.endswith("```"):
        cleaned_output = cleaned_output.strip("```").strip()

    if cleaned_output.startswith("json"):
        cleaned_output = cleaned_output[4:].strip()

    try:
        return json.loads(cleaned_output)
    except json.JSONDecodeError:
        return None


def extract_skills_from_jobs(job_listings, llm):
    job_skills = {}

    for job in job_listings:
        description = job.get("description", "").strip()
        title = job.get("title", "Unknown Job Title")

        if not description:
            continue

        prompt_template = PromptTemplate(
            input_variables=["job_description"],
            template=(
                "From the following job description, extract a list of key skills, software, tools, "
                "or programming languages explicitly mentioned:\n"
                "Job Description:\n{job_description}\n\n"
                "Return the results strictly as a valid JSON list of unique skills without repetition. "
                "If no skills are mentioned, return an empty JSON list ([])."
            )
        )
        chain = LLMChain(prompt=prompt_template, llm=llm)

        try:
            result = chain.run({"job_description": description}).strip()
            parsed_result = clean_and_validate_json(result)

            if isinstance(parsed_result, list) and parsed_result:
                unique_skills = sorted(set(skill.strip() for skill in parsed_result if isinstance(skill, str)))
                job_skills[title] = unique_skills

        except Exception:
            continue

    return job_skills

# 6. Rank jobs by relevance to find the most suitable jobs (a comparison of job description skills and resume skills)

def rank_jobs_by_relevance(resume_skills, job_skills):
    ranked_jobs = []

    # Convert resume skills to a set for efficient computation
    resume_skills_set = set(resume_skills)

    for job_title, skills in job_skills.items():
        job_skills_set = set(skills)
        # Calculate the Jaccard similarity: |Intersection| / |Union|
        intersection = resume_skills_set & job_skills_set
        union = resume_skills_set | job_skills_set
        relevance_score = len(intersection) / len(union) if union else 0

        # Append the job title and relevance score to the ranking list
        ranked_jobs.append((job_title, relevance_score))

    # Sort jobs by relevance score in descending order
    ranked_jobs.sort(key=lambda x: x[1], reverse=True)

    return ranked_jobs

# 7. A comparison of the missed skills from job description (job skills - resume skills)

def skill_gap_analysis(resume_skills, ranked_jobs, job_skills):
    # print("Performing skill gap analysis on top 20 ranked jobs...")
    skill_gaps = {} 
    top_jobs = ranked_jobs[:20]

    for job_title, _ in top_jobs:
        if job_title in job_skills:
            job_skills_list = job_skills[job_title]

            # print(f"Job Skills for '{job_title}': {job_skills_list}")

            # Identify missing skills (focused on technical skills)
            missing_skills = list(set(job_skills_list) - set(resume_skills))
            skill_gaps[job_title] = missing_skills

            # print(f"Missing Skills for {job_title}: {missing_skills}")
        else:
            print(f"No skills found for '{job_title}'. Skipping.")

    return skill_gaps

# 8. Providing references from the missed skills to the user for upgrading of their skills
def fetch_courses(missing_skills):
    recommended_courses = {}

    for skill in missing_skills:
        # print(f"Generating search link for skill '{skill}'...")

        # Format skill for the Coursera search query
        search_query = skill.replace(" ", "%20")
        search_url = f"https://www.coursera.org/search?query={search_query}"

        # Simulated course results based on the search URL
        recommended_courses[skill] = [
            {
                "title": f"Explore courses for {skill}",
                "description": f"Search Coursera for courses related to {skill}.",
                "url": search_url
            }
        ]

    return recommended_courses


def recommend_courses(skill_gaps):
    recommendations = {}
    for job_title, missing_skills in skill_gaps.items():
        courses = [
            {
                "title": f"Explore {skill}",
                "url": f"https://www.coursera.org/search?query={skill.replace(' ', '%20')}"
            } for skill in missing_skills
        ]
        recommendations[job_title] = courses
    return recommendations



# Streamlit App Interface
st.title("Career Path Agent")

# Step 1: Upload resume
uploaded_file = st.file_uploader("Upload Your Resume (PDF or DOCX)", type=["pdf", "docx"])

if uploaded_file:
    with st.spinner("Extracting text from the resume..."):
        resume_text = extract_resume_context(uploaded_file)

    if resume_text:
        st.subheader("Parsed Resume Text")
        st.text_area("Extracted Text", resume_text, height=200)
        
        # Step 2: Parse resume
        with st.spinner("Parsing the resume..."):
            parsed_resume = parse_resume(resume_text, llm)
        
        if parsed_resume:
            st.subheader("Resume Details")
            st.json(parsed_resume)
            
            # Step 3: Scrape jobs
            with st.spinner("Finding job listings..."):
                job_listings = scrape_jobs(parsed_resume)
            
            if job_listings:
                st.subheader("Job Listings")
                for idx, job in enumerate(job_listings, start=1):
                    st.write(f"**{idx}. {job['title']}**")
                    st.write(f"[View Job Posting]({job['url']})")

                # Step 4: Extract skills from job descriptions
                with st.spinner("Extracting skills from job descriptions..."):
                    job_skills = extract_skills_from_jobs(job_listings, llm)

                st.subheader("Extracted Skills from Jobs")
                st.json(job_skills)

                # Step 5: Rank jobs by relevance
                ranked_jobs = rank_jobs_by_relevance(parsed_resume.get("skills", []), job_skills)
                st.subheader("Ranked Jobs by Relevance")
                for job, score in ranked_jobs:
                    st.write(f"{job}: {score:.2f}")

                # Step 6: Skill gap analysis
                skill_gaps = skill_gap_analysis(parsed_resume.get("skills", []), ranked_jobs, job_skills)
                st.subheader("Skill Gaps")
                st.json(skill_gaps)

                # Step 7: Course recommendations
                course_recommendations = recommend_courses(skill_gaps)
                if course_recommendations:
                    st.subheader("Recommended Courses")
                    for job, courses in course_recommendations.items():
                        st.write(f"**{job}**")
                        if isinstance(courses, list):  # Ensure it's a list
                            for course in courses:
                                if isinstance(course, dict) and 'title' in course and 'url' in course:
                                    st.write(f"- [{course['title']}]({course['url']})")
                                else:
                                    st.write("- Invalid course data")
                        else:
                            st.write("- No valid courses found")


