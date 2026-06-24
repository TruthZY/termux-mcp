# Termux-MCP

[English](README.md) | 中文

一个为 Termux 的独立 MCP（模型上下文协议）服务器。公开 88+ 个工具，涵盖 shell 执行、文件操作、设备控制、媒体和开发者工具，通过标准 [MCP](https://modelcontextprotocol.io) 协议提供。

```text
MCP 客户端 ──JSON-RPC 2.0──> POST /mcp ──> Termux-MCP ──> 工具处理
  (MiClaw, Claude, 等)        <── 结果 ──     │
                                              ├── shell_exec()
                                              ├── file_read()
                                              ├── battery_status()
                                              └── ...88+ 工具
```

## 架构

```
termux_mcp/
├── __main__.py          # 入口点 (argparse + 处理器导入)
├── mcp_server.py        # MCP Streamable HTTP 服务器 (JSON-RPC 2.0)
├── registry.py          # 中央工具注册表 (@register_tool 装饰器)
├── config.py            # 基于环境的配置
├── shell.py             # Shell 执行引擎 (流式输出)
├── utils.py             # 路径安全、shell 引用、JSON 辅助
└── handlers/
    ├── basic.py         # Shell、文件、系统基础功能
    ├── device.py        # 设备、传感器、通信、媒体
    ├── tools.py         # 开发工具、Git、诊断、工具集
    ├── ai_power.py      # AI 增强的电源功能
    ├── terminal.py      # 终端超级工具
    ├── features.py      # 系统、定时任务、备份、配方
    └── history.py       # 命令历史
```

工具通过每个处理器模块中的 `@register_tool` 装饰器注册。注册表自动从单一来源生成 MCP 和 OpenAI 函数调用架构。不需要外部配置文件。

## 快速开始

```bash
# 一次性设置
pkg install python git -y
git clone -b main https://github.com/TruthZY/termux-mcp.git
cd termux-mcp
chmod +x start-mcp.sh
./start-mcp.sh
```

首次运行后，在任何 Termux 会话中输入 `mcp` 即可启动服务器。

## 手动启动

```bash
cd ~/termux-mcp
python -m termux_mcp                    # 默认: 端口 3000, 绑定 0.0.0.0
python -m termux_mcp --port 3000        # 自定义端口
python -m termux_mcp --host 127.0.0.1   # 仅本地绑定
```

## 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TERMUX_MCP_PORT` | `3000` | MCP 服务器监听端口 |
| `TERMUX_MCP_HOST` | `0.0.0.0` | 绑定地址 |
| `TERMUX_MCP_TIMEOUT` | `120` | Shell 命令超时时间 (秒) |
| `TERMUX_MCP_AUTH_TOKEN` | *(无)* | 用于身份验证的 API 密钥 |

设置 `TERMUX_MCP_AUTH_TOKEN` (16+ 字符) 以在所有请求上要求 `X-API-Key` 或 `Authorization: Bearer` 身份验证。

## MCP 协议

服务器通过 Streamable HTTP 实现 [模型上下文协议](https://modelcontextprotocol.io):

- **端点**: `POST /mcp`
- **协议**: JSON-RPC 2.0
- **方法**: `initialize`, `tools/list`, `tools/call`, `notifications/initialized`
- **健康检查**: `GET /health`

### MiClaw 配置

```json
{
  "mcpServers": {
    "termux-mcp": {
      "url": "http://127.0.0.1:3000/mcp"
    }
  }
}
```

### Claude Desktop / Cursor

```json
{
  "mcpServers": {
    "termux-mcp": {
      "url": "http://<手机IP>:3000/mcp"
    }
  }
}
```

## 工具 (88+)

### Shell 和文件

| 工具 | 说明 |
|------|------|
| `shell_exec` | 执行 shell 命令，流式输出 |
| `shell_cancel` | 取消运行的命令 |
| `file_list` | 列出目录内容 |
| `file_read` | 读取文件 (前 500 行) |
| `file_write` | 写入/创建文件 |
| `file_mkdir` | 创建目录 (递归) |
| `file_delete` | 删除文件/目录 (需确认) |
| `file_search` | 按模式搜索文件 |

### 设备和传感器

| 工具 | 说明 |
|------|------|
| `battery_status` | 电池电量、充电状态、温度 |
| `vibrate` | 触发触觉振动 |
| `torch` | 切换手电筒 |
| `wallpaper` | 设置设备壁纸 |
| `brightness` | 获取/设置屏幕亮度 (0-255) |
| `volume` | 获取/设置音量 |
| `sensor_read` | 读取加速度计、陀螺仪等 |
| `fingerprint` | 指纹认证 |
| `infrared` | 传输红外信号 |

### 网络和位置

| 工具 | 说明 |
|------|------|
| `wifi_info` | 当前 WiFi 连接详情 |
| `wifi_scan` | 扫描附近 WiFi 网络 |
| `location` | GPS/网络定位 |
| `public_ip` | 公网 IP 地址 |

### 通信

| 工具 | 说明 |
|------|------|
| `clipboard_get` / `clipboard_set` | 读/写系统剪贴板 |
| `sms_send` / `sms_inbox` | 发送/读取短信 |
| `contacts` | 列出通讯录 |
| `phone_call` | 拨打电话 |
| `notify` / `notify_remove` | 系统通知 |
| `share` | Android 分享菜单 |
| `open_url` | 在浏览器中打开 URL |

### 媒体和相机

| 工具 | 说明 |
|------|------|
| `camera_photo` / `camera_info` | 拍照 / 列出相机 |
| `screenshot` | 截屏 |
| `screen_record` | 开始/停止屏幕录制 |
| `tts_speak` | 文本转语音 |
| `speech_to_text` | 语音识别 |
| `microphone_record` | 录音 |
| `media_player` | 媒体播放控制 |
| `qrcode` / `scan_barcode` | 生成/扫描二维码 |

### 系统和进程

| 工具 | 说明 |
|------|------|
| `system_info` | CPU、RAM、磁盘、温度、运行时间 |
| `process_list` / `process_kill` | 进程管理 |
| `health` | 完整系统诊断 |
| `env` / `ping` | 环境信息 / 健康检查 |

### 开发者工具

| 工具 | 说明 |
|------|------|
| `git_op` | Git 克隆/状态/日志/差异/拉取/推送 |
| `git_smart` | AI 友好的 Git (建议提交、修复冲突) |
| `git_pr` | GitHub PR 管理 |
| `review` | 代码审查 (语法检查、Lint) |
| `script_gen` | 生成 Shell/Python 脚本 |
| `regex_test` | 测试正则表达式 |
| `db_query` / `db_design` | SQLite 查询 / 架构设计 |
| `explain` | 解释 Shell 命令 |
| `dev_env` | 一键开发环境设置 |

### 工具集

| 工具 | 说明 |
|------|------|
| `image_process` | 图像操作 (需要 ImageMagick) |
| `video_process` | 视频操作 (需要 FFmpeg) |
| `text_extract` | OCR 文本提取 (需要 Tesseract) |
| `translate` | 文本翻译 |
| `weather` | 天气查询 |
| `speedtest` | 网速测试 |
| `download` | 通过系统管理器下载 |
| `web_server` | 启动/停止 HTTP 文件服务器 |
| `smart_install` | 智能包安装 |
| `diagnose` | 环境诊断 |
| `ssh_wizard` | SSH 服务器设置 |
| `backup` / `restore` | 备份和恢复 |
| `migrate` | 环境迁移 |
| `cron_add` / `cron_list` / `cron_remove` | 定时任务 |
| `recipe_save` / `recipe_run` | 自动化配方 |

## 安全

- Shell 命令检查是否存在风险模式 (fork 炸弹、`rm -rf /` 等)
- 文件路径验证以防止访问 `/dev/`、`/proc/`、`/sys/`
- 支持通过 `X-API-Key` 或 `Authorization: Bearer` 进行 API 密钥认证
- 请求体限制为 5 MB
- 危险操作需要显式确认

## 许可证

MIT
