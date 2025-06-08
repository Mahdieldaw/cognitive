import { Workflow, WorkflowStep, JobStatus, DashboardSummaryData, WorkflowTemplate, ApiError } from '../types';
import { API_BASE_URL } from '../constants';

// Simulating API delay
const MOCK_API_DELAY = 500; // ms

const mockWorkflows: Workflow[] = [
  {
    id: 'wf_001', name: 'Initial Data Analysis', status: JobStatus.COMPLETED, createdAt: new Date(Date.now() - 86400000 * 2).toISOString(), updatedAt: new Date(Date.now() - 86400000 * 2 + 3600000).toISOString(),
    description: 'Analyzes sales data from Q1 and generates a summary report.',
    tags: ['data-analysis', 'sales', 'q1-report'],
    progress: 100,
    metrics: { totalTokens: 15000, totalTimeSec: 120, totalCost: 0.075},
    steps: [
      { id: 's1', name: 'Load Data', action: 'load_data_from_source', status: JobStatus.COMPLETED, dependencies: [], startTime: new Date(Date.now() - 86400000 * 2).toISOString(), endTime: new Date(Date.now() - 86400000 * 2 + 60000).toISOString(), duration: '1 min', metadata: { time_sec: 60} },
      { id: 's2', name: 'Clean Data', action: 'clean_data_transformer', status: JobStatus.COMPLETED, dependencies: ['s1'], startTime: new Date(Date.now() - 86400000 * 2 + 60000).toISOString(), endTime: new Date(Date.now() - 86400000 * 2 + 120000).toISOString(), duration: '1 min', metadata: { time_sec: 60}  },
      { id: 's3', name: 'Generate Insights', action: 'gemini_insight_generator', status: JobStatus.COMPLETED, dependencies: ['s2'], startTime: new Date(Date.now() - 86400000 * 2 + 120000).toISOString(), endTime: new Date(Date.now() - 86400000 * 2 + 300000).toISOString(), duration: '3 mins', metadata: { tokens: 15000, time_sec: 180, cost: 0.075}  },
      { id: 's4', name: 'Create Report', action: 'report_writer_markdown', status: JobStatus.COMPLETED, dependencies: ['s3'], outputs: { "report_file": "/vault/reports/q1_sales_summary.md" }, startTime: new Date(Date.now() - 86400000 * 2 + 300000).toISOString(), endTime: new Date(Date.now() - 86400000 * 2 + 360000).toISOString(), duration: '1 min', metadata: { time_sec: 60} },
    ]
  },
  {
    id: 'wf_002', name: 'Content Generation Pipeline', status: JobStatus.RUNNING, createdAt: new Date(Date.now() - 3600000).toISOString(), updatedAt: new Date().toISOString(),
    description: 'Generates blog posts based on trending topics.',
    tags: ['content', 'blogging', 'seo'],
    progress: 66,
    metrics: { totalTokens: 5000, totalTimeSec: 180 },
    steps: [
      { id: 's1', name: 'Fetch Topics', action: 'google_search_tool', status: JobStatus.COMPLETED, dependencies: [], startTime: new Date(Date.now() - 3600000).toISOString(), endTime: new Date(Date.now() - 3540000).toISOString(), duration: '1 min', metadata: { time_sec: 60}},
      { id: 's2', name: 'Draft Article', action: 'gemini_text_model', status: JobStatus.RUNNING, dependencies: ['s1'], startTime: new Date(Date.now() - 3540000).toISOString(), metadata: { tokens: 5000, time_sec: 120 } },
      { id: 's3', name: 'Review & Edit', action: 'human_review_step', status: JobStatus.PENDING, dependencies: ['s2'] },
      { id: 's4', name: 'Publish Post', action: 'wordpress_adapter', status: JobStatus.WAITING_FOR_DEPENDENCY, dependencies: ['s3'] },
    ]
  },
  {
    id: 'wf_003', name: 'Daily System Maintenance', status: JobStatus.FAILED, createdAt: new Date(Date.now() - 86400000).toISOString(), updatedAt: new Date(Date.now() - 86400000 + 1800000).toISOString(),
    description: 'Performs daily cleanup and backup tasks.',
    tags: ['maintenance', 'backup', 'system'],
    progress: 25,
    metrics: { totalTimeSec: 30 },
    steps: [
      { id: 's1', name: 'Cleanup Temp Files', action: 'cleanup_temp_action', status: JobStatus.COMPLETED, dependencies: [], startTime: new Date(Date.now() - 86400000).toISOString(), endTime: new Date(Date.now() - 86400000 + 30000).toISOString(), duration: '30 sec', metadata: { time_sec: 30 } },
      { id: 's2', name: 'Backup Database', action: 'db_backup_script', status: JobStatus.FAILED, dependencies: ['s1'], error: 'Connection to database server timed out after 3 attempts.', startTime: new Date(Date.now() - 86400000 + 30000).toISOString(), logs: ['Attempt 1: Timeout', 'Attempt 2: Timeout', 'Attempt 3: Timeout. Marking as failed.'] },
      { id: 's3', name: 'Verify Backup', action: 'backup_verifier', status: JobStatus.PENDING, dependencies: ['s2'] },
    ],
    branches: [ {id: 'wf_003_retry1', name: 'Retry with increased timeout'}]
  },
  {
    id: 'wf_004', name: 'Image Generation Batch', status: JobStatus.PENDING, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
    description: 'Generates a batch of 10 images based on prompts.',
    tags: ['image-generation', 'batch'],
    progress: 0,
    steps: [
      { id: 's1', name: 'Load Prompts', action: 'load_prompts_from_file', status: JobStatus.PENDING, dependencies: [] },
      { id: 's2', name: 'Generate Images (Batch)', action: 'imagen_3_batch_generator', status: JobStatus.WAITING_FOR_DEPENDENCY, dependencies: ['s1'] },
      { id: 's3', name: 'Save Images', action: 'save_images_to_vault', status: JobStatus.WAITING_FOR_DEPENDENCY, dependencies: ['s2'] },
    ]
  },
];

