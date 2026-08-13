# FarmScout Backend

FastAPI backend for mobile clients and AI scan analysis.

## AI Providers

`POST /api/scans/analyze` accepts:

```json
{
  "provider": "gemini",
  "language": "en",
  "imageBase64": "...",
  "imageMimeType": "image/jpeg",
  "cropId": "crop-id",
  "greenhouseId": "greenhouse-id",
  "sectionId": "section-id",
  "tableId": "table-id",
  "rowId": "row-id"
}
```

Provider options:

- `gemini`: calls the Gemini Developer API using `GEMINI_API_KEY` and `GEMINI_MODEL`.
- `api_provider`: uses OpenAI when `OPENAI_API_KEY` is set, Anthropic when `ANTHROPIC_API_KEY` is set, otherwise a mock response.
- `local_vlm`: calls `LOCAL_VLM_URL`, expected to return the same JSON response schema.
- `mock`: always returns a deterministic sample response for local UI development.

## Gemini setup

Copy `.env.example` to `.env`, then set the key only in the backend environment:

```env
GEMINI_API_KEY=your-key-from-google-ai-studio
GEMINI_MODEL=gemini-3.6-flash
```

Never add the key to `mobile/.env` or commit `backend/.env`.

## Deploy to Vercel

Import the GitHub repository in Vercel and set the project's Root Directory to
`backend`. The included `vercel.json` pins the FastAPI function to the
Washington, D.C. region (`iad1`). Configure these Vercel environment variables:

```env
APP_ENV=production
GEMINI_API_KEY=your-current-key
GEMINI_MODEL=gemini-3.6-flash
```

## Response

```json
{
  "crop_is_lettuce": true,
  "crop_confidence": 0.96,
  "image_quality": {
    "usable": true,
    "issues": [],
    "retake_guidance": []
  },
  "plant_stress_detected": true,
  "stress_level": "medium",
  "severity_score": 3,
  "confidence": 0.74,
  "diagnosis": "string",
  "observed_symptoms": [],
  "possible_causes": [],
  "detected_issues": ["string"],
  "recommendations": ["string"],
  "needs_human_review": true
}
```
