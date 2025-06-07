
import React from 'react';
import { Link } from 'react-router-dom';
import { Workflow, JobStatus } from '../../types';
import Card from '../common/Card';
import StatusBadge from '../common/StatusBadge';
import Button from '../common/Button';
import { ArrowPathIcon } from '../../constants'; // For a "Rerun" example

const WorkflowListItem: React.FC<{ workflow: Workflow }> = ({ workflow }) => {
  const { id, name, status, description, updatedAt, progress } = workflow;

  const formattedDate = new Date(updatedAt).toLocaleString();

  return (
    <Card className="hover:shadow-sky-500/30 transition-shadow duration-200 flex flex-col justify-between">
      <div>
        <div className="flex justify-between items-start mb-2">
          <Link to={`/workflows/${id}`} className="block">
            <h2 className="text-xl font-semibold text-sky-400 hover:text-sky-300 truncate" title={name}>
              {name}
            </h2>
          </Link>
          <StatusBadge status={status} />
        </div>
        <p className="text-sm text-gray-400 mb-3 h-10 overflow-hidden">
          {description || 'No description available.'}
        </p>
        {typeof progress === 'number' && (
          <div className="w-full bg-gray-700 rounded-full h-2.5 mb-3">
            <div
              className="bg-sky-600 h-2.5 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        )}
        <p className="text-xs text-gray-500">Last updated: {formattedDate}</p>
        <p className="text-xs text-gray-500">ID: {id}</p>
      </div>
      <div className="mt-4 pt-4 border-t border-gray-700 flex justify-end space-x-2">
        {/* Example actions - functionality to be implemented */}
        {status === JobStatus.FAILED && (
          <Button size="sm" variant="outline" leftIcon={<ArrowPathIcon className="w-4 h-4" />}>
            Retry
          </Button>
        )}
        <Link to={`/workflows/${id}`}>
          <Button size="sm" variant="primary">
            View Details
          </Button>
        </Link>
      </div>
    </Card>
  );
};

export default WorkflowListItem;
