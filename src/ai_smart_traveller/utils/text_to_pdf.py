#!/usr/bin/env python3
"""
文本转PDF工具
支持中文文本转换为PDF文件
"""

import os
import logging
from datetime import datetime
from pathlib import Path

# 尝试导入reportlab
try:
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("reportlab未安装，PDF生成功能不可用")

logger = logging.getLogger(__name__)


def text_to_pdf(text: str, filename_prefix: str = "output") -> str:
    """
    将文本转换为PDF文件

    Args:
        text: 要转换的文本内容
        filename_prefix: 文件名前缀

    Returns:
        str: 生成的PDF文件路径，失败时返回空字符串
    """
    if not REPORTLAB_AVAILABLE:
        logger.error("reportlab未安装，无法生成PDF")
        return ""

    try:
        # 创建输出目录
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.pdf"
        filepath = output_dir / filename

        # 创建PDF文档
        doc = SimpleDocTemplate(
            str(filepath), pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72
        )

        # 设置中文字体
        _setup_chinese_font()

        # 创建内容
        story = []

        # 添加标题
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=getSampleStyleSheet()["Title"],
            fontSize=16,
            spaceAfter=30,
            alignment=1,  # 居中对齐
            textColor=HexColor("#2E86AB"),
        )
        title = Paragraph(f"AI智能旅游咨询专家系统", title_style)
        story.append(title)

        # 添加生成时间
        time_style = ParagraphStyle(
            "CustomTime",
            parent=getSampleStyleSheet()["Normal"],
            fontSize=10,
            spaceAfter=20,
            alignment=1,  # 居中对齐
            textColor=HexColor("#666666"),
        )
        time_text = f"生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"
        time_para = Paragraph(time_text, time_style)
        story.append(time_para)

        # 添加分隔线
        story.append(Spacer(1, 20))

        # 添加正文内容
        content_style = ParagraphStyle(
            "CustomContent",
            parent=getSampleStyleSheet()["Normal"],
            fontSize=12,
            spaceAfter=12,
            leading=18,
            textColor=HexColor("#333333"),
        )

        # 处理文本内容，支持markdown格式
        content = _process_markdown_text(text)
        content_para = Paragraph(content, content_style)
        story.append(content_para)

        # 生成PDF
        doc.build(story)

        logger.info(f"PDF文件生成成功: {filepath}")
        return str(filepath)

    except Exception as e:
        logger.error(f"PDF生成失败: {e}")
        return ""


def _setup_chinese_font():
    """设置中文字体支持"""
    try:
        # 1. 尝试注册系统中文字体
        font_paths = [
            "/System/Library/Fonts/PingFang.ttc",  # macOS
            "/System/Library/Fonts/STHeiti Light.ttc",  # macOS
            "C:/Windows/Fonts/simsun.ttc",  # Windows
            "C:/Windows/Fonts/msyh.ttc",  # Windows
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont("ChineseFont", font_path))
                    logger.info(f"成功注册中文字体: {font_path}")
                    return
                except Exception as e:
                    logger.debug(f"注册字体失败: {font_path}, 错误: {e}")
                    continue

        # 2. 回退到 reportlab 内置字体
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            logger.info("使用内置中文字体: STSong-Light")
        except Exception as e:
            logger.warning(f"内置中文字体注册失败: {e}")

    except Exception as e:
        logger.error(f"字体设置失败: {e}")


def _process_markdown_text(text: str) -> str:
    """
    简单处理markdown文本，转换为HTML格式

    Args:
        text: 原始文本

    Returns:
        str: 处理后的HTML文本
    """
    if not text:
        return ""

    # 简单的markdown转HTML处理
    processed = text

    # 处理标题 - 只处理一级标题
    lines = processed.split("\n")
    processed_lines = []

    for line in lines:
        if line.startswith("# "):
            # 一级标题
            title = line[2:].strip()
            processed_lines.append(f"<b>{title}</b>")
        elif line.startswith("## "):
            # 二级标题
            title = line[3:].strip()
            processed_lines.append(f"<b>{title}</b>")
        elif line.startswith("### "):
            # 三级标题
            title = line[4:].strip()
            processed_lines.append(f"<b>{title}</b>")
        elif line.startswith("• ") or line.startswith("- "):
            # 列表项
            item = line[2:].strip()
            processed_lines.append(f"• {item}")
        elif line.strip() == "":
            # 空行
            processed_lines.append("<br/>")
        else:
            # 普通文本
            # 处理粗体
            line = line.replace("**", "<b>").replace("**", "</b>")
            # 处理斜体
            line = line.replace("*", "<i>").replace("*", "</i>")
            processed_lines.append(line)

    # 重新组合文本
    processed = "\n".join(processed_lines)

    return processed


if __name__ == "__main__":
    # 测试功能
    test_text = """
# 测试标题

这是一个测试文本，用于验证PDF生成功能。

## 功能特点
• 支持中文显示
• 自动字体设置
• 时间戳标记
• 格式美化

**重要提示**：请确保已安装reportlab库。
"""

    result = text_to_pdf(test_text, "test")
    if result:
        print(f"PDF生成成功: {result}")
    else:
        print("PDF生成失败")
