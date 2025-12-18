"""
PDF reading service for the Web Invoice Processor.

This module provides PDF file reading capabilities adapted for the web environment,
including page dimension extraction and image conversion functionality.
"""

import logging
from typing import Optional, Tuple
import fitz
from PIL import Image
import io


logger = logging.getLogger(__name__)


class PDFDocument:
    """Represents a PDF document for processing."""
    
    def __init__(self, file_path: str, page_count: int, dimensions: tuple, content=None):
        self.file_path = file_path
        self.page_count = page_count
        self.dimensions = dimensions
        self.content = content


class PDFReader:
    """
    PDF reader implementation for web environment.
    
    Provides functionality to read PDF files, extract page dimensions,
    and convert pages to images for processing.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def read_pdf(self, file_path: str) -> Optional[PDFDocument]:
        """
        Read PDF file.
        
        Args:
            file_path: PDF file path
            
        Returns:
            Optional[PDFDocument]: PDF document object, None if reading failed
        """
        try:
            # Open PDF file
            doc = fitz.open(file_path)
            
            # Get page count
            page_count = doc.page_count
            
            if page_count == 0:
                self.logger.warning(f"PDF file has no pages: {file_path}")
                doc.close()
                return None
            
            # Get first page dimensions as document dimensions
            first_page = doc[0]
            rect = first_page.rect
            dimensions = (rect.width, rect.height)
            
            # Create PDFDocument object
            pdf_document = PDFDocument(
                file_path=file_path,
                page_count=page_count,
                dimensions=dimensions,
                content=doc  # Keep document open, caller responsible for closing
            )
            
            self.logger.info(f"Successfully read PDF file: {file_path}, pages: {page_count}, dimensions: {dimensions}")
            return pdf_document
            
        except Exception as e:
            self.logger.error(f"Failed to read PDF file {file_path}: {str(e)}")
            return None
    
    def get_page_dimensions(self, pdf_doc: PDFDocument) -> Tuple[float, float]:
        """
        Get page dimensions.
        
        Args:
            pdf_doc: PDF document object
            
        Returns:
            Tuple[float, float]: Page dimensions (width, height) in points
        """
        try:
            if pdf_doc.content is None:
                self.logger.error("PDF document content is empty")
                return (0.0, 0.0)
            
            # Return stored dimension information
            return pdf_doc.dimensions
            
        except Exception as e:
            self.logger.error(f"Failed to get page dimensions: {str(e)}")
            return (0.0, 0.0)
    
    def extract_page_as_image(self, pdf_doc: PDFDocument, page_num: int = 0) -> Optional[Image.Image]:
        """
        Extract PDF page as image.
        
        Args:
            pdf_doc: PDF document object
            page_num: Page number, default 0 (first page)
            
        Returns:
            Optional[Image.Image]: PIL image object, None if extraction failed
        """
        try:
            if pdf_doc.content is None:
                self.logger.error("PDF document content is empty")
                return None
            
            doc = pdf_doc.content
            
            # Check if page number is valid
            if page_num < 0 or page_num >= doc.page_count:
                self.logger.error(f"Invalid page number: {page_num}, document total pages: {doc.page_count}")
                return None
            
            # Get specified page
            page = doc[page_num]
            
            # Set rendering parameters for high quality output
            # Use 2.0 scale factor for higher resolution (~300 DPI)
            matrix = fitz.Matrix(2.0, 2.0)
            
            # Render page as pixmap
            pix = page.get_pixmap(matrix=matrix)
            
            # Convert pixmap to PIL image
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            
            # Clean up resources
            pix = None
            
            self.logger.info(f"Successfully extracted page {page_num} as image, size: {img.size}")
            return img
            
        except Exception as e:
            self.logger.error(f"Failed to extract page as image (page {page_num}): {str(e)}")
            return None
    
    def close_document(self, pdf_doc: PDFDocument) -> None:
        """
        Close PDF document.
        
        Args:
            pdf_doc: PDF document object
        """
        try:
            if pdf_doc.content is not None:
                pdf_doc.content.close()
                self.logger.debug(f"Closed PDF document: {pdf_doc.file_path}")
        except Exception as e:
            self.logger.error(f"Failed to close PDF document: {str(e)}")