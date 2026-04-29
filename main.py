import os
import shutil
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Using the editor import for the simplest command names
from moviepy.editor import VideoFileClip

app = FastAPI()

# Cloud Folders - Ensures the server has a place to save your results
os.makedirs("processed_videos", exist_ok=True)
app.mount("/videos", StaticFiles(directory="processed_videos"), name="videos")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.post("/upload")
async def handle_upload(
    request: Request, 
    video_file: UploadFile = File(...),
    start_time: int = Form(...),  
    end_time: int = Form(...),
    export_type: str = Form(...), 
    aspect_ratio: str = Form(...),
    quality: str = Form(...),          
    remove_audio: str = Form(None),
    generate_thumb: str = Form(None)   
): 
    # 1. Save the uploaded file to the server
    temp_input_path = f"processed_videos/raw_{video_file.filename}"
    with open(temp_input_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    try:
        clip = VideoFileClip(temp_input_path)
        
        # 2. Applying the Edits (Stable v1.0.3 Commands)
        short_clip = clip.subclip(start_time, end_time)
        
        if aspect_ratio == "vertical":
            w, h = short_clip.size
            target_w = int(h * 9 / 16)
            x_center = w / 2
            # Simple .crop() command
            short_clip = short_clip.crop(x1=x_center-(target_w/2), y1=0, x2=x_center+(target_w/2), y2=h)

        if quality == "480p":
            # Simple .resize() command
            short_clip = short_clip.resize(height=480)

        if remove_audio == "true":
            short_clip = short_clip.without_audio()

        # 3. Exporting the result
        base_name = video_file.filename.split('.')[0]
        output_filename = f"short_{base_name}.mp4"
        output_path = f"processed_videos/{output_filename}"
        
        # Writing the file with high compatibility settings
        short_clip.write_videofile(
            output_path, 
            codec="libx264", 
            audio_codec="aac",
            temp_audiofile='temp-audio.m4a', 
            remove_temp=True
        )
        
        clip.close()
        short_clip.close()
        
        return templates.TemplateResponse("result.html", {"request": request, "video_name": output_filename})

    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)
