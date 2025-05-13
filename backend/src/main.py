import uvicorn
from fastapi import FastAPI

from backend.src.apis.chat import app as chat_app

app = FastAPI(title="Automated learning paths")
app.include_router(chat_app)


@app.get("/")
async def root():
    return {"message": "Learning Path Chatbot"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