const mockTemplates: WorkflowTemplate[] = [
  { id: 'tmpl_001', name: 'Basic Text Summarization', description: 'Summarizes a given text using an LLM.', category: 'Text Processing', estimatedDuration: '1-2 minutes', parameters: [{name: 'inputText', type: 'string', description: 'Text to summarize'}] },
  { id: 'tmpl_002', name: 'Perspective Comparison', description: 'Compares two texts from different perspectives.', category: 'Analysis', estimatedDuration: '5-10 minutes', parameters: [{name: 'textA', type: 'string', description: 'First text'}, {name: 'textB', type: 'string', description: 'Second text'}, {name: 'question', type: 'string', description: 'Question to compare against'}]},
  { id: 'tmpl_003', name: 'Image Generation (Single)', description: 'Generates a single image from a prompt.', category: 'Image Generation', estimatedDuration: '1 minute', parameters: [{name: 'prompt', type: 'string', description: 'Image prompt'}] },
];


export const getWorkflows = async (): Promise<Workflow[]> => {
  // In a real app, this would be:
  // const response = await fetch(`${API_BASE_URL}/workflows`);
  // if (!response.ok) throw new Error('Failed to fetch workflows');
  // return response.json();
  console.log('Fetching workflows from mock service...');
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(JSON.parse(JSON.stringify(mockWorkflows))); // Deep copy
    }, MOCK_API_DELAY);
  });
};

export const getWorkflowById = async (id: string): Promise<Workflow | undefined> => {
  console.log(`Fetching workflow ${id} from mock service...`);
  return new Promise((resolve) => {
    setTimeout(() => {
      const workflow = mockWorkflows.find(wf => wf.id === id);
      resolve(workflow ? JSON.parse(JSON.stringify(workflow)) : undefined);
    }, MOCK_API_DELAY);
  });
};

