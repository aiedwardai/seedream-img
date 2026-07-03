---
name: volcengine-seedream
description: Hermes Agent 火山引擎 Seedream 文生图插件 — 使用火山方舟 Ark API 生成图片，无需额外 API Key
version: 1.1.0
aliases: [volcengine-seedream, seedream, volcengine-img]
source: https://github.com/aiedwardai/volcengine_seedream_hermes_plugin_setup
author: aiedwardai
tags: [image-generation, seedream, volcengine, doubao, plugin]
---

# volcengine-seedream — 火山 Seedream 文生图插件

## 简介

在 Hermes Agent 中使用 `image_generate` 工具调用火山方舟 Ark / 豆包 Seedream 生成图片。

## 安装步骤

### 1. 创建插件目录

```bash
mkdir -p ~/.hermes/profiles/h8900/plugins/image_gen/volcengine-seedream/
```

### 2. 写入 plugin.yaml

```yaml
name: volcengine-seedream
version: 1.1.0
description: Volcengine Ark Seedream image generation backend for Hermes
author: local
kind: backend
requires_env:
  - ARK_API_KEY
  - SEEDREAM_MODEL_ID
```

### 3. 写入 __init__.py

从 GitHub 仓库复制完整代码：
https://github.com/aiedwardai/volcengine_seedream_hermes_plugin_setup/blob/main/plugin/volcengine-seedream/__init__.py

### 4. 配置环境变量

```bash
hermes config set ARK_API_KEY "你的火山Ark API Key"
hermes config set SEEDREAM_MODEL_ID "doubao-seedream-4-0-250828"
hermes config set ARK_BASE_URL "https://ark.cn-beijing.volces.com/api/v3"
```

### 5. 启用插件和工具集

```bash
hermes plugins enable volcengine-seedream
hermes config set image_gen.provider volcengine-seedream
hermes tools enable image_gen
```

### 6. 重启会话

```
/reset
```

## 验证

```
生成一张方形图片：一只在樱花树下的橘猫，半写实风格
```

## 环境变量参考

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `ARK_API_KEY` | ✅ | — | 火山方舟 API Key |
| `SEEDREAM_MODEL_ID` | ✅ | `doubao-seedream-4-0-250828` | 模型 ID 或 `ep-...` |
| `ARK_BASE_URL` | ❌ | `https://ark.cn-beijing.volces.com/api/v3` | API 基础地址 |
| `SEEDREAM_SQUARE_SIZE` | ❌ | `1024x1024` | 方形图尺寸 |
| `SEEDREAM_PORTRAIT_SIZE` | ❌ | `1024x1536` | 竖屏图尺寸 |
| `SEEDREAM_LANDSCAPE_SIZE` | ❌ | `1536x1024` | 横屏图尺寸 |
| `SEEDREAM_WATERMARK` | ❌ | `false` | 是否加水印 |
| `SEEDREAM_NEGATIVE_PROMPT` | ❌ | — | 全局负向提示词 |
| `SEEDREAM_CFG_SCALE` | ❌ | — | CFG 引导系数 |
| `SEEDREAM_STEPS` | ❌ | — | 生成步数 |
| `SEEDREAM_DEBUG` | ❌ | `false` | 调试日志 |

## 常见问题

- **ARK_API_KEY is not set**: 检查 `.env` 文件，确保已配置
- **InvalidParameter size**: 火山 API 要求最小 921600 像素（约 960x960），设置较大尺寸
- **404 endpoint**: 检查 `ARK_BASE_URL` 和 `SEEDREAM_IMAGE_ENDPOINT`