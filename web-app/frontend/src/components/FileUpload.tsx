import React, { useState, useRef, useCallback, useEffect } from 'react';
import { apiClient } from '../utils/api';
import { FileUploadItem, Task } from '../types';

interface FileUploadProps {
  onTaskCreated: (task: Task) => void;
}

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ACCEPTED_TYPES = ['application/pdf', 'application/zip', 'application/x-zip-compressed'];

const validateFile = (file: File): string | null => {
  if (!ACCEPTED_TYPES.includes(file.type) && !file.name.toLowerCase().endsWith('.pdf') && !file.name.toLowerCase().endsWith('.zip')) {
    return `File "${file.name}" is not a valid PDF or ZIP file`;
  }
  if (file.size > MAX_FILE_SIZE) {
    return `File "${file.name}" exceeds the maximum size limit of 50MB`;
  }
  return null;
};

const FileUpload: React.FC<FileUploadProps> = ({ onTaskCreated }) => {
  const [files, setFiles] = useState<FileUploadItem[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isTouchDevice, setIsTouchDevice] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Detect touch device
  useEffect(() => {
    setIsTouchDevice('ontouchstart' in window || navigator.maxTouchPoints > 0);
  }, []);

  const createFileItem = (file: File): FileUploadItem => ({
    file,
    id: Math.random().toString(36).substring(2, 11),
    status: 'pending',
    progress: 0,
  });

  const handleFiles = useCallback((fileList: FileList) => {
    const newFiles: FileUploadItem[] = [];
    const errors: string[] = [];

    Array.from(fileList).forEach(file => {
      const error = validateFile(file);
      if (error) {
        errors.push(error);
      } else {
        newFiles.push(createFileItem(file));
      }
    });

    if (errors.length > 0) {
      setError(errors.join(', '));
    } else {
      setError(null);
    }

    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  // Touch gesture handlers
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 1) {
      setIsDragOver(true);
    }
  }, []);

  const handleTouchEnd = useCallback((e: React.TouchEvent) => {
    setIsDragOver(false);
    // On touch devices, trigger file selection on tap
    if (e.touches.length === 0) {
      fileInputRef.current?.click();
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  }, [handleFiles]);

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const clearFiles = () => {
    setFiles([]);
    setError(null);
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;

    setIsUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      const filesToUpload = files.map(f => f.file);
      
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await apiClient.uploadFiles(filesToUpload);
      
      clearInterval(progressInterval);
      setUploadProgress(100);

      // Create task object from response
      const task: Task = {
        taskId: response.taskId,
        status: response.status,
        progress: 0,
        createdAt: new Date().toISOString(),
        message: response.message,
      };

      onTaskCreated(task);
      clearFiles();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4 sm:p-6">
      <h2 className="text-xl sm:text-2xl font-semibold text-gray-800 mb-4">Upload Files</h2>
      
      {/* Drag and drop area */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 sm:p-8 text-center transition-colors touch-manipulation ${
          isDragOver
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400 active:border-blue-400 active:bg-blue-50'
        } ${isTouchDevice ? 'cursor-pointer' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onTouchStart={isTouchDevice ? handleTouchStart : undefined}
        onTouchEnd={isTouchDevice ? handleTouchEnd : undefined}
        onClick={isTouchDevice ? () => fileInputRef.current?.click() : undefined}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        aria-label="Upload files area"
      >
        <div className="space-y-4">
          <div className="text-gray-500">
            <svg
              className="mx-auto h-10 w-10 sm:h-12 sm:w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
              aria-hidden="true"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <div>
            <p className="text-base sm:text-lg text-gray-600">
              {isTouchDevice ? 'Tap to select your PDF or ZIP files' : 'Drag and drop your PDF or ZIP files here'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {isTouchDevice ? 'Max 50MB each' : 'or click to select files (max 50MB each)'}
            </p>
          </div>
          {!isTouchDevice && (
            <button
              type="button"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              onClick={() => fileInputRef.current?.click()}
            >
              Select Files
            </button>
          )}
        </div>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.zip"
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* File list */}
      {files.length > 0 && (
        <div className="mt-6">
          <h3 className="text-base sm:text-lg font-medium text-gray-800 mb-3">Selected Files</h3>
          <div className="space-y-2">
            {files.map((fileItem) => (
              <div
                key={fileItem.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {fileItem.file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {(fileItem.file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button
                  onClick={() => removeFile(fileItem.id)}
                  className="ml-4 p-1 text-red-600 hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 rounded transition-colors"
                  aria-label={`Remove ${fileItem.file.name}`}
                >
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload progress */}
      {isUploading && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Uploading...</span>
            <span className="text-sm text-gray-600">{uploadProgress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Action buttons */}
      {files.length > 0 && (
        <div className="mt-6 flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-3">
          <button
            onClick={uploadFiles}
            disabled={isUploading}
            className="flex-1 bg-blue-600 text-white py-3 sm:py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors text-base sm:text-sm font-medium"
          >
            {isUploading ? 'Uploading...' : `Upload ${files.length} file${files.length > 1 ? 's' : ''}`}
          </button>
          <button
            onClick={clearFiles}
            disabled={isUploading}
            className="px-4 py-3 sm:py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors text-base sm:text-sm font-medium"
          >
            Clear
          </button>
        </div>
      )}
    </div>
  );
};

export default FileUpload;