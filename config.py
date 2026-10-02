from pydantic import Field
from maibot_sdk.config import PluginConfigBase


class PluginSectionConfig(PluginConfigBase):
    """插件元信息"""

    __ui_label__ = "插件"
    __ui_order__ = -1

    enabled: bool = Field(default=True, description="是否启用本插件")
    config_version: str = Field(default="1.1.0", description="配置版本")


class ThemeConfig(PluginConfigBase):
    """看板主题"""

    __ui_label__ = "主题外观"
    __ui_order__ = 1

    theme: str = Field(
        default="light",
        description="看板主题色：light(浅色蓝) / dark(暗夜) / warm(暖阳橙) / sakura(樱粉) / mint(薄荷绿) / grape(葡萄紫)。",
    )
    header_text: str = Field(
        default="",
        description="卡片头部提问标题左侧的引导文案，留空则自动显示提问内容。",
    )
    footer_text: str = Field(
        default="",
        description="卡片底部水印署名，留空自动用「Bot昵称 · 麦麦知识看板」。",
    )
    footer_right_text: str = Field(
        default="智能知识生成 · 仅供参考",
        description="卡片底部右下角文案。",
    )


class ExternalModelConfig(PluginConfigBase):
    """自定义外部模型渠道（优先于 MaiBot 内置模型配置）"""

    __ui_label__ = "自定义模型渠道"
    __ui_order__ = 2

    enabled: bool = Field(default=False, description="启用后优先使用下方自定义渠道，失败才回退到 MaiBot 内置模型。")
    protocol: str = Field(
        default="openai",
        description="API 协议格式：openai(/v1/chat/completions) / openai_responses(/v1/responses) / claude(/v1/messages) / gemini(:generateContent)。",
    )
    base_url: str = Field(default="", description="API 基础地址，例如 https://api.openai.com 或你的中转站地址。")
    api_key: str = Field(default="", description="API Key。")
    model: str = Field(default="", description="模型名，例如 gpt-4o-mini / claude-sonnet-4 / gemini-2.5-flash。")
    backup_base_url: str = Field(default="", description="备用渠道地址（主渠道失败时尝试）。")
    backup_api_key: str = Field(default="", description="备用渠道 Key。")
    backup_model: str = Field(default="", description="备用渠道模型名。")
    timeout_seconds: int = Field(default=60, description="单次请求超时秒数。")


class BuiltinModelConfig(PluginConfigBase):
    """使用 MaiBot 内置模型配置（推荐默认）"""

    __ui_label__ = "内置模型路由"
    __ui_order__ = 3

    task_names: str = Field(
        default="",
        description="按顺序尝试的 MaiBot 任务名，逗号分隔，例如 utils,replyer,planner。留空用默认 [utils, replyer, planner]。",
    )
    model_name: str = Field(
        default="",
        description="直接指定 MaiBot 已配置的具体模型名（最高优先级），留空走任务路由。",
    )
    vision_task: str = Field(
        default="image",
        description="带图提问时优先使用的视觉任务名。",
    )


class GeneralConfig(PluginConfigBase):
    __ui_label__ = "基础设置"
    __ui_order__ = 0

    enabled: bool = Field(default=True, description="是否启用看板插件")
    max_tokens: int = Field(default=1536, description="LLM 单次回答最大 token 数。")
    temperature: float = Field(default=0.3, description="LLM 采样温度。")


class DashboardPluginConfig(PluginConfigBase):
    """麦麦知识看板插件配置"""

    plugin: PluginSectionConfig = Field(default_factory=PluginSectionConfig)
    general: GeneralConfig = Field(default_factory=GeneralConfig)
    theme: ThemeConfig = Field(default_factory=ThemeConfig)
    external_model: ExternalModelConfig = Field(default_factory=ExternalModelConfig)
    builtin_model: BuiltinModelConfig = Field(default_factory=BuiltinModelConfig)
