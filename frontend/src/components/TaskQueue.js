import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useDrag, useDrop } from 'react-dnd';

const TaskItem = ({ task, index, moveTask, onCancel }) => {
  const [{ isDragging }, drag] = useDrag({
    type: 'TASK',
    item: { index },
    collect: monitor => ({
      isDragging: monitor.isDragging()
    })
  });

  const [, drop] = useDrop({
    accept: 'TASK',
    hover: (item) => {
      if (item.index !== index) {
        moveTask(item.index, index);
        item.index = index;
      }
    }
  });

  return (
    <div ref={node => drag(drop(node))} className={`task-item ${isDragging ? 'dragging' : ''}`}>
      <p>Task {task.id}: {task.task_archetype_content.pipeline} (Jobs: {task.num_jobs_remaining})</p>
      <button onClick={() => onCancel(task.id)}>Cancel</button>
    </div>
  );
};

const TaskQueue = ({ onQueueChange }) => {
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchTasks = async () => {
    const res = await axios.get('http://localhost:5000/api/task_instances?state=pending');
    setTasks(res.data);
  };

  const moveTask = async (fromIndex, toIndex) => {
    const newTasks = [...tasks];
    const [movedTask] = newTasks.splice(fromIndex, 1);
    newTasks.splice(toIndex, 0, movedTask);
    setTasks(newTasks);
    
    // Update positions in backend
    await Promise.all(newTasks.map((task, index) => 
      axios.put(`http://localhost:5000/api/task_instances/${task.id}`, {
        position: index
      })
    ));
  };

  const handleCancel = async (id) => {
    await axios.put(`http://localhost:5000/api/task_instances/${id}`, { state: 'cancelled' });
    fetchTasks();
    onQueueChange();
  };

  return (
    <div className="queue">
      <h2>Task Queue</h2>
      {tasks.map((task, index) => (
        <TaskItem
          key={task.id}
          task={task}
          index={index}
          moveTask={moveTask}
          onCancel={handleCancel}
        />
      ))}
    </div>
  );
};

export default TaskQueue;