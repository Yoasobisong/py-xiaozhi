# py-xiaozhi 助手功能路线图

> 按任务大小排序（S → L），优先实现小任务

## 已完成功能一览

| 分类 | 工具名 | 功能 | 触发示例 |
|------|--------|------|----------|
| **音量** | `self.audio_speaker.set_volume` | 设置系统音量 (0-100) | "音量调到50" |
| **音量** | `self.audio_speaker.get_volume` | 获取当前音量 | "现在音量多少" |
| **应用** | `self.application.launch` | 启动应用程序 | "打开微信" |
| **应用** | `self.application.kill` | 关闭应用程序 | "关掉Chrome" |
| **应用** | `self.application.scan_installed` | 扫描已安装应用 | "电脑上装了什么软件" |
| **应用** | `self.application.list_running` | 列出运行中进程 | "哪些程序在运行" |
| **电源** | `system.shutdown` | 关机（默认30s延迟，可取消） | "关机" |
| **电源** | `system.restart` | 重启（默认30s延迟，可取消） | "重启电脑" |
| **电源** | `system.sleep` | 休眠/睡眠 | "休眠" |
| **电源** | `system.lock_screen` | 锁屏 | "锁屏" |
| **电源** | `system.cancel_shutdown` | 取消已计划的关机/重启 | "取消关机" |
| **亮度** | `system.set_brightness` | 设置屏幕亮度 (0-100) | "亮度调到50" |
| **亮度** | `system.get_brightness` | 获取当前亮度 | "亮度多少" |
| **日历** | `self.calendar.create_event` | 创建日历事件 | "明天下午3点开会" |
| **日历** | `self.calendar.get_events` | 查询事件 | "今天有什么安排" |
| **日历** | `self.calendar.get_upcoming_events` | 获取即将到来的事件 | "接下来有什么事" |
| **日历** | `self.calendar.update_event` | 修改事件 | "把会议改到4点" |
| **日历** | `self.calendar.delete_event` | 删除事件 | "取消明天的会议" |
| **日历** | `self.calendar.delete_events_batch` | 批量删除事件 | "清空本周日程" |
| **日历** | `self.calendar.get_categories` | 获取事件分类 | "有哪些日程分类" |
| **定时** | `timer.start_countdown` | 倒计时/提醒（纯提醒 + MCP调用） | "10秒后提醒我上厕所" |
| **定时** | `timer.cancel_countdown` | 取消倒计时 | "取消倒计时" |
| **定时** | `timer.get_active_timers` | 查看活动倒计时 | "现在有几个定时器" |
| **音乐** | `music_player.play` | 打开网易云音乐并播放（自动检测播放状态） | "放首歌" |
| **音乐** | `music_player.search_and_play` | 搜索指定歌曲并播放 | "播放稻香" |
| **音乐** | `music_player.play_favorites` | 播放「我喜欢的音乐」歌单 | "放我收藏的歌" |
| **音乐** | `music_player.pause` | 暂停音乐 | "暂停音乐" |
| **音乐** | `music_player.stop` | 停止音乐 | "停止音乐" |
| **音乐** | `music_player.next_track` | 下一首 | "下一首" |
| **音乐** | `music_player.previous_track` | 上一首 | "上一首" |
| **音乐** | `music_player.get_current_track` | 获取当前播放歌曲信息 | "现在放的什么歌" |
| **视觉** | `take_photo` | 摄像头拍照 + 分析 | "帮我看看这是什么" |
| **视觉** | `take_screenshot` | 桌面截图 + 分析 | "截个屏看看" |
| **网页** | `web.open_url` | 用Chrome打开URL | "打开B站" |
| **网页** | `web.search` | 用Chrome搜索（支持Google/百度/Bing/GitHub/B站/知乎） | "帮我搜Python教程" |
| **剪贴板** | `clipboard.read_text` | 读取剪贴板文本（自动翻译：中→英，非中→中） | "翻译剪贴板内容" |
| **剪贴板** | `clipboard.write_text` | 写入文本到剪贴板 | "把翻译结果复制到剪贴板" |
| **剪贴板** | `clipboard.analyze_image` | 分析剪贴板中的图片（OCR/翻译/代码解读） | "分析剪贴板图片" |
| **网络** | `network.ping` | Ping 主机测试连通性和延迟 | "ping一下百度" |
| **网络** | `network.speedtest` | 简单下载测速 | "测一下网速" |
| **网络** | `network.get_ip` | 获取局域网 IP 和公网 IP | "我的IP是多少" |
| **命理** | `self.bazi.*` | 八字命理分析（6个工具） | "帮我算一下八字" |

