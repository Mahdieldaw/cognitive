
import React, { useEffect, useState } from 'react';
import { Workflow } from '../types';
import { getWorkflows } from '../services/orchestratorService';
import WorkflowListItem from '../components/workflows/WorkflowListItem';
import Spinner from '../components/common/Spinner';
import Button from '../components/common/Button';
import { PlusCircleIcon } from '../constants';
import { useNavigate } from 'react-router-dom';

const WorkflowsPage: React.FC = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchWorkflows = async () => {
      try {
        setIsLoading(true);
        const data = await getWorkflows();
        setWorkflows(data);
      } catch (err) {
        setError('Failed to load workflows.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchWorkflows();
  }, []);

  const handleCreateWorkflow = () => {
    navigate('/templates'); // Navigate to templates page to create new workflow
  };

  if (isLoading) return <div className="flex justify-center items-center h-full"><Spinner message="Loading workflows..." /></div>;
  if (error) return <div className="text-red-500 p-4">{error}</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-100">Workflows</h1>
        <Button onClick={handleCreateWorkflow} variant="primary" leftIcon={<PlusCircleIcon />}>
          New Workflow
        </Button>
      </div>

      {workflows.length === 0 ? (
        <div className="text-center py-10">
          <FolderIcon className="mx-auto h-12 w-12 text-gray-500" />
          <h3 className="mt-2 text-sm font-medium text-gray-200">No workflows</h3>
          <p className="mt-1 text-sm text-gray-400">Get started by creating a new workflow.</p>
          <div className="mt-6">
            <Button onClick={handleCreateWorkflow} variant="primary" leftIcon={<PlusCircleIcon />}>
              New Workflow
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workflows.map(workflow => (
            <WorkflowListItem key={workflow.id} workflow={workflow} />
          ))}
        </div>
      )}
    </div>
  );
};

// Placeholder for FolderIcon if not already in constants.tsx
const FolderIcon: React.FC<{className?: string}> = ({ className = "w-6 h-6" }) => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z" />
    </svg>
);


export default WorkflowsPage;
