# AI Video Notes (YouTube Summarizer)

A modern Chrome Extension and FastAPI backend that instantly extracts YouTube transcripts and uses the Gemini API to generate customized notes based on your specific prompts.

## Features
- **Custom Prompts**: Ask the AI to extract specific information (e.g., "Give me a recipe", "Summarize key points").
- **Lightning Fast**: Uses `youtube-transcript-api` to instantly extract close-captioned text, bypassing video downloads and anti-bot IP bans.
- **Beautiful UI**: Modern Chrome Extension interface with Markdown rendering for readable, rich-text output.
- **Local Background Processing**: Runs efficiently on your local machine using PM2, keeping your API key secure and avoiding cloud datacenter restrictions.

## Architecture
1. **Frontend**: Chrome Extension (HTML, CSS, JS)
2. **Backend**: FastAPI (Python 3.11)
3. **AI**: Google Gemini (gemini-flash-lite-latest)

---

## Installation & Setup

### 1. Backend Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/shubhamnaikk/youtube-agent.git
   cd youtube-agent
   ```

2. **Set up the Python environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure the Gemini API Key:**
   - Go to [Google AI Studio](https://aistudio.google.com/app/apikey) and create an API Key.
   - Create a `.env` file in the root directory:
     ```env
     GEMINI_API_KEY="your_api_key_here"
     ```

### 2. Run the Backend as a Background Service

To prevent terminal windows from staying open, we use `pm2` to run the API silently in the background.

1. **Install PM2 globally (requires Node.js):**
   ```bash
   npm install -g pm2
   ```

2. **Start the API:**
   ```bash
   pm2 start ./.venv/bin/python3 --name "video-summarizer-api" -- api.py
   ```

3. **Save the process list** (so it restarts automatically on reboot):
   ```bash
   pm2 save
   ```

*To check logs later, run: `pm2 logs video-summarizer-api`*

### 3. Chrome Extension Setup

1. Open Google Chrome (or Microsoft Edge) and go to `chrome://extensions/`.
2. Turn on **Developer mode** in the top-right corner.
3. Click **Load unpacked** in the top-left corner.
4. Select the `extension/` folder from this repository.
5. The "YouTube Summarizer" extension will now appear in your browser!

## Usage

1. Open any YouTube video.
2. Click the extension icon.
3. Enter what you want the AI to look for (e.g., "Give me 3 takeaways from this video").
4. Click **Generate AI Notes**.

## Technologies Used
- `FastAPI`, `Uvicorn`, `Pydantic`
- `google-generativeai`
- `youtube-transcript-api`
- `marked.js`
- `pm2`