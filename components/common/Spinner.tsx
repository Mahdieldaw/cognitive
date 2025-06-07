
import React from 'react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
}

const Spinner: React.FC<SpinnerProps> = ({ size = 'md', message }) => {
  const sizeClasses = {
    sm: 'w-6 h-6 border-2',
    md: 'w-10 h-10 border-4',
    lg: 'w-16 h-16 border-4',
  };

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div
        className={`animate-spin rounded-full border-sky-500 border-t-transparent ${sizeClasses[size]}`}
      ></div>
      {message && <p className="mt-2 text-sm text-gray-400">{message}</p>}
    </div>
  );
};

export default Spinner;
