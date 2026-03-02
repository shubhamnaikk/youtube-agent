from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import time
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import yt_dlp
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

class AnalyzeRequest(BaseModel):
    url: str
    prompt: str

@app.post("/summarize")
async def summarize_video(request: AnalyzeRequest):
    youtube_url = request.url
    custom_prompt = request.prompt
    
    if not youtube_url:
        raise HTTPException(status_code=400, detail="YouTube URL is required")

    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API key is not configured.")

    audio_path = None
    processed_file = None
    try:
        # Step 1: Download Audio from YouTube
        print(f"Analyzing video: {youtube_url}")
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio',
            'outtmpl': tempfile.gettempdir() + '/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            audio_path = ydl.prepare_filename(info)

        # Step 2: Upload to Gemini API
        print("Coming Up with the solution...")
        processed_file = genai.upload_file(audio_path)
        
        while processed_file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(2)
            processed_file = genai.get_file(processed_file.name)
        
        if processed_file.state.name == "FAILED":
            raise Exception("Gemini audio processing failed.")

        print("\nAudio uploaded and ready.")

        # Step 3: Analyze via Gemini
        print(f"Generating notes for prompt: '{custom_prompt}'...")
        # We use gemini-1.5-flash as the standard robust model
        model = genai.GenerativeModel('gemini-flash-lite-latest')
        
        full_prompt = (
            f"You are a helpful YouTube video transcriber and assistant.\n"
            f"The user has provided an audio file of a video and asked the following:\n\n"
            f"--- \n{custom_prompt}\n ---\n\n"
            f"Please respond specifically to their request using the information from the audio. Format the output in clean Markdown."
        )

        response = model.generate_content([full_prompt, processed_file])

        print("Processing complete.")
        return {"summary": response.text}

    except Exception as e:
        error_msg = str(e)
        print(f"\nError during processing: {error_msg}")
        if "Quota" in error_msg or "429" in error_msg:
            raise HTTPException(status_code=429, detail="Gemini API Quota Exceeded. Please try again later.")
        raise HTTPException(status_code=500, detail=error_msg)
    finally:
        # Cleanup temporary audio file locally
        if audio_path and Path(audio_path).exists():
            Path(audio_path).unlink(missing_ok=True)
        # Cleanup file from Gemini servers to save space
        if processed_file:
            try:
                genai.delete_file(processed_file.name)
                print(f"Deleted file {processed_file.name} from Gemini API.")
            except Exception as cleanup_err:
                print(f"Failed to delete file from Gemini: {cleanup_err}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
