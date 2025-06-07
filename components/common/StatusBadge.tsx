
import React from 'react';
import { JobStatus } from '../../types';
import { CheckCircleIcon, ExclamationTriangleIcon, InformationCircleIcon, ArrowPathIcon } from '../../constants'; // Assuming ArrowPathIcon for running/pending

interface StatusBadgeProps {
  status: JobStatus;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  let bgColor = 'bg-gray-500';
  let textColor = 'text-gray-100';
  let IconComponent = InformationCircleIcon;

  switch (status) {
    case JobStatus.PENDING:
      bgColor = 'bg-yellow-500';
      textColor = 'text-yellow-900';
      IconComponent = ArrowPathIcon; // Or a clock icon
      break;
    case JobStatus.RUNNING:
      bgColor = 'bg-blue-500';
      textColor = 'text-blue-100';
      IconComponent = ArrowPathIcon; // Or a spinner-like icon
      break;
    case JobStatus.COMPLETED:
      bgColor = 'bg-green-500';
      textColor = 'text-green-100';
      IconComponent = CheckCircleIcon;
      break;
    case JobStatus.FAILED:
      bgColor = 'bg-red-500';
      textColor = 'text-red-100';
      IconComponent = ExclamationTriangleIcon;
      break;
    case JobStatus.WAITING_FOR_DEPENDENCY:
      bgColor = 'bg-indigo-500';
      textColor = 'text-indigo-100';
      IconComponent = InformationCircleIcon; // Or a pause icon
      break;
    case JobStatus.STOPPED:
      bgColor = 'bg-gray-600';
      textColor = 'text-gray-100';
      IconComponent = ExclamationTriangleIcon;
      break;
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${bgColor} ${textColor}`}
    >
      <IconComponent className="w-3.5 h-3.5 mr-1.5" />
      {status.replace('_', ' ')}
    </span>
  );
};

export default StatusBadge;
