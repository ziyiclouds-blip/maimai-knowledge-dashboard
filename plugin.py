from __future__ import annotations

import base64
import json
import re
from typing import Any, Optional

from maibot_sdk import MaiBotPlugin, Command, Tool
from maibot_sdk.types import ToolParameterInfo, ToolParamType

from .config import DashboardPluginConfig
from .renderer import render_natural_knowledge_card, render_qa_card, THEMES


class MaimaiKnowledgeDashboardPlugin(MaiBotPlugin):
    """麦麦知识看板：把问答渲染为优雅的知识长图卡片（多主题 / 多渠道模型）"""

    config_model = DashboardPluginConfig

    async def on_load(self) -> None:
        self.ctx.logger.info("麦麦知识看板插件已加载 (支持 /问, /ask, /查, /看板 指令)")

    async def on_unload(self) -> None:
        self.ctx.logger.info("麦麦知识看板插件已卸载")

    async def on_config_update(self, scope: str, config_data: dict[str, Any], version: str) -> None:
        if scope == "self":
            self._config_cache = None
            self.ctx.logger.info("麦麦知识看板配置已更新 (version=%s)", version)

    # ---------------- 配置读取 ----------------

    def _cfg(self) -> DashboardPluginConfig:
        cache = getattr(self, "_config_cache", None)
        if cache is not None:
            return cache
        cfg: Optional[DashboardPluginConfig] = None
        try:
            raw = getattr(self, "_plugin_config_data", None)
            if isinstance(raw, dict) and raw:
                cfg = DashboardPluginConfig.model_validate(raw)
        except Exception:
            cfg = None
        if cfg is None:
            try:
                c = self.config
                if isinstance(c, DashboardPluginConfig):
                    cfg = c
            except Exception:
                cfg = None
        if cfg is None:
            cfg = DashboardPluginConfig()
        self._config_cache = cfg
        return cfg

    def _get_cfg_value(self, section: str, key: str, default: Any = None) -> Any:
        try:
            return getattr(getattr(self._cfg(), section), key)
        except Exception:
            return default

    async def _get_bot_name(self) -> str:
        """动态读取当前 MaiBot 自己的名字（bot.nickname），失败回退默认值"""
        if getattr(self, "_bot_name_cache", ""):
            return self._bot_name_cache
        name = ""
        try:
            name = str(await self.ctx.config.get("bot.nickname", "") or "").strip()
        except Exception as e:
            self.ctx.logger.warning("读取 bot.nickname 失败: %s", e)
        if not name:
            name = "麦麦"
        self._bot_name_cache = name
        return name

    async def _get_footer_text(self) -> str:
        custom = str(self._get_cfg_value("theme", "footer_text", "") or "").strip()
        if custom:
            return custom
        bot_name = await self._get_bot_name()
        return f"{bot_name} · 麦麦知识看板"

    # ---------------- 图片提取 ----------------

    async def _extract_reply_image(self, message_dict: dict, stream_id: str) -> str:
        raw_message = message_dict.get("raw_message", [])
        if not isinstance(raw_message, list):
            return ""

        # 1. 当前消息本身带图
        seg_types = [s.get("type") for s in raw_message if isinstance(s, dict)]
        for segment in raw_message:
            if isinstance(segment, dict) and segment.get("type") == "image":
                b64 = segment.get("binary_data_base64")
                if b64:
                    self.ctx.logger.info("从当前消息提取图片 (len=%d)", len(b64))
                    return b64

        # 1.5 image 段二进制可能被 RPC 剥离，按 message_id 重拉
        msg_id = message_dict.get("message_id")
        if msg_id and any(t == "image" for t in seg_types):
            try:
                current = await self.ctx.message.get_by_id(
                    msg_id, stream_id=stream_id, include_binary_data=True,
                )
                cur_raw = current.get("raw_message", []) if isinstance(current, dict) else []
                for seg in cur_raw:
                    if isinstance(seg, dict) and seg.get("type") == "image":
                        b64 = seg.get("binary_data_base64")
                        if b64:
                            self.ctx.logger.info("重新拉取当前消息提取图片 (len=%d)", len(b64))
                            return b64
            except Exception as e:
                self.ctx.logger.warning("重新拉取当前消息失败: %s", e)

        # 2. 引用消息中的图片
        for segment in raw_message:
            if not isinstance(segment, dict) or segment.get("type") != "reply":
                continue
            reply_data = segment.get("data", {})
            target_msg_id = reply_data.get("target_message_id")
            if not target_msg_id:
                break
            try:
                original = await self.ctx.message.get_by_id(
                    target_msg_id, stream_id=stream_id, include_binary_data=True,
                )
                orig_raw = original.get("raw_message", []) if isinstance(original, dict) else []
                for orig_seg in orig_raw:
                    if isinstance(orig_seg, dict) and orig_seg.get("type") == "image":
                        b64 = orig_seg.get("binary_data_base64")
                        if b64:
                            self.ctx.logger.info("成功提取引用消息图片 (len=%d)", len(b64))
                            return b64
            except Exception as e:
                self.ctx.logger.warning("获取引用消息图片失败: %s", e)
            break
        return ""

    # ---------------- LLM 调用 ----------------

    async def _call_external_llm(self, prompt: str, image_base64: str = "") -> tuple[str, str]:
        """自定义渠道：主渠道 -> 备用渠道。返回 (内容, 模型标签)，全部失败返回 ("", "")。"""
        from . import llm_client

        ext = self._cfg().external_model
        if not (ext.enabled and ext.base_url and ext.model):
            return "", ""
        gen = self._cfg().general
        channels = []
        if ext.base_url and ext.model:
            channels.append(("主渠道", ext.base_url, ext.api_key, ext.model))
        if ext.backup_base_url and ext.backup_model:
            channels.append(("备用渠道", ext.backup_base_url, ext.backup_api_key, ext.backup_model))
        for label, url, key, model in channels:
            try:
                self.ctx.logger.info("调用自定义渠道: %s protocol=%s model=%s", label, ext.protocol, model)
                content = await llm_client.call_external(
                    ext.protocol, url, key, model, prompt,
                    image_base64=image_base64,
                    max_tokens=gen.max_tokens, temperature=gen.temperature,
                    timeout=ext.timeout_seconds,
                )
                if content and content.strip():
                    return content, f"{model}（{label}）"
                self.ctx.logger.warning("自定义渠道 %s 返回空内容", label)
            except Exception as e:
                self.ctx.logger.warning("自定义渠道 %s 调用失败: %s", label, e)
        return "", ""

    async def _call_builtin_llm(self, prompt: str, image_base64: str = "") -> tuple[str, str]:
        """MaiBot 内置模型：model_name 直选 > 任务路由。返回 (内容, 模型标签)。"""
        bi = self._cfg().builtin_model
        gen = self._cfg().general

        llm_prompt: Any = prompt
        if image_base64:
            llm_prompt = [{
                "role": "user",
                "content": [
                    {"type": "image", "image_format": "jpeg", "image_base64": image_base64},
                    {"type": "text", "text": prompt},
                ],
            }]

        # 最高优先：直接指定模型名
        model_name = str(bi.model_name or "").strip()
        if model_name:
            try:
                self.ctx.logger.info("调用指定内置模型: model_name=%s", model_name)
                res = await self.ctx.llm.generate(
                    llm_prompt, model_name=model_name,
                    max_tokens=gen.max_tokens, temperature=gen.temperature,
                )
                content = self._extract_llm_text(res)
                if content:
                    return content, model_name
            except Exception as e:
                self.ctx.logger.warning("指定模型 %s 生成失败: %s", model_name, e)

        # 任务路由
        task_names = [t.strip() for t in str(bi.task_names or "").split(",") if t.strip()]
        if not task_names:
            task_names = ["utils", "replyer", "planner"]
        if image_base64:
            vt = str(bi.vision_task or "image").strip() or "image"
            task_names = [vt] + [t for t in task_names if t != vt]

        for task_name in task_names:
            try:
                self.ctx.logger.info("调用 LLM 任务: task=%r, has_image=%s", task_name, bool(image_base64))
                res = await self.ctx.llm.generate(
                    llm_prompt, model=task_name,
                    max_tokens=gen.max_tokens, temperature=gen.temperature,
                )
                content = self._extract_llm_text(res)
                if content:
                    tag = str(res.get("model") or task_name) if isinstance(res, dict) else task_name
                    return content, self._resolve_model_display_name(tag)
            except Exception as e:
                self.ctx.logger.warning("LLM 任务 %s 生成失败: %s", task_name, e)
        return "", ""

    def _extract_llm_text(self, res: Any) -> str:
        if not isinstance(res, dict):
            return ""
        content = str(res.get("response") or res.get("content") or res.get("text") or "")
        if content.strip() and not content.startswith("生成内容时出错"):
            return content
        if content.strip():
            self.ctx.logger.warning("LLM 返回异常内容: %s", content)
        return ""

    def _resolve_model_display_name(self, name: str) -> str:
        """把模型短名映射成 model_config.toml 里的 model_identifier 展示名。"""
        if getattr(self, "_model_name_map", None) is None:
            self._model_name_map = {}
            for path in ("/MaiMBot/config/model_config.toml", "./config/model_config.toml",
                         "../config/model_config.toml"):
                try:
                    import tomllib
                    with open(path, "rb") as f:
                        data = tomllib.load(f)
                    for m in data.get("models", []):
                        n = str(m.get("name") or "").strip()
                        ident = str(m.get("model_identifier") or "").strip()
                        if n and ident:
                            self._model_name_map[n] = ident
                    if self._model_name_map:
                        break
                except Exception:
                    continue
        return self._model_name_map.get(name, name)

    async def _call_llm(self, prompt: str, image_base64: str = "") -> tuple[str, str]:
        """自定义渠道优先，失败后回退内置模型。返回 (内容, 模型标签)。"""
        content, tag = await self._call_external_llm(prompt, image_base64)
        if content:
            return content, tag
        return await self._call_builtin_llm(prompt, image_base64)

    # ---------------- 内容规整 ----------------

    def _normalize_content_to_markdown(self, raw_text: str, default_query: str, bot_name: str = "麦麦") -> str:
        if not raw_text.strip():
            return f"{bot_name}已针对「{default_query}」完成检索，暂时未找到足够详实的资料呢。"

        text = raw_text.strip()

        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
            text = re.sub(r"```$", "", text.strip())
            text = text.strip()

        if text.startswith("{") and text.endswith("}"):
            try:
                data = json.loads(text)
                parts = []
                if "summary" in data and data["summary"]:
                    parts.append(f"> {data['summary']}\n")
                if "points" in data and isinstance(data["points"], list):
                    for pt in data["points"]:
                        t = pt.get("title", "").strip()
                        d = pt.get("desc", "").strip()
                        if t:
                            parts.append(f"## {t}")
                        if d:
                            parts.append(f"{d}\n")
                if parts:
                    return "\n".join(parts)
            except Exception:
                pass

        return text

    async def _render_and_send(self, question: str, markdown_content: str,
                               model_tag: str, stream_id: str) -> bytes:
        cfg = self._cfg()
        footer = await self._get_footer_text()
        png_bytes = render_natural_knowledge_card(
            question=question,
            markdown_content=markdown_content,
            model_tag=model_tag or "MaiBot",
            footer_text=footer,
            footer_right_text=str(cfg.theme.footer_right_text or ""),
            header_text=str(cfg.theme.header_text or ""),
            theme=str(cfg.theme.theme or "light"),
        )
        b64_img = base64.b64encode(png_bytes).decode("utf-8")
        if stream_id:
            await self.ctx.send.image(b64_img, stream_id)
        return png_bytes

    # ---------------- 指令 ----------------

    @Command(
        "ask",
        description="向麦麦提问，并将解答渲染为优雅的知识卡片（主题可在插件配置中切换）",
        pattern=r"[!/](?:问|ask|查|看板)\s*(?P<query>.*?)(?:\s*@\S+\s*)?$",
        aliases=["/问", "!问", "/ask", "!ask", "/查", "!查", "/看板", "!看板"],
    )
    async def handle_ask_command(
        self,
        query: str = "",
        stream_id: str = "",
        **kwargs: Any,
    ) -> tuple[bool, str, bool]:
        """处理 /问 xxx 指令"""
        if not self._get_cfg_value("general", "enabled", True):
            return False, "插件已禁用", True

        # 1. 提取提问内容
        target_query = (query or "").strip()
        if not target_query:
            matched_groups = kwargs.get("matched_groups")
            if isinstance(matched_groups, dict):
                target_query = (matched_groups.get("query") or "").strip()

        raw_text = (kwargs.get("text") or "").strip()
        if not raw_text and "message" in kwargs and isinstance(kwargs["message"], dict):
            raw_text = kwargs["message"].get("processed_plain_text") or kwargs["message"].get("plain_text") or ""

        if not target_query and raw_text:
            m = re.search(r"[!/](?:问|ask|查|看板)\s*(.+?)(?:\s+@\S+\s*)?$", raw_text)
            if m:
                target_query = m.group(1).strip()

        # 1.5 统一清理 query：去掉 @提及、占位符
        if target_query:
            target_query = re.sub(r"@\S+(?:\s+|$)", "", target_query)
            target_query = re.sub(r"\[(?:image|reply|emoji|at)\]", "", target_query)
            target_query = target_query.strip()

        # 2. stream_id
        if not stream_id:
            stream_id = str(kwargs.get("stream_id") or "")
            if not stream_id and "message" in kwargs and isinstance(kwargs["message"], dict):
                stream_id = str(kwargs["message"].get("session_id") or "")

        if not target_query:
            if stream_id:
                await self.ctx.send.text("请输入要提问或查询的内容，例如：/问 什么是大模型的注意力机制", stream_id)
            return False, "query 不能为空", True

        self.ctx.logger.info("收到知识看板提问: target_query=%r (stream_id=%s)", target_query, stream_id)

        # 3. 图片提取
        image_base64 = ""
        message_dict = kwargs.get("message", {})
        if isinstance(message_dict, dict):
            image_base64 = await self._extract_reply_image(message_dict, stream_id)

        bot_name = await self._get_bot_name()
        if stream_id:
            if image_base64:
                await self.ctx.send.text(f"{bot_name}正在识别图片并生成「{target_query}」的知识卡片，稍等一下下哦~ 📋", stream_id)
            else:
                await self.ctx.send.text(f"{bot_name}正在为你生成「{target_query}」的知识卡片，稍等一下下哦~ 📋", stream_id)

        # 4. Prompt
        if image_base64:
            prompt = f"""你是一个专业且亲和的智能知识专家"{bot_name}"。用户发送了一张图片，请分析图片内容并回答用户的问题。

排版与输出原则：
1. 采用自然流畅的 Markdown 格式；
2. 先描述图片中的关键内容，再针对问题给出解答；
3. 对于简单问题，直接给出精炼明确的答案；
4. 对于复杂的技术机制、系统架构或流程分析，合理使用层级结构；
5. 直接输出 Markdown 正文，不要输出"好的"、"这是解答"等无关客套话。

用户提问：{target_query}"""
        else:
            prompt = f"""你是一个专业且亲和的智能知识专家"{bot_name}"。请针对用户提出的问题进行清晰、准确、优雅的解答。

排版与输出原则：
1. 采用自然流畅的 Markdown 格式；
2. 对于简单问题（如算术、概念速查、一句话事实），直接给出精炼明确的答案和步骤，不要刻意堆砌内容；
3. 对于复杂的技术机制、系统架构或流程分析，合理使用层级结构（例如 `> ` 核心结论、`## ` 二级标题、`- ` 或 `1. ` 列表分点、代码块）；
4. 杜绝死板生硬的套路模版，根据问题本身的复杂度自由排版；
5. 直接输出 Markdown 正文，不要输出"好的"、"这是解答"等无关客套话。

用户提问：{target_query}"""

        llm_raw, model_tag = await self._call_llm(prompt, image_base64=image_base64)
        markdown_content = self._normalize_content_to_markdown(llm_raw, target_query, bot_name)

        try:
            await self._render_and_send(target_query, markdown_content, model_tag, stream_id)
            return True, "已生成并发送知识卡片", True
        except Exception as e:
            self.ctx.logger.error("渲染或发送知识卡片失败: %s", e, exc_info=True)
            if stream_id:
                await self.ctx.send.text(f"生成知识卡片失败啦：{e}", stream_id)
            return False, str(e), True

    # ---------------- Tool ----------------

    @Tool(
        "render_dashboard_card",
        description="当用户询问复杂的架构、流程、技术机制或需要结构化大纲时，主动调用此工具将答案渲染为优雅的知识长图卡片发给用户",
        parameters=[
            ToolParameterInfo(
                name="title",
                param_type=ToolParamType.STRING,
                description="卡片标题或问题概述（如：大模型注意力机制详解）",
                required=True,
            ),
            ToolParameterInfo(
                name="content",
                param_type=ToolParamType.STRING,
                description="排版优美的 Markdown 文本内容（支持标题、列表、引用与代码）",
                required=True,
            ),
        ],
    )
    async def tool_render_dashboard(
        self,
        title: str = "",
        content: str = "",
        summary: str = "",
        points_json: str = "",
        stream_id: str = "",
        **kwargs: Any,
    ) -> dict[str, str]:
        """Tool 接口：供大模型自主渲染知识卡片"""
        if not self._get_cfg_value("general", "enabled", True):
            return {"name": "render_dashboard_card", "content": "看板插件当前已禁用。"}

        bot_name = await self._get_bot_name()
        md_text = content.strip()
        if not md_text:
            if summary or points_json:
                md_text = self._normalize_content_to_markdown(
                    json.dumps({"summary": summary, "points": json.loads(points_json or "[]")}),
                    title, bot_name,
                )
            else:
                md_text = title

        try:
            await self._render_and_send(title, md_text, "MaiBot 工具调用", stream_id)
            return {"name": "render_dashboard_card", "content": "知识卡片已成功渲染并发送给用户。"}
        except Exception as e:
            self.ctx.logger.error("Tool 渲染知识卡片失败: %s", e)
            return {"name": "render_dashboard_card", "content": f"渲染失败: {e}"}


def create_plugin() -> MaimaiKnowledgeDashboardPlugin:
    """MaiBot SDK 2.x 插件工厂函数"""
    return MaimaiKnowledgeDashboardPlugin()
