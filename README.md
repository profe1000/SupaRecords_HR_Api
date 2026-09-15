# supaRecords_Hotel_Management_addons__python_api

Minimal FastAPI + SQLAlchemy + Alembic + Redis scaffold for the hotel booking
database model described in the issue.

## Requirements

- Python 3.11+

## Install

```bash
pip install -r requirements.txt
```

## Run the API

```bash
uvicorn app.main:app --reload
```

## Run migrations

```bash
alembic upgrade head
```

## Run tests

```bash
python -m unittest discover -s tests
```

## Realtime / Apinator

This project includes a small realtime helper endpoint that can publish server-side events to Apinator.

- Endpoint: `POST /misc/broadcast/apinator`
- Payload: JSON with keys `name`, `channel`, and `data` (data can be an object)

Example payload:

```json
{
	"name": "message",
	"channel": "chat-room",
	"data": { "text": "Hello from Python!" }
}
```

Environment variables (recommended):

- `APINATOR_APP_ID` — your Apinator app id
- `APINATOR_KEY` — your Apinator API key
- `APINATOR_SECRET` — your Apinator secret
- `APINATOR_CLUSTER` — cluster (default: `us`)

Install the SDK from the Apinator GitHub repo into your virtualenv:

```bash
python -m pip install git+https://github.com/apinator-io/sdk-python.git
```

Trigger example (curl):

```bash
curl -X POST "http://localhost:8000/misc/broadcast/apinator" \
	-H "Content-Type: application/json" \
	-d '{"name":"message","channel":"chat-room","data":{"text":"Hello from Python!"}}'
```

