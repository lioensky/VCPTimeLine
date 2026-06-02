# VCPTimeLine (时间线生成器)

一个能够自动从本地或局域网目录中，提取特定角色的日记和记忆碎片，并按照月份通过 AI 进行并发总结，最终生成独立 Markdown 时间线文件的桌面端小工具。

## 功能特性
- **支持多格式日期匹配**：兼容多种日记前缀格式，如 `[2026-02-22] - Nova`，`[2025.5.17] - 小绝` 等。
- **高并发智能分块**：当单月日记超过 AI 的上下文限制时，自动切分文本，利用多协程高并发请求总结模型。
- **增量更新与断点续联**：自动检查角色时间线目录，如果某月已总结则跳过，方便长期持续维护更新。
- **支持 Windows UNC 路径**：原生支持类似 `\\DESKTOP-QULL1SM\Share` 的局域网文件共享路径。
- **角色目录前缀过滤**：扫描记忆库时，只进入角色名前缀目录和公共前缀目录，减少大目录下的无效遍历。

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

# 局域网记忆库地址、过滤文件夹与公共目录前缀配置（用逗号分隔）
MEMORY_BASE_PATH=\\DESKTOP-QULL1SM...
IGNORE_FOLDERS=待整理,公共知识库,小克的知识
PUBLIC_FOLDER_PREFIXES=公共
```

## 扫描规则

程序会从 `MEMORY_BASE_PATH` 指向的记忆库根目录开始扫描。为了降低扫描成本，只会进入根目录下符合以下规则的一级文件夹：

- 以当前角色名开头的文件夹，例如角色名为 `小克` 时，会扫描 `小克知识`、`小克学习`。
- 以 `PUBLIC_FOLDER_PREFIXES` 配置项中任一前缀开头的公共文件夹，例如默认 `公共` 会扫描 `公共知识`、`公共记忆`。

进入这些一级文件夹后，程序会继续递归扫描其内部 `.txt` 和 `.md` 文件，并仍然跳过 `IGNORE_FOLDERS` 配置中的目录。

## 使用方法

在此目录下运行：
```bash
python main.py
```
在弹出的 GUI 界面中输入**角色名**、**起始年月**以及**结束年月**，点击生成即可。程序会在控制台中打印详细进度，完成后将在当前目录下生成对应的 `[角色名]timeline` 文件夹。
