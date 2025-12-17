#!/usr/bin/env python3
"""
PDF发票拼版打印系统 - 简化命令行版本
避免复杂的包导入问题
"""

import sys
import os
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List
import fitz
from PIL import Image
import io
import tempfile

def setup_logging(debug=False):
    """设置日志"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def validate_pdf_file(file_path: str) -> bool:
    """验证PDF文件"""
    try:
        if not file_path.lower().endswith('.pdf'):
            return False
        
        doc = fitz.open(file_path)
        page_count = doc.page_count
        doc.close()
        
        return page_count > 0
    except Exception:
        return False

def validate_zip_file(file_path: str) -> bool:
    """验证ZIP文件"""
    try:
        if not file_path.lower().endswith('.zip'):
            return False
        
        import zipfile
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            bad_file = zip_file.testzip()
            return bad_file is None
    except Exception:
        return False

def extract_pdfs_from_zip(zip_path: str) -> List[str]:
    """从ZIP文件中提取PDF文件"""
    import zipfile
    import tempfile
    
    extracted_pdfs = []
    
    try:
        if not validate_zip_file(zip_path):
            return extracted_pdfs
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix='invoice_zip_')
        
        print(f"正在解压ZIP文件: {Path(zip_path).name}")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            file_list = zip_file.namelist()
            
            for file_name in file_list:
                if file_name.lower().endswith('.pdf'):
                    try:
                        zip_file.extract(file_name, temp_dir)
                        extracted_path = os.path.join(temp_dir, file_name)
                        
                        if validate_pdf_file(extracted_path):
                            extracted_pdfs.append(extracted_path)
                            print(f"  提取PDF: {file_name}")
                    except Exception as e:
                        print(f"  提取失败 {file_name}: {e}")
        
        print(f"从ZIP文件中提取了 {len(extracted_pdfs)} 个PDF文件")
        
    except Exception as e:
        print(f"处理ZIP文件失败: {e}")
    
    return extracted_pdfs

def get_pdf_files(directory: str) -> List[str]:
    """获取目录中的PDF文件，支持ZIP文件自动解压"""
    pdf_files = []
    directory_path = Path(directory)
    
    if directory_path.is_file():
        # 处理单个文件
        if directory_path.suffix.lower() == '.pdf':
            if validate_pdf_file(str(directory_path)):
                return [str(directory_path)]
        elif directory_path.suffix.lower() == '.zip':
            return extract_pdfs_from_zip(str(directory_path))
        return []
    
    # 处理目录
    for file_path in directory_path.iterdir():
        if file_path.is_file():
            if file_path.suffix.lower() == '.pdf':
                if validate_pdf_file(str(file_path)):
                    pdf_files.append(str(file_path))
            elif file_path.suffix.lower() == '.zip':
                # 处理ZIP文件
                extracted_pdfs = extract_pdfs_from_zip(str(file_path))
                pdf_files.extend(extracted_pdfs)
    
    return sorted(pdf_files)

def calculate_scale_factor(original_size, target_size):
    """计算缩放因子，保持纵横比"""
    orig_width, orig_height = original_size
    target_width, target_height = target_size
    
    if orig_width <= 0 or orig_height <= 0 or target_width <= 0 or target_height <= 0:
        return 1.0
    
    scale_x = target_width / orig_width
    scale_y = target_height / orig_height
    
    return min(scale_x, scale_y)

def process_invoices(input_files: List[str], output_path: str) -> dict:
    """处理发票文件"""
    logger = logging.getLogger(__name__)
    
    try:
        # 布局配置 (2列4行)
        page_width_mm = 210  # A4宽度
        page_height_mm = 297  # A4高度
        margin_mm = 10
        spacing_mm = 5
        columns = 2
        rows = 4
        
        # 计算单元格尺寸
        available_width = page_width_mm - 2 * margin_mm - (columns - 1) * spacing_mm
        available_height = page_height_mm - 2 * margin_mm - (rows - 1) * spacing_mm
        cell_width = available_width / columns
        cell_height = available_height / rows
        
        # 转换为点 (1mm = 2.834645669 points)
        mm_to_points = 2.834645669
        page_width = page_width_mm * mm_to_points
        page_height = page_height_mm * mm_to_points
        margin = margin_mm * mm_to_points
        spacing = spacing_mm * mm_to_points
        cell_w = cell_width * mm_to_points
        cell_h = cell_height * mm_to_points
        
        logger.info(f"开始处理 {len(input_files)} 个PDF文件")
        
        # 读取所有发票
        invoice_images = []
        processed_files = []
        
        for file_path in input_files:
            try:
                doc = fitz.open(file_path)
                if doc.page_count > 0:
                    page = doc[0]  # 只处理第一页
                    
                    # 转换为图像
                    mat = fitz.Matrix(2.0, 2.0)  # 2x缩放提高质量
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    
                    # 转换为PIL图像
                    pil_image = Image.open(io.BytesIO(img_data))
                    invoice_images.append((pil_image, file_path))
                    processed_files.append(file_path)
                    
                doc.close()
                logger.info(f"处理文件: {Path(file_path).name}")
                
            except Exception as e:
                logger.warning(f"跳过文件 {file_path}: {e}")
        
        if not invoice_images:
            return {
                'success': False,
                'error': '没有成功处理的PDF文件',
                'processed_count': 0
            }
        
        # 创建输出PDF
        output_doc = fitz.open()
        invoices_per_page = columns * rows
        total_pages = (len(invoice_images) + invoices_per_page - 1) // invoices_per_page
        
        logger.info(f"将创建 {total_pages} 页输出")
        
        for page_num in range(total_pages):
            # 创建新页面
            page = output_doc.new_page(width=page_width, height=page_height)
            
            # 计算当前页面的发票范围
            start_idx = page_num * invoices_per_page
            end_idx = min(start_idx + invoices_per_page, len(invoice_images))
            
            # 放置发票
            for i in range(start_idx, end_idx):
                invoice_img, _ = invoice_images[i]
                
                # 计算网格位置
                grid_idx = i - start_idx
                row = grid_idx // columns
                col = grid_idx % columns
                
                # 计算位置
                x = margin + col * (cell_w + spacing)
                y = margin + row * (cell_h + spacing)
                
                # 计算缩放
                orig_width, orig_height = invoice_img.size
                scale = calculate_scale_factor((orig_width, orig_height), (cell_w, cell_h))
                
                scaled_width = orig_width * scale
                scaled_height = orig_height * scale
                
                # 居中
                center_x = x + (cell_w - scaled_width) / 2
                center_y = y + (cell_h - scaled_height) / 2
                
                # 保存图像为临时文件
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    invoice_img.save(tmp_file.name, 'PNG')
                    
                    # 插入图像
                    rect = fitz.Rect(center_x, center_y, center_x + scaled_width, center_y + scaled_height)
                    page.insert_image(rect, filename=tmp_file.name)
                    
                    # 清理临时文件
                    os.unlink(tmp_file.name)
        
        # 保存输出文件
        output_doc.save(output_path)
        output_doc.close()
        
        logger.info(f"输出保存到: {output_path}")
        
        return {
            'success': True,
            'output_file': output_path,
            'processed_count': len(processed_files),
            'total_pages': total_pages,
            'processed_files': processed_files
        }
        
    except Exception as e:
        logger.error(f"处理失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'processed_count': 0
        }

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PDF发票拼版打印系统 - 命令行版本')
    parser.add_argument('input', help='输入PDF文件或目录路径')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    args = parser.parse_args()
    
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    # 验证输入路径
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误: 输入路径不存在: {input_path}")
        sys.exit(1)
    
    # 设置输出路径
    if args.output:
        output_path = Path(args.output)
    else:
        if input_path.is_file():
            output_path = input_path.parent / f"拼版_{input_path.stem}.pdf"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = input_path / f"拼版输出_{timestamp}.pdf"
    
    print(f"输入: {input_path}")
    print(f"输出: {output_path}")
    
    # 获取PDF文件
    if input_path.is_file():
        if input_path.suffix.lower() == '.pdf':
            if validate_pdf_file(str(input_path)):
                input_files = [str(input_path)]
            else:
                print("错误: 不是有效的PDF文件")
                sys.exit(1)
        elif input_path.suffix.lower() == '.zip':
            input_files = extract_pdfs_from_zip(str(input_path))
            if not input_files:
                print("错误: ZIP文件中没有找到有效的PDF文件")
                sys.exit(1)
        else:
            print("错误: 不支持的文件格式，请使用PDF或ZIP文件")
            sys.exit(1)
    else:
        input_files = get_pdf_files(str(input_path))
        if not input_files:
            print("错误: 目录中没有找到有效的PDF文件")
            sys.exit(1)
    
    print(f"找到 {len(input_files)} 个PDF文件")
    
    # 处理文件
    result = process_invoices(input_files, str(output_path))
    
    if result['success']:
        print(f"✓ 处理成功!")
        print(f"  输出文件: {result['output_file']}")
        print(f"  处理文件数: {result['processed_count']}")
        print(f"  生成页数: {result['total_pages']}")
    else:
        print(f"✗ 处理失败: {result['error']}")
        sys.exit(1)

if __name__ == '__main__':
    main()