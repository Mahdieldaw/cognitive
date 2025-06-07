
import React from 'react';
import { NavLink } from 'react-router-dom';
import { ChartPieIcon, ListBulletIcon, DocumentDuplicateIcon, BeakerIcon } from '../../constants';

const navigationItems = [
  { name: 'Dashboard', path: '/dashboard', icon: ChartPieIcon },
  { name: 'Workflows', path: '/workflows', icon: ListBulletIcon },
  { name: 'Templates', path: '/templates', icon: DocumentDuplicateIcon },
  // Add more items as needed
];

const Sidebar: React.FC = () => {
  const NavItem: React.FC<{item: typeof navigationItems[0]}> = ({ item }) => (
    <NavLink
      to={item.path}
      className={({ isActive }) =>
        `flex items-center px-4 py-3 text-sm font-medium rounded-md group hover:bg-sky-700 hover:text-white transition-colors duration-150 ease-in-out
         ${isActive ? 'bg-sky-600 text-white' : 'text-gray-300'}`
      }
    >
      <item.icon className="mr-3 h-5 w-5" />
      {item.name}
    </NavLink>
  );

  return (
    <aside className="w-64 bg-gray-800 flex-shrink-0 border-r border-gray-700">
      <div className="h-full flex flex-col">
        <div className="flex items-center justify-center h-16 border-b border-gray-700">
          <BeakerIcon className="w-8 h-8 text-sky-500" />
          <span className="ml-2 text-2xl font-bold text-gray-100">Hybrid</span>
        </div>
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {navigationItems.map((item) => (
            <NavItem key={item.name} item={item} />
          ))}
        </nav>
        <div className="p-4 border-t border-gray-700">
          <p className="text-xs text-gray-500">© 2024 Hybrid Engine</p>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
