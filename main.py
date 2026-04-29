import os
import shutil
import subprocess
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Ensure folders exist
os.makedirs("processed_videos", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app.mount("/videos", StaticFiles(directory="processed_videos"), name="videos")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # This renders your home.html file
    return templates.TemplateResponse("home.html", {"request": request})

@app.post("/upload")
async def handle_upload(
    request: Request, 
    video_file: UploadFile = File(...),
    start_time: int = Form(...),  
    end_time: int = Form(...),
    export_type: str = Form("video"), 
    aspect_ratio: str = Form("landscape"),
    quality: str = Form("720p"),
    remove_audio: str = Form("false")
): # <--- Ensure there is only ONE ')' before the colon ':'
    base_name = video_file.filename.split('.')[0]
    # ... (rest of your code below stays the same)
