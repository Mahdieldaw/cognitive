
import React from 'react';
import { CogIcon } from '../../constants'; // Assuming you'll add a settings page or similar

const Header: React.FC = () => {
  return (
    <header className="bg-gray-800 shadow-md p-4 flex justify-between items-center">
      <div>
        {/* Can add breadcrumbs or page title here */}
        <h1 className="text-xl font-semibold text-gray-100">Hybrid Engine</h1>
      </div>
      <div className="flex items-center space-x-4">
        {/* Placeholder for user actions or settings */}
        <button className="p-2 rounded-full hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-sky-500">
          <CogIcon className="w-6 h-6 text-gray-400" />
        </button>
      </div>
    </header>
  );
};

export default Header;
