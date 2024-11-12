from fastapi import FastAPIs

app = FastAPI()

@app.get("/")
def index():
    return {"message": "Welcome TO FastAPI World"}
