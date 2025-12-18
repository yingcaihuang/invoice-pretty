import React, { useState, useEffect } from 'react';
import { SessionManager } from '../utils/sessionManager';

interface PDFPreviewProps {
  pdfUrl: string;
  filename: string;
}

const PDFPreview: React.FC<PDFPreviewProps> = ({ pdfUrl, filename }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [authenticatedUrl, setAuthenticatedUrl] = useState<string>('');

  useEffect(() => {
    // Add session ID to the URL as a query parameter since iframe can't use custom headers
    const sessionId = SessionManager.getSessionId();
    const separator = pdfUrl.includes('?') ? '&' : '?';
    const urlWithSession = `${pdfUrl}${separator}session=${encodeURIComponent(sessionId)}`;
    setAuthenticatedUrl(urlWithSession);
  }, [pdfUrl]);

  const handleLoad = () => {
    setIsLoading(false);
    setHasError(false);
  };

  const handleError = () => {
    setIsLoading(false);
    setHasError(true);
  };

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <div className="mt-4 border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
          </svg>
          <span className="text-sm font-medium text-gray-700">PDF 预览</span>
          <span className="text-xs text-gray-500">({filename})</span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={toggleExpanded}
            className="text-sm text-blue-600 hover:text-blue-800 focus:outline-none"
          >
            {isExpanded ? '收起' : '展开'}
          </button>
        </div>
      </div>

      {/* Preview Content */}
      <div className={`transition-all duration-300 ${isExpanded ? 'h-96' : 'h-64'}`}>
        {isLoading && (
          <div className="flex items-center justify-center h-full bg-gray-50">
            <div className="flex items-center space-x-2 text-gray-600">
              <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span className="text-sm">加载 PDF 预览中...</span>
            </div>
          </div>
        )}

        {hasError && (
          <div className="flex flex-col items-center justify-center h-full bg-gray-50 text-gray-600">
            <svg className="w-12 h-12 mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm mb-2">PDF 预览加载失败</p>
            <p className="text-xs text-gray-500">请尝试直接下载文件查看</p>
          </div>
        )}

        {!hasError && authenticatedUrl && (
          <iframe
            src={authenticatedUrl}
            className={`w-full h-full border-0 ${isLoading ? 'opacity-0' : 'opacity-100'}`}
            title={`PDF Preview: ${filename}`}
            onLoad={handleLoad}
            onError={handleError}
          />
        )}
      </div>

      {/* Footer with actions */}
      <div className="bg-gray-50 px-4 py-2 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>提示：可以在预览框中直接滚动查看 PDF 内容</span>
          <a
            href={authenticatedUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800"
          >
            在新窗口中打开
          </a>
        </div>
      </div>
    </div>
  );
};

export default PDFPreview;