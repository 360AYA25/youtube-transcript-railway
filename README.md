# YouTube Transcript FastAPI

FastAPI wrapper for `youtube-transcript-api` library.

## Endpoints

### GET /
Root endpoint with API information

### GET /health
Health check

### POST /transcript
Get transcript for YouTube video

**Request:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "lang": "en"
}
```

**Response:**
```json
{
  "success": true,
  "videoId": "dQw4w9WgXcQ",
  "transcript": "Full text here...",
  "length": 2089
}
```

### GET /transcript?video_id=XXX&lang=en
GET alternative for transcript

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload

# Test
curl http://localhost:8000/health
curl -X POST http://localhost:8000/transcript \
  -H "Content-Type: application/json" \
  -d '{"video_id":"dQw4w9WgXcQ"}'
```

## Railway Deployment

1. Push code to GitHub
2. Create Railway account (https://railway.app)
3. Deploy from GitHub repo
4. Railway auto-detects Dockerfile
5. Get public URL

## Deployment

See: `../plan.md` - Tasks 2 & 3
