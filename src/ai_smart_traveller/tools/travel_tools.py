"""
旅游咨询工具函数
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def get_travel_info(destination: str) -> str:
    """
    获取旅游目的地基本信息

    Args:
        destination: 目的地名称，如"北京"、"巴黎"等

    Returns:
        目的地的基本旅游信息
    """
    try:
        logger.info(f"查询目的地信息: {destination}")

        # 模拟旅游信息数据库
        travel_info = {
            "北京": {
                "description": "中国首都，历史文化名城",
                "highlights": ["故宫", "长城", "天坛", "颐和园"],
                "best_time": "春秋两季",
                "tips": "建议游览3-5天，注意避开节假日高峰",
            },
            "上海": {
                "description": "国际化大都市，东方明珠",
                "highlights": ["外滩", "东方明珠", "豫园", "南京路"],
                "best_time": "春秋两季",
                "tips": "建议游览2-3天，可以体验现代与传统",
            },
            "巴黎": {
                "description": "浪漫之都，艺术与时尚的中心",
                "highlights": ["埃菲尔铁塔", "卢浮宫", "凯旋门", "塞纳河"],
                "best_time": "4-10月",
                "tips": "建议游览4-5天，注意防盗，提前预订博物馆门票",
            },
            "东京": {
                "description": "现代与传统并存的日本首都",
                "highlights": ["浅草寺", "东京塔", "银座", "秋叶原"],
                "best_time": "3-5月和9-11月",
                "tips": "建议游览4-6天，注意礼仪，可以体验温泉",
            },
        }

        if destination in travel_info:
            info = travel_info[destination]
            result = f"""📍 **{destination}旅游信息**

**简介**: {info['description']}

**主要景点**:
{chr(10).join([f"• {spot}" for spot in info['highlights']])}

**最佳旅游时间**: {info['best_time']}

**小贴士**: {info['tips']}"""
        else:
            result = f"抱歉，我暂时没有{destination}的详细旅游信息。建议您可以查询官方旅游网站或咨询当地旅游局。"

        logger.info(f"目的地信息查询完成: {destination}")
        return result

    except Exception as e:
        logger.error(f"查询目的地信息失败: {e}")
        return f"查询{destination}旅游信息时出现错误，请稍后重试。"


def search_destinations(keyword: str, category: str = "all") -> str:
    """
    搜索旅游目的地

    Args:
        keyword: 搜索关键词，如"海岛"、"古城"等
        category: 目的地类别，如"海岛"、"古城"、"美食"等

    Returns:
        符合条件的目的地列表
    """
    try:
        logger.info(f"搜索目的地: 关键词={keyword}, 类别={category}")

        # 模拟目的地分类数据库
        destinations_db = {
            "海岛": ["马尔代夫", "巴厘岛", "普吉岛", "塞班岛", "毛里求斯"],
            "古城": ["西安", "丽江", "平遥", "凤凰", "乌镇"],
            "美食": ["成都", "广州", "西安", "重庆", "杭州"],
            "购物": ["香港", "东京", "首尔", "新加坡", "迪拜"],
            "自然": ["张家界", "九寨沟", "黄山", "桂林", "香格里拉"],
        }

        results = []

        # 根据关键词和类别搜索
        if category == "all" or category in destinations_db:
            search_categories = [category] if category != "all" else destinations_db.keys()

            for cat in search_categories:
                if cat in destinations_db:
                    for dest in destinations_db[cat]:
                        if keyword.lower() in dest.lower() or any(
                            kw in dest for kw in keyword.split()
                        ):
                            results.append(f"• {dest} ({cat})")

        if results:
            result = f"""🔍 **搜索结果: {keyword}**

找到以下相关目的地:

{chr(10).join(results[:10])}  # 限制显示前10个结果

💡 提示: 使用 get_travel_info 工具可以获取具体目的地的详细信息"""
        else:
            result = f"抱歉，没有找到与'{keyword}'相关的旅游目的地。请尝试其他关键词，如'海岛'、'古城'、'美食'等。"

        logger.info(f"目的地搜索完成，找到 {len(results)} 个结果")
        return result

    except Exception as e:
        logger.error(f"搜索目的地失败: {e}")
        return f"搜索目的地时出现错误，请稍后重试。"


# 工具函数列表，供Agent使用
def get_available_tools() -> List[Dict[str, Any]]:
    """获取可用工具列表"""
    return [
        {
            "name": "get_travel_info",
            "description": "获取指定旅游目的地的详细信息，包括景点、最佳时间、小贴士等",
            "function": get_travel_info,
        },
        {
            "name": "search_destinations",
            "description": "根据关键词搜索旅游目的地，支持按类别筛选",
            "function": search_destinations,
        },
    ]
