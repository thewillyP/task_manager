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
      <button onClick={() => onCancel(task.id)} className="bg-red-500">Cancel</button>
    </div>
  );
};

const TaskQueue = ({ onQueueChange, refreshKey }) => {
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    fetchTasks();
  }, [refreshKey]);

  const fetchTasks = async () => {
    try {
      const res = await axios.get('/api/task_instances?state=pending');
      setTasks(res.data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  const moveTask = async (fromIndex, toIndex) => {
    const newTasks = [...tasks];
    const [movedTask] = newTasks.splice(fromIndex, 1);
    newTasks.splice(toIndex, 0, movedTask);
    setTasks(newTasks);
    
    try {
      await Promise.all(newTasks.map((task, index) => 
        axios.put(`/api/task_instances/${task.id}`, {
          position: index
        })
      ));
      onQueueChange();
    } catch (error) {
      console.error('Error updating task positions:', error);
      alert('Error updating task positions: ' + (error.response?.data?.error || error.message));
    }
  };

  const handleCancel = async (id) => {
    try {
      await axios.put(`/api/task_instances/${id}`, { state: 'cancelled' });
      onQueueChange();
    } catch (error) {
      console.error('Error cancelling task:', error);
      alert('Error cancelling task: ' + (error.response?.data?.error || error.message));
    }
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