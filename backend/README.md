# Hybrid Engine Backend

A resilient, local-first Python backend that executes workflows through a file-based queue system with persistent state management.

## Features

- **Local-First Architecture**: All workflow state persisted to local filesystem
- **File-Based Queue**: Resilient job queue that survives restarts
- **Background Worker**: Asynchronous workflow execution
- **REST API**: FastAPI-based endpoints for workflow management
- **Progress Tracking**: Real-time workflow and step progress monitoring
- **Error Recovery**: Comprehensive error handling and logging

## Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the server:
```bash
uvicorn app:app --reload
```

3. Access the API:
- Health check: http://127.0.0.1:8000/api/health
- API docs: http://127.0.0.1:8000/docs
- Interactive docs: http://127.0.0.1:8000/redoc

## API Endpoints

### Health Check
```
GET /api/health
```

### Workflows
```
GET /api/workflows              # List all workflows
GET /api/workflows/{id}         # Get specific workflow
POST /api/workflows/from-template  # Create workflow from template
```

### Example Usage

#### Create a Workflow
```bash
curl -X POST "http://127.0.0.1:8000/api/workflows/from-template?template_id=data_processing&params={}" \
  -H "Content-Type: application/json"
```

#### List Workflows
```bash
curl "http://127.0.0.1:8000/api/workflows"
```

## Architecture

### Components

- **FastAPI App** (`app.py`): REST API server with lifecycle management
- **Worker** (`worker.py`): Background job processor
- **State Manager** (`services/state_manager.py`): Persistent workflow state
- **Queue Service** (`services/queue_service.py`): File-based job queue
- **Models** (`models/workflow.py`): Pydantic data models

### Data Flow

1. Client creates workflow via POST `/api/workflows/from-template`
2. Workflow state saved to `workflows/{id}/state.json`
3. Initial jobs added to `queue-state.json`
4. Background worker processes jobs asynchronously
5. State updates persisted on each status change
6. Client polls workflow status via GET endpoints

### File Structure

```
backend/
├── workflows/              # Workflow state directories
│   └── {workflow-id}/
│       └── state.json      # Workflow state file
├── queue-state.json        # Job queue persistence
├── app.py                  # FastAPI application
├── worker.py               # Background worker
├── config.py               # Configuration
├── models/                 # Data models
└── services/               # Core services
```

## Configuration

Environment variables (`.env`):

- `WORKFLOWS_DIR`: Directory for workflow state (default: "workflows")
- `QUEUE_STATE_FILE`: Queue persistence file (default: "queue-state.json")
- `MAX_PARALLEL_NODES`: Max concurrent jobs (default: 4)
- `LOG_LEVEL`: Logging level (default: "INFO")

## Development

### Running in Development

```bash
# Start with auto-reload
uvicorn app:app --reload --log-level debug

# Or with custom host/port
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

### Testing

```bash
# Test health endpoint
curl http://127.0.0.1:8000/api/health

# Create test workflow
curl -X POST "http://127.0.0.1:8000/api/workflows/from-template?template_id=test&params={}" \
  -H "Content-Type: application/json"

# Monitor workflow progress
curl http://127.0.0.1:8000/api/workflows
```

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker (Optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Monitoring

- Logs: Structured logging via Loguru
- Health: `/api/health` endpoint
- Metrics: Workflow progress and status tracking
- Queue: Monitor `queue-state.json` for job backlog

## Recovery

The system is designed for resilience:

- **State Recovery**: All workflow state persisted to disk
- **Queue Recovery**: Jobs survive server restarts
- **Worker Recovery**: Background worker auto-restarts on errors
- **Error Handling**: Comprehensive error logging and status tracking