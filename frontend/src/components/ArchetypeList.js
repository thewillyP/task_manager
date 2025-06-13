import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ArchetypeList = ({ onDelete }) => {
  const [buildArchetypes, setBuildArchetypes] = useState([]);
  const [taskArchetypes, setTaskArchetypes] = useState([]);
  const [editing, setEditing] = useState(null);
  const [editJson, setEditJson] = useState('');

  useEffect(() => {
    fetchArchetypes();
  }, []);

  const fetchArchetypes = async () => {
    const buildRes = await axios.get('http://localhost:5000/api/build_archetypes');
    const taskRes = await axios.get('http://localhost:5000/api/task_archetypes');
    setBuildArchetypes(buildRes.data);
    setTaskArchetypes(taskRes.data);
  };

  const handleEdit = (archetype, type) => {
    setEditing({ id: archetype.id, type });
    setEditJson(JSON.stringify(archetype.content, null, 2));
  };

  const handleSaveEdit = async () => {
    try {
      await axios.post(`http://localhost:5000/api/${editing.type}_archetypes`, { content: JSON.parse(editJson) });
      setEditing(null);
      setEditJson('');
      fetchArchetypes();
      onDelete();
    } catch (error) {
      alert('Invalid JSON or server error');
    }
  };

  const handleDelete = async (id, type) => {
    if (window.confirm('Are you sure you want to delete this archetype?')) {
      await axios.delete(`http://localhost:5000/api/${type}_archetypes/${id}`);
      fetchArchetypes();
      onDelete();
    }
  };

  return (
    <div className="list">
      <h2>Archetypes</h2>
      <h3>Build Archetypes</h3>
      {buildArchetypes.map(arch => (
        <div key={arch.id}>
          <pre onClick={() => handleEdit(arch, 'build')}>{JSON.stringify(arch.content, null, 2)}</pre>
          <button onClick={() => handleDelete(arch.id, 'build')}>Delete</button>
        </div>
      ))}
      <h3>Task Archetypes</h3>
      {taskArchetypes.map(arch => (
        <div key={arch.id}>
          <pre onClick={() => handleEdit(arch, 'task')}>{JSON.stringify(arch.content, null, 2)}</pre>
          <button onClick={() => handleDelete(arch.id, 'task')}>Delete</button>
        </div>
      ))}
      {editing && (
        <div>
          <h3>Edit {editing.type} Archetype</h3>
          <textarea value={editJson} onChange={e => setEditJson(e.target.value)} />
          <button onClick={handleSaveEdit}>Save New Version</button>
          <button onClick={() => setEditing(null)}>Cancel</button>
        </div>
      )}
    </div>
  );
};

export default ArchetypeList;