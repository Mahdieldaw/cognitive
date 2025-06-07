
import React, { useState } from 'react';
import { Workflow, WorkflowStep, JobStatus, ApiError } from '../../types';
import Card from '../common/Card';
import StatusBadge from '../common/StatusBadge';
import WorkflowStepItem from './WorkflowStepItem';
import DAGView from './DAGView';
import Button from '../common/Button';
import Modal from '../common/Modal';
import { ArrowPathIcon, DocumentDuplicateIcon } from '../../constants';
import { createWorkflowBranch } from '../../services/orchestratorService';
import { useNavigate, Link } from 'react-router-dom';

interface WorkflowDetailProps {
  workflow: Workflow;
  onRefresh: () => void;
}

const WorkflowDetail: React.FC<WorkflowDetailProps> = ({ workflow, onRefresh }) => {
  const [isBranchModalOpen, setIsBranchModalOpen] = useState(false);
  const [branchName, setBranchName] = useState(`${workflow.name} Branch`);
  const [branchingError, setBranchingError] = useState<string | null>(null);
  const [isBranching, setIsBranching] = useState(false);
  const navigate = useNavigate();

  const handleOpenBranchModal = () => {
    setBranchName(`${workflow.name} Branch ${ (workflow.branches?.length || 0) + 1}`);
    setBranchingError(null);
    setIsBranchModalOpen(true);
  };

  const handleCreateBranch = async () => {
    if (!branchName.trim()) {
      setBranchingError("Branch name cannot be empty.");
      return;
    }
    setIsBranching(true);
    setBranchingError(null);
    try {
      const result = await createWorkflowBranch(workflow.id, branchName);
      setIsBranchModalOpen(false);
      // Optionally navigate to the new branch or show a success message
      navigate(`/workflows/${result.newWorkflowId}`);
      // Or: onRefresh(); // if staying on the same page makes sense
    } catch (err) {
      const apiError = err as ApiError;
      setBranchingError(apiError.message || 'Failed to create branch.');
      console.error(err);
    } finally {
      setIsBranching(false);
    }
  };
  
  const TABS = ['Steps', 'Details', 'Metrics', 'DAG'];
  const [activeTab, setActiveTab] = useState(TABS[0]);


  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-100 truncate" title={workflow.name}>{workflow.name}</h1>
          <p className="text-sm text-gray-400">ID: {workflow.id}</p>
          {workflow.parentId && (
            <p className="text-sm text-sky-400">
              Branched from: <Button variant="outline" size="sm" onClick={() => navigate(`/workflows/${workflow.parentId}`)}>{workflow.parentId}</Button>
            </p>
          )}
        </div>
        <div className="flex space-x-2 mt-2 sm:mt-0">
          <Button onClick={onRefresh} variant="outline" leftIcon={<ArrowPathIcon className="w-4 h-4"/>} size="sm">
            Refresh
          </Button>
          <Button onClick={handleOpenBranchModal} variant="secondary" leftIcon={<DocumentDuplicateIcon className="w-4 h-4"/>} size="sm">
            Branch
          </Button>
        </div>
      </div>

      <Card>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div><span className="font-semibold">Status:</span> <StatusBadge status={workflow.status} /></div>
          <div><span className="font-semibold">Created:</span> {new Date(workflow.createdAt).toLocaleString()}</div>
          <div><span className="font-semibold">Last Updated:</span> {new Date(workflow.updatedAt).toLocaleString()}</div>
        </div>
        {workflow.description && <p className="mt-2 text-gray-300">{workflow.description}</p>}
         {typeof workflow.progress === 'number' && (
          <div className="mt-4">
            <div className="flex justify-between mb-1">
                <span className="text-base font-medium text-sky-400">Progress</span>
                <span className="text-sm font-medium text-sky-400">{workflow.progress}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2.5">
                <div className="bg-sky-600 h-2.5 rounded-full" style={{width: `${workflow.progress}%`}}></div>
            </div>
          </div>
        )}
      </Card>

      <div className="border-b border-gray-700">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${activeTab === tab
                  ? 'border-sky-500 text-sky-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-500'
                }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>
      
      {activeTab === 'Steps' && (
        <Card title="Workflow Steps">
            {workflow.steps.length > 0 ? (
            <div className="space-y-4">
                {workflow.steps.map(step => (
                <WorkflowStepItem key={step.id} step={step} allSteps={workflow.steps} />
                ))}
            </div>
            ) : (
            <p className="text-gray-400">No steps defined for this workflow.</p>
            )}
        </Card>
      )}

      {activeTab === 'Details' && (
        <Card title="Workflow Details">
          <div className="space-y-2 text-sm">
            <p><strong>ID:</strong> {workflow.id}</p>
            <p><strong>Name:</strong> {workflow.name}</p>
            <p><strong>Status:</strong> {workflow.status}</p>
            <p><strong>Description:</strong> {workflow.description || 'N/A'}</p>
            <p><strong>Tags:</strong> {workflow.tags?.join(', ') || 'N/A'}</p>
            <p><strong>Created At:</strong> {new Date(workflow.createdAt).toLocaleString()}</p>
            <p><strong>Updated At:</strong> {new Date(workflow.updatedAt).toLocaleString()}</p>
            {workflow.parentId && <p><strong>Parent Workflow ID:</strong> <Link to={`/workflows/${workflow.parentId}`} className="text-sky-400 hover:underline">{workflow.parentId}</Link></p>}
            {workflow.branches && workflow.branches.length > 0 && (
              <div>
                <strong>Branches:</strong>
                <ul className="list-disc list-inside ml-4">
                  {workflow.branches.map(branch => (
                    <li key={branch.id}><Link to={`/workflows/${branch.id}`} className="text-sky-400 hover:underline">{branch.name} ({branch.id})</Link></li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Card>
      )}

      {activeTab === 'Metrics' && (
        <Card title="Workflow Metrics">
          {workflow.metrics ? (
            <div className="space-y-2 text-sm">
              <p><strong>Total Tokens:</strong> {workflow.metrics.totalTokens?.toLocaleString() || 'N/A'}</p>
              <p><strong>Total Execution Time:</strong> {workflow.metrics.totalTimeSec ? `${workflow.metrics.totalTimeSec.toLocaleString()} seconds` : 'N/A'}</p>
              <p><strong>Estimated Cost:</strong> {workflow.metrics.totalCost ? `$${workflow.metrics.totalCost.toFixed(4)}` : 'N/A'}</p>
            </div>
          ) : (
            <p className="text-gray-400">No aggregate metrics available for this workflow.</p>
          )}
        </Card>
      )}
      
      {activeTab === 'DAG' && (
         <Card title="Workflow DAG">
           <DAGView steps={workflow.steps} />
         </Card>
      )}


      <Modal isOpen={isBranchModalOpen} onClose={() => setIsBranchModalOpen(false)} title="Create Workflow Branch">
        <div className="space-y-4">
          <p className="text-sm text-gray-300">
            Create a new branch from workflow: <span className="font-semibold">{workflow.name}</span>.
            This will create a copy of the workflow structure that can be run independently.
          </p>
          <div>
            <label htmlFor="branchName" className="block text-sm font-medium text-gray-300">Branch Name</label>
            <input
              type="text"
              id="branchName"
              value={branchName}
              onChange={(e) => setBranchName(e.target.value)}
              className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-sky-500 focus:border-sky-500 sm:text-sm text-gray-100"
            />
          </div>
          {branchingError && <p className="text-sm text-red-500">{branchingError}</p>}
        </div>
        <div className="pt-4 flex justify-end space-x-3">
            <Button variant="outline" onClick={() => setIsBranchModalOpen(false)} disabled={isBranching}>Cancel</Button>
            <Button variant="primary" onClick={handleCreateBranch} isLoading={isBranching} disabled={!branchName.trim()}>Create Branch</Button>
        </div>
      </Modal>

    </div>
  );
};

export default WorkflowDetail;
