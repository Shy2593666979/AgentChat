import os
import sys
import platform
import subprocess
from loguru import logger

def convert_to_pdf(input_path):
    if not os.path.exists(input_path):
        raise ValueError(f"文件不存在: {input_path}")

    filename, ext = os.path.splitext(input_path)
    output_path = filename + ".pdf"
    
    # 支持的文件格式
    supported_formats = ['.docx', '.doc', '.odt', '.rtf', '.txt', '.html', '.htm', 
                        '.xls', '.xlsx', '.ods', '.ppt', '.pptx', '.odp']
    
    if ext.lower() not in supported_formats:
        raise ValueError(f"不支持的文件类型: {ext}，支持的格式有: {', '.join(supported_formats)}")
    
    try:
        # 获取LibreOffice可执行文件路径
        libreoffice_cmd = get_libreoffice_command()
        
        # 获取输出目录
        output_dir = os.path.dirname(output_path)
        if not output_dir:
            output_dir = '../rag'
            
        # 构建LibreOffice命令
        cmd = [
            libreoffice_cmd,
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', output_dir,
            input_path
        ]
        
        # 执行转换命令
        logger.info(f"执行命令: {' '.join(cmd)}")
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 检查转换结果
        if process.returncode != 0:
            logger.error(f"转换失败: {process.stderr}")
            raise ValueError(f"LibreOffice转换失败: {process.stderr}")
        
        # 验证输出文件是否存在
        if not os.path.exists(output_path):
            raise ValueError(f"转换后的PDF文件未找到: {output_path}")
            
        logger.info(f"已转换为PDF: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"转换失败: {str(e)}")
        raise ValueError(f"转换失败: {str(e)}")

def get_libreoffice_command():
    """根据操作系统获取LibreOffice可执行文件路径"""
    system = platform.system()
    
    if system == "Windows":
        # Windows下可能的LibreOffice安装路径
        possible_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return "soffice"  # 如果在PATH中
    
    elif system == "Darwin":  # macOS
        # macOS下可能的LibreOffice安装路径
        possible_paths = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return "soffice"  # 如果在PATH中
    
    else:  # Linux和其他系统
        # 尝试常见的命令名
        for cmd in ["libreoffice", "soffice"]:
            try:
                subprocess.run([cmd, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return cmd
            except FileNotFoundError:
                continue
        
        # 如果都找不到
        logger.warning("未找到LibreOffice，使用默认命令'libreoffice'")
        return "libreoffice"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("请提供一个要转换的文件路径。")
        logger.info("示例: python convert_to_pdf.py example.docx")
        sys.exit(1)

    file_path = sys.argv[1]
    convert_to_pdf(file_path)