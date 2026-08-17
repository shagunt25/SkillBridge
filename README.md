# 🚀 AI-Driven Skill Gap Analysis & Learning Roadmap Platform

An intelligent, full-stack application designed to ingest resumes, evaluate skill gaps against targeted career roles, and generate interactive, personalized learning roadmaps using multi-model AI orchestration.

---

## 📌 Tech Stack & Architecture

| Layer | Technology | Hosting / Infrastructure |
| :--- | :--- | :--- |
| **Frontend** | React (Modular CSS) | Vercel (Automated CI/CD) |
| **Backend** | FastAPI (Python, Asynchronous) | Render (Containerized via Docker) |
| **Database** | MongoDB Atlas | M0 Shared Cluster |
| **AI Layer** | Multi-Model Orchestration (LiteLLM / Gemini / Groq) | Local Spacy NER / External APIs |
| **DevOps** | Docker, Docker Compose, GitHub Actions | GitHub Container Registry (GHCR) |

---

## 🏗️ Repository Structure (Target Layout)

```text
├── .github/
│   └── workflows/
│       └── deploy.yml        # Automated CI/CD pipeline for backend
├── backend/
│   ├── app/                  # FastAPI source code & endpoints
│   ├── Dockerfile            # Container definition
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/                  # React source code & components
│   ├── package.json          # Node dependencies & build scripts
│   └── vercel.json           # Client-side routing rewrite rules
├── .gitignore                # Global git ignore rules
├── docker-compose.yml        # Local multi-service orchestration
└── README.md