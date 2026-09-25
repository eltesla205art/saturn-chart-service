# Where Is Saturn? — Chart Service

Draws full birth-chart wheels (SVG) for [whereismysaturn.com](https://whereismysaturn.com)
using [Kerykeion](https://github.com/g-battaglia/kerykeion).

**License: AGPL-3.0.** This repository is the complete, corresponding source of the
chart service running at `https://chart.whereismysaturn.com`, published to meet the
AGPL's network-use terms. The rest of whereismysaturn.com calculates Saturn in the
visitor's browser; only the optional chart wheel uses this service.

## API

`POST /api/chart` with a JSON body:

```json
{
  "date": "1990-05-15",
  "time": "14:30",
  "lat": 28.0836,
  "lon": -80.6081,
  "tz": "America/New_York",
  "place": "Melbourne, FL, USA",
  "zodiac": "tropical",
  "ayanamsa": "LAHIRI"
}
```

Returns `image/svg+xml`. `zodiac` may be `tropical` (default) or `sidereal`; `ayanamsa`
(`LAHIRI`, `RAMAN`, `KRISHNAMURTI`) applies to sidereal charts. `GET /api/chart` returns
service info.

## Privacy

Birth data is used in memory to draw one chart and is never stored or logged. Data is
sent in the request body (never in URLs), responses are `Cache-Control: no-store`, and
CORS only admits whereismysaturn.com.

## Run locally

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m http.server  # static page; for the API use `vercel dev`
```

## Deploy

```bash
npx vercel deploy --prod
```

Environment: `SOURCE_URL` (this repo's URL), optional `ALLOWED_ORIGINS` (comma list).
