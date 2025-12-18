// API utilities for communicating with the backend

import { SessionManager } from './sessionManager';
import { UploadResponse, TaskStatusResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiClient {
  private sessionInitialized = false;

  private async ensureSession(): Promise<void> {
    if (this.sessionInitialized) {
      return;
    }

    try {
      // Try to create a session with the backend using our frontend-generated session ID
      const sessionId = SessionManager.getSessionId();
      const response = await fetch(`${API_BASE_URL}/api/session`, {
        method: 'POST',
        headers: {
          'X-Session-ID': sessionId,
        },
      });

      if (response.ok) {
        console.log('Session initialized with backend');
      } else {
        console.warn('Failed to initialize session with backend, continuing with auto-creation');
      }
    } catch (error) {
      console.warn('Session initialization failed, continuing with auto-creation:', error);
    }

    this.sessionInitialized = true;
  }

  private getHeaders(): HeadersInit {
    return {
      'X-Session-ID': SessionManager.getSessionId(),
    };
  }

  async uploadFiles(files: File[]): Promise<UploadResponse> {
    await this.ensureSession();
    
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Upload failed' }));
      throw new Error(error.message || 'Upload failed');
    }

    return response.json();
  }

  async getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
    await this.ensureSession();
    
    const response = await fetch(`${API_BASE_URL}/api/task/${taskId}/status`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to get task status' }));
      throw new Error(error.message || 'Failed to get task status');
    }

    return response.json();
  }

  getDownloadUrl(taskId: string, filename: string): string {
    return `${API_BASE_URL}/api/download/${taskId}/${filename}`;
  }

  getPreviewUrl(taskId: string, filename: string): string {
    return `${API_BASE_URL}/api/download/${taskId}/${filename}?inline=true`;
  }
}

export const apiClient = new ApiClient();