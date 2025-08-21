"""
文本转PDF工具
"""

import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def text_to_pdf(
    content: str, filename_prefix: str = "document", output_dir: str = "outputs"
) -> Optional[str]:
    """
    将文本内容转换为PDF文件

    Args:
        content: 要转换的文本内容
        filename_prefix: 文件名前缀
        output_dir: 输出目录

    Returns:
        PDF文件路径，如果失败返回None
    """
    try:
        # 清理内容中的无效颜色标签
        content = _clean_content_for_pdf(content)

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)

        # 导入reportlab相关模块
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
        from reportlab.lib.colors import HexColor

        # 设置中文字体
        font_name = _setup_chinese_font()

        # 创建PDF文档
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []

        # 获取样式
        styles = getSampleStyleSheet()

        # 创建自定义样式
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontName=font_name,
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=HexColor("#2E86AB"),
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontName=font_name,
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=HexColor("#A23B72"),
        )

        normal_style = ParagraphStyle(
            "CustomNormal",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=11,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            leading=16,
        )

        # 添加标题
        story.append(Paragraph(f"📄 {filename_prefix.replace('_', ' ').title()}", title_style))
        story.append(Spacer(1, 20))

        # 添加生成时间
        story.append(
            Paragraph(f"生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}", normal_style)
        )
        story.append(Spacer(1, 20))

        # 处理内容
        lines = content.split("\n")
        current_section = []

        for line in lines:
            line = line.strip()
            if not line:
                if current_section:
                    # 处理当前段落
                    text = " ".join(current_section)
                    if text:
                        story.append(Paragraph(text, normal_style))
                        story.append(Spacer(1, 6))
                    current_section = []
                continue

            # 检查是否是标题
            if line.startswith("**") and line.endswith("**"):
                # 粗体标题
                title_text = line.strip("*")
                story.append(Paragraph(title_text, heading_style))
                story.append(Spacer(1, 12))
            elif line.startswith("📍") or line.startswith("🔍"):
                # 特殊图标标题
                story.append(Paragraph(line, heading_style))
                story.append(Spacer(1, 12))
            elif line.startswith("•") or line.startswith("-"):
                # 列表项
                if current_section:
                    # 先处理之前的段落
                    text = " ".join(current_section)
                    if text:
                        story.append(Paragraph(text, normal_style))
                        story.append(Spacer(1, 6))
                    current_section = []

                # 添加列表项
                story.append(Paragraph(line, normal_style))
                story.append(Spacer(1, 6))
            else:
                # 普通文本行
                current_section.append(line)

        # 处理最后一个段落
        if current_section:
            text = " ".join(current_section)
            if text:
                story.append(Paragraph(text, normal_style))

        # 构建PDF
        doc.build(story)

        logger.info(f"PDF文件生成成功: {filepath}")
        return filepath

    except ImportError as e:
        logger.error(f"缺少必要的依赖包: {e}")
        logger.error("请安装: pip install reportlab")
        return None
    except Exception as e:
        logger.error(f"PDF生成失败: {e}")
        return None


def _process_markdown_text(text: str) -> str:
    """
    处理Markdown格式的文本，转换为适合PDF的格式

    Args:
        text: Markdown格式的文本

    Returns:
        处理后的文本
    """
    try:
        # 简单的Markdown处理
        lines = text.split("\n")
        processed_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                processed_lines.append("")
                continue

            # 处理标题
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                title = line.lstrip("#").strip()
                if level == 1:
                    processed_lines.append(f"**{title}**")
                elif level == 2:
                    processed_lines.append(f"**{title}**")
                else:
                    processed_lines.append(f"**{title}**")
            # 处理粗体
            elif "**" in line:
                processed_lines.append(line)
            # 处理列表
            elif line.startswith("- ") or line.startswith("• "):
                processed_lines.append(line)
            else:
                processed_lines.append(line)

        return "\n".join(processed_lines)

    except Exception as e:
        logger.error(f"Markdown处理失败: {e}")
        return text


def _clean_content_for_pdf(content: str) -> str:
    """
    清理内容，移除或替换不适合PDF的格式

    Args:
        content: 原始内容

    Returns:
        清理后的内容
    """
    try:
        import re

        # 移除HTML颜色标签
        content = re.sub(r'<font\s+color="[^"]*">(.*?)</font>', r"\1", content)

        # 移除其他HTML标签
        content = re.sub(r"<[^>]+>", "", content)

        # 移除可能的颜色警告标记
        content = re.sub(r'<font\s+color="warning">(.*?)</font>', r"⚠️ \1", content)
        content = re.sub(r'<font\s+color="error">(.*?)</font>', r"❌ \1", content)
        content = re.sub(r'<font\s+color="success">(.*?)</font>', r"✅ \1", content)

        # 清理多余的空行
        content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

        # 移除可能的特殊字符
        content = re.sub(
            r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef.,!?;:()\[\]{}"\'-_+=<>/\\|@#$%^&*~`📍🔍⚠️❌✅•\n]',
            "",
            content,
        )

        return content.strip()

    except Exception as e:
        logger.error(f"内容清理失败: {e}")
        return content


def _setup_chinese_font() -> str:
    """
    设置中文字体，解决PDF乱码问题

    Returns:
        可用的字体名称
    """
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        import platform

        system = platform.system()
        logger.info(f"检测到系统: {system}")

        # 尝试注册系统字体
        if system == "Darwin":  # macOS
            system_fonts = [
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/System/Library/Fonts/STHeiti Medium.ttc",
                "/System/Library/Fonts/ArialHB.ttc",
                "/Library/Fonts/Arial Unicode MS.ttf",
            ]

            for font_path in system_fonts:
                if os.path.exists(font_path):
                    try:
                        font_name = f"SystemFont_{os.path.basename(font_path)}"
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        logger.info(f"成功注册系统字体: {font_path}")
                        return font_name
                    except Exception as e:
                        logger.debug(f"注册字体失败 {font_path}: {e}")
                        continue

        elif system == "Linux":  # Linux
            system_fonts = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            ]

            for font_path in system_fonts:
                if os.path.exists(font_path):
                    try:
                        font_name = f"SystemFont_{os.path.basename(font_path)}"
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        logger.info(f"成功注册系统字体: {font_path}")
                        return font_name
                    except Exception as e:
                        logger.debug(f"注册字体失败 {font_path}: {e}")
                        continue

        # 回退到内置中文字体
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            logger.info("使用内置中文字体: STSong-Light")
            return "STSong-Light"
        except Exception as e:
            logger.debug(f"内置字体注册失败: {e}")

        # 最后回退到默认字体
        logger.warning("无法找到中文字体，使用默认字体（可能出现乱码）")
        return "Helvetica"

    except Exception as e:
        logger.error(f"字体设置失败: {e}")
        return "Helvetica"


def create_sample_pdf() -> Optional[str]:
    """
    创建示例PDF文件，用于测试

    Returns:
        PDF文件路径
    """
    sample_content = """# 旅游咨询示例

## 目的地信息

**北京旅游指南**

北京是中国的首都，拥有丰富的历史文化遗产。

### 主要景点
• 故宫博物院
• 长城
• 天坛公园
• 颐和园

### 最佳旅游时间
春秋两季气候宜人，是游览北京的最佳时间。

### 小贴士
建议游览3-5天，注意避开节假日高峰。

---
*本PDF由AI智能旅游咨询系统生成*"""

    return text_to_pdf(sample_content, "sample_travel_guide")


if __name__ == "__main__":
    # 测试PDF生成
    result = create_sample_pdf()
    if result:
        print(f"示例PDF生成成功: {result}")
    else:
        print("示例PDF生成失败")
