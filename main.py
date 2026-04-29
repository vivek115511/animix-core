import shutil
import os
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from moviepy import VideoFileClip

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Ensure folders exist and can be safely viewed
os.makedirs("processed_videos", exist_ok=True)
app.mount("/videos", StaticFiles(directory="processed_videos"), name="videos")

# --- THE FRONT DOOR (This fixes the 404 Error!) ---
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="home.html")

# --- THE CREATOR STUDIO UPLOAD LOGIC ---
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
    # 1. Safety Checks
    if not video_file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Please upload a valid video file.")
    if start_time >= end_time:
        raise HTTPException(status_code=400, detail="Start time must be before end time!")
    
    # 2. Save the raw video
    temp_input_path = f"processed_videos/raw_{video_file.filename}"
    with open(temp_input_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    try:
        clip = VideoFileClip(temp_input_path)
        short_clip = clip.subclipped(start_time, end_time) 
        
        # 3. Apply Aspect Ratio (Vertical Crop)
        if aspect_ratio == "vertical":
            width, height = short_clip.size
            target_width = int(height * 9 / 16)
            x_center = width / 2
            short_clip = short_clip.cropped(x1=x_center-(target_width/2), y1=0, x2=x_center+(target_width/2), y2=height)

        # 4. Apply Compression
        if quality == "480p":
            short_clip = short_clip.resized(height=480)

        # 5. Apply Mute
        if remove_audio == "true":
            short_clip = short_clip.without_audio()

        base_name = video_file.filename.split('.')[0]
        
        # 6. Generate Thumbnail (.jpg)
        thumb_filename = None
        if generate_thumb == "true" and export_type != "mp3":
            thumb_filename = f"thumb_{base_name}.jpg"
            short_clip.save_frame(f"processed_videos/{thumb_filename}", t=min(0.5, short_clip.duration - 0.1))

        # 7. Final Export
        if export_type == "mp3":
            output_filename = f"audio_{base_name}.mp3"
            short_clip.audio.write_audiofile(f"processed_videos/{output_filename}")
        elif export_type == "gif":
            output_filename = f"meme_{base_name}.gif"
            short_clip.write_gif(f"processed_videos/{output_filename}", fps=10)
        else:
            output_filename = f"short_{base_name}.mp4"
            short_clip.write_videofile(f"processed_videos/{output_filename}", codec="libx264", audio_codec="aac")
        
        # Clean up memory
        clip.close()
        short_clip.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

    # 8. Send to Success Page
    return templates.TemplateResponse(
        request=request, 
        name="result.html", 
        context={"video_name": output_filename, "thumb_name": thumb_filename}
    )