
# Hybrid Engine Architecture

This document outlines the architecture of the Hybrid Engine system, of which this dashboard is a key component. The Hybrid Engine is designed to be a local-first, event-driven system that transforms a user's knowledge base into an active, intelligent partner.

## Core Layers

The Hybrid Engine comprises three main layers:

1.  **The Knowledge Layer (Obsidian Vault):**
    *   **Description**: The user's Obsidian vault acts as the single source of truth. It's a structured, file-based database.
    *   **Function**:
        *   Defines workflows (e.g., via Markdown files with frontmatter).
        *   Stores inputs for workflows.
        *   Archives all intermediate and final results of workflow execution.
        *   Serves as a primary interface for initiating and reviewing work (though the dashboard provides an alternative, focused view).
    *   **Interaction**: The Orchestration Layer reads workflow definitions and data from the vault and writes results back to it.

2.  **The Orchestration Layer (Local Python Server):**
    *   **Description**: A local Python server (e.g., FastAPI or Flask) acts as the central nervous system.
    *   **Key Components**:
        *   **File-Backed Job Queue (`memory_queue.py`)**: Manages tasks to be executed. It's persistent (e.g., `queue-state.json`) for resilience.
        *   **Workflow Engine (`worker.py`, DAGs)**: Executes workflows, which are often Directed Acyclic Graphs (DAGs) of steps. It handles dependencies between steps.
        *   **State Management (`state_manager.py`)**: Tracks the status of each workflow and its individual steps (e.g., in a `state.json` file per workflow).
        *   **Context Management (`context_manager.py`)**: Allows data and outputs from one step or workflow to be used in subsequent steps or branched workflows. Supports workflow branching (`shutil.copytree`).
        *   **Model Adapters (`adapters/base_adapter.py` and implementations)**: A pluggable system for interacting with various AI models (local or API-based, like Gemini).
        *   **Recovery Manager (`recovery_manager.py`)**: Identifies and potentially resumes interrupted workflows.
        *   **Vault Service (`services/vault_service.py`)**: Provides an abstraction for file system operations within the knowledge layer (e.g., user's vault).
        *   **REST API (`app.py`)**: Exposes endpoints for the frontend (this dashboard) and potentially other clients (like the Chrome Extension) to interact with the orchestrator (e.g., get workflows, start workflows, create branches).
    *   **Principles**: Event-driven, asynchronous (using Python's `async/await`), stateful, persistent, resilient.

3.  **The Access Layer (Adapters & Frontend UI/Extension):**
    *   **Description**: Provides interfaces for users and the system to interact with AI models and external data.
    *   **Components**:
        *   **Dynamic Adapters (Python)**: Python classes that implement the `ModelAdapter` interface to communicate with specific LLMs (e.g., Gemini API, OpenAI API, local models).
        *   **Hybrid Engine Dashboard (This Web Application)**: A React-based web UI that communicates with the Orchestration Layer's REST API. It allows users to:
            *   Monitor workflow status.
            *   View workflow details, steps, and outputs.
            *   Initiate new workflows from templates.
            *   Manage workflow branches.
        *   **Browser Integration (Chrome Extension - Long-term Vision)**: A JavaScript-based Chrome extension that communicates with the Python Orchestrator via its REST API. It would act as a "robot arm" for:
            *   Sending web page content (e.g., selected text, chat logs) to the orchestrator as input for workflows.
            *   Potentially displaying notifications or quick actions related to the Hybrid Engine.

## Data Flow & Communication

*   **Workflow Initiation**:
    1.  User defines a workflow in their Obsidian vault or selects a template via the Dashboard.
    2.  If via Dashboard, a request is sent to the Orchestrator's API to start the workflow (e.g., `POST /workflows/from-template`).
    3.  The Orchestrator adds the job to its queue.
*   **Workflow Execution**:
    1.  The `Worker` process picks up jobs from the queue.
    2.  It validates the workflow DAG (`dag_validator.py`).
    3.  For each step, it:
        *   Checks dependencies.
        *   Calls the appropriate `ModelAdapter` (e.g., to query an LLM like Gemini).
        *   Updates the step's status via the `StateManager`.
        *   Saves outputs to the vault via `VaultService`.
*   **Dashboard Interaction**:
    1.  The Dashboard (React app) makes API calls to the Orchestrator (e.g., `GET /workflows`, `GET /workflows/{id}`).
    2.  The Orchestrator's API handlers retrieve data (from `StateManager`, `VaultService`, etc.) and return it as JSON.
    3.  The Dashboard displays this information.
*   **Chrome Extension (Future)**:
    1.  User interacts with a web page (e.g., right-clicks, selects text).
    2.  The extension's `content_script.js` extracts data.
    3.  The `background.js` sends this data via `fetch` to a specific endpoint on the Python Orchestrator's API (e.g., `POST /workflow/add-external-step`).
    4.  The Orchestrator processes this external input, potentially creating a new step in a workflow or a new workflow.

## Key Architectural Principles

*   **Workflow as First-Class Citizen**: Every execution is a job with a unique `workflowId`.
*   **Event-Driven & Asynchronous**: Leverages Python's `async/await` and potentially threading for non-blocking operations.
*   **Stateful & Persistent**: All significant events and outputs are persisted, primarily in the file system (Obsidian vault, queue state, workflow states).
*   **Resilient & Recoverable**: Designed to handle failures and resume, with file-based state aiding recovery.
*   **Evolvable & Composable**: Workflows can be branched and chained.
*   **Local-First & Secure**: Core engine runs locally, prioritizing user data control.

This architecture aims to create a powerful, integrated system for complex cognitive work, bridging the gap between passive knowledge storage and active AI-driven processing.
