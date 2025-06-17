import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TaskHistory = ({ onRerun, refreshKey }) => {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetchHistory();
  }, [refreshKey]);

  const fetchHistory = async () => {
    try {
      const res = await axios.get('/api/task_instances?state=done,cancelled');
      setHistory(res.data);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  const handleRerun = async (task) => {
    try {
      await axios.post('/api/task_instances', {
        build_archetype_id: task.build_archetype_id,
        task_archetype_id: task.task_archetype_id,
      });
      onRerun();
    } catch (error) {
      console.error('Error rerunning task:', error);
      alert('Error rerunning task: ' + (error.response?.data?.error || error.message));
    }
  };

  return (
    <div className="history">
      <h2>Task History</h2>
      {history.map(task => (
        <div key={task.id} className="task-item">
          <p>
            Task {task.id}: (State: {task.state}, Build ID: {task.build_archetype_id})
          </p>
          {['done', 'cancelled'].includes(task.state?.toLowerCase()) && (
            <button onClick={() => handleRerun(task)}>Rerun</button>
          )}
        </div>
      ))}
    </div>
  );
};

export default TaskHistory;