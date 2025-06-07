
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Workflow } from '../types';
import { getWorkflowById } from '../services/orchestratorService';
import WorkflowDetail from '../components/workflows/WorkflowDetail';
import Spinner from '../components/common/Spinner';
import Button from '../components/common/Button';

const WorkflowDetailPageRouter: React.FC = () => {
  const { workflowId } = useParams<{ workflowId: string }>();
  const navigate = useNavigate();
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!workflowId) {
      setError('Workflow ID is missing.');
      setIsLoading(false);
      return;
    }

    const fetchWorkflow = async () => {
      try {
        setIsLoading(true);
        const data = await getWorkflowById(workflowId);
        if (data) {
          setWorkflow(data);
        } else {
          setError(`Workflow with ID ${workflowId} not found.`);
        }
      } catch (err) {
        setError('Failed to load workflow details.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchWorkflow();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workflowId]); // Re-fetch if workflowId changes

  const handleRefresh = async () => {
    if (!workflowId) return;
    try {
        setIsLoading(true);
        setError(null);
        const data = await getWorkflowById(workflowId);
        if (data) {
          setWorkflow(data);
        } else {
          setError(`Workflow with ID ${workflowId} not found.`);
        }
      } catch (err) {
        setError('Failed to refresh workflow details.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
  };


  if (isLoading) return <div className="flex justify-center items-center h-full"><Spinner message="Loading workflow details..." /></div>;
  
  if (error) return (
    <div className="text-center p-10">
        <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-500" />
        <h3 className="mt-2 text-lg font-medium text-red-400">{error}</h3>
        <p className="mt-1 text-sm text-gray-400">Please check the workflow ID or try again later.</p>
        <div className="mt-6 space-x-3">
            <Button onClick={() => navigate('/workflows')} variant="outline">Go to Workflows</Button>
            <Button onClick={handleRefresh} variant="primary">Try Again</Button>
        </div>
    </div>
  );
  
  if (!workflow) return <div className="text-gray-400 p-4">Workflow data is unexpectedly missing.</div>; // Should be covered by error state

  return <WorkflowDetail workflow={workflow} onRefresh={handleRefresh} />;
};

// Placeholder for ExclamationTriangleIcon if not already in constants.tsx
const ExclamationTriangleIcon: React.FC<{className?: string}> = ({ className = "w-5 h-5" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
  </svg>
);

export default WorkflowDetailPageRouter;
