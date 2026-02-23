# VCPTimeLine (时间线生成器)

一个能够自动从本地或局域网目录中，提取特定角色的日记和记忆碎片，并按照月份通过 AI 进行并发总结，最终生成独立 Markdown 时间线文件的桌面端小工具。

## 功能特性
- **支持多格式日期匹配**：兼容多种日记前缀格式，如 `[2026-02-22] - Nova`，`[2025.5.17] - 小绝` 等。
- **高并发智能分块**：当单月日记超过 AI 的上下文限制时，自动切分文本，利用多协程高并发请求总结模型。
- **增量更新与断点续联**：自动检查角色时间线目录，如果某月已总结则跳过，方便长期持续维护更新。
- **支持 Windows UNC 路径**：原生支持类似 `\\DESKTOP-QULL1SM\Share` 的局域网文件共享路径。

## 安装与配置

1. 安装依赖库：
```bash
pip install -r requirements.txt
```

2. 配置文件：
将项目自带的 `.env.example` 复制为 `.env`，并在其中配置：
```ini
# API 地址和密钥配置
SUMMARY_MODEL_URL=https://api.openai.com/v1/chat/completions
SUMMARY_MODEL_API_KEY=你的真实的API_KEY
SUMMARY_MODEL_NAME=gpt-4o

# 最大上下文长度设定和高并发切分配置（默认6万字符）
SUMMARY_MODEL_MAX_CONTEXT=60000
MAX_CONCURRENT_TASKS=5

# 局域网记忆库地址与过滤文件夹配置（用逗号分隔）
MEMORY_BASE_PATH=\\DESKTOP-QULL1SM...
IGNORE_FOLDERS=待整理,公共知识库,小克的知识
```

## 使用方法

在此目录下运行：
```bash
python main.py
```
在弹出的 GUI 界面中输入**角色名**、**起始年月**以及**结束年月**，点击生成即可。程序会在控制台中打印详细进度，完成后将在当前目录下生成对应的 `[角色名]timeline` 文件夹。
