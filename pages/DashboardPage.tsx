
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { DashboardSummaryData, JobStatus, Workflow } from '../types';
import { getDashboardSummary } from '../services/orchestratorService';
import Spinner from '../components/common/Spinner';
import Card from '../components/common/Card';
import StatusBadge from '../components/common/StatusBadge';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip as RechartsTooltip } from 'recharts';
import { InformationCircleIcon, ArrowPathIcon, CheckCircleIcon, ExclamationTriangleIcon } from '../constants';

const MetricCard: React.FC<{ title: string; value: number | string; icon: React.ReactNode; description?: string }> = ({ title, value, icon, description }) => (
  <Card className="shadow-lg">
    <div className="flex items-center">
      <div className="p-3 rounded-full bg-sky-500 bg-opacity-20 mr-4">
        {icon}
      </div>
      <div>
        <p className="text-sm text-gray-400">{title}</p>
        <p className="text-2xl font-semibold text-gray-100">{value}</p>
      </div>
    </div>
    {description && <p className="mt-2 text-xs text-gray-500">{description}</p>}
  </Card>
);

const DashboardPage: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummaryData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setIsLoading(true);
        const data = await getDashboardSummary();
        setSummary(data);
      } catch (err) {
        setError('Failed to load dashboard data.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchSummary();
  }, []);

  if (isLoading) return <div className="flex justify-center items-center h-full"><Spinner message="Loading dashboard..." /></div>;
  if (error) return <div className="text-red-500 p-4">{error}</div>;
  if (!summary) return <div className="text-gray-400 p-4">No dashboard data available.</div>;

  const COLORS: {[key in JobStatus]?: string} = {
    [JobStatus.COMPLETED]: '#10B981', // green-500
    [JobStatus.RUNNING]: '#3B82F6',   // blue-500
    [JobStatus.PENDING]: '#F59E0B',   // amber-500
    [JobStatus.FAILED]: '#EF4444',    // red-500
    [JobStatus.STOPPED]: '#6B7280',   // gray-500
    [JobStatus.WAITING_FOR_DEPENDENCY]: '#8B5CF6', // violet-500
  };

  const chartData = summary.statusDistribution
    .filter(item => item.count > 0)
    .map(item => ({ name: item.status.replace('_', ' '), value: item.count, fill: COLORS[item.status] || '#A0AEC0' }));

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-100">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard title="Total Workflows" value={summary.totalWorkflows} icon={<InformationCircleIcon className="w-6 h-6 text-sky-500" />} />
        <MetricCard title="Active Workflows" value={summary.activeWorkflows} icon={<ArrowPathIcon className="w-6 h-6 text-sky-500 animate-spin-slow" />} description="Running or Pending" />
        <MetricCard title="Completed Successfully" value={summary.completedWorkflows} icon={<CheckCircleIcon className="w-6 h-6 text-green-500" />} />
        <MetricCard title="Failed/Stopped" value={summary.failedWorkflows} icon={<ExclamationTriangleIcon className="w-6 h-6 text-red-500" />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="Workflow Status Distribution" className="lg:col-span-2">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: 'rgba(31, 41, 55, 0.8)', border: '1px solid #4B5563', borderRadius: '0.5rem' }}
                  itemStyle={{ color: '#F3F4F6' }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-center py-10">No workflow data for chart.</p>
          )}
        </Card>

        <Card title="Recent Activity">
          {summary.recentActivity.length > 0 ? (
            <ul className="space-y-3 max-h-80 overflow-y-auto">
              {summary.recentActivity.map((wf: Workflow) => (
                <li key={wf.id} className="p-3 bg-gray-700 rounded-md hover:bg-gray-600 transition-colors">
                  <Link to={`/workflows/${wf.id}`} className="block">
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-gray-200 truncate" title={wf.name}>{wf.name}</span>
                      <StatusBadge status={wf.status} />
                    </div>
                    <p className="text-xs text-gray-400">
                      Last updated: {new Date(wf.updatedAt).toLocaleString()}
                    </p>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-400">No recent activity.</p>
          )}
        </Card>
      </div>
    </div>
  );
};

export default DashboardPage;
