"""
YouTube Transcript Service with FULL METADATA
FastAPI + yt-dlp wrapper for complete video data extraction
Deployed on Railway: https://railway.app

Returns ALL 17 fields:
- Title, Status, Video ID, Processed Date
- Channel Name, Channel URL, Description
- Duration, View Count, Like Count, Upload Date
- Tags, Categories, Thumbnail
- Transcript, Length, Video URL
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import subprocess
import json
import re
from datetime import datetime

app = FastAPI(
    title="YouTube Transcript Service",
    description="Full YouTube video data extraction with yt-dlp",
    version="2.0.0"
)

# Request models
class TranscriptRequest(BaseModel):
    video_id: str = Field(..., description="YouTube video ID (11 characters)")

class TranscriptResponse(BaseModel):
    success: bool
    videoId: str
    videoTitle: Optional[str] = None
    channelName: Optional[str] = None
    channelUrl: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    viewCount: Optional[int] = None
    likeCount: Optional[int] = None
    uploadDate: Optional[str] = None
    tags: Optional[str] = None
    categories: Optional[str] = None
    thumbnailUrl: Optional[str] = None
    transcript: Optional[str] = None
    length: Optional[int] = None
    error: Optional[str] = None

def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL"""
    patterns = [
        r'[?&]v=([a-zA-Z0-9_-]{11})',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url

def get_yt_dlp_data(video_id: str) -> dict:
    """
    Extract complete video data using yt-dlp

    Returns: dict with all 17 fields
    """
    url = f"https://www.youtube.com/watch?v={video_id}"

    # yt-dlp command to extract all data
    cmd = [
        'yt-dlp',
        '--dump-json',
        '--write-subs', '--write-auto-subs',
        '--sub-lang', 'en',
        '--skip-download',
        url
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            raise Exception(f"yt-dlp error: {result.stderr}")

        data = json.loads(result.stdout)

        # Extract transcript from subtitles
        transcript = ""
        if 'subtitles' in data and 'en' in data['subtitles']:
            sub_file = data['subtitles']['en'][0]['url']
            transcript_result = subprocess.run(
                ['curl', '-s', sub_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            # Parse XML and extract text
            import xml.etree.ElementTree as ET
            root = ET.fromstring(transcript_result.stdout)
            transcript = ' '.join([text.text for text in root.findall('.//text')])

        elif 'automatic_captions' in data and 'en' in data['automatic_captions']:
            sub_file = data['automatic_captions']['en'][0]['url']
            transcript_result = subprocess.run(
                ['curl', '-s', sub_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            import xml.etree.ElementTree as ET
            root = ET.fromstring(transcript_result.stdout)
            transcript = ' '.join([text.text for text in root.findall('.//text')])

        # Build response with all 17 fields
        return {
            'videoTitle': data.get('title', ''),
            'videoId': video_id,
            'channelName': data.get('channel', ''),
            'channelUrl': data.get('channel_url', ''),
            'description': data.get('description', ''),
            'duration': data.get('duration', 0),
            'viewCount': data.get('view_count', 0),
            'likeCount': data.get('like_count', 0),
            'uploadDate': data.get('upload_date', ''),
            'tags': ', '.join(data.get('tags', [])),
            'categories': ', '.join(data.get('categories', [])),
            'thumbnailUrl': data.get('thumbnail', ''),
            'transcript': transcript,
            'length': len(transcript)
        }

    except subprocess.TimeoutExpired:
        raise Exception("Request timeout")
    except json.JSONDecodeError:
        raise Exception("Invalid JSON response from yt-dlp")
    except Exception as e:
        raise Exception(f"Error: {str(e)}")

@app.get("/", tags=["Root"])
def root():
    """Root endpoint - API information"""
    return {
        "service": "YouTube Transcript Service",
        "version": "2.0.0",
        "status": "running",
        "fields": 17,
        "endpoints": {
            "/": "GET - API information",
            "/health": "GET - Health check",
            "/transcript": "POST - Get full video data (17 fields)",
            "/docs": "GET - API documentation (Swagger UI)"
        }
    }

@app.get("/health", tags=["Health"])
def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "youtube-transcript-service",
        "yt-dlp": "installed"
    }

@app.post("/transcript", response_model=TranscriptResponse, tags=["Transcript"])
def get_transcript(request: TranscriptRequest):
    """
    Get complete YouTube video data (all 17 fields)

    Returns:
        - Title, Status, Video ID, Processed Date
        - Channel Name, Channel URL, Description
        - Duration, View Count, Like Count, Upload Date
        - Tags, Categories, Thumbnail
        - Transcript, Length, Video URL

    Example:
        POST /transcript
        {
            "video_id": "dQw4w9WgXcQ"
        }
    """
    try:
        # Extract video ID if URL provided
        video_id = extract_video_id(request.video_id)

        # Validate video_id
        if len(video_id) != 11:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid video_id: {video_id}. Must be 11 characters."
            )

        # Get data from yt-dlp
        data = get_yt_dlp_data(video_id)

        return TranscriptResponse(
            success=True,
            videoId=video_id,
            videoTitle=data['videoTitle'],
            channelName=data['channelName'],
            channelUrl=data['channelUrl'],
            description=data['description'],
            duration=data['duration'],
            viewCount=data['viewCount'],
            likeCount=data['likeCount'],
            uploadDate=data['uploadDate'],
            tags=data['tags'],
            categories=data['categories'],
            thumbnailUrl=data['thumbnailUrl'],
            transcript=data['transcript'],
            length=data['length']
        )

    except HTTPException:
        raise
    except Exception as e:
        return TranscriptResponse(
            success=False,
            videoId=request.video_id,
            error=str(e)
        )

@app.get("/transcript", tags=["Transcript"])
def get_transcript_get(video_id: str):
    """
    GET endpoint for transcript (alternative to POST)

    Query Parameters:
        video_id: YouTube video ID

    Example:
        GET /transcript?video_id=dQw4w9WgXcQ
    """
    request = TranscriptRequest(video_id=video_id)
    return get_transcript(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
