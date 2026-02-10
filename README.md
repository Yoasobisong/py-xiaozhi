# py-xiaozhi (个人增强版)

> 本项目 Fork 自 [huangjunsen0406/py-xiaozhi](https://github.com/huangjunsen0406/py-xiaozhi)，原项目的完整介绍、安装教程、技术架构请参阅 [原项目 README](https://github.com/huangjunsen0406/py-xiaozhi/blob/main/README.md)。

---

## 本 Fork 的改动

在原项目基础上，主要做了以下修改和新增：

### 1. 音乐系统重写

**替换酷我音乐为网易云音乐 (pyncm)**

原项目音乐功能基于酷我音乐 API + FFmpeg 本地解码播放。本 Fork 完全重写为：

- 使用 [pyncm](https://github.com/mos9527/pyncm) 调用网易云音乐 API（搜索、歌单、登录）
- 通过 `orpheus://` URI 协议直接调用网易云音乐桌面客户端播放，不再需要 FFmpeg
- 使用 pycaw 实现单应用音量控制（仅控制 cloudmusic.exe，不影响系统音量）
- 使用 Windows Media Key 控制播放/暂停/上一首/下一首

**MCP 工具从 3 个扩展到 8 个：**

| 工具 | 功能 | 触发示例 |
|------|------|----------|
| `music_player.play` | 播放音乐（自动检测状态） | "放首歌" |
| `music_player.search_and_play` | 搜索指定歌曲播放 | "播放稻香" |
| `music_player.play_favorites` | 播放「我喜欢的音乐」歌单 | "放我收藏的歌" |
| `music_player.pause` | 暂停 | "暂停音乐" |
| `music_player.stop` | 停止 | "停止音乐" |
| `music_player.next_track` | 下一首 | "下一首" |
| `music_player.previous_track` | 上一首 | "上一首" |
| `music_player.get_current_track` | 获取当前歌曲信息 | "现在放的什么歌" |

**配置：** 在 `config/config.json` 中添加 `MUSIC.NETEASE_MUSIC_U` 字段，填入网易云 MUSIC_U Cookie 即可使用搜索和收藏功能。

### 2. TTS 音量闪避 (Volume Ducking)

原项目在 AI 说话 (TTS) 时会暂停音乐，说完后恢复。这导致体验不连贯。

本 Fork 改为 **音量闪避**：
- TTS 开始 → 网易云音量降到 20%（通过 pycaw `ISimpleAudioVolume`）
- TTS 结束 → 恢复原始音量
- 不影响系统音量和其他应用

### 3. 麦克风可选（无麦克风也能听 TTS）

原项目的 `AudioCodec` 创建输入流（麦克风）和输出流（扬声器）是一体的，麦克风不可用会导致整个音频系统初始化失败，连 TTS 播放也无法工作。

本 Fork 修改为：
- 输入流和输出流独立创建
- 麦克风不可用时仅 warning，不影响 TTS 播放
- 适用于无麦克风设备或只想用文字交互的场景

### 4. 新增系统电源管理工具

| 工具 | 功能 | 触发示例 |
|------|------|----------|
| `system.shutdown` | 关机（30s 延迟，可取消） | "关机" |
| `system.restart` | 重启（30s 延迟，可取消） | "重启电脑" |
| `system.sleep` | 休眠 | "休眠" |
| `system.lock_screen` | 锁屏 | "锁屏" |
| `system.cancel_shutdown` | 取消已计划的关机/重启 | "取消关机" |
| `system.set_brightness` | 设置屏幕亮度 | "亮度调到50" |
| `system.get_brightness` | 获取当前亮度 | "亮度多少" |

### 5. 新增剪贴板工具

| 工具 | 功能 | 触发示例 |
|------|------|----------|
| `clipboard.read_text` | 读取剪贴板文本 | "翻译剪贴板内容" |
| `clipboard.write_text` | 写入文本到剪贴板 | "把结果复制到剪贴板" |

### 6. 新增网页工具

| 工具 | 功能 | 触发示例 |
|------|------|----------|
| `web.open_url` | 用 Chrome 打开 URL | "打开B站" |
| `web.search` | Chrome 搜索（Google/百度/Bing/GitHub/B站/知乎） | "帮我搜Python教程" |

### 7. 定时器修复

- 修复倒计时结束后 MCP 工具调用失败的问题
- 优化定时器服务的异步逻辑

### 8. 已修改文件清单

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `src/mcp/tools/music/music_player.py` | **重写** | 酷我→网易云，FFmpeg→orpheus URI，新增 pycaw 音量控制 |
| `src/mcp/tools/music/manager.py` | **重写** | 3 个工具→8 个工具 |
| `src/plugins/audio.py` | **修改** | TTS 暂停/恢复→音量闪避 (duck/restore) |
| `src/audio_codecs/audio_codec.py` | **修改** | 输入流/输出流独立创建，麦克风可选 |
| `src/mcp/tools/system/manager.py` | **修改** | 新增电源管理工具注册 |
| `src/mcp/tools/system/tools.py` | **新增** | 电源管理工具实现 |
| `src/mcp/tools/clipboard/` | **新增** | 剪贴板工具 |
| `src/mcp/tools/web/` | **新增** | 网页打开/搜索工具 |
| `src/mcp/mcp_server.py` | **修改** | 注册新增工具 |
| `src/mcp/tools/timer/` | **修改** | 定时器 bug 修复 |
| `requirements.txt` | **修改** | 新增 pyncm 依赖 |
| `src/utils/config_manager.py` | **修改** | 新增 MUSIC_U 配置项支持 |

---

## 额外依赖

在原项目依赖基础上，额外需要：

```bash
pip install pyncm pycaw
```

## 许可证

[MIT License](LICENSE) （同原项目）
