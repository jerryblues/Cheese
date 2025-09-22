import os
import html2text

# 配置HTML文件路径（在这里修改要转换的HTML文件路径）
HTML_FILE_PATH = r"C:/Users/howar/Downloads/tension-relaxation-webpage.html"

def html_to_markdown(html_path):
    """将HTML文件转换为Markdown文件，保存在HTML文件同目录下"""
    # 检查HTML文件是否存在
    if not os.path.exists(html_path):
        print(f"错误: HTML文件 '{html_path}' 不存在")
        return None
    
    # 设置输出路径为HTML文件同目录下的同名markdown文件
    output_path = os.path.splitext(html_path)[0] + ".md"
    
    try:
        # 读取HTML文件内容
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 创建HTML到Markdown的转换器
        converter = html2text.HTML2Text()
        converter.ignore_links = False  # 保留链接
        converter.ignore_images = False  # 保留图片
        converter.ignore_emphasis = False  # 保留强调文本
        converter.body_width = 0  # 不限制行宽
        
        # 转换HTML为Markdown
        markdown_content = converter.handle(html_content)
        
        # 保存Markdown文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"成功将HTML转换为Markdown文件: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"转换过程中出错: {str(e)}")
        return None

if __name__ == "__main__":
    result = html_to_markdown(HTML_FILE_PATH)
    if result is None:
        exit(1)
    else:
        exit(0)