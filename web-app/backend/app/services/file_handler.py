"""
File handling service for the Web Invoice Processor.

This module provides file validation, ZIP extraction, and file management
functionality adapted for the web environment with proper cleanup.
"""

import os
import logging
import tempfile
import shutil
from pathlib import Path
from typing import List
from datetime import datetime
import fitz
import zipfile

from .file_storage import FileStorageManager


logger = logging.getLogger(__name__)


class WebFileHandler:
    """
    Web-adapted file handler for invoice processing.
    
    Provides file validation, ZIP extraction, and cleanup functionality
    specifically designed for the web environment with proper resource management.
    """
    
    def __init__(self, file_storage: FileStorageManager):
        """
        Initialize the web file handler.
        
        Args:
            file_storage: File storage manager instance
        """
        self.logger = logging.getLogger(__name__)
        self.file_storage = file_storage
        self.temp_dirs = []  # Track temporary directories for cleanup
        
    def validate_pdf_file(self, file_path: str) -> bool:
        """
        Validate PDF file format.
        
        Args:
            file_path: PDF file path
            
        Returns:
            bool: True if file is valid PDF format
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                self.logger.warning(f"File does not exist: {file_path}")
                return False
            
            # Check file extension
            if not file_path.lower().endswith('.pdf'):
                self.logger.warning(f"File extension is not PDF: {file_path}")
                return False
            
            # Try to open with PyMuPDF to validate format
            try:
                doc = fitz.open(file_path)
                # Check if at least one page exists
                if doc.page_count == 0:
                    self.logger.warning(f"PDF file has no pages: {os.path.basename(file_path)}")
                    doc.close()
                    return False
                self.logger.debug(f"PDF file validation successful: {os.path.basename(file_path)} ({doc.page_count} pages)")
                doc.close()
                return True
            except Exception as e:
                self.logger.warning(f"Cannot open PDF file {os.path.basename(file_path)}: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error validating PDF file {file_path}: {str(e)}")
            return False
    
    def validate_zip_file(self, file_path: str) -> bool:
        """
        Validate ZIP file format.
        
        Args:
            file_path: ZIP file path
            
        Returns:
            bool: True if file is valid ZIP format
        """
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"File does not exist: {file_path}")
                return False
            
            if not file_path.lower().endswith('.zip'):
                return False
            
            # Try to open ZIP file
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Check if ZIP file is corrupted
                bad_file = zip_file.testzip()
                if bad_file:
                    self.logger.warning(f"ZIP file corrupted, contains bad file: {bad_file}")
                    return False
                return True
                
        except Exception as e:
            self.logger.warning(f"Cannot open ZIP file {file_path}: {str(e)}")
            return False
    
    def extract_pdfs_from_zip(self, zip_path: str, task_id: str) -> List[str]:
        """
        Extract PDF files from ZIP file for web environment.
        
        Args:
            zip_path: ZIP file path
            task_id: Task identifier for temporary directory naming
            
        Returns:
            List[str]: List of extracted PDF file paths
        """
        extracted_pdfs = []
        
        try:
            if not self.validate_zip_file(zip_path):
                return extracted_pdfs
            
            # Create temporary directory using file storage manager
            temp_dir = self.file_storage.create_temp_directory(task_id)
            if temp_dir is None:
                self.logger.error(f"Failed to create temp directory for task {task_id}")
                return extracted_pdfs
            
            self.temp_dirs.append(temp_dir)
            
            self.logger.info(f"Starting ZIP file extraction: {zip_path}")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                # Get all files in ZIP
                file_list = zip_file.namelist()
                
                pdf_count = 0
                for file_name in file_list:
                    # Only process PDF files, ignore OFD and other files
                    if file_name.lower().endswith('.pdf'):
                        try:
                            # Extract PDF file
                            zip_file.extract(file_name, temp_dir)
                            extracted_path = temp_dir / file_name
                            
                            # Validate extracted PDF file
                            if self.validate_pdf_file(str(extracted_path)):
                                extracted_pdfs.append(str(extracted_path))
                                pdf_count += 1
                                self.logger.info(f"Successfully extracted PDF file: {file_name}")
                            else:
                                self.logger.warning(f"Extracted PDF file is invalid: {file_name}")
                                
                        except Exception as e:
                            self.logger.warning(f"Failed to extract file {file_name}: {str(e)}")
                
                self.logger.info(f"Successfully extracted {pdf_count} PDF files from ZIP file {zip_path}")
                
        except Exception as e:
            self.logger.error(f"Error processing ZIP file {zip_path}: {str(e)}")
        
        return extracted_pdfs
    
    def cleanup_temp_dirs(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    self.logger.debug(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up temp directory {temp_dir}: {str(e)}")
        self.temp_dirs.clear()
    
    def get_pdf_files_from_uploads(self, session_id: str, task_id: str, uploaded_files: List[str]) -> List[str]:
        """
        Get PDF files from uploaded files, supporting ZIP file auto-extraction.
        
        Args:
            session_id: Session identifier
            task_id: Task identifier
            uploaded_files: List of uploaded file names
            
        Returns:
            List[str]: List of valid PDF file paths
        """
        pdf_files = []
        
        try:
            for filename in uploaded_files:
                # Get file path from storage
                file_path = self.file_storage.get_upload_path(session_id, task_id, filename)
                if file_path is None:
                    self.logger.warning(f"Upload file not found: {filename}")
                    continue
                
                file_path_str = str(file_path)
                
                # Process PDF files
                if filename.lower().endswith('.pdf'):
                    if self.validate_pdf_file(file_path_str):
                        pdf_files.append(file_path_str)
                        self.logger.info(f"Found valid PDF file: {filename}")
                    else:
                        self.logger.warning(f"Skipping invalid PDF file: {filename}")
                
                # Process ZIP files
                elif filename.lower().endswith('.zip'):
                    self.logger.info(f"Found ZIP file, starting processing: {filename}")
                    extracted_pdfs = self.extract_pdfs_from_zip(file_path_str, task_id)
                    pdf_files.extend(extracted_pdfs)
            
            self.logger.info(f"Total found {len(pdf_files)} valid PDF files")
            
        except Exception as e:
            self.logger.error(f"Error getting PDF files from uploads: {str(e)}")
        
        return sorted(pdf_files)  # Return sorted file list
    
    def generate_output_filename(self, input_files: List[str], task_id: str) -> str:
        """
        Generate output filename for web environment.
        
        Args:
            input_files: List of input file paths
            task_id: Task identifier
            
        Returns:
            str: Generated output filename
        """
        try:
            # Get current date time
            now = datetime.now()
            date_str = now.strftime("%Y%m%d_%H%M%S")
            
            # Calculate invoice count
            invoice_count = len(input_files)
            
            # Generate descriptive filename with task ID
            filename = f"invoice_layout_{date_str}_{invoice_count}invoices_{task_id[:8]}.pdf"
            
            self.logger.info(f"Generated output filename: {filename}")
            return filename
            
        except Exception as e:
            # If generation fails, use default filename
            self.logger.error(f"Error generating output filename: {str(e)}")
            fallback_name = f"invoice_layout_{datetime.now().strftime('%Y%m%d')}_{task_id[:8]}.pdf"
            self.logger.info(f"Using fallback filename: {fallback_name}")
            return fallback_name
    
    def validate_upload_file(self, filename: str, content_type: str, file_size: int, max_size: int = 50 * 1024 * 1024) -> bool:
        """
        Validate uploaded file before processing.
        
        Args:
            filename: Original filename
            content_type: MIME type
            file_size: File size in bytes
            max_size: Maximum allowed file size in bytes (default: 50MB)
            
        Returns:
            bool: True if file is valid for processing
        """
        try:
            # Check file size
            if file_size > max_size:
                self.logger.warning(f"File size {file_size} exceeds maximum {max_size}: {filename}")
                return False
            
            # Check file extension
            if not (filename.lower().endswith('.pdf') or filename.lower().endswith('.zip')):
                self.logger.warning(f"Invalid file extension: {filename}")
                return False
            
            # Check content type
            allowed_types = [
                'application/pdf',
                'application/zip',
                'application/x-zip-compressed',
                'application/octet-stream'  # Some browsers send this for ZIP files
            ]
            
            if content_type not in allowed_types:
                self.logger.warning(f"Invalid content type {content_type}: {filename}")
                return False
            
            self.logger.debug(f"Upload file validation successful: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating upload file {filename}: {str(e)}")
            return False