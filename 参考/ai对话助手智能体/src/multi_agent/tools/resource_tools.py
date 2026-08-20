"""
资源助手专用工具集（多智能体使用）
Resource Tools for Multi-Agent System

提供联网搜索能力，让 resource_agent 能够搜索真实的互联网资源
"""

import logging
from typing import Dict, List, Any, Optional

from langchain.tools import tool
from coze_coding_dev_sdk import SearchClient
from coze_coding_utils.runtime_ctx.context import new_context

logger = logging.getLogger(__name__)


@tool
def search_internet(query: str, count: int = 5) -> str:
    """
    搜索互联网上的资源，返回高质量的学习资料、技术博客、官方文档等。

    Args:
        query: 搜索关键词（可以是技术主题、工具名称、学习问题等）
        count: 返回结果数量，默认5条

    Returns:
        格式化的搜索结果，包含标题、URL、摘要、来源网站和质量评分
    """
    try:
        ctx = new_context(method="resource.search_internet")
        client = SearchClient(ctx=ctx)

        response = client.web_search(
            query=query,
            count=count,
            need_summary=True
        )

        if not response.web_items:
            return f"未找到与「{query}」相关的资源，请尝试其他关键词。"

        results = []
        results.append(f"🔍 搜索「{query}」找到 {len(response.web_items)} 条相关资源：\n")

        for i, item in enumerate(response.web_items, 1):
            authority = item.auth_info_des or "一般"
            results.append(
                f"{i}. **{item.title}**\n"
                f"   📌 来源：{item.site_name}（权威度：{authority}）\n"
                f"   🔗 链接：{item.url}\n"
                f"   💡 摘要：{item.snippet[:150]}..."
                f"{'（由AI总结）' if item.summary else ''}\n"
            )
            if item.summary:
                results.append(f"   📝 AI总结：{item.summary[:200]}...\n")
            results.append("")

        return "\n".join(results).strip()

    except Exception as e:
        logger.error(f"search_internet failed: {e}")
        return f"搜索「{query}」时出错：{str(e)}。请稍后重试。"


@tool
def search_bilibili(keyword: str, count: int = 5) -> str:
    """
    搜索B站上的视频教程，特别适合查找技术教程、学习视频。

    Args:
        keyword: 搜索关键词（如：Hadoop入门、Spark教程）
        count: 返回结果数量，默认5条

    Returns:
        B站视频搜索结果，包含标题、UP主、时长、链接等
    """
    try:
        ctx = new_context(method="resource.search_bilibili")
        client = SearchClient(ctx=ctx)

        # 在B站站内搜索
        search_query = f"{keyword} 教程"
        response = client.search(
            query=search_query,
            count=count,
            sites="bilibili.com",
            need_summary=True
        )

        if not response.web_items:
            # Fallback: 通用搜索
            response = client.web_search(
                query=f"bilibili {keyword} 教程",
                count=count,
                need_summary=True
            )

        if not response.web_items:
            return f"未找到「{keyword}」相关的B站视频，试试在B站官网搜索：\nhttps://search.bilibili.com/all?keyword={keyword}"

        results = []
        results.append(f"🎬 「{keyword}」相关B站视频教程：\n")

        for i, item in enumerate(response.web_items, 1):
            # 从URL中提取av号
            av号 = ""
            if "av" in item.url.lower():
                av号 = item.url.split("av")[1][:10].split("?")[0]
                av号 = f"av{av号}"

            results.append(
                f"{i}. **{item.title}**\n"
                f"   📺 频道：{item.site_name}\n"
                f"   🔗 链接：{item.url}\n"
                f"   💡 简介：{item.snippet[:120]}...\n"
            )
            if item.summary:
                results.append(f"   📝 AI推荐：{item.summary[:150]}...\n")
            results.append("")

        results.append(f"\n💡 更多视频请访问：https://search.bilibili.com/all?keyword={keyword}")

        return "\n".join(results).strip()

    except Exception as e:
        logger.error(f"search_bilibili failed: {e}")
        return f"搜索B站「{keyword}」时出错：{str(e)}。请稍后重试。"


