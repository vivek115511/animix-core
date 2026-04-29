import os
import shutil
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# ULTRA-LIGHT IMPORT: Only loads exactly what we need
from moviepy.video.io.VideoFileClip import VideoFileClip
import moviepy.video.fx.all as vfx

app = FastAPI()

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
    remove_audio: str = Form(None)
): 
    temp_input_path = f"processed_videos/raw_{video_file.filename}"
    with open(temp_input_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    try:
        # Load the clip
        clip = VideoFileClip(temp_input_path)
        
        # 1. Trimming (subclip)
        short_clip = clip.subclip(start_time, end_time)
        
        # 2. Aspect Ratio (Using vfx for stability)
        if aspect_ratio == "vertical":
            w, h = short_clip.size
            target_w = int(h * 9 / 16)
            x_center = w / 2
            short_clip = vfx.crop(short_clip, x1=x_center-(target_w/2), y1=0, x2=x_center+(target_w/2), y2=h)

        # 3. Quality (Using vfx for stability)
        if quality == "480p":
            short_clip = vfx.resize(short_clip, height=480)

        if remove_audio == "true":
            short_clip = short_clip.without_audio()

        output_filename = f"short_{video_file.filename.split('.')[0]}.mp4"
        output_path = f"processed_videos/{output_filename}"
        
        # Write file
        short_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        
        clip.close()
        short_clip.close()
        
        return templates.TemplateResponse("result.html", {"request": request, "video_name": output_filename})

    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)
