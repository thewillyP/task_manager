import React, { useState } from 'react';
import axios from 'axios';

const ArchetypeEditor = ({ onSave }) => {
  const [buildJson, setBuildJson] = useState('');
  const [taskJson, setTaskJson] = useState('{\n  "num_jobs": 1,\n  "pipeline": ""\n}');
  const [type, setType] = useState('build');

  const handleSave = async () => {
    try {
      const json = type === 'build' ? buildJson : taskJson;
      await axios.post(`http://localhost:5000/api/${type}_archetypes`, { content: JSON.parse(json) });
      setBuildJson('');
      setTaskJson('{\n  "num_jobs": 1,\n  "pipeline": ""\n}');
      onSave();
    } catch (error) {
      alert('Invalid JSON or server error');
    }
  };

  const handleSubmitTask = async () => {
    try {
      const buildArchetype = await axios.get('http://localhost:5000/api/build_archetypes');
      const taskArchetype = JSON.parse(taskJson);
      if (!buildArchetype.data.length) {
        alert('Please create a build archetype first');
        return;
      }
      await axios.post('http://localhost:5000/api/task_instances', {
        build_archetype_id: buildArchetype.data[0].id,
        task_archetype_id: (await axios.post('http://localhost:5000/api/task_archetypes', { content: taskArchetype })).data.id,
        num_jobs: taskArchetype.num_jobs
      });
      onSave();
    } catch (error) {
      alert('Error submitting task');
    }
  };

  return (
    <div className="editor">
      <h2>Create Archetype</h2>
      <select value={type} onChange={e => setType(e.target.value)}>
        <option value="build">Build Archetype</option>
        <option value="task">Task Archetype</option>
      </select>
      <textarea
        value={type === 'build' ? buildJson : taskJson}
        onChange={e => type === 'build' ? setBuildJson(e.target.value) : setTaskJson(e.target.value)}
        placeholder="Enter JSON"
      />
      <button onClick={handleSave}>Save Archetype</button>
      {type === 'task' && <button onClick={handleSubmitTask}>Submit Task</button>}
    </div>
  );
};

export default ArchetypeEditor;