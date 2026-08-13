# FarmScout Mobile and Web Demo

Cross-platform Expo app for iOS, Android, and the browser.

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

## Backend URL

By default, the app connects to the production backend at
`https://agriculture-app-green.vercel.app`.

For local development, override it before starting Expo:

```bash
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000 npm run start
```

## Web Demo

Build the static browser version with:

```bash
npx expo export --platform web
```

Deploy the generated `dist` directory. The private demo asks for an access code,
which is verified by the backend through `DEMO_ACCESS_CODE`; do not store that
code in this repository.
