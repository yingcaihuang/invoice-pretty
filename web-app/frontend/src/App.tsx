import React, { useState, useEffect } from 'react';
import Layout from './components/Layout';
import FileUpload from './components/FileUpload';
import TaskTracker from './components/TaskTracker';
import TaskHistory from './components/TaskHistory';
import NotificationContainer from './components/NotificationContainer';
import { SessionManager } from './utils/sessionManager';
import { useNotifications } from './hooks/useNotifications';
import { Task } from './types';

function App() {
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [sessionId] = useState(() => {
    // Clean up old sessions and initialize
    SessionManager.cleanupOldSessions();
    return SessionManager.getSessionId();
  });
  const { notifications, removeNotification } = useNotifications();

  useEffect(() => {
    // Initialize session on app load
    console.log('Session initialized:', sessionId);
    console.log('Session created:', SessionManager.getSessionCreatedAt());
    console.log('Stored tasks:', SessionManager.getTaskCount());
  }, [sessionId]);

  const handleTaskCreated = (task: Task) => {
    setCurrentTask(task);
    SessionManager.addTask(task.taskId);
  };

  const handleTaskSelected = (task: Task) => {
    setCurrentTask(task);
  };

  const handleTaskUpdate = (updatedTask: Task) => {
    setCurrentTask(updatedTask);
    // Ensure task is still in localStorage (in case it was added from history)
    SessionManager.addTask(updatedTask.taskId);
  };

  return (
    <Layout>
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
        {/* Main upload and tracking area */}
        <div className="xl:col-span-2 space-y-4 sm:space-y-6">
          <FileUpload onTaskCreated={handleTaskCreated} />
          {currentTask && (
            <TaskTracker 
              task={currentTask} 
              onTaskUpdate={handleTaskUpdate}
            />
          )}
        </div>
        
        {/* Task history sidebar */}
        <div className="xl:col-span-1 order-first xl:order-last">
          <TaskHistory 
            onTaskSelected={handleTaskSelected}
            currentTaskId={currentTask?.taskId}
          />
        </div>
      </div>

      {/* Notification system */}
      <NotificationContainer 
        notifications={notifications}
        onRemove={removeNotification}
      />
    </Layout>
  );
}

export default App;