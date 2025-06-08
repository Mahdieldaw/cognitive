// services/orchestratorService.ts

import { 
  Workflow, 
  DashboardSummaryData, 
  WorkflowTemplate, 
  ApiError 
} from '../types';

// The REAL URL of your Python backend
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// A helper function to handle API responses and errors
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `API Error: ${response.status} ${response.statusText}`;
    try {
      const errorData: ApiError = await response.json();
      errorMessage = errorData.message || errorMessage;
    } catch (e) {
      // The response body was not valid JSON, use the status text.
    }
    throw new Error(errorMessage);
  }
  return await response.json() as T;
}

// --- REAL API IMPLEMENTATIONS ---

export const getWorkflows = async (): Promise<Workflow[]> => {
  const response = await fetch(`${API_BASE_URL}/workflows`);
  return handleResponse<Workflow[]>(response);
};

export const getWorkflowById = async (id: string): Promise<Workflow | undefined> => {
  const response = await fetch(`${API_BASE_URL}/workflows/${id}`);
  // A 404 from the backend is a valid case (workflow not found), not an error.
  if (response.status === 404) {
    return undefined;
  }
  return handleResponse<Workflow>(response);
};

export const createWorkflowBranch = async (
  workflowId: string, 
  branchName: string
): Promise<Workflow> => { // The backend now returns the full new workflow object
  const response = await fetch(`${API_BASE_URL}/workflows/${workflowId}/branch`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    // The body must match what the Python endpoint expects
    body: JSON.stringify({ branch_name: branchName }), 
  });
  return handleResponse<Workflow>(response);
};


// --- PLACEHOLDER IMPLEMENTATIONS ---
// These functions need their corresponding backend endpoints to be built.
// For now, they return empty/default data to prevent the UI from crashing.

export const getDashboardSummary = async (): Promise<DashboardSummaryData> => {
  console.warn("getDashboardSummary is using placeholder data. Backend endpoint not implemented.");
  // In the future, this would be:
  // const response = await fetch(`${API_BASE_URL}/dashboard/summary`);
  // return handleResponse<DashboardSummaryData>(response);
  return {
    totalWorkflows: 0,
    activeWorkflows: 0,
    completedWorkflows: 0,
    failedWorkflows: 0,
    statusDistribution: [],
    recentActivity: [],
  };
};

export const getWorkflowTemplates = async (): Promise<WorkflowTemplate[]> => {
  console.warn("getWorkflowTemplates is using placeholder data. Backend endpoint not implemented.");
  // In the future, this would be:
  // const response = await fetch(`${API_BASE_URL}/templates`);
  // return handleResponse<WorkflowTemplate[]>(response);
  return [];
};

export const createWorkflowFromTemplate = async (
  templateId: string, 
  params: Record<string, any>
): Promise<Workflow> => {
  console.warn("createWorkflowFromTemplate is using placeholder data. Backend endpoint not implemented.");
  // In the future, this would be:
  // const response = await fetch(`${API_BASE_URL}/workflows/from-template`, {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify({ template_id: templateId, params: params })
  // });
  // return handleResponse<Workflow>(response);
  
  // Return a dummy object to prevent UI crash
  throw new Error("Creating workflows from templates via the UI is not yet connected to the backend.");
};