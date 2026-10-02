# 麦麦知识看板（MaiMai Knowledge Dashboard）

把麦麦的问答渲染为一张优雅的知识长图卡片：指令触发 + 大模型自主 Tool 调用两用，多主题配色、多渠道模型、署名文案全部可在插件配置里调整。

## 功能

- `/问`、`/ask`、`/查`、`/看板` 指令提问，回答渲染为知识卡片长图
- 支持图片提问（带图或引用图片消息）
- 提供 `render_dashboard_card` Tool，大模型遇到复杂架构/流程类问题可自主调用
- **6 套主题**：`light` 浅色蓝、`dark` 暗夜、`warm` 暖阳橙、`sakura` 樱粉、`mint` 薄荷绿、`grape` 葡萄紫
- **双模型来源**：
  - MaiBot 内置模型配置（默认）：可直选模型名，或按任务路由依次尝试
  - 自定义渠道：`openai` / `openai_responses` / `claude` / `gemini` 四种协议，支持主备两个渠道自动切换，失败自动回退内置模型
- 可自定义卡片开头引导语、底部署名、右下角文案
- 渲染为纯本地 PIL 绘制，速度快、不依赖外部渲染服务

## 安装

把本目录解压到 MaiBot 的 `plugins/` 目录，重启 MaiBot（或热重载插件），然后在 WebUI 插件配置里调整参数。

## 指令

```
/问 什么是大模型的注意力机制
/ask transformer 架构
/看板 什么是 RAG
```

## 配置说明（config.toml / WebUI 插件配置）

### [general]

| 项 | 默认 | 说明 |
|---|---|---|
| enabled | true | 插件开关 |
| max_tokens | 1536 | 单次回答最大 token |
| temperature | 0.3 | 采样温度 |

### [theme]

| 项 | 默认 | 说明 |
|---|---|---|
| theme | light | 主题色：light / dark / warm / sakura / mint / grape |
| header_text | 空 | 卡片头部引导文案，留空自动显示提问内容 |
| footer_text | 空 | 底部署名，留空自动为「Bot昵称 · 麦麦知识看板」 |
| footer_right_text | 智能知识生成 · 仅供参考 | 右下角文案 |

### [external_model]（自定义渠道，优先级最高）

| 项 | 说明 |
|---|---|
| enabled | 开启后优先走自定义渠道 |
| protocol | `openai`（/v1/chat/completions）、`openai_responses`（/v1/responses）、`claude`（/v1/messages）、`gemini`（:generateContent） |
| base_url / api_key / model | 主渠道地址、Key、模型名 |
| backup_base_url / backup_api_key / backup_model | 备用渠道（可选），主渠道失败时自动尝试 |
| timeout_seconds | 单次请求超时，默认 60 |

主备都失败后自动回退 MaiBot 内置模型路由，保证有图可出。

### [builtin_model]（MaiBot 内置模型）

| 项 | 默认 | 说明 |
|---|---|---|
| model_name | 空 | 直接指定模型配置里的模型名（最高优先级） |
| task_names | 空 | 任务路由顺序，逗号分隔，默认 `utils,replyer,planner` |
| vision_task | image | 带图提问时优先尝试的视觉任务 |

## 协议速查

| protocol | 请求 | 鉴权 |
|---|---|---|
| openai | POST `{base}/v1/chat/completions` | `Authorization: Bearer key` |
| openai_responses | POST `{base}/v1/responses` | `Authorization: Bearer key` |
| claude | POST `{base}/v1/messages` | `x-api-key` + `anthropic-version` |
| gemini | POST `{base}/v1beta/models/{model}:generateContent?key=` | URL key |

## 依赖

- Pillow >= 9.0.0（渲染）
- aiohttp >= 3.8.0（仅自定义渠道需要）

## 许可

MIT
