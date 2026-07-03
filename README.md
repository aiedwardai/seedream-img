# volcengine-seedream — Hermes Agent 火山引擎 Seedream 文生图插件

> 在 Hermes Agent 中使用火山方舟 Ark / 豆包 Seedream 生成图片。无需额外 API，完全利用火山引擎的 OpenAI 兼容接口。

## 特性

- ✅ 零 API Key 成本 — 直接使用火山方舟 Ark API
- ✅ 3 种比例支持（方形 / 竖屏 / 横屏）
- ✅ 负向提示词支持
- ✅ 智能错误处理（含 API 400 级错误详情）
- ✅ 调试日志模式
- ✅ 可选 cfg_scale / steps / seed 参数
- ✅ 已通过 `doubao-seedream-4-0-250828` 实测

## 快速安装

```bash
# 1. 创建目录
mkdir -p ~/.hermes/profiles/$(hermes config path | sed 's/.*\/profiles\///;s/\/config.yaml//')/plugins/image_gen/volcengine-seedream/

# 2. 复制文件
cp plugin/volcengine-seedream/* ~/.hermes/profiles/$(hermes config path | sed 's/.*\/profiles\///;s/\/config.yaml//')/plugins/image_gen/volcengine-seedream/

# 3. 配置环境变量
hermes config set ARK_API_KEY "你的火山Ark API Key"
hermes config set SEEDREAM_MODEL_ID "doubao-seedream-4-0-250828"

# 4. 启用插件和工具集
hermes plugins enable volcengine-seedream
hermes config set image_gen.provider volcengine-seedream
hermes tools enable image_gen   # 如未启用

# 5. 重启会话
/reset
```

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `ARK_API_KEY` | ✅ | — | 火山方舟 API Key |
| `SEEDREAM_MODEL_ID` | ✅ | `doubao-seedream-4-0-250828` | 模型 ID 或 `ep-...` endpoint |
| `ARK_BASE_URL` | ❌ | `https://ark.cn-beijing.volces.com/api/v3` | API 基础地址 |
| `SEEDREAM_IMAGE_ENDPOINT` | ❌ | `/images/generations` | 图片生成接口路径 |
| `SEEDREAM_SQUARE_SIZE` | ❌ | `1024x1024` | 方形图尺寸 |
| `SEEDREAM_PORTRAIT_SIZE` | ❌ | `1024x1536` | 竖屏图尺寸 |
| `SEEDREAM_LANDSCAPE_SIZE` | ❌ | `1536x1024` | 横屏图尺寸 |
| `SEEDREAM_WATERMARK` | ❌ | `false` | 是否加水印 |
| `SEEDREAM_RESPONSE_FORMAT` | ❌ | `url` | 返回格式（url/b64_json） |
| `SEEDREAM_TIMEOUT` | ❌ | `180` | API 超时（秒） |
| `SEEDREAM_NEGATIVE_PROMPT` | ❌ | — | 全局负向提示词 |
| `SEEDREAM_CFG_SCALE` | ❌ | — | CFG 引导系数 |
| `SEEDREAM_STEPS` | ❌ | — | 生成步数 |
| `SEEDREAM_DEBUG` | ❌ | `false` | 调试日志 |

## 验证

```text
生成一张 1024x1024 的方形图片：一只在樱花树下的橘猫
```

## 项目结构

```
seedream-img/
├── SKILL.md                              # 可用作 Hermes skill 安装
├── README.md                             # 本文档
├── volcengine_seedream_hermes_plugin_setup.md  # 详细安装指南
└── plugin/
    └── volcengine-seedream/
        ├── plugin.yaml                   # 插件元数据
        └── __init__.py                   # Provider 实现代码
```