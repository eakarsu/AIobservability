import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchProjects, createProject, createApiKey, setApiKey } from '../api/client';
import { Settings as SettingsIcon, Key, Plus, Copy, Check } from 'lucide-react';
import type { ApiKeyResponse } from '../types';

export default function Settings() {
  const queryClient = useQueryClient();
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [createdKey, setCreatedKey] = useState<ApiKeyResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [activeKey, setActiveKey] = useState('');

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: fetchProjects,
  });

  const createProjectMutation = useMutation({
    mutationFn: () => createProject({ name: newProjectName, description: newProjectDesc }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setNewProjectName('');
      setNewProjectDesc('');
    },
  });

  const createKeyMutation = useMutation({
    mutationFn: (projectId: string) => createApiKey(projectId),
    onSuccess: (data) => {
      setCreatedKey(data);
    },
  });

  const copyKey = () => {
    if (createdKey?.raw_key) {
      navigator.clipboard.writeText(createdKey.raw_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleSetApiKey = () => {
    setApiKey(activeKey);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <SettingsIcon className="w-7 h-7 text-gray-500" />
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
      </div>

      {/* API Key Configuration */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Dashboard API Key</h3>
        <p className="text-xs text-gray-500 mb-3">
          Set the API key used by the dashboard to fetch data. Get a key by creating a project below.
        </p>
        <div className="flex gap-2">
          <input
            type="text"
            value={activeKey}
            onChange={e => setActiveKey(e.target.value)}
            className="flex-1 border rounded px-3 py-2 text-sm font-mono"
            placeholder="aio_..."
          />
          <button
            onClick={handleSetApiKey}
            className="bg-blue-600 text-white rounded px-4 py-2 text-sm font-medium hover:bg-blue-700"
          >
            Set Key
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Create Project */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Create New Project</h3>
          <div className="space-y-3">
            <input
              type="text"
              value={newProjectName}
              onChange={e => setNewProjectName(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm"
              placeholder="Project name"
            />
            <input
              type="text"
              value={newProjectDesc}
              onChange={e => setNewProjectDesc(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm"
              placeholder="Description (optional)"
            />
            <button
              onClick={() => createProjectMutation.mutate()}
              disabled={!newProjectName || createProjectMutation.isPending}
              className="w-full bg-green-600 text-white rounded py-2 text-sm font-medium hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Create Project
            </button>
          </div>
        </div>

        {/* Projects List */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Projects</h3>
          {projects && projects.length > 0 ? (
            <div className="space-y-2">
              {projects.map(project => (
                <div key={project.id} className="border rounded-lg p-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{project.name}</p>
                    <p className="text-xs text-gray-400">{project.description || 'No description'}</p>
                    <p className="text-xs text-gray-300 font-mono mt-0.5">{project.id}</p>
                  </div>
                  <button
                    onClick={() => createKeyMutation.mutate(project.id)}
                    disabled={createKeyMutation.isPending}
                    className="p-2 text-blue-500 hover:bg-blue-50 rounded transition-colors"
                    title="Generate API Key"
                  >
                    <Key className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400 text-center py-4">No projects yet</p>
          )}
        </div>
      </div>

      {/* Created API Key Display */}
      {createdKey?.raw_key && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-yellow-800 mb-2">New API Key Created</h3>
          <p className="text-xs text-yellow-600 mb-2">
            Copy this key now. You won't be able to see it again!
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 bg-white border rounded px-3 py-2 text-sm font-mono text-gray-800">
              {createdKey.raw_key}
            </code>
            <button
              onClick={copyKey}
              className="p-2 bg-white border rounded hover:bg-gray-50 transition-colors"
            >
              {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4 text-gray-500" />}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
