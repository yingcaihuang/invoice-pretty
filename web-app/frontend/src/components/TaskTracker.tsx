import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../utils/api';
import { Task, TaskStatus } from '../types';
import { usePolling } from '../hooks/usePolling';
import { useNotifications } from '../hooks/useNotifications';
import PDFPreview from './PDFPreview';

interface TaskTrackerProps {
  task: Task;
  onTaskUpdate: (task: Task) => void;
}

const TaskTracker: React.FC<TaskTrackerProps> = ({ task, onTaskUpdate }) => {
  const [error, setError] = useState<string | null>(null);
  const [lastStatus, setLastStatus] = useState<TaskStatus>(task.status);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'reconnecting'>('connected');
  const { addNotification, showBrowserNotification } = useNotifications();

  const pollTaskStatus = useCallback(async () => {
    try {
      setConnectionStatus('connected');
      const response = await apiClient.getTaskStatus(task.taskId);
      const updatedTask: Task = {
        taskId: response.taskId,
        status: response.status,
        progress: response.progress,
        message: response.message,
        downloadUrls: response.downloadUrls,
        createdAt: response.createdAt,
        completedAt: response.completedAt,
      };

      // Check for status changes and show notifications
      if (lastStatus !== response.status) {
        setLastStatus(response.status);
        
        switch (response.status) {
          case 'completed':
            addNotification({
              type: 'success',
              title: 'Task Completed',
              message: `Task ${task.taskId.slice(0, 8)}... has finished processing`,
              duration: 8000,
            });
            showBrowserNotification('Task Completed', {
              body: `Your PDF processing task has finished successfully`,
              tag: task.taskId,
            });
            break;
          case 'failed':
            addNotification({
              type: 'error',
              title: 'Task Failed',
              message: `Task ${task.taskId.slice(0, 8)}... encountered an error`,
              duration: 10000,
            });
            showBrowserNotification('Task Failed', {
              body: `Your PDF processing task has failed`,
              tag: task.taskId,
            });
            break;
          case 'processing':
            if (lastStatus === 'queued') {
              addNotification({
                type: 'info',
                title: 'Processing Started',
                message: `Task ${task.taskId.slice(0, 8)}... is now being processed`,
                duration: 5000,
              });
            }
            break;
        }
      }

      onTaskUpdate(updatedTask);
      setError(null);
    } catch (err) {
      setConnectionStatus('disconnected');
      const errorMessage = err instanceof Error ? err.message : 'Failed to get task status';
      setError(errorMessage);
      
      // Show error notification only on first failure
      if (connectionStatus === 'connected') {
        addNotification({
          type: 'warning',
          title: 'Connection Issue',
          message: 'Retrying connection...',
          duration: 3000,
        });
      }
      
      throw err; // Re-throw to trigger polling retry logic
    }
  }, [task.taskId, onTaskUpdate, lastStatus, connectionStatus, addNotification, showBrowserNotification]);

  // Determine if polling should be enabled
  const shouldPoll = ['queued', 'processing'].includes(task.status);

  // Use polling hook with automatic retry and backoff
  usePolling(pollTaskStatus, {
    interval: 2000, // Poll every 2 seconds
    enabled: shouldPoll,
    maxRetries: 5,
    backoffMultiplier: 1.5,
  });

  // Update last status when task prop changes
  useEffect(() => {
    setLastStatus(task.status);
  }, [task.status]);

  const getStatusColor = (status: TaskStatus): string => {
    switch (status) {
      case 'queued':
        return 'text-yellow-600 bg-yellow-100';
      case 'processing':
        return 'text-blue-600 bg-blue-100';
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      case 'expired':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: TaskStatus) => {
    switch (status) {
      case 'queued':
        return (
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
        );
      case 'processing':
        return (
          <svg className="h-5 w-5 animate-spin" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
          </svg>
        );
      case 'completed':
        return (
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'failed':
        return (
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      case 'expired':
        return (
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm.707-10.293a1 1 0 00-1.414-1.414l-3 3a1 1 0 000 1.414l3 3a1 1 0 001.414-1.414L9.414 11H13a1 1 0 100-2H9.414l1.293-1.293z" clipRule="evenodd" />
          </svg>
        );
      default:
        return null;
    }
  };

  const handleDownload = async (url: string, filename: string) => {
    try {
      // Convert relative URLs to absolute URLs using the API base URL
      const absoluteUrl = url.startsWith('http') ? url : `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}${url}`;
      
      // Import SessionManager to get session ID
      const { SessionManager } = await import('../utils/sessionManager');
      
      // Fetch the file with session headers
      const response = await fetch(absoluteUrl, {
        headers: {
          'X-Session-ID': SessionManager.getSessionId(),
        },
      });

      if (!response.ok) {
        throw new Error(`Download failed: ${response.statusText}`);
      }

      // Create blob and download
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed. Please try again.');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN', {
      timeZone: 'Asia/Shanghai',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  const calculateTimeRemaining = (completedAt: string | undefined): string | null => {
    if (!completedAt) return null;
    
    const completed = new Date(completedAt);
    const now = new Date();
    const expiresAt = new Date(completed.getTime() + 24 * 60 * 60 * 1000); // 24 hours after completion
    const remainingMs = expiresAt.getTime() - now.getTime();
    
    if (remainingMs <= 0) {
      return '已过期';
    }
    
    const remainingHours = Math.floor(remainingMs / (1000 * 60 * 60));
    const remainingMinutes = Math.floor((remainingMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (remainingHours > 0) {
      return `剩余 ${remainingHours} 小时 ${remainingMinutes} 分钟`;
    } else if (remainingMinutes > 0) {
      return `剩余 ${remainingMinutes} 分钟`;
    } else {
      const remainingSeconds = Math.floor((remainingMs % (1000 * 60)) / 1000);
      return `剩余 ${remainingSeconds} 秒`;
    }
  };

  // Auto-refresh countdown every minute for completed tasks
  const [, setCountdownTick] = useState(0);
  useEffect(() => {
    if (task.status === 'completed' && task.completedAt) {
      const interval = setInterval(() => {
        setCountdownTick(tick => tick + 1);
      }, 60000); // Update every minute
      
      return () => clearInterval(interval);
    }
  }, [task.status, task.completedAt]);

  return (
    <div className="bg-white rounded-lg shadow-md p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 space-y-2 sm:space-y-0">
        <h2 className="text-xl sm:text-2xl font-semibold text-gray-800">Task Status</h2>
        <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium self-start ${getStatusColor(task.status)}`}>
          {getStatusIcon(task.status)}
          <span className="ml-2 capitalize">{task.status}</span>
        </div>
      </div>

      {/* Task ID */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">Task ID</label>
        <div className="flex items-center">
          <code className="bg-gray-100 px-2 py-1 rounded text-xs sm:text-sm font-mono flex-1 overflow-x-auto">
            {task.taskId}
          </code>
          <button
            onClick={() => navigator.clipboard.writeText(task.taskId)}
            className="ml-2 p-2 text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 rounded transition-colors"
            title="Copy Task ID"
            aria-label="Copy Task ID"
          >
            <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" />
              <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z" />
            </svg>
          </button>
        </div>
      </div>

      {/* Progress bar for processing tasks */}
      {task.status === 'processing' && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Progress</span>
            <span className="text-sm text-gray-600">{task.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${task.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Message */}
      {task.message && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
          <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded">{task.message}</p>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Download links */}
      {task.status === 'completed' && task.downloadUrls && task.downloadUrls.length > 0 && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Download Results</label>
          <div className="space-y-2">
            {task.downloadUrls.map((url, index) => {
              const filename = url.split('/').pop() || `result-${index + 1}.pdf`;
              return (
                <button
                  key={index}
                  onClick={() => handleDownload(url, filename)}
                  className="flex items-center w-full p-3 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors touch-manipulation"
                >
                  <svg className="h-5 w-5 text-green-600 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm font-medium text-green-800 truncate">{filename}</span>
                </button>
              );
            })}
          </div>

          {/* PDF Preview */}
          {task.downloadUrls.map((url, index) => {
            const filename = url.split('/').pop() || `result-${index + 1}.pdf`;
            // Only show preview for PDF files
            if (filename.toLowerCase().endsWith('.pdf')) {
              // Extract task ID and filename from the download URL to create preview URL
              const urlParts = url.split('/');
              const taskId = urlParts[urlParts.length - 2];
              const previewUrl = apiClient.getPreviewUrl(taskId, filename);
              
              return (
                <PDFPreview
                  key={`preview-${index}`}
                  pdfUrl={previewUrl}
                  filename={filename}
                />
              );
            }
            return null;
          })}
        </div>
      )}

      {/* Task timestamps */}
      <div className="text-xs text-gray-500 space-y-1">
        <div>Created: {formatDate(task.createdAt)}</div>
        {task.completedAt && (
          <div>Completed: {formatDate(task.completedAt)}</div>
        )}
      </div>

      {/* File expiration countdown for completed tasks */}
      {task.status === 'completed' && task.completedAt && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
            <div className="text-sm">
              {(() => {
                const timeRemaining = calculateTimeRemaining(task.completedAt);
                if (timeRemaining === '已过期') {
                  return (
                    <span className="text-red-600 font-medium">
                      文件已过期，无法下载
                    </span>
                  );
                } else if (timeRemaining) {
                  const remainingHours = Math.floor((new Date(task.completedAt).getTime() + 24 * 60 * 60 * 1000 - new Date().getTime()) / (1000 * 60 * 60));
                  const isExpiringSoon = remainingHours <= 2;
                  return (
                    <div>
                      <span className={`${isExpiringSoon ? 'text-orange-600' : 'text-blue-600'} font-medium`}>
                        文件过期倒计时：{timeRemaining}
                      </span>
                      {isExpiringSoon && (
                        <div className="text-xs text-orange-600 mt-1">
                          ⚠️ 文件即将过期，请尽快下载
                        </div>
                      )}
                    </div>
                  );
                }
                return null;
              })()}
            </div>
          </div>
        </div>
      )}

      {/* Connection status indicator */}
      {shouldPoll && (
        <div className="mt-4 flex items-center text-sm">
          {connectionStatus === 'connected' && (
            <div className="flex items-center text-green-600">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
              Live updates active
            </div>
          )}
          {connectionStatus === 'disconnected' && (
            <div className="flex items-center text-red-600">
              <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
              Connection lost - retrying...
            </div>
          )}
          {connectionStatus === 'reconnecting' && (
            <div className="flex items-center text-yellow-600">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Reconnecting...
            </div>
          )}
        </div>
      )}

      {/* Manual refresh button for failed connections */}
      {error && !shouldPoll && (
        <div className="mt-4">
          <button
            onClick={() => pollTaskStatus()}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg className="h-4 w-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
            </svg>
            Retry
          </button>
        </div>
      )}
    </div>
  );
};

export default TaskTracker;