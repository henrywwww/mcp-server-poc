# main.py
from fastapi import FastAPI
app = FastAPI()

@app.get("/status")
def check():
    return {"status": "ok"}