from fastapi import FastAPI

app = FastAPI(title="News Agent API")

@app.get("/health")
def health():
    return {"status": "ok"}
