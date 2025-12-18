// Type definitions for the Web Invoice Processor

export type TaskStatus = 'queued' | 'processing' | 'completed' | 'failed' | 'expired';

export interface Task {
  taskId: string;
  status: TaskStatus;
  progress: number;
  message?: string;
  downloadUrls?: string[];
  createdAt: string;
  completedAt?: string;
  error?: string;
}

export interface UploadResponse {
  taskId: string;
  status: TaskStatus;
  message: string;
}

export interface TaskStatusResponse {
  taskId: string;
  status: TaskStatus;
  progress: number;
  message?: string;
  downloadUrls?: string[];
  createdAt: string;
  completedAt?: string;
}

export interface FileUploadItem {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
}