export const createWorkflowFromTemplate = async (templateId: string, params: Record<string, any>): Promise<Workflow> => {
  // Use real API call
  const response = await fetch(`${API_BASE_URL}/workflows/from-template`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ template_id: templateId, params }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to create workflow from template');
  }
  return response.json();
};

export const createWorkflowBranch = async (workflowId: string, branchName: string): Promise<{ workflowId: string; branchName: string; newWorkflowId: string }> => {
  console.log(`Branching workflow ${workflowId} into ${branchName}...`);
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const parentWorkflow = mockWorkflows.find(wf => wf.id === workflowId);
      if (!parentWorkflow) {
        reject({ message: `Workflow ${workflowId} not found`, statusCode: 404 } as ApiError);
        return;
      }
      const newWorkflowId = `${workflowId}_branch_${(parentWorkflow.branches?.length || 0) + 1}`;
      const branchedWorkflow: Workflow = {
        ...JSON.parse(JSON.stringify(parentWorkflow)), // Deep copy
        id: newWorkflowId,
        name: `${parentWorkflow.name} (Branch: ${branchName})`,
        parentId: workflowId,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        status: JobStatus.PENDING, // Reset status for the branch
        progress: 0,
        branches: [], // Branches don't inherit branches initially
      };
      // Reset step statuses for the new branch
      branchedWorkflow.steps = branchedWorkflow.steps.map(step => ({ ...step, status: JobStatus.PENDING, startTime: undefined, endTime: undefined, duration: undefined, outputs: undefined, error: undefined, logs: [] }));

      if (!parentWorkflow.branches) parentWorkflow.branches = [];
      parentWorkflow.branches.push({id: newWorkflowId, name: branchName});
      
      mockWorkflows.unshift(branchedWorkflow);
      resolve({ workflowId, branchName, newWorkflowId });
    }, MOCK_API_DELAY);
  });
};


export const getDashboardSummary = async (): Promise<DashboardSummaryData> => {
  console.log('Fetching dashboard summary from mock service...');
  return new Promise((resolve) => {
    setTimeout(() => {
      const statusCounts: { [key in JobStatus]?: number } = {};
      mockWorkflows.forEach(wf => {
        statusCounts[wf.status] = (statusCounts[wf.status] || 0) + 1;
      });
      
      resolve({
        totalWorkflows: mockWorkflows.length,
        activeWorkflows: mockWorkflows.filter(wf => wf.status === JobStatus.RUNNING || wf.status === JobStatus.PENDING).length,
        completedWorkflows: mockWorkflows.filter(wf => wf.status === JobStatus.COMPLETED).length,
        failedWorkflows: mockWorkflows.filter(wf => wf.status === JobStatus.FAILED || wf.status === JobStatus.STOPPED).length,
        statusDistribution: Object.entries(statusCounts).map(([status, count]) => ({ status: status as JobStatus, count: count! })),
        recentActivity: mockWorkflows.slice(0, 5).map(wf => JSON.parse(JSON.stringify(wf))),
      });
    }, MOCK_API_DELAY);
  });
};

export const getWorkflowTemplates = async (): Promise<WorkflowTemplate[]> => {
  console.log('Fetching workflow templates from mock service...');
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(JSON.parse(JSON.stringify(mockTemplates)));
    }, MOCK_API_DELAY);
  });
};

// Simulate updating a workflow (e.g. a step completes) - for potential live updates later
export const simulateStepCompletion = (workflowId: string, stepId: string) => {
  const workflow = mockWorkflows.find(wf => wf.id === workflowId);
  if (workflow) {
    const step = workflow.steps.find(s => s.id === stepId);
    if (step && step.status !== JobStatus.COMPLETED) {
      step.status = JobStatus.COMPLETED;
      step.endTime = new Date().toISOString();
      // Potentially trigger next step etc. This is simplified.
      console.log(`Mock: Step ${stepId} in workflow ${workflowId} completed.`);
    }
  }
};

