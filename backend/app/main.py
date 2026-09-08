from fastapi import FastAPI
from app.routes import auth, users

app = FastAPI(title="SkillBridge AI Backend")

app.include_router(auth.router)
app.include_router(users.router)

@app.get("/")
def read_root():
    return {"message": "SkillBridge AI backend is running"}

