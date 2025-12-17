"""
文件处理服务
实现PDF文件的验证、批量获取和输出文件名生成功能
"""

import os
import logging
from pathlib import Path
from typing import List
from datetime import datetime
import fitz
import zipfile
import tempfile
import shutil

from src.interfaces.base_interfaces import IFileHandler


class FileHandler(IFileHandler):
    """文件处理实现类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.temp_dirs = []  # 跟踪临时目录以便清理
        
    def validate_pdf_file(self, file_path: str) -> bool:
        """
        验证PDF文件格式
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            bool: 文件是否为有效的PDF格式
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.logger.warning(f"文件不存在: {file_path}")
                return False
            
            # 检查文件扩展名
            if not file_path.lower().endswith('.pdf'):
                self.logger.warning(f"文件扩展名不是PDF: {file_path}")
                return False
            
            # 尝试使用PyMuPDF打开文件验证格式
            try:
                doc = fitz.open(file_path)
                # 检查是否至少有一页
                if doc.page_count == 0:
                    self.logger.warning(f"PDF文件没有页面: {os.path.basename(file_path)}")
                    doc.close()
                    return False
                self.logger.debug(f"PDF文件验证成功: {os.path.basename(file_path)} ({doc.page_count} 页)")
                doc.close()
                return True
            except Exception as e:
                self.logger.warning(f"无法打开PDF文件 {os.path.basename(file_path)}: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"验证PDF文件时发生错误 {file_path}: {str(e)}")
            return False
    
    def validate_zip_file(self, file_path: str) -> bool:
        """
        验证ZIP文件格式
        
        Args:
            file_path: ZIP文件路径
            
        Returns:
            bool: 文件是否为有效的ZIP格式
        """
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"文件不存在: {file_path}")
                return False
            
            if not file_path.lower().endswith('.zip'):
                return False
            
            # 尝试打开ZIP文件
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # 检查ZIP文件是否损坏
                bad_file = zip_file.testzip()
                if bad_file:
                    self.logger.warning(f"ZIP文件损坏，包含坏文件: {bad_file}")
                    return False
                return True
                
        except Exception as e:
            self.logger.warning(f"无法打开ZIP文件 {file_path}: {str(e)}")
            return False
    
    def extract_pdfs_from_zip(self, zip_path: str) -> List[str]:
        """
        从ZIP文件中提取PDF文件
        
        Args:
            zip_path: ZIP文件路径
            
        Returns:
            List[str]: 提取的PDF文件路径列表
        """
        extracted_pdfs = []
        
        try:
            if not self.validate_zip_file(zip_path):
                return extracted_pdfs
            
            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix='invoice_zip_')
            self.temp_dirs.append(temp_dir)
            
            self.logger.info(f"开始解压ZIP文件: {zip_path}")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                # 获取ZIP文件中的所有文件
                file_list = zip_file.namelist()
                
                pdf_count = 0
                for file_name in file_list:
                    # 只处理PDF文件，忽略OFD和其他文件
                    if file_name.lower().endswith('.pdf'):
                        try:
                            # 提取PDF文件
                            zip_file.extract(file_name, temp_dir)
                            extracted_path = os.path.join(temp_dir, file_name)
                            
                            # 验证提取的PDF文件
                            if self.validate_pdf_file(extracted_path):
                                extracted_pdfs.append(extracted_path)
                                pdf_count += 1
                                self.logger.info(f"成功提取PDF文件: {file_name}")
                            else:
                                self.logger.warning(f"提取的PDF文件无效: {file_name}")
                                
                        except Exception as e:
                            self.logger.warning(f"提取文件 {file_name} 失败: {str(e)}")
                
                self.logger.info(f"从ZIP文件 {zip_path} 中成功提取 {pdf_count} 个PDF文件")
                
        except Exception as e:
            self.logger.error(f"处理ZIP文件时发生错误 {zip_path}: {str(e)}")
        
        return extracted_pdfs
    
    def cleanup_temp_dirs(self):
        """清理临时目录"""
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    self.logger.debug(f"清理临时目录: {temp_dir}")
            except Exception as e:
                self.logger.warning(f"清理临时目录失败 {temp_dir}: {str(e)}")
        self.temp_dirs.clear()
    
    def get_pdf_files(self, directory: str) -> List[str]:
        """
        获取目录中的PDF文件列表，支持ZIP文件自动解压
        
        Args:
            directory: 目录路径
            
        Returns:
            List[str]: 有效PDF文件路径列表
        """
        pdf_files = []
        
        try:
            # 检查目录是否存在
            if not os.path.exists(directory):
                self.logger.warning(f"目录不存在: {directory}")
                return pdf_files
            
            if not os.path.isdir(directory):
                self.logger.warning(f"路径不是目录: {directory}")
                return pdf_files
            
            # 遍历目录中的所有文件
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                
                # 跳过子目录
                if os.path.isdir(file_path):
                    continue
                
                # 处理PDF文件
                if filename.lower().endswith('.pdf'):
                    if self.validate_pdf_file(file_path):
                        pdf_files.append(file_path)
                        self.logger.info(f"找到有效PDF文件: {file_path}")
                    else:
                        self.logger.warning(f"跳过无效PDF文件: {file_path}")
                
                # 处理ZIP文件
                elif filename.lower().endswith('.zip'):
                    self.logger.info(f"发现ZIP文件，开始处理: {file_path}")
                    extracted_pdfs = self.extract_pdfs_from_zip(file_path)
                    pdf_files.extend(extracted_pdfs)
            
            self.logger.info(f"在目录 {directory} 中总共找到 {len(pdf_files)} 个有效PDF文件")
            
        except Exception as e:
            self.logger.error(f"获取PDF文件列表时发生错误: {str(e)}")
        
        return sorted(pdf_files)  # 返回排序后的文件列表
    
    def generate_output_filename(self, input_files: List[str]) -> str:
        """
        生成输出文件名
        
        Args:
            input_files: 输入文件路径列表
            
        Returns:
            str: 生成的输出文件名
        """
        try:
            # 获取当前日期时间
            now = datetime.now()
            date_str = now.strftime("%Y%m%d_%H%M%S")
            
            # 计算发票数量
            invoice_count = len(input_files)
            
            # 生成描述性文件名
            filename = f"发票拼版_{date_str}_{invoice_count}张.pdf"
            
            self.logger.info(f"生成输出文件名: {filename}")
            return filename
            
        except Exception as e:
            # 如果生成失败，使用默认文件名
            self.logger.error(f"生成输出文件名时发生错误: {str(e)}")
            fallback_name = f"发票拼版_{datetime.now().strftime('%Y%m%d')}.pdf"
            self.logger.info(f"使用备用文件名: {fallback_name}")
            return fallback_name