@tool
def search_official_docs(query: str, count: int = 3) -> str:
    """
    搜索官方文档，特别适合查找技术框架、工具的官方文档和API参考。

    Args:
        query: 技术名词（如：Hadoop、Spark、Flink）
        count: 返回结果数量，默认3条

    Returns:
        官方文档搜索结果，包含文档链接、版本信息等
    """
    try:
        ctx = new_context(method="resource.search_official_docs")
        client = SearchClient(ctx=ctx)

        # 搜索官方文档
        search_query = f"{query} official documentation site:apache.org OR site:docs.python.org OR site:getcomposer.org OR site:npmjs.com"
        response = client.search(
            query=search_query,
            search_type="web",
            count=count,
            need_content=False,
            need_summary=True
        )

        if not response.web_items:
            # Fallback: 直接搜索官方文档
            response = client.web_search(
                query=f"{query} 官方文档 官方网站",
                count=count,
                need_summary=True
            )

        if not response.web_items:
            return f"未找到「{query}」的官方文档，建议访问：\n- Apache: https://{query.lower()}.apache.org/docs/\n- GitHub: https://github.com/apache/{query.lower()}"

        results = []
        results.append(f"📚 「{query}」官方文档：\n")

        for i, item in enumerate(response.web_items, 1):
            results.append(
                f"{i}. **{item.title}**\n"
                f"   🔗 文档地址：{item.url}\n"
                f"   💡 简介：{item.snippet[:120]}...\n"
            )
            if item.summary:
                results.append(f"   📝 内容概要：{item.summary[:150]}...\n")
            results.append("")

        return "\n".join(results).strip()

    except Exception as e:
        logger.error(f"search_official_docs failed: {e}")
        return f"搜索「{query}」官方文档时出错：{str(e)}。请稍后重试。"


@tool
def search_github(keyword: str, count: int = 5) -> str:
    """
    搜索GitHub上的开源项目，适合查找优质代码仓库、示例项目。

    Args:
        keyword: 搜索关键词（如：hadoop-spark-connector、data-pipeline）
        count: 返回结果数量，默认5条

    Returns:
        GitHub项目搜索结果，包含仓库名、星标数、描述等
    """
    try:
        ctx = new_context(method="resource.search_github")
        client = SearchClient(ctx=ctx)

        response = client.search(
            query=f"{keyword} site:github.com",
            count=count,
            need_summary=True
        )

        if not response.web_items:
            return f"未找到「{keyword}」相关的GitHub项目，建议访问：\nhttps://github.com/search?q={keyword}"

        results = []
        results.append(f"💻 「{keyword}」相关GitHub开源项目：\n")

        for i, item in enumerate(response.web_items, 1):
            # 尝试提取仓库信息
            repo_info = ""
            if "github.com" in item.url:
                parts = item.url.split("github.com/")[-1].split("/")
                if len(parts) >= 2:
                    repo_info = f"{parts[0]}/{parts[1].split('?')[0]}"

            results.append(
                f"{i}. **{item.title}**\n"
                f"   📦 仓库：{repo_info or '未知'}\n"
                f"   🔗 地址：{item.url}\n"
                f"   💡 描述：{item.snippet[:120]}...\n"
            )
            if item.summary:
                results.append(f"   📝 项目亮点：{item.summary[:150]}...\n")
            results.append("")

        results.append(f"\n🔍 更多项目：https://github.com/search?q={keyword}")
        return "\n".join(results).strip()

    except Exception as e:
        logger.error(f"search_github failed: {e}")
        return f"搜索GitHub「{keyword}」时出错：{str(e)}。请稍后重试。"


@tool
def search_community_posts(topic: str, count: int = 5) -> str:
    """
    搜索技术社区的讨论和文章，适合查找实战经验、踩坑分享。

    Args:
        topic: 技术话题（如：Spark性能优化、Hive SQL技巧）
        count: 返回结果数量，默认5条

    Returns:
        社区讨论搜索结果，包含文章标题、来源社区、点赞数等
    """
    try:
        ctx = new_context(method="resource.search_community")
        client = SearchClient(ctx=ctx)

        response = client.search(
            query=f"{topic} site:stackoverflow.com OR site:juejin.cn OR site:zhihu.com OR site:csdn.net OR site:v2ex.com",
            count=count,
            need_summary=True
        )

        if not response.web_items:
            # Fallback: 通用社区搜索
            response = client.web_search(
                query=f"{topic} 经验分享 实战",
                count=count,
                need_summary=True
            )

        if not response.web_items:
            return f"未找到「{topic}」相关的社区讨论，建议：\n- 知乎：https://www.zhihu.com/search?q={topic}\n- 掘金：https://juejin.cn/search?q={topic}"

        results = []
        results.append(f"💬 「{topic}」社区经验分享：\n")

        for i, item in enumerate(response.web_items, 1):
            # 判断来源平台
            platform = item.site_name or "技术社区"
            icon = "📖"
            if "zhihu" in item.site_name.lower():
                icon = "❓"
            elif "stackoverflow" in item.site_name.lower():
                icon = "💬"
            elif "juejin" in item.site_name.lower():
                icon = "✍️"
            elif "csdn" in item.site_name.lower():
                icon = "📝"

            results.append(
                f"{i}. {icon} **{item.title}**\n"
                f"   🏠 来自：{platform}\n"
                f"   🔗 链接：{item.url}\n"
                f"   💡 摘要：{item.snippet[:120]}...\n"
            )
            if item.summary:
                results.append(f"   📝 AI解读：{item.summary[:150]}...\n")
            results.append("")

        return "\n".join(results).strip()

    except Exception as e:
        logger.error(f"search_community_posts failed: {e}")
        return f"搜索社区「{topic}」时出错：{str(e)}。请稍后重试。"
