import uvicorn
from fastapi import FastAPI

from backend.src.apis.chat import app as invoke

app = FastAPI(title="Learning Path Assistant")
app.include_router(invoke)


@app.get("/")
async def root():
    return {"message": "Learning Path Chatbot"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")