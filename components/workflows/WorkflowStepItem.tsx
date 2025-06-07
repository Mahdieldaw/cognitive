
import React, { useState } from 'react';
import { WorkflowStep, JobStatus } from '../../types';
import StatusBadge from '../common/StatusBadge';
import { ChevronDownIcon, InformationCircleIcon, ExclamationTriangleIcon, CheckCircleIcon } from '../../constants';

interface WorkflowStepItemProps {
  step: WorkflowStep;
  allSteps: WorkflowStep[]; // Needed to resolve dependency names
}

const WorkflowStepItem: React.FC<WorkflowStepItemProps> = ({ step, allSteps }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getStepNameById = (id: string) => {
    const foundStep = allSteps.find(s => s.id === id);
    return foundStep ? foundStep.name : id;
  };

  const getIconForStatus = (status: JobStatus) => {
    switch (status) {
        case JobStatus.COMPLETED: return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
        case JobStatus.FAILED: return <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />;
        case JobStatus.RUNNING: return (
            <svg className="animate-spin h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
        );
        case JobStatus.PENDING:
        case JobStatus.WAITING_FOR_DEPENDENCY:
        default: return <InformationCircleIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow">
      <div className="flex items-center justify-between cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="flex items-center">
          <div className="mr-3 flex-shrink-0">{getIconForStatus(step.status)}</div>
          <div>
            <h4 className="text-md font-semibold text-gray-100">{step.name} <span className="text-xs text-gray-500">({step.action})</span></h4>
            <p className="text-xs text-gray-400">ID: {step.id}</p>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <StatusBadge status={step.status} />
          <ChevronDownIcon className={`w-5 h-5 text-gray-400 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
        </div>
      </div>

      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-700 text-sm text-gray-300 space-y-2">
          {step.startTime && <p><strong>Start Time:</strong> {new Date(step.startTime).toLocaleString()}</p>}
          {step.endTime && <p><strong>End Time:</strong> {new Date(step.endTime).toLocaleString()}</p>}
          {step.duration && <p><strong>Duration:</strong> {step.duration}</p>}
          
          {step.dependencies && step.dependencies.length > 0 && (
            <div>
              <strong>Dependencies:</strong>
              <ul className="list-disc list-inside ml-4">
                {step.dependencies.map(depId => (
                  <li key={depId} className="text-xs">{getStepNameById(depId)} ({depId})</li>
                ))}
              </ul>
            </div>
          )}

          {step.outputs && Object.keys(step.outputs).length > 0 && (
            <div>
              <strong>Outputs:</strong>
              <pre className="mt-1 p-2 bg-gray-900 rounded text-xs overflow-x-auto">
                {JSON.stringify(step.outputs, null, 2)}
              </pre>
            </div>
          )}
          
          {step.metadata && (
            <div>
              <strong>Metadata:</strong>
              <ul className="list-disc list-inside ml-4 text-xs">
                {step.metadata.tokens && <li>Tokens: {step.metadata.tokens.toLocaleString()}</li>}
                {step.metadata.time_sec && <li>Execution Time: {step.metadata.time_sec}s</li>}
                {step.metadata.cost && <li>Estimated Cost: ${step.metadata.cost.toFixed(4)}</li>}
              </ul>
            </div>
          )}

          {step.error && (
            <div>
              <strong className="text-red-400">Error:</strong>
              <p className="mt-1 p-2 bg-red-900 bg-opacity-30 border border-red-700 rounded text-xs text-red-300">{step.error}</p>
            </div>
          )}
          
          {step.logs && step.logs.length > 0 && (
            <div>
              <strong>Logs:</strong>
              <pre className="mt-1 p-2 bg-gray-900 rounded text-xs max-h-40 overflow-y-auto">
                {step.logs.join('\n')}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WorkflowStepItem;
