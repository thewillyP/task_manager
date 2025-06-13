import React, { useState } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import ArchetypeEditor from './components/ArchetypeEditor';
import ArchetypeList from './components/ArchetypeList';
import TaskQueue from './components/TaskQueue';
import TaskHistory from './components/TaskHistory';
import './App.css';

function App() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="app">
        <h1>Task Queue Manager</h1>
        <div className="container">
          <ArchetypeEditor onSave={handleRefresh} refreshKey={refreshKey} />
          <ArchetypeList onDelete={handleRefresh} refreshKey={refreshKey} />
          <TaskQueue onQueueChange={handleRefresh} refreshKey={refreshKey} />
          <TaskHistory onRerun={handleRefresh} refreshKey={refreshKey} />
        </div>
      </div>
    </DndProvider>
  );
}

export default App;