import React, { useState, useEffect } from 'react';
import axios from 'axios';
import JSONInput from 'react-json-editor-ajrm';
import locale from 'react-json-editor-ajrm/locale/en';

const ArchetypeEditor = ({ onSave }) => {
  const [buildJson, setBuildJson] = useState({});
  const [taskJson, setTaskJson] = useState({ num_jobs: 1, pipeline: "" });
  const [selectedBuildId, setSelectedBuildId] = useState('');
  const [selectedTaskId, setSelectedTaskId] = useState('');
  const [buildArchetypes, setBuildArchetypes] = useState([]);
  const [taskArchetypes, setTaskArchetypes] = useState([]);

  useEffect(() => {
    fetchArchetypes();
  }, []);

  const fetchArchetypes = async () => {
    try {
      const buildRes = await axios.get('/api/build_archetypes');
      const taskRes = await axios.get('/api/task_archetypes');
      setBuildArchetypes(buildRes.data);
      setTaskArchetypes(taskRes.data);
    } catch (error) {
      console.error('Error fetching archetypes:', error);
    }
  };

  const handleSaveBuild = async () => {
    try {
      await axios.post('/api/build_archetypes', { content: buildJson });
      setBuildJson({});
      onSave();
    } catch (error) {
      alert('Invalid JSON or server error');
    }
  };

  const handleSaveTask = async () => {
    try {
      if (!taskJson.num_jobs || !taskJson.pipeline) {
        alert('Task archetype must have num_jobs and pipeline');
        return;
      }
      await axios.post('/api/task_archetypes', { content: taskJson });
      setTaskJson({ num_jobs: 1, pipeline: "" });
      onSave();
    } catch (error) {
      alert('Invalid JSON or server error');
    }
  };

  const handleSubmitTask = async () => {
    try {
      if (!selectedBuildId || !selectedTaskId) {
        alert('Please select both build and task archetypes');
        return;
      }
      const taskArchetype = taskArchetypes.find(t => t.id === parseInt(selectedTaskId));
      await axios.post('/api/task_instances', {
        build_archetype_id: parseInt(selectedBuildId),
        task_archetype_id: parseInt(selectedTaskId),
        num_jobs: taskArchetype.content.num_jobs
      });
      onSave();
    } catch (error) {
      alert('Error submitting task');
    }
  };

  return (
    <div className="editor">
      <h2>Create Archetypes</h2>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3>Build Archetype</h3>
          <JSONInput
            placeholder={buildJson}
            onChange={(e) => setBuildJson(e.jsObject)}
            locale={locale}
            height="200px"
            width="100%"
          />
          <button onClick={handleSaveBuild}>Save Build Archetype</button>
        </div>
        <div>
          <h3>Task Archetype</h3>
          <JSONInput
            placeholder={taskJson}
            onChange={(e) => setTaskJson(e.jsObject)}
            locale={locale}
            height="200px"
            width="100%"
          />
          <button onClick={handleSaveTask}>Save Task Archetype</button>
        </div>
      </div>
      <div className="mt-4">
        <h3>Submit Task Instance</h3>
        <div className="flex gap-4 mb-2">
          <select
            value={selectedBuildId}
            onChange={(e) => setSelectedBuildId(e.target.value)}
          >
            <option value="">Select Build Archetype</option>
            {buildArchetypes.map(arch => (
              <option key={arch.id} value={arch.id}>
                Build #{arch.id}
              </option>
            ))}
          </select>
          <select
            value={selectedTaskId}
            onChange={(e) => setSelectedTaskId(e.target.value)}
          >
            <option value="">Select Task Archetype</option>
            {taskArchetypes.map(arch => (
              <option key={arch.id} value={arch.id}>
                Task #{arch.id} ({arch.content.pipeline})
              </option>
            ))}
          </select>
        </div>
        <button onClick={handleSubmitTask}>Submit Task Instance</button>
      </div>
    </div>
  );
};

export default ArchetypeEditor;