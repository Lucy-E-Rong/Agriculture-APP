# FarmScout Mobile

Cross-platform Expo app for iOS and Android.

## Screens

- Dashboard
- Crops
- Scan
- Locations
- Reports
- Settings

## Language

Default language is English. Users can switch to Simplified Chinese in Settings.

## AI Provider

The Scan screen can request either:

- Gemini Developer API (default)
- Local GPU VLM provider

The mobile app calls only the FastAPI backend. It does not call the VLM server directly.
