from typing import Literal

from pydantic import Field
from maibot_sdk.config import PluginConfigBase


class PluginSectionConfig(PluginConfigBase):
    """插件元信息"""

    __ui_label__ = "插件"
    __ui_order__ = -1

    enabled: bool = Field(
        default=True, description="是否启用本插件",
        json_schema_extra={"label": "启用插件", "x-icon": "power"},
    )
    config_version: str = Field(
        default="1.1.0", description="配置版本",
        json_schema_extra={"label": "配置版本", "hidden": True},
    )


class ThemeConfig(PluginConfigBase):
    """看板主题"""

    __ui_label__ = "主题外观"
    __ui_icon__ = "palette"
    __ui_order__ = 1

    theme: Literal["light", "dark", "warm", "sakura", "mint", "grape"] = Field(
        default="light",
        description="卡片配色方案。",
        json_schema_extra={"label": "主题色", "x-icon": "palette"},
    )
    header_text: str = Field(
        default="",
        description="卡片头部标题左侧的引导文案。",
        json_schema_extra={"label": "开头引导语", "placeholder": "留空自动显示提问内容"},
    )
    footer_text: str = Field(
        default="",
        description="卡片底部水印署名。",
        json_schema_extra={"label": "底部署名", "placeholder": "留空自动为「Bot昵称 · 麦麦知识看板」"},
    )
    footer_right_text: str = Field(
        default="智能知识生成 · 仅供参考",
        description="卡片底部右下角文案。",
        json_schema_extra={"label": "右下角文案"},
    )


class ExternalModelConfig(PluginConfigBase):
    """自定义外部模型渠道（优先于 MaiBot 内置模型配置）"""

    __ui_label__ = "自定义模型渠道"
    __ui_icon__ = "cloud"
    __ui_order__ = 2

    enabled: bool = Field(
        default=False,
        description="启用后优先使用下方自定义渠道，失败才回退到 MaiBot 内置模型。",
        json_schema_extra={"label": "启用自定义渠道", "x-icon": "toggle-right"},
    )
    protocol: Literal["openai", "openai_responses", "claude", "gemini"] = Field(
        default="openai",
        description="API 协议格式：openai(/v1/chat/completions) / openai_responses(/v1/responses) / claude(/v1/messages) / gemini(:generateContent)。",
        json_schema_extra={"label": "协议格式"},
    )
    base_url: str = Field(
        default="", description="API 基础地址。",
        json_schema_extra={"label": "渠道地址", "placeholder": "https://api.openai.com 或中转站地址"},
    )
    api_key: str = Field(
        default="", description="API Key。",
        json_schema_extra={"label": "API Key", "input_type": "password"},
    )
    model: str = Field(
        default="", description="模型名。",
        json_schema_extra={"label": "模型名", "placeholder": "如 gpt-4o-mini / claude-sonnet-4 / gemini-2.5-flash"},
    )
    backup_base_url: str = Field(
        default="", description="备用渠道地址（主渠道失败时尝试）。",
        json_schema_extra={"label": "备用渠道地址"},
    )
    backup_api_key: str = Field(
        default="", description="备用渠道 Key。",
        json_schema_extra={"label": "备用 Key", "input_type": "password"},
    )
    backup_model: str = Field(
        default="", description="备用渠道模型名。",
        json_schema_extra={"label": "备用模型名"},
    )
    timeout_seconds: int = Field(
        default=60, description="单次请求超时秒数。", ge=5, le=600,
        json_schema_extra={"label": "超时秒数"},
    )


class BuiltinModelConfig(PluginConfigBase):
    """使用 MaiBot 内置模型配置（推荐默认）"""

    __ui_label__ = "内置模型路由"
    __ui_icon__ = "cpu"
    __ui_order__ = 3

    model_name: str = Field(
        default="",
        description="直接指定 MaiBot 已配置的具体模型名（最高优先级）。",
        json_schema_extra={"label": "指定模型名", "placeholder": "模型管理里的 name，留空走任务路由"},
    )
    task_names: str = Field(
        default="",
        description="按顺序尝试的 MaiBot 任务名。",
        json_schema_extra={"label": "任务路由顺序", "placeholder": "逗号分隔，留空默认 utils,replyer,planner"},
    )
    vision_task: str = Field(
        default="image",
        description="带图提问时优先使用的视觉任务名。",
        json_schema_extra={"label": "视觉任务名"},
    )


class GeneralConfig(PluginConfigBase):
    __ui_label__ = "基础设置"
    __ui_icon__ = "settings"
    __ui_order__ = 0

    enabled: bool = Field(
        default=True, description="是否响应 /问 /ask 指令与 Tool 调用。",
        json_schema_extra={"label": "启用看板功能", "x-icon": "power"},
    )
    max_tokens: int = Field(
        default=1536, description="LLM 单次回答最大 token 数。", ge=256, le=32000,
        json_schema_extra={"label": "最大 Token 数"},
    )
    temperature: float = Field(
        default=0.3, description="LLM 采样温度。", ge=0.0, le=2.0,
        json_schema_extra={"label": "采样温度"},
    )


class DashboardPluginConfig(PluginConfigBase):
    """麦麦知识看板插件配置"""

    plugin: PluginSectionConfig = Field(default_factory=PluginSectionConfig)
    general: GeneralConfig = Field(default_factory=GeneralConfig)
    theme: ThemeConfig = Field(default_factory=ThemeConfig)
    external_model: ExternalModelConfig = Field(default_factory=ExternalModelConfig)
    builtin_model: BuiltinModelConfig = Field(default_factory=BuiltinModelConfig)
