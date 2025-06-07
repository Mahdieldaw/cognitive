
# Hybrid Engine - API Integration (Frontend Perspective)

This document describes how the Hybrid Engine Dashboard (frontend) interacts with the Hybrid Engine Orchestrator (Python backend) via its REST API. For the current version of the dashboard, API interactions are simulated by the `orchestratorService.ts` file.

## 1. Core Principles

*   **RESTful API**: The backend exposes RESTful endpoints for CRUD-like operations on resources like workflows and templates, as well as actions like creating branches.
*   **JSON**: Data is exchanged in JSON format.
*   **Asynchronous Communication**: The frontend makes asynchronous HTTP requests (e.g., using `fetch` or a library like Axios, though currently mocked) to the backend.

## 2. Key Endpoints (Conceptual / Mocked)

The `services/orchestratorService.ts` file currently mocks the behavior of these conceptual endpoints.

*   **Dashboard Summary**:
    *   `GET /api/dashboard/summary` (Mocked by `getDashboardSummary()`)
    *   **Purpose**: Fetches aggregate data for the dashboard overview (total workflows, status distribution, recent activity).
    *   **Response**: `DashboardSummaryData` object.

*   **Workflows**:
    *   `GET /api/workflows` (Mocked by `getWorkflows()`)
        *   **Purpose**: Retrieves a list of all workflows.
        *   **Response**: Array of `Workflow` objects.
    *   `GET /api/workflows/{workflowId}` (Mocked by `getWorkflowById(id)`)
        *   **Purpose**: Fetches details for a specific workflow.
        *   **Response**: A single `Workflow` object or a 404 if not found.
    *   `POST /api/workflows/from-template` (Mocked by `createWorkflowFromTemplate(templateId, params)`)
        *   **Purpose**: Creates a new workflow instance from a specified template and parameters.
        *   **Request Body**: `{ templateId: string, parameters: Record<string, any> }`
        *   **Response**: The newly created `Workflow` object.
    *   `POST /api/workflows/{workflowId}/branch` (Mocked by `createWorkflowBranch(workflowId, branchName)`)
        *   **Purpose**: Creates a new branch from an existing workflow.
        *   **Request Body**: `{ branchName: string }`
        *   **Response**: An object containing IDs, e.g., `{ workflowId, branchName, newWorkflowId }`.

*   **Workflow Templates**:
    *   `GET /api/templates` (Mocked by `getWorkflowTemplates()`)
        *   **Purpose**: Retrieves a list of available workflow templates.
        *   **Response**: Array of `WorkflowTemplate` objects.

*   **External Step Ingestion (for Chrome Extension integration - as per project brief)**:
    *   `POST /api/workflow/add-external-step` (Conceptual, mocked in Python `app.py` in the brief)
        *   **Purpose**: Allows an external source (like the Chrome extension) to send content to be added as a step or input to a workflow.
        *   **Request Body**: `{ workflowId: string, externalContent: any }` (content could be text, structured data, etc.)
        *   **Response**: Status confirmation, e.g., `{ status: "success", stepId: "new_step_id" }`.

## 3. Data Types

The interactions rely on shared data structures defined in `types.ts`. Key types include:
*   `Workflow`
*   `WorkflowStep`
*   `JobStatus` (Enum)
*   `WorkflowTemplate`
*   `DashboardSummaryData`
*   `ApiError`

## 4. Error Handling

*   The frontend should gracefully handle API errors.
*   When an API call fails (e.g., network error, 4xx/5xx HTTP status codes), the service functions (in `orchestratorService.ts`) are expected to throw an error or return a rejected Promise.
*   The UI components then catch these errors and display appropriate messages to the user (e.g., "Failed to load workflows.").
*   The `ApiError` type can be used to pass structured error information from the (mocked) service layer.

## 5. State Management in Frontend

*   React's `useState` and `useEffect` hooks are primarily used to manage the state derived from API calls (e.g., lists of workflows, details of a specific workflow).
*   Loading states (`isLoading`) are maintained to provide user feedback during API calls.
*   Error states (`error`) store error messages for display.

## 6. Future Considerations (Real API)

When moving from a mocked service to a real API:

*   **Actual HTTP Requests**: Replace mock function calls with `fetch` or a library like `axios`.
*   **Environment Configuration**: The `API_BASE_URL` (currently in `constants.tsx`) would point to the actual backend server and might be configured via environment variables.
*   **Authentication/Authorization**: If the API requires authentication, mechanisms for handling tokens (e.g., JWT) would need to be implemented (storing tokens, adding them to request headers).
*   **CORS**: The backend server would need to be configured for Cross-Origin Resource Sharing (CORS) to allow requests from the dashboard's domain.
*   **More Sophisticated State Management**: For larger applications, libraries like Redux Toolkit, Zustand, or React Query could be considered for managing server state, caching, and optimistic updates. React Query is particularly well-suited for handling server state.
*   **Real-time Updates**: For live updates of workflow statuses, technologies like WebSockets or Server-Sent Events (SSE) could be integrated, or polling strategies implemented. The `simulateStepCompletion` function in the mock service hints at this.

The current `orchestratorService.ts` provides a solid foundation by defining the expected API contract from the frontend's perspective, making the transition to a real backend more straightforward.
