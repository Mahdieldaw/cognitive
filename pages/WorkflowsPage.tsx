// pages/WorkflowsPage.tsx

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Workflow } from '../types';
import { getWorkflows } from '../services/orchestratorService';
import WorkflowListItem from '../components/workflows/WorkflowListItem';
import Spinner from '../components/common/Spinner';
import Button from '../components/common/Button';
import { PlusCircleIcon } from '../constants';

// This is a placeholder icon, ensure it's defined or imported correctly.
const FolderIcon: React.FC<{className?: string}> = ({ className = "w-6 h-6" }) => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z" />
    </svg>
);

const WorkflowsPage: React.FC = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  // This useEffect hook is responsible for fetching the data.
  useEffect(() => {
    // Define an async function inside the effect to call the service.
    const fetchWorkflows = async () => {
      try {
        // Explicitly set loading to true at the start of the fetch.
        setIsLoading(true);
        setError(null); // Clear previous errors

        console.log("WorkflowsPage: Attempting to fetch workflows...");
        const data = await getWorkflows();
        console.log("WorkflowsPage: Successfully fetched data:", data);

        setWorkflows(data);
      } catch (err: any) {
        console.error("WorkflowsPage: Failed to fetch workflows.", err);
        setError(err.message || 'An unknown error occurred.');
      } finally {
        // This will run whether the fetch succeeded or failed.
        setIsLoading(false);
      }
    };

    fetchWorkflows();
  }, []); // The empty dependency array [] means this runs only once when the component mounts.

  const handleCreateWorkflow = () => {
    navigate('/templates');
  };

  if (isLoading) {
    return <div className="flex justify-center items-center h-full"><Spinner message="Loading workflows..." /></div>;
  }

  if (error) {
    return <div className="text-red-500 p-4">Error: {error}</div>;
  }

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
              <h3 className="mt-2 text-sm font-medium text-gray-200">No Workflows Found</h3>
              <p className="mt-1 text-sm text-gray-400">The backend returned no workflows. Try creating one or check the backend status.</p>
              <div className="mt-6">
                <Button onClick={handleCreateWorkflow} variant="primary" leftIcon={<PlusCircleIcon />}>
                  Create from Template
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

export default WorkflowsPage;