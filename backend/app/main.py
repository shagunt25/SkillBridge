from fastapi import FastAPI
from app.routes import auth, users, resume, target, analysis, prioritization, roadmap, progress, dashboard

app = FastAPI(title="SkillBridge AI Backend")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(resume.router)
app.include_router(target.router)
app.include_router(analysis.router)
app.include_router(prioritization.router)
app.include_router(roadmap.router)
app.include_router(progress.router)
app.include_router(dashboard.router)

@app.get("/")
def read_root():
    return {"message": "SkillBridge AI backend is running"}