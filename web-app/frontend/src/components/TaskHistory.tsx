import React, { useState, useEffect, useMemo } from 'react';
import { SessionManager } from '../utils/sessionManager';
import { apiClient } from '../utils/api';
import { useNotifications } from '../hooks/useNotifications';
import { Task, TaskStatus } from '../types';

interface TaskHistoryProps {
  onTaskSelected: (task: Task) => void;
  currentTaskId?: string;
}

type SortOption = 'newest' | 'oldest' | 'status' | 'progress';
type FilterOption = 'all' | 'queued' | 'processing' | 'completed' | 'failed' | 'expired';

const TaskHistory: React.FC<TaskHistoryProps> = ({ onTaskSelected, currentTaskId }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('newest');
  const [filterBy, setFilterBy] = useState<FilterOption>('all');
  const [selectedTasks, setSelectedTasks] = useState<Set<string>>(new Set());
  const [showBulkActions, setShowBulkActions] = useState(false);
  const { addNotification } = useNotifications();

  const loadTasks = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const taskIds = SessionManager.getStoredTasks();
      const taskPromises = taskIds.map(async (taskId) => {
        try {
          const response = await apiClient.getTaskStatus(taskId);
          return {
            taskId: response.taskId,
            status: response.status,
            progress: response.progress,
            message: response.message,
            downloadUrls: response.downloadUrls,
            createdAt: response.createdAt,
            completedAt: response.completedAt,
          } as Task;
        } catch (err) {
          // If task doesn't exist anymore, remove it from localStorage
          SessionManager.removeTask(taskId);
          return null;
        }
      });

      const resolvedTasks = await Promise.all(taskPromises);
      const validTasks = resolvedTasks.filter((task): task is Task => task !== null);
      
      // Sort by creation date, newest first
      validTasks.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
      
      setTasks(validTasks);
    } catch (err) {
      setError('Failed to load task history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const clearHistory = () => {
    SessionManager.clearSession();
    setTasks([]);
    window.location.reload(); // Refresh to get new session
  };

  const removeTask = (taskId: string) => {
    SessionManager.removeTask(taskId);
    setTasks(prev => prev.filter(task => task.taskId !== taskId));
    setSelectedTasks(prev => {
      const newSet = new Set(prev);
      newSet.delete(taskId);
      return newSet;
    });
  };

  const toggleTaskSelection = (taskId: string) => {
    setSelectedTasks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(taskId)) {
        newSet.delete(taskId);
      } else {
        newSet.add(taskId);
      }
      return newSet;
    });
  };

  const selectAllTasks = () => {
    setSelectedTasks(new Set(filteredAndSortedTasks.map(task => task.taskId)));
  };

  const clearSelection = () => {
    setSelectedTasks(new Set());
  };

  const bulkRemoveTasks = () => {
    const count = selectedTasks.size;
    selectedTasks.forEach(taskId => {
      SessionManager.removeTask(taskId);
    });
    setTasks(prev => prev.filter(task => !selectedTasks.has(task.taskId)));
    setSelectedTasks(new Set());
    setShowBulkActions(false);
    
    addNotification({
      type: 'success',
      title: 'Tasks Removed',
      message: `${count} task${count !== 1 ? 's' : ''} removed from history`,
      duration: 3000,
    });
  };

  const bulkDownloadCompleted = () => {
    const completedTasks = filteredAndSortedTasks.filter(
      task => selectedTasks.has(task.taskId) && task.status === 'completed' && task.downloadUrls
    );
    
    if (completedTasks.length === 0) {
      addNotification({
        type: 'warning',
        title: 'No Downloads Available',
        message: 'No completed tasks with download links found in selection',
        duration: 4000,
      });
      return;
    }
    
    let totalFiles = 0;
    completedTasks.forEach(task => {
      task.downloadUrls?.forEach(async (url, index) => {
        try {
          const filename = url.split('/').pop() || `${task.taskId}-${index + 1}.pdf`;
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
          totalFiles++;
        } catch (error) {
          console.error('Download failed:', error);
        }
      });
    });
    
    addNotification({
      type: 'success',
      title: 'Downloads Started',
      message: `Downloading ${totalFiles} file${totalFiles !== 1 ? 's' : ''} from ${completedTasks.length} task${completedTasks.length !== 1 ? 's' : ''}`,
      duration: 5000,
    });
  };

  // Filtered and sorted tasks
  const filteredAndSortedTasks = useMemo(() => {
    let filtered = tasks;

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(task => 
        task.taskId.toLowerCase().includes(query) ||
        task.message?.toLowerCase().includes(query) ||
        task.status.toLowerCase().includes(query)
      );
    }

    // Apply status filter
    if (filterBy !== 'all') {
      filtered = filtered.filter(task => task.status === filterBy);
    }

    // Apply sorting
    const sorted = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
        case 'oldest':
          return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
        case 'status':
          return a.status.localeCompare(b.status);
        case 'progress':
          return b.progress - a.progress;
        default:
          return 0;
      }
    });

    return sorted;
  }, [tasks, searchQuery, filterBy, sortBy]);

  const getStatusColor = (status: TaskStatus): string => {
    switch (status) {
      case 'queued':
        return 'bg-yellow-100 text-yellow-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'expired':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    // For recent times, show relative time
    if (diffDays > 0) {
      return `${diffDays} 天前`;
    } else if (diffHours > 0) {
      return `${diffHours} 小时前`;
    } else if (diffMs > 0) {
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      if (diffMinutes > 0) {
        return `${diffMinutes} 分钟前`;
      } else {
        return '刚刚';
      }
    } else {
      // For absolute time display, show Beijing time
      return date.toLocaleString('zh-CN', {
        timeZone: 'Asia/Shanghai',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      });
    }
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

  // Auto-refresh countdown every minute
  const [, setCountdownTick] = useState(0);
  useEffect(() => {
    const interval = setInterval(() => {
      setCountdownTick(tick => tick + 1);
    }, 60000); // Update every minute
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-white rounded-lg shadow-md p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 space-y-2 sm:space-y-0">
        <h2 className="text-lg sm:text-xl font-semibold text-gray-800">Task History</h2>
        <div className="flex space-x-2">
          <button
            onClick={loadTasks}
            disabled={loading}
            className="p-2 text-gray-500 hover:text-gray-700 disabled:opacity-50"
            title="Refresh"
          >
            <svg className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
            </svg>
          </button>
          {tasks.length > 0 && (
            <>
              <button
                onClick={() => setShowBulkActions(!showBulkActions)}
                className={`p-2 ${showBulkActions ? 'text-blue-600' : 'text-gray-500'} hover:text-blue-700`}
                title="Bulk Actions"
              >
                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" />
                  <path fillRule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clipRule="evenodd" />
                </svg>
              </button>
              <button
                onClick={clearHistory}
                className="p-2 text-red-500 hover:text-red-700"
                title="Clear History"
              >
                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clipRule="evenodd" />
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 012 0v4a1 1 0 11-2 0V7zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V7a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Search bar */}
      {tasks.length > 0 && (
        <div className="mb-4">
          <div className="relative">
            <input
              type="text"
              placeholder="Search tasks by ID, status, or message..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <svg
              className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>
      )}

      {/* Filter and Sort controls */}
      {tasks.length > 0 && (
        <div className="mb-4 flex flex-col sm:flex-row gap-2">
          <select
            value={filterBy}
            onChange={(e) => setFilterBy(e.target.value as FilterOption)}
            className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            aria-label="Filter tasks by status"
          >
            <option value="all">All Status</option>
            <option value="queued">Queued</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="expired">Expired</option>
          </select>
          
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortOption)}
            className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            aria-label="Sort tasks"
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="status">By Status</option>
            <option value="progress">By Progress</option>
          </select>
        </div>
      )}

      {/* Bulk actions bar */}
      {showBulkActions && tasks.length > 0 && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-blue-900">
              {selectedTasks.size} task{selectedTasks.size !== 1 ? 's' : ''} selected
            </span>
            <div className="flex space-x-2">
              <button
                onClick={selectAllTasks}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Select All
              </button>
              <button
                onClick={clearSelection}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Clear
              </button>
            </div>
          </div>
          {selectedTasks.size > 0 && (
            <div className="flex space-x-2">
              <button
                onClick={bulkRemoveTasks}
                className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
              >
                Remove Selected
              </button>
              <button
                onClick={bulkDownloadCompleted}
                className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
              >
                Download Completed
              </button>
            </div>
          )}
        </div>
      )}

      {/* Session info */}
      <div className="mb-4 p-3 bg-gray-50 rounded-lg">
        <div className="text-xs text-gray-500">
          <div>Session ID: {SessionManager.getSessionId().slice(-8)}</div>
          <div>
            {filteredAndSortedTasks.length} of {tasks.length} task{tasks.length !== 1 ? 's' : ''} 
            {searchQuery && ` matching "${searchQuery}"`}
            {filterBy !== 'all' && ` (${filterBy})`}
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-8">
          <svg className="animate-spin h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        </div>
      )}

      {!loading && tasks.length === 0 && (
        <div className="text-center py-8">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="mt-2 text-sm text-gray-500">No tasks yet</p>
          <p className="text-xs text-gray-400">Upload files to get started</p>
        </div>
      )}

      {!loading && filteredAndSortedTasks.length === 0 && tasks.length > 0 && (
        <div className="text-center py-8">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <p className="mt-2 text-sm text-gray-500">No tasks match your search</p>
          <p className="text-xs text-gray-400">Try adjusting your filters or search terms</p>
        </div>
      )}

      {!loading && filteredAndSortedTasks.length > 0 && (
        <div className="space-y-3">
          {filteredAndSortedTasks.map((task) => (
            <div
              key={task.taskId}
              className={`p-3 border rounded-lg transition-colors ${
                currentTaskId === task.taskId
                  ? 'border-blue-300 bg-blue-50'
                  : selectedTasks.has(task.taskId)
                  ? 'border-blue-200 bg-blue-25'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  {showBulkActions && (
                    <input
                      type="checkbox"
                      checked={selectedTasks.has(task.taskId)}
                      onChange={() => toggleTaskSelection(task.taskId)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      onClick={(e) => e.stopPropagation()}
                    />
                  )}
                  <span 
                    className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium cursor-pointer ${getStatusColor(task.status)}`}
                    onClick={() => onTaskSelected(task)}
                  >
                    {task.status}
                  </span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeTask(task.taskId);
                  }}
                  className="text-gray-400 hover:text-red-500"
                  title="Remove from history"
                >
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
              
              <div 
                className="text-sm cursor-pointer"
                onClick={() => onTaskSelected(task)}
              >
                <div className="font-mono text-xs text-gray-600 mb-1">
                  {task.taskId.slice(0, 8)}...
                </div>
                
                {task.status === 'processing' && (
                  <div className="mb-1">
                    <div className="w-full bg-gray-200 rounded-full h-1">
                      <div
                        className="bg-blue-600 h-1 rounded-full"
                        style={{ width: `${task.progress}%` }}
                      />
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {task.progress}% complete
                    </div>
                  </div>
                )}
                
                <div className="text-xs text-gray-500">
                  {formatDate(task.createdAt)}
                </div>
                
                {task.message && (
                  <div className="text-xs text-gray-600 mt-1 truncate" title={task.message}>
                    {task.message}
                  </div>
                )}

                {task.status === 'completed' && task.downloadUrls && (
                  <div className="text-xs text-green-600 mt-1">
                    {task.downloadUrls.length} file{task.downloadUrls.length !== 1 ? 's' : ''} ready
                  </div>
                )}

                {task.status === 'completed' && task.completedAt && (
                  <div className="text-xs mt-1">
                    {(() => {
                      const timeRemaining = calculateTimeRemaining(task.completedAt);
                      if (timeRemaining === '已过期') {
                        return <span className="text-red-600 font-medium">⏰ 文件已过期</span>;
                      } else if (timeRemaining) {
                        const remainingHours = Math.floor((new Date(task.completedAt).getTime() + 24 * 60 * 60 * 1000 - new Date().getTime()) / (1000 * 60 * 60));
                        const isExpiringSoon = remainingHours <= 2;
                        return (
                          <span className={`${isExpiringSoon ? 'text-orange-600' : 'text-blue-600'} font-medium`}>
                            ⏰ {timeRemaining}
                          </span>
                        );
                      }
                      return null;
                    })()}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TaskHistory;