import React, { useState, useEffect } from 'react';
import axios from 'axios';
import JSONInput from 'react-json-editor-ajrm';
import locale from 'react-json-editor-ajrm/locale/en';

const ArchetypeList = ({ onDelete }) => {
  const [buildArchetypes, setBuildArchetypes] = useState([]);
  const [taskArchetypes, setTaskArchetypes] = useState([]);
  const [editing, setEditing] = useState(null);
  const [editJson, setEditJson] = useState({});

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:5000/ws');
    ws.onmessage = () => {
      fetchArchetypes();
    };
    fetchArchetypes();
    return () => ws.close();
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

  const handleEdit = (archetype, type) => {
    setEditing({ id: archetype.id, type });
    setEditJson(archetype.content);
  };

  const handleSaveEdit = async () => {
    try {
      await axios.post(`/api/${editing.type}_archetypes`, { content: editJson });
      setEditing(null);
      setEditJson({});
      onDelete();
    } catch (error) {
      alert('Invalid JSON or server error');
    }
  };

  const handleDelete = async (id, type) => {
    if (window.confirm('Are you sure you want to delete this archetype?')) {
      try {
        await axios.delete(`/api/${type}_archetypes/${id}`);
        onDelete();
      } catch (error) {
        console.error('Error deleting archetype:', error);
      }
    }
  };

  return (
    <div className="list">
      <h2>Archetypes</h2>
      <h3>Build Archetypes</h3>
      {buildArchetypes.map(arch => (
        <div key={arch.id} className="mb-2">
          <pre onClick={() => handleEdit(arch, 'build')} className="cursor-pointer">
            {JSON.stringify(arch.content, null, 2)}
          </pre>
          <button onClick={() => handleDelete(arch.id, 'build')} className="bg-red-500">Delete</button>
        </div>
      ))}
      <h3>Task Archetypes</h3>
      {taskArchetypes.map(arch => (
        <div key={arch.id} className="mb-2">
          <pre onClick={() => handleEdit(arch, 'task')} className="cursor-pointer">
            {JSON.stringify(arch.content, null, 2)}
          </pre>
          <button onClick={() => handleDelete(arch.id, 'task')} className="bg-red-500">Delete</button>
        </div>
      ))}
      {editing && (
        <div>
          <h3>Edit {editing.type} Archetype</h3>
          <JSONInput
            placeholder={editJson}
            onChange={(e) => setEditJson(e.jsObject)}
            locale={locale}
            height="200px"
            width="100%"
          />
          <button onClick={handleSaveEdit}>Save New Version</button>
          <button onClick={() => setEditing(null)} className="bg-gray-500">Cancel</button>
        </div>
      )}
    </div>
  );
};

export default ArchetypeList;