from fastapi import FastAPI

app = FastAPI(title="SkillBridge AI Backend")

@app.get("/")
def read_root():
    return {"message": "SkillBridge AI backend is running"}