> 共 **48 个** MCP 工具已注册

---

## 待实现功能

### M1. 剪贴板图片 → 视觉分析（OCR/翻译/代码解读）
- **大小**: M（中）
- **目录**: `src/mcp/tools/clipboard/`
- **说明**: 读取 Win+Shift+S 截图或复制的图片，发送到 VL API 分析
- **依赖**: `PIL.ImageGrab.grabclipboard()`
- **实现**:
  - 检测剪贴板是否有图片
  - 提取图片 → 编码为 JPEG
  - 复用现有 camera 的 `analyze()` 方法发送到 VL API
  - 支持场景：OCR识别文字、翻译截图中的英文、解读代码截图、分析错误截图
- **工具**: `clipboard.analyze_image`
- **注意**: 需要配置 VL API（智谱 GLM-4V 或其他视觉模型）

### M2. 网络工具
- **大小**: M（中）
- **目录**: `src/mcp/tools/network/` （新建）
- **说明**: 基础网络诊断工具
- **实现**:
  - Ping 指定主机
  - 简单测速（下载测试文件计算速度）
  - 获取本机 IP（局域网 + 公网）
- **工具**: `network.ping`, `network.speedtest`, `network.get_ip`

### M3. 网页内容抓取与总结框架
- **大小**: M（中）
- **目录**: `src/mcp/tools/web/`
- **说明**: 通用网页抓取框架，提取正文内容供 AI 总结
- **依赖**: `requests`, `beautifulsoup4`
- **实现**:
  - 抓取指定 URL 网页内容
  - 提取正文（去除导航、广告等）
  - 返回 markdown 格式文本
  - AI 后端负责总结/翻译/提取信息
- **工具**: `web.fetch_content`, `web.summarize_url`
- **注意**: 这是后续所有内容聚合功能的基础

### M4. 进程管理增强
- **大小**: M（中）
- **目录**: `src/mcp/tools/system/`
- **说明**: 现有 kill/list 功能增强
- **实现**:
  - 查询 CPU/内存占用 top 进程
  - 按关键词过滤进程
  - 确认后关闭（AI 交互层面）
- **工具**: 复用现有 `self.application.kill` + `self.application.list_running`

### L1. GitHub Trending 周报
- **大小**: L（大）
- **目录**: `src/mcp/tools/web/sources/`
- **说明**: 每周自动抓取 GitHub Trending，生成摘要
- **依赖**: M3 网页框架
- **实现**:
  - 抓取 `github.com/trending` 页面（可按语言过滤）
  - 提取仓库名、描述、star 数、语言
  - 生成周报格式摘要
  - 支持手动触发："这周 GitHub 有什么热门项目？"
- **工具**: `web.github_trending`
- **数据源**: `https://github.com/trending?since=weekly`

### L2. B站热门周报
- **大小**: L（大）
- **目录**: `src/mcp/tools/web/sources/`
- **说明**: 抓取B站热门/每周必看，生成摘要
- **实现**:
  - 使用B站 API: `https://api.bilibili.com/x/web-interface/popular`
  - 或每周必看: `https://api.bilibili.com/x/web-interface/popular/series/one`
  - 提取标题、UP主、播放量、简介
  - 按分类过滤（科技/知识/编程相关优先）
- **工具**: `web.bilibili_trending`

### L3. ArXiv 论文每日推荐（自动化/机器人/CV方向）
- **大小**: L（大）
- **目录**: `src/mcp/tools/web/sources/`
- **说明**: 每天推荐一篇与自动化相关的论文
- **依赖**: M3 网页框架
- **实现**:
  - 使用 ArXiv API: `http://export.arxiv.org/api/query`
  - 搜索分类: `cs.RO`(机器人), `cs.CV`(计算机视觉), `cs.SY`(系统控制), `eess.SY`(电子系统)
  - 每天获取最新论文，选择最相关的一篇
  - 提取标题、作者、摘要，翻译为中文
  - 支持手动触发："今天有什么新论文？"
