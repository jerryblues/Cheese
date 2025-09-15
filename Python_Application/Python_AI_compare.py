import os
import fitz  # PyMuPDF
import difflib
from typing import Tuple, List
import re

# 配置PDF文件所在目录路径
PDF_DIR = r'C:\Users\yuanb\Downloads\PDF test'  # 请修改为实际的PDF文件目录路径

def get_pdf_files(directory: str) -> List[str]:
    """获取目录下所有的PDF文件"""
    if not os.path.isdir(directory):
        print(f'错误：目录 {directory} 不存在！')
        return []
    
    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
    if len(pdf_files) < 2:
        print(f'错误：目录 {directory} 下需要至少两个PDF文件！')
        return []
    
    return pdf_files

def clean_text(text: str) -> str:
    """清理文本，移除不可打印字符和乱码"""
    # 定义有效字符范围
    def is_valid_char(char: str) -> bool:
        code = ord(char)
        return (
            char in '\n\t' or  # 保留换行和制表符
            (code >= 0x20 and code <= 0x7E) or  # ASCII可打印字符
            (code >= 0x4E00 and code <= 0x9FFF) or  # 基本汉字
            (code >= 0x3400 and code <= 0x4DBF) or  # 扩展A区汉字
            (code >= 0xF900 and code <= 0xFAFF) or  # 兼容汉字
            (code >= 0xFF00 and code <= 0xFFEF) or  # 全角ASCII、全角中文标点
            (code >= 0x3000 and code <= 0x303F)     # 中文标点
        )
    
    # 移除无效字符
    text = ''.join(char for char in text if is_valid_char(char))
    
    # 标准化空白字符
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)  # 移除零宽字符
    text = re.sub(r'[\u0020\u00A0\u3000]+', ' ', text)  # 统一空格
    text = re.sub(r'\s*\n\s*', '\n', text)  # 处理换行周围的空白
    
    # 移除空行并规范化段落
    text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
    return text

def extract_text_from_pdf(pdf_path: str) -> str:
    """从PDF文件中提取文本，使用PyMuPDF处理中文字符"""
    try:
        # 打开PDF文件
        doc = fitz.open(pdf_path)
        text = ''
        
        # 遍历所有页面提取文本
        for page in doc:
            # 使用PyMuPDF的内置文本提取，能更好地处理中文
            text += page.get_text()
        
        # 关闭文档
        doc.close()
        
        # 清理提取的文本
        cleaned_text = clean_text(text)
        
        # 检查是否成功提取了中文文本
        if not any(ord(c) > 127 for c in cleaned_text):
            print('警告：提取的文本不包含中文字符，请检查PDF文件是否包含可提取的文本层')
        
        return cleaned_text
    except Exception as e:
        print(f'读取PDF文件时出错：{e}')
        return ''

def calculate_similarity(text1: str, text2: str) -> Tuple[float, int, int, List[str]]:
    """计算两个文本的相似度
    返回：(相似度百分比, 重复字数, 总字数, 差异段落列表)
    """
    # 将文本分割成段落并进行预处理
    def preprocess_paragraphs(text: str) -> List[str]:
        # 移除多余的空白字符并分割成段落
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        # 对每个段落进行额外的清理
        return [re.sub(r'\s+', ' ', p) for p in paragraphs]
    
    paragraphs1 = preprocess_paragraphs(text1)
    paragraphs2 = preprocess_paragraphs(text2)
    
    # 计算整体相似度
    matcher = difflib.SequenceMatcher(None, text1, text2)
    matching_blocks = matcher.get_matching_blocks()
    duplicate_chars = sum(size for _, _, size in matching_blocks)
    total_chars = (len(text1) + len(text2)) // 2
    similarity = (duplicate_chars / total_chars * 100) if total_chars > 0 else 0
    
    # 分析段落级别的差异
    differences = []
    matcher = difflib.SequenceMatcher(None, paragraphs1, paragraphs2)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != 'equal':
            # 格式化差异输出
            def format_diff(p1_idx: int, p1: str, p2_idx: int, p2: str, diff_type: str) -> str:
                if diff_type == 'replace':
                    return f'段落顺序不同：\n文件1 第{p1_idx+1}段：{p1}\n文件2 第{p2_idx+1}段：{p2}'
                elif diff_type == 'delete':
                    return f'文件1独有段落（第{p1_idx+1}段）：{p1}'
                else:  # insert
                    return f'文件2独有段落（第{p2_idx+1}段）：{p2}'
            
            if tag == 'replace':
                # 只有当段落内容确实不同时才添加差异
                if paragraphs1[i1] != paragraphs2[j1]:
                    differences.append(format_diff(i1, paragraphs1[i1], j1, paragraphs2[j1], 'replace'))
            elif tag == 'delete':
                differences.append(format_diff(i1, paragraphs1[i1], 0, '', 'delete'))
            elif tag == 'insert':
                differences.append(format_diff(0, '', j1, paragraphs2[j1], 'insert'))
    
    return similarity, duplicate_chars, total_chars, differences

def main():
    # 获取目录下的所有PDF文件
    pdf_files = get_pdf_files(PDF_DIR)
    if not pdf_files:
        return
    
    # 显示找到的PDF文件
    print('\n找到以下PDF文件：')
    for i, file in enumerate(pdf_files, 1):
        print(f'{i}. {file}')
    
    # 选择前两个文件进行比较
    file1, file2 = pdf_files[:2]
    file1_path = os.path.join(PDF_DIR, file1)
    file2_path = os.path.join(PDF_DIR, file2)
    
    # 提取文本
    print('\n正在提取PDF文本...')
    text1 = extract_text_from_pdf(file1_path)
    text2 = extract_text_from_pdf(file2_path)
    
    if text1 and text2:
        # 计算相似度
        similarity, duplicate_chars, total_chars, differences = calculate_similarity(text1, text2)
        
        # 输出结果
        print('\n比较结果：')
        print(f'文件1：{file1}')
        print(f'文件2：{file2}')
        print(f'总字数：{total_chars}')
        print(f'重复字数：{duplicate_chars}')
        print(f'相似度：{similarity:.2f}%')
        
        # 输出详细差异
        if differences:
            print('\n发现以下差异：')
            for diff in differences:
                print(f'\n{diff}')
        else:
            print('\n未发现段落级别的差异。')
    else:
        print('无法比较文件，请确保PDF文件格式正确且可以访问。')

if __name__ == '__main__':
    main()