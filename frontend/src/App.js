import React, { useState } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import ArchetypeEditor from './components/ArchetypeEditor';
import ArchetypeList from './components/ArchetypeList';
import TaskQueue from './components/TaskQueue';
import TaskHistory from './components/TaskHistory';
import './App.css';

function App() {
  const [refresh, setRefresh] = useState(0);

  const handleRefresh = () => {
    setRefresh(prev => prev + 1);
  };

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="app">
        <h1>Task Queue Manager</h1>
        <div className="container">
          <ArchetypeEditor onSave={handleRefresh} />
          <ArchetypeList onDelete={handleRefresh} />
          <TaskQueue onQueueChange={handleRefresh} />
          <TaskHistory onRerun={handleRefresh} />
        </div>
      </div>
    </DndProvider>
  );
}

export default App;