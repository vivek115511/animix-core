import shutil
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.templating import Jinja2Templates
from moviepy import VideoFileClip

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.post("/upload")
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
    # 1. Save the file temporarily
    temp_input_path = f"processed_videos/raw_{video_file.filename}"
    with open(temp_input_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    try:
        clip = VideoFileClip(temp_input_path)
        short_clip = clip.subclipped(start_time, end_time) 
        
        # 2. Aspect Ratio / Quality / Mute
        if aspect_ratio == "vertical":
            width, height = short_clip.size
            target_width = int(height * 9 / 16)
            short_clip = short_clip.cropped(x1=(width/2)-(target_width/2), y1=0, x2=(width/2)+(target_width/2), y2=height)

        if quality == "480p":
            short_clip = short_clip.resized(height=480)

        if remove_audio == "true":
            short_clip = short_clip.without_audio()

        # 3. Export and Thumbnails
        base_name = video_file.filename.split('.')[0]
        thumb_name = None
        if generate_thumb == "true" and export_type != "mp3":
            thumb_name = f"thumb_{base_name}.jpg"
            short_clip.save_frame(f"processed_videos/{thumb_name}", t=min(0.5, short_clip.duration - 0.1))

        if export_type == "mp3":
            output_filename = f"audio_{base_name}.mp3"
            short_clip.audio.write_audiofile(f"processed_videos/{output_filename}")
        elif export_type == "gif":
            output_filename = f"meme_{base_name}.gif"
            short_clip.write_gif(f"processed_videos/{output_filename}", fps=10)
        else:
            output_filename = f"short_{base_name}.mp4"
            short_clip.write_videofile(f"processed_videos/{output_filename}", codec="libx264", audio_codec="aac")
        
        clip.close()
        short_clip.close()
        return templates.TemplateResponse(request, "result.html", {"video_name": output_filename, "thumb_name": thumb_name})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
