"""
PDF processing service for the Web Invoice Processor.

This module adapts the desktop PDF processing logic for the web environment,
providing thread-safe processing with proper file path handling and web-compatible logging.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import List, Optional, Callable
import fitz
from PIL import Image
import io
import threading

from .file_storage import FileStorageManager
from .pdf_reader import PDFReader
from .layout_manager import LayoutManager
from ..models.data_models import Task, TaskStatus


logger = logging.getLogger(__name__)

# Progress callback type for web environment
ProgressCallback = Callable[[int, str], None]


class ProcessResult:
    """Result of PDF processing operation."""
    
    def __init__(self):
        self.success = False
        self.output_file = ""
        self.processed_count = 0
        self.total_pages = 0
        self.errors = []
        self.skipped_files = []


class PDFDocument:
    """Represents a PDF document for processing."""
    
    def __init__(self, file_path: str, page_count: int, dimensions: tuple, content=None):
        self.file_path = file_path
        self.page_count = page_count
        self.dimensions = dimensions
        self.content = content


class PositionedInvoice:
    """Represents a positioned invoice in the layout."""
    
    def __init__(self, image: Image.Image, x: float, y: float, width: float, height: float, 
                 page_number: int, original_file_path: str):
        self.image = image
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.page_number = page_number
        self.original_file_path = original_file_path


class WebPDFProcessor:
    """
    Web-adapted PDF processor for invoice layout processing.
    
    This class adapts the desktop PDF processing logic for the web environment,
    ensuring thread safety and proper integration with the web application's
    file storage and task management systems.
    """
    
    def __init__(self, file_storage: FileStorageManager):
        """
        Initialize the web PDF processor.
        
        Args:
            file_storage: File storage manager instance
        """
        self.logger = logging.getLogger(__name__)
        self.file_storage = file_storage
        self.pdf_reader = PDFReader()
        self.layout_manager = LayoutManager()
        
        # Thread-safe processing settings
        self._lock = threading.Lock()
        
        # Output quality parameters (300 DPI or higher)
        self.output_dpi = 300
        self.scale_factor = self.output_dpi / 72  # From 72 DPI to 300 DPI
    
    def process_invoices_async(self, task_id: str, session_id: str, 
                              input_file_paths: List[str],
                              progress_callback: Optional[ProgressCallback] = None) -> ProcessResult:
        """
        Process invoice files asynchronously for web environment.
        
        Args:
            task_id: Unique task identifier
            session_id: Session identifier
            input_file_paths: List of input file paths
            progress_callback: Optional progress callback function
            
        Returns:
            ProcessResult: Processing result with success status and details
        """
        with self._lock:  # Ensure thread safety
            self.logger.info(f"Starting async processing for task {task_id} with {len(input_file_paths)} files")
            
            # Initialize result
            result = ProcessResult()
            result.output_file = f"invoice_layout_{task_id}.pdf"
            
            try:
                # Step 1: Validate input files
                if progress_callback:
                    progress_callback(10, "Validating input files...")
                
                valid_files = []
                for file_path in input_file_paths:
                    if self._validate_pdf_file(file_path):
                        valid_files.append(file_path)
                        self.logger.info(f"✓ Validation passed: {os.path.basename(file_path)}")
                    else:
                        result.skipped_files.append(file_path)
                        result.errors.append(f"Invalid PDF file: {file_path}")
                        self.logger.warning(f"✗ Validation failed: {os.path.basename(file_path)}")
                
                if not valid_files:
                    result.errors.append("No valid PDF files found")
                    self.logger.error("No valid PDF files found")
                    return result
                
                result.processed_count = len(valid_files)
                self.logger.info(f"File validation complete, valid files: {len(valid_files)}")
                
                # Step 2: Read PDF files and extract images
                if progress_callback:
                    progress_callback(30, "Reading PDF files...")
                
                invoice_images = []
                pdf_documents = []
                
                for i, file_path in enumerate(valid_files):
                    try:
                        filename = os.path.basename(file_path)
                        self.logger.info(f"Reading file: {filename}")
                        
                        # Read PDF document
                        pdf_doc = self.pdf_reader.read_pdf(file_path)
                        if pdf_doc is None:
                            result.skipped_files.append(file_path)
                            result.errors.append(f"Cannot read PDF file: {file_path}")
                            self.logger.error(f"✗ Cannot read PDF file: {filename}")
                            continue
                        
                        pdf_documents.append(pdf_doc)
                        
                        # Extract first page as image
                        image = self.pdf_reader.extract_page_as_image(pdf_doc, 0)
                        if image is None:
                            result.skipped_files.append(file_path)
                            result.errors.append(f"Cannot extract PDF page image: {file_path}")
                            self.logger.error(f"✗ Cannot extract image: {filename}")
                            continue
                        
                        invoice_images.append(image)
                        self.logger.info(f"✓ Successfully extracted image: {filename} (size: {image.size})")
                        
                        # Update progress
                        if progress_callback:
                            progress = 30.0 + (i + 1) / len(valid_files) * 30.0
                            progress_callback(int(progress), f"Read {i + 1}/{len(valid_files)} files")
                    
                    except Exception as e:
                        self.logger.error(f"Error processing file {os.path.basename(file_path)}: {str(e)}")
                        result.skipped_files.append(file_path)
                        result.errors.append(f"Processing file failed {file_path}: {str(e)}")
                
                if not invoice_images:
                    result.errors.append("No invoice images extracted successfully")
                    return result
                
                # Step 3: Calculate layout and positions
                if progress_callback:
                    progress_callback(60, "Calculating layout...")
                
                self.logger.info(f"Starting layout calculation, invoice count: {len(invoice_images)}")
                layout = self.layout_manager.calculate_layout(len(invoice_images))
                self.logger.info(f"Layout config: {layout.columns}x{layout.rows}, margin: {layout.margin}mm")
                
                positioned_invoices = self.layout_manager.position_invoices(
                    invoice_images, layout, valid_files
                )
                
                result.total_pages = self.layout_manager.calculate_pages_needed(len(invoice_images))
                self.logger.info(f"Layout calculation complete, will generate {result.total_pages} pages")
                
                # Step 4: Create layout PDF
                if progress_callback:
                    progress_callback(80, "Creating layout PDF...")
                
                self.logger.info("Starting layout PDF creation...")
                output_pdf = self._create_layout_pdf(positioned_invoices)
                if output_pdf is None:
                    result.errors.append("Failed to create layout PDF")
                    self.logger.error("Failed to create layout PDF")
                    return result
                
                self.logger.info(f"Layout PDF created successfully, {output_pdf.page_count} pages")
                
                # Step 5: Save PDF file to storage
                if progress_callback:
                    progress_callback(90, "Saving PDF file...")
                
                self.logger.info(f"Starting PDF file save: {result.output_file}")
                output_data = self._pdf_to_bytes(output_pdf)
                if output_data is None:
                    result.errors.append("Failed to convert PDF to bytes")
                    self.logger.error("Failed to convert PDF to bytes")
                    return result
                
                # Store output file using file storage manager
                output_path = self.file_storage.store_output(
                    session_id, task_id, output_data, result.output_file
                )
                
                if output_path is None:
                    result.errors.append("Failed to save PDF file")
                    self.logger.error("Failed to save PDF file")
                    return result
                
                result.output_file = str(output_path)
                self.logger.info(f"PDF file saved successfully: {output_path}")
                
                # Clean up resources
                for pdf_doc in pdf_documents:
                    self.pdf_reader.close_document(pdf_doc)
                
                if output_pdf.content:
                    output_pdf.content.close()
                
                # Complete
                if progress_callback:
                    progress_callback(100, "Processing complete")
                
                result.success = True
                self.logger.info(f"Successfully processed {len(invoice_images)} invoices, generated {result.total_pages} pages")
                
            except Exception as e:
                self.logger.error(f"Error during invoice processing: {str(e)}")
                result.errors.append(f"Processing error: {str(e)}")
            
            return result
    
    def _validate_pdf_file(self, file_path: str) -> bool:
        """
        Validate PDF file format.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            bool: True if file is valid PDF
        """
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"File does not exist: {file_path}")
                return False
            
            if not file_path.lower().endswith('.pdf'):
                self.logger.warning(f"File extension is not PDF: {file_path}")
                return False
            
            # Try to open with PyMuPDF to validate format
            try:
                doc = fitz.open(file_path)
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
    
    def _create_layout_pdf(self, positioned_invoices: List[PositionedInvoice]) -> Optional[PDFDocument]:
        """
        Create layout PDF document.
        
        Args:
            positioned_invoices: List of positioned invoices
            
        Returns:
            Optional[PDFDocument]: Created PDF document, None if failed
        """
        try:
            if not positioned_invoices:
                self.logger.error("No invoices to create PDF")
                return None
            
            # Create new PDF document
            doc = fitz.open()
            
            # Calculate A4 page dimensions (units: points, 1mm = 2.834645669 points)
            mm_to_points = 2.834645669
            page_width = 210 * mm_to_points  # A4 width
            page_height = 297 * mm_to_points  # A4 height
            
            # Group invoices by page
            pages_dict = {}
            for invoice in positioned_invoices:
                page_num = invoice.page_number
                if page_num not in pages_dict:
                    pages_dict[page_num] = []
                pages_dict[page_num].append(invoice)
            
            # Create PDF pages for each page
            for page_num in sorted(pages_dict.keys()):
                page_invoices = pages_dict[page_num]
                
                # Create new page
                page = doc.new_page(width=page_width, height=page_height)
                
                # Place each invoice on the page
                for invoice in page_invoices:
                    try:
                        # Convert invoice image to bytes
                        img_bytes = self._image_to_bytes(invoice.image)
                        if img_bytes is None:
                            continue
                        
                        # Calculate position and dimensions (convert mm to points)
                        x = invoice.x * mm_to_points
                        y = invoice.y * mm_to_points
                        width = invoice.width * mm_to_points
                        height = invoice.height * mm_to_points
                        
                        # Create rectangle area
                        rect = fitz.Rect(x, y, x + width, y + height)
                        
                        # Insert image to page
                        page.insert_image(rect, stream=img_bytes)
                        
                    except Exception as e:
                        self.logger.error(f"Failed to insert invoice image: {str(e)}")
                        continue
            
            # Create PDFDocument object
            pdf_document = PDFDocument(
                file_path="",  # Output file path will be set later
                page_count=doc.page_count,
                dimensions=(page_width, page_height),
                content=doc
            )
            
            self.logger.info(f"Successfully created layout PDF, {doc.page_count} pages")
            return pdf_document
            
        except Exception as e:
            self.logger.error(f"Failed to create layout PDF: {str(e)}")
            return None
    
    def _pdf_to_bytes(self, pdf_doc: PDFDocument) -> Optional[bytes]:
        """
        Convert PDF document to bytes.
        
        Args:
            pdf_doc: PDF document object
            
        Returns:
            Optional[bytes]: PDF bytes, None if failed
        """
        try:
            if pdf_doc.content is None:
                self.logger.error("PDF document content is empty")
                return None
            
            # Convert PDF to bytes
            pdf_bytes = pdf_doc.content.tobytes()
            
            self.logger.debug(f"Successfully converted PDF to bytes, size: {len(pdf_bytes)}")
            return pdf_bytes
            
        except Exception as e:
            self.logger.error(f"Failed to convert PDF to bytes: {str(e)}")
            return None
    
    def _image_to_bytes(self, image: Image.Image) -> Optional[bytes]:
        """
        Convert PIL image to bytes.
        
        Args:
            image: PIL image object
            
        Returns:
            Optional[bytes]: Image bytes, None if failed
        """
        try:
            # Ensure image is RGB mode
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save image to bytes
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG', quality=95, dpi=(self.output_dpi, self.output_dpi))
            img_bytes = img_buffer.getvalue()
            img_buffer.close()
            
            return img_bytes
            
        except Exception as e:
            self.logger.error(f"Failed to convert image to bytes: {str(e)}")
            return None
    
    def get_output_quality_dpi(self) -> int:
        """
        Get output quality DPI setting.
        
        Returns:
            int: DPI value
        """
        return self.output_dpi
    
    def set_output_quality_dpi(self, dpi: int) -> None:
        """
        Set output quality DPI.
        
        Args:
            dpi: DPI value, minimum 300
        """
        if dpi < 300:
            self.logger.warning(f"DPI value {dpi} below minimum requirement 300, setting to 300")
            dpi = 300
        
        self.output_dpi = dpi
        self.scale_factor = dpi / 72
        self.logger.info(f"Output quality DPI set to: {dpi}")