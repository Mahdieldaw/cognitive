
import React, { useEffect, useState } from 'react';
import { WorkflowTemplate, ApiError } from '../types';
import { getWorkflowTemplates, createWorkflowFromTemplate } from '../services/orchestratorService';
import Spinner from '../components/common/Spinner';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import { PlayIcon, DocumentDuplicateIcon } from '../constants';
import { useNavigate } from 'react-router-dom';

const TemplatesPage: React.FC = () => {
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const [selectedTemplate, setSelectedTemplate] = useState<WorkflowTemplate | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formValues, setFormValues] = useState<Record<string, any>>({});
  const [isCreating, setIsCreating] = useState(false);
  const [creationError, setCreationError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        setIsLoading(true);
        const data = await getWorkflowTemplates();
        setTemplates(data);
      } catch (err) {
        setError('Failed to load workflow templates.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchTemplates();
  }, []);

  const handleOpenModal = (template: WorkflowTemplate) => {
    setSelectedTemplate(template);
    // Initialize form values with defaults
    const initialValues: Record<string, any> = {};
    template.parameters?.forEach(param => {
      initialValues[param.name] = param.defaultValue !== undefined ? param.defaultValue : '';
    });
    setFormValues(initialValues);
    setCreationError(null);
    setIsModalOpen(true);
  };

  const handleInputChange = (paramName: string, value: any) => {
    setFormValues(prev => ({ ...prev, [paramName]: value }));
  };

  const handleCreateWorkflow = async () => {
    if (!selectedTemplate) return;
    setIsCreating(true);
    setCreationError(null);
    try {
      const newWorkflow = await createWorkflowFromTemplate(selectedTemplate.id, formValues);
      setIsModalOpen(false);
      navigate(`/workflows/${newWorkflow.id}`);
    } catch (err) {
      const apiError = err as ApiError;
      setCreationError(apiError.message || 'Failed to create workflow from template.');
      console.error(err);
    } finally {
      setIsCreating(false);
    }
  };

  if (isLoading) return <div className="flex justify-center items-center h-full"><Spinner message="Loading templates..." /></div>;
  if (error) return <div className="text-red-500 p-4">{error}</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-100">Workflow Templates</h1>
      
      {templates.length === 0 ? (
        <div className="text-center py-10">
          <DocumentDuplicateIcon className="mx-auto h-12 w-12 text-gray-500" />
          <h3 className="mt-2 text-sm font-medium text-gray-200">No templates available</h3>
          <p className="mt-1 text-sm text-gray-400">Contact your administrator to add workflow templates.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates.map(template => (
            <Card key={template.id} title={template.name} className="flex flex-col justify-between">
              <div>
                <p className="text-sm text-gray-400 mb-2 h-16 overflow-hidden">{template.description}</p>
                {template.category && <p className="text-xs text-gray-500 mb-1">Category: {template.category}</p>}
                {template.estimatedDuration && <p className="text-xs text-gray-500">Est. Duration: {template.estimatedDuration}</p>}
              </div>
              <div className="mt-4 pt-4 border-t border-gray-700 flex justify-end">
                <Button variant="primary" size="sm" onClick={() => handleOpenModal(template)} leftIcon={<PlayIcon />}>
                  Use Template
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {selectedTemplate && (
        <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={`Use Template: ${selectedTemplate.name}`}>
          <div className="space-y-4">
            <p className="text-sm text-gray-300">{selectedTemplate.description}</p>
            {selectedTemplate.parameters && selectedTemplate.parameters.length > 0 ? (
              selectedTemplate.parameters.map(param => (
                <div key={param.name}>
                  <label htmlFor={param.name} className="block text-sm font-medium text-gray-300">
                    {param.name} {param.type === 'string' && !param.defaultValue && <span className="text-red-500">*</span>}
                  </label>
                  {param.type === 'string' && (
                     <textarea
                        id={param.name}
                        rows={3}
                        value={formValues[param.name] || ''}
                        onChange={(e) => handleInputChange(param.name, e.target.value)}
                        className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-sky-500 focus:border-sky-500 sm:text-sm text-gray-100"
                        placeholder={param.description}
                    />
                  )}
                  {param.type === 'number' && (
                     <input
                        type="number"
                        id={param.name}
                        value={formValues[param.name] || ''}
                        onChange={(e) => handleInputChange(param.name, e.target.valueAsNumber)}
                        className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-sky-500 focus:border-sky-500 sm:text-sm text-gray-100"
                        placeholder={param.description}
                    />
                  )}
                   {param.type === 'boolean' && (
                    <div className="mt-1 flex items-center">
                        <input
                            id={param.name}
                            type="checkbox"
                            checked={!!formValues[param.name]}
                            onChange={(e) => handleInputChange(param.name, e.target.checked)}
                            className="h-4 w-4 text-sky-600 border-gray-600 rounded focus:ring-sky-500 bg-gray-700"
                        />
                        <label htmlFor={param.name} className="ml-2 text-sm text-gray-300">{param.description || param.name}</label>
                    </div>
                   )}
                  <p className="text-xs text-gray-500 mt-1">{param.description}</p>
                </div>
              ))
            ) : (
              <p className="text-gray-400">This template requires no parameters to start.</p>
            )}
            {creationError && <p className="text-sm text-red-500">{creationError}</p>}
          </div>
          <div className="pt-4 flex justify-end space-x-3">
              <Button variant="outline" onClick={() => setIsModalOpen(false)} disabled={isCreating}>Cancel</Button>
              <Button variant="primary" onClick={handleCreateWorkflow} isLoading={isCreating}>Create Workflow</Button>
          </div>
        </Modal>
      )}

    </div>
  );
};

export default TemplatesPage;
