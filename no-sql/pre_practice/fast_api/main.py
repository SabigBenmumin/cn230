from fastapi import FastAPI

app = FastAPI()

@app.get("/")

def index():
    return {"message": "Welcome To FastAPI World"}