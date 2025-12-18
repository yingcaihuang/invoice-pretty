"""
Layout management service for the Web Invoice Processor.

This module provides layout calculation and positioning logic for invoice
layout processing, adapted for the web environment.
"""

import math
from typing import List, Tuple
from PIL import Image


class LayoutConfig:
    """Configuration for invoice layout."""
    
    def __init__(self, page_width: float = 210.0, page_height: float = 297.0,
                 columns: int = 2, rows: int = 4, margin: float = 10.0, spacing: float = 5.0):
        self.page_width = page_width  # A4 width in mm
        self.page_height = page_height  # A4 height in mm
        self.columns = columns
        self.rows = rows
        self.margin = margin
        self.spacing = spacing
        
        # Calculate derived properties
        self.total_slots = columns * rows
        self.cell_width = (page_width - 2 * margin - (columns - 1) * spacing) / columns
        self.cell_height = (page_height - 2 * margin - (rows - 1) * spacing) / rows


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


class LayoutManager:
    """
    Layout manager implementation for web environment.
    
    Provides layout calculation and invoice positioning functionality
    for creating properly formatted PDF layouts.
    """
    
    def __init__(self):
        """Initialize layout manager."""
        self.default_config = LayoutConfig()
    
    def calculate_layout(self, invoice_count: int) -> LayoutConfig:
        """
        Calculate layout configuration.
        
        Args:
            invoice_count: Number of invoices
            
        Returns:
            LayoutConfig: Layout configuration object
        """
        # Use default 2x4 grid configuration
        return LayoutConfig(
            page_width=210.0,  # A4 width in mm
            page_height=297.0,  # A4 height in mm
            columns=2,
            rows=4,
            margin=10.0,
            spacing=5.0
        )
    
    def calculate_scale_factor(self, original_size: Tuple[float, float], target_size: Tuple[float, float]) -> float:
        """
        Calculate scale factor while maintaining aspect ratio.
        
        Args:
            original_size: Original size (width, height)
            target_size: Target size (width, height)
            
        Returns:
            float: Scale factor
        """
        if original_size[0] <= 0 or original_size[1] <= 0:
            return 1.0
        
        if target_size[0] <= 0 or target_size[1] <= 0:
            return 1.0
        
        # Calculate width and height scale ratios
        width_scale = target_size[0] / original_size[0]
        height_scale = target_size[1] / original_size[1]
        
        # Choose smaller scale ratio to maintain aspect ratio
        scale_factor = min(width_scale, height_scale)
        
        return scale_factor
    
    def position_invoices(self, invoices: List[Image.Image], layout: LayoutConfig, file_paths: List[str]) -> List[PositionedInvoice]:
        """
        Calculate invoice position allocation.
        
        Args:
            invoices: List of invoice images
            layout: Layout configuration
            file_paths: Corresponding file paths list
            
        Returns:
            List[PositionedInvoice]: List of positioned invoices
        """
        positioned_invoices = []
        
        if not invoices:
            return positioned_invoices
        
        # Ensure file paths list length matches
        if len(file_paths) != len(invoices):
            # If paths are insufficient, fill with empty strings
            file_paths = file_paths + [''] * (len(invoices) - len(file_paths))
        
        # Calculate invoices per page
        invoices_per_page = layout.total_slots  # 2 * 4 = 8
        total_pages = math.ceil(len(invoices) / invoices_per_page)
        
        for page_num in range(total_pages):
            # Calculate current page invoice range
            start_idx = page_num * invoices_per_page
            end_idx = min(start_idx + invoices_per_page, len(invoices))
            page_invoices = invoices[start_idx:end_idx]
            page_file_paths = file_paths[start_idx:end_idx]
            
            # Calculate position for each invoice on current page
            for i, (invoice_image, file_path) in enumerate(zip(page_invoices, page_file_paths)):
                # Calculate grid position (from top-left, fill by rows)
                row = i // layout.columns
                col = i % layout.columns
                
                # Calculate target cell dimensions
                cell_width = layout.cell_width
                cell_height = layout.cell_height
                
                # Get original image dimensions (convert to mm, assuming 72 DPI)
                original_width_px, original_height_px = invoice_image.size
                # Convert pixels to mm (72 DPI = 72/25.4 pixels per mm)
                pixels_per_mm = 72 / 25.4
                original_width_mm = original_width_px / pixels_per_mm
                original_height_mm = original_height_px / pixels_per_mm
                
                # Calculate scale factor
                scale_factor = self.calculate_scale_factor(
                    (original_width_mm, original_height_mm),
                    (cell_width, cell_height)
                )
                
                # Calculate scaled dimensions
                scaled_width = original_width_mm * scale_factor
                scaled_height = original_height_mm * scale_factor
                
                # Calculate position (center aligned)
                cell_x = layout.margin + col * (cell_width + layout.spacing)
                cell_y = layout.margin + row * (cell_height + layout.spacing)
                
                # Center within cell
                x = cell_x + (cell_width - scaled_width) / 2
                y = cell_y + (cell_height - scaled_height) / 2
                
                # Create positioned invoice object
                positioned_invoice = PositionedInvoice(
                    image=invoice_image,
                    x=x,
                    y=y,
                    width=scaled_width,
                    height=scaled_height,
                    page_number=page_num,
                    original_file_path=file_path
                )
                
                positioned_invoices.append(positioned_invoice)
        
        return positioned_invoices
    
    def calculate_pages_needed(self, invoice_count: int) -> int:
        """
        Calculate number of pages needed.
        
        Args:
            invoice_count: Number of invoices
            
        Returns:
            int: Number of pages needed
        """
        if invoice_count <= 0:
            return 0
        
        layout = self.calculate_layout(invoice_count)
        return math.ceil(invoice_count / layout.total_slots)
    
    def get_invoice_positions_for_page(self, page_number: int, layout: LayoutConfig) -> List[Tuple[int, int]]:
        """
        Get invoice grid positions for specified page.
        
        Args:
            page_number: Page number (starting from 0)
            layout: Layout configuration
            
        Returns:
            List[Tuple[int, int]]: Grid position list [(row, col), ...]
        """
        positions = []
        invoices_per_page = layout.total_slots
        
        for i in range(invoices_per_page):
            row = i // layout.columns
            col = i % layout.columns
            positions.append((row, col))
        
        return positions