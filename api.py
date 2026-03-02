from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

load_dotenv()

app = FastAPI()

# Enable CORS for Chrome Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize API Key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # Try looking for old GOOGLE_API_KEY variable
    api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
else:
    print("WARNING: No GEMINI_API_KEY found in .env file.")

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Video Summarizer API is running"}

class AnalyzeRequest(BaseModel):
    url: str
    prompt: str

def extract_video_id(url: str):
    # Regex to extract video ID from various YouTube URL formats
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

@app.post("/summarize")
async def summarize_video(request: AnalyzeRequest):
    youtube_url = request.url
    custom_prompt = request.prompt
    
    if not youtube_url:
        raise HTTPException(status_code=400, detail="YouTube URL is required")

    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API key is not configured.")

    video_id = extract_video_id(youtube_url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL. Could not extract video ID.")

    try:
        # Step 1: Get Video Subtitles (Bypasses Render bot detection)
        print(f"Extracting transcript for video ID: {video_id}")
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Combine all text pieces
        transcript_text = " ".join([item['text'] for item in transcript_list])
        print(f"Successfully extracted {len(transcript_text)} characters of transcript.")

        # Step 2: Analyze via Gemini
        print(f"Generating notes for prompt: '{custom_prompt}'...")
        # We use gemini-1.5-flash as the standard robust model
        model = genai.GenerativeModel('gemini-flash-lite-latest')
        
        full_prompt = (
            f"You are a helpful YouTube video reading assistant. "
            f"The user has provided the full text transcript of a YouTube video and asked the following:\n\n"
            f"--- \n{custom_prompt}\n ---\n\n"
            f"Here is the video transcript:\n\n{transcript_text}\n\n"
            f"Please respond specifically to their request using the information from the transcript. Format the output in clean Markdown."
        )

        response = model.generate_content(full_prompt)

        print("Processing complete.")
        return {"summary": response.text}

    except Exception as e:
        error_msg = str(e)
        print(f"\nError during processing: {error_msg}")
        
        if "Subtitles are disabled for this video" in error_msg or "Could not retrieve a transcript" in error_msg:
            raise HTTPException(status_code=400, detail="This video does not have closed captions or subtitles enabled, so it cannot be analyzed.")
            
        if "Quota" in error_msg or "429" in error_msg:
            raise HTTPException(status_code=429, detail="Gemini API Quota Exceeded. Please try again later.")
            
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
