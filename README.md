# JobHunter.AI (powered by OpenAI GPT APIs)

**JobHunter.AI** is a Python + Streamlit-powered AI assistant that helps software engineers **find jobs, generate tailored resumes and cover letters, and track applications**, all from one interface.

It combines **job listing parsing**, **profile-based skill matching**, and **AI-driven document generation** to streamline the application process and save time.

This app uses the latest **GPT-5** models for maximum impact.

---

## 🚀 Features

- **Paste Job URLs**  
  Add job listings manually. The app parses and extracts job details using AI-powered agents.

- **AI Job Summary & Skill Matching**  
  Automatically summarizes the job description and compares it against your profile (`profile.json`) to highlight strengths, gaps, and recommendations.

- **Tailored Resume & Cover Letter Generation**  
  Uses OpenAI GPT models to create concise, human-like application documents (cover letters under 300 words by default).  
  Editable in-app before export.

- **Google Docs Integration**  
  Edit documents easily with google docs and generate PDFs easily

- **Application Tracking**  
  Logs each application to Google Sheets

- **Profile Memory**  
  Persistent local JSON (`profile.json`) stores your skills, experience, and preferences.  
Can be updated via the Profile page. This is how the app learns about me.

- **Prompt Templates**  
  Editable prompt files in `/prompts/` for customizing resume and cover letter generation.

---

## 🛠️ Tech Stack

### **Frontend**
- [Streamlit](https://streamlit.io/) — UI framework for quick web apps in Python
- Streamlit Quill Editor — Rich text editing for resumes and cover letters

### **Backend**
- **Python 3.11+**
- **OpenAI API** — GPT-5, GPT-5-mini, and GPT-5-nano for:
- Job extraction & summarization
- Skill matching & analysis
- Resume and cover letter generation
- **BeautifulSoup4** — Job listing HTML parsing (if applicable)