import uvicorn
from fastapi import FastAPI

from backend.src.apis.chat import app as chat_app
from backend.src.a2a.controller import router

app = FastAPI(title="Automated learning paths")
app.include_router(chat_app)
app.include_router(router, prefix="/api/v1/a2a", tags=["a2a"])


@app.get("/")
async def root():
    return {"message": "Learning Path Chatbot"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