- **工具**: `web.arxiv_daily`

### L4. Hacker News 热门摘要
- **大小**: L（大）
- **目录**: `src/mcp/tools/web/sources/`
- **说明**: 抓取 HN 热门帖子，生成中文摘要
- **实现**:
  - 使用 HN API: `https://hacker-news.firebaseio.com/v0/topstories.json`
  - 获取 top 10 帖子详情
  - 提取标题、链接、得分、评论数
  - 翻译标题为中文
- **工具**: `web.hackernews_top`

### L5. 组合工作流/快捷指令
- **大小**: L（大）
- **目录**: `src/mcp/tools/workflow/` （新建）
- **说明**: 将多个工具组合为一个工作流
- **实现**:
  - 预定义工作流配置（JSON/YAML）
  - 支持顺序执行多个 MCP 工具
  - 例: "开始工作" → 打开 VSCode + 打开浏览器 + 音量调到30
  - 例: "下班" → 关闭所有应用 + 休眠
  - 用户可自定义工作流
- **工具**: `workflow.run`, `workflow.list`, `workflow.create`

### L6. Notion 集成（语音笔记）
- **大小**: L（大）
- **目录**: `src/mcp/tools/notion/` （新建）
- **说明**: 将语音口述内容保存到 Notion
- **依赖**: `notion-client` 库 + Notion API Token
- **实现**:
  - 连接 Notion API
  - 创建笔记页面
  - 追加内容到已有页面
  - 查询笔记内容
- **工具**: `notion.create_note`, `notion.append_note`, `notion.search_notes`

---

## 实现顺序

```
Phase 1 (基础工具) ✅ 已完成:
  S1 系统电源管理 → S2 打开网页/搜索 → S3 亮度控制 → S4 剪贴板文本

Phase 2 (视觉 + 网络):
  M1 剪贴板图片分析 → M2 网络工具 → M3 网页抓取框架

Phase 3 (内容聚合):
  L1 GitHub周报 → L2 B站周报 → L3 ArXiv论文 → L4 HN摘要

Phase 4 (高级功能):
  L5 组合工作流 → L6 Notion集成
```

## 备注

- 所有新工具遵循现有 MCP 工具架构（Manager + Tools + __init__.py）
- 工具描述使用英文，支持中英文用户指令
- 每个工具需在 `src/mcp/mcp_server.py` 中注册
- 网页内容抓取相关功能（L1-L4）依赖 M3 框架先完成

---

## 待解决问题

| 功能 | 状态 | 问题 | 下一步 |
|------|------|------|--------|
| `music_player.search_and_play` | WIP | orpheus URI 打开歌曲页不自动播放，PostMessage Space 键对 CEF 应用无效 | 用 pywinauto `set_focus()` + `type_keys("{VK_SPACE}")` 替换（已安装 pywinauto） |
| `music_player.play_favorites` | WIP | orpheus `?autoplay=1` 参数无效，同上播放触发问题 | 同上，pywinauto 方案 |

---

## 待实现功能优先级速查

| 优先级 | 功能 | 说明 |
|--------|------|------|
| **M1** | ~~剪贴板图片→视觉分析~~ | ✅ 已完成 (`clipboard.analyze_image`) |
| **M2** | ~~网络工具~~ | ✅ 已完成 (`network.ping`, `network.speedtest`, `network.get_ip`) |
| **M3** | 网页内容抓取框架 | 用 requests+BeautifulSoup 抓取网页正文，为后续工具铺路 |
| **M4** | 进程管理增强 | CPU/内存 top 进程、按关键词过滤 |
| **L1** | GitHub Trending 周报 | 抓取热门项目生成摘要（依赖 M3） |
| **L2** | B站热门周报 | 抓取B站热门/每周必看（依赖 M3） |
| **L3** | ArXiv 论文每日推荐 | 自动化/机器人/CV 方向论文推荐（依赖 M3） |
| **L4** | Hacker News 热门摘要 | HN top 10 中文摘要（依赖 M3） |
| **L5** | 组合工作流/快捷指令 | 多工具组合执行，如"开始工作"→打开应用+调音量 |
| **L6** | Notion 集成 | 语音口述保存到 Notion 笔记 |
