
export enum JobStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  WAITING_FOR_DEPENDENCY = 'WAITING_FOR_DEPENDENCY',
  STOPPED = 'STOPPED', // Added for workflows halted due to on_failure: stop_workflow
}

export interface WorkflowStep {
  id: string;
  name: string; // More user-friendly than just 'action'
  action: string;
  status: JobStatus;
  dependencies: string[];
  outputs?: Record<string, any>;
  error?: string;
  startTime?: string; // ISO 8601 string
  endTime?: string; // ISO 8601 string
  duration?: string; // Human-readable duration
  logs?: string[]; // Array of log messages
  metadata?: {
    tokens?: number;
    time_sec?: number;
    cost?: number; // Example: cost in USD
  };
}

export interface Workflow {
  id:string;
  name: string;
  status: JobStatus;
  steps: WorkflowStep[];
  createdAt: string; // ISO 8601 string
  updatedAt: string; // ISO 8601 string
  description?: string;
  tags?: string[];
  progress?: number; // Percentage 0-100
  parentId?: string; 
  branches?: { id: string, name: string }[];
  metrics?: {
    totalTokens?: number;
    totalTimeSec?: number;
    totalCost?: number;
  }
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category?: string;
  version?: string;
  estimatedDuration?: string; // e.g., "5-10 minutes"
  // Structure of steps or parameters needed to initiate workflow
  parameters?: { name: string; type: 'string' | 'number' | 'boolean'; defaultValue?: any; description?: string }[];
}

export interface DashboardSummaryData {
  totalWorkflows: number;
  activeWorkflows: number;
  completedWorkflows: number;
  failedWorkflows: number;
  statusDistribution: { status: JobStatus; count: number }[];
  recentActivity: Workflow[]; // Last 5-10 workflows
}

export interface ApiError {
  message: string;
  statusCode?: number;
}
