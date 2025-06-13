import React, { useState, useEffect } from 'react';
import axios from 'axios';
import AceEditor from 'react-ace';
import 'brace/mode/json';
import 'brace/theme/monokai';

const ArchetypeList = ({ onDelete, refreshKey }) => {
  const [buildArchetypes, setBuildArchetypes] = useState([]);
  const [taskArchetypes, setTaskArchetypes] = useState([]);
  const [editing, setEditing] = useState(null);
  const [editJson, setEditJson] = useState('{}');

  useEffect(() => {
    fetchArchetypes();
  }, [refreshKey]);

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
    setEditJson(JSON.stringify(archetype.content, null, 2));
  };

  const handleSaveEdit = async () => {
    try {
      const parsedJson = JSON.parse(editJson);
      await axios.post(`/api/${editing.type}_archetypes`, { content: parsedJson });
      setEditing(null);
      setEditJson('{}');
      onDelete();
    } catch (error) {
      alert('Invalid JSON or server error: ' + (error.response?.data?.error || error.message));
    }
  };

  const handleDelete = async (id, type) => {
    if (window.confirm('Are you sure you want to delete this archetype?')) {
      try {
        await axios.delete(`/api/${type}_archetypes/${id}`);
        onDelete();
      } catch (error) {
        console.error('Error deleting archetype:', error);
        alert('Error deleting archetype: ' + (error.response?.data?.error || error.message));
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
          <AceEditor
            mode="json"
            theme="monokai"
            value={editJson}
            onChange={setEditJson}
            name="edit-editor"
            editorProps={{ $blockScrolling: true }}
            setOptions={{ useWorker: false }}
            className="ace-editor"
          />
          <button onClick={handleSaveEdit}>Save New Version</button>
          <button onClick={() => setEditing(null)} className="bg-gray-500">Cancel</button>
        </div>
      )}
    </div>
  );
};

export default ArchetypeList;