import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Import the router - This is where the error likely is!
try:
    from routers import video
except ImportError:
    # If the folder is named differently on your GitHub, 
    # this will help us see it in the logs.
    video = None

app = FastAPI()

# Create the folder for processed videos if it doesn't exist
os.makedirs("processed_videos", exist_ok=True)

# Mount static files and templates
app.mount("/videos", StaticFiles(directory="processed_videos"), name="videos")
templates = Jinja2Templates(directory="templates")

# Only include the router if it was found
if video:
    app.include_router(video.router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})
