---
title: "让 AI 通过 UIA 操作 Electron 桌面应用：Windows-MCP 实测"
slug: "ai-agent-drives-electron-app-windows-mcp-uia"
date: "2026-10-18T18:00:00+08:00"
tags: ["AI Agent", "Windows", "UI Automation", "MCP", "Electron", "Testing"]
description: "想让 AI 自动验收 Electron 桌面应用，冷启动时它的无障碍树几乎是空的，窗口标题、残留弹窗和 UIA 的瞬时错误又会让回放时好时坏；用 Windows-MCP 读 UIA 语义树，按进程路径找窗口、限定搜索范围、给清理加重试；修复后连续 45 轮测试步骤零失败，除去模型等待每轮约 9 秒，整条链路没有用到 SealDesk。"
---

[上一篇]({{< relref "yet-another-remote-desktop-application-sealdesk.md" >}})把 SealDesk 开源之后，我在想它下一步该补什么。远控之上再加 AI 操作，听起来顺理成章，但这个组合已经有不少现成方案了，所以我没有急着改 SealDesk，先用现成的东西跑一遍，看够不够用。

这次让 AI 助手（Claude）通过一个远程 shell 工具，在我的 Windows 机器上用 Windows-MCP 操作一个 Electron 桌面客户端：新建对话、输入、发送、等回复、断言结果，最后把测试产生的会话删掉。实验和调试都是 AI 助手在我的指挥下完成的，这些问题不是我手动排查的；下面的数字来自它实际跑出来的日志。

结论放前面：这条路走得通，修掉几处问题之后，连续 45 轮测试步骤没有失败；整条链路里没有用到 SealDesk。

## 链路

AI 助手手里只有一个远程 shell 工具，看不到 Windows-MCP 的工具列表，所以我们写了一个小的命令行桥 `wmcp.py`，提供 `ping`、`tools`、`call` 三条命令，把 MCP 工具调用变成 shell 命令。

{{< mermaid >}}
flowchart LR
    A["AI 助手"] --> B["远程 shell 工具"]
    B --> C["wmcp.py"]
    C --> D["Windows-MCP<br/>127.0.0.1:8000 + bearer key"]
    D --> E["UIA 语义树 / 输入注入"]
    E --> F["Electron 桌面应用"]
    H["在用这台机器的人"] -.->|"USER_CONTROL：让出控制权"| D
{{< /mermaid >}}

Windows-MCP 只绑 `127.0.0.1`，带 bearer key。安装用 `uv tool install`，不用 `uvx`：uvx 的环境放在 uv 缓存里，缓存一清，常驻服务就起不来了。

截图返回的图片会超过 MCP Python SDK 对单个 SSE 事件的默认 1 MiB 上限，桥里改用底层的 `streamable_http_client` 并关掉这个限制。有人在用机器时，Windows-MCP 会返回 `USER_CONTROL`，桥按它给的等待时间重试，超时就退出，不去抢控制权。

## 装之前先处理遥测

以下基于 0.8.8 版本的源码。上游 README 里写了会收集使用数据，细节是这样的：

- 只有环境变量 `ANONYMIZED_TELEMETRY` 等于 `false` 才会关闭，默认开启。
- 客户端是 PostHog，初始化时没有关 geoip，并且开了异常自动捕获。
- 每次工具调用上报工具名、耗时、是否成功、客户端名称和版本，再加一个持久化在 `~/.windows-mcp/` 下的匿名 ID。调用参数不在这个事件里。
- 出错时会上报错误信息原文和 traceback，里面带什么取决于报错内容。

`windows-mcp install` 生成的启动脚本没有设置这个变量，要自己加一行：

```bat
@echo off
setlocal
set ANONYMIZED_TELEMETRY=false
"<uv tool dir>\windows-mcp\Scripts\python.exe" -m windows_mcp serve --transport streamable-http --host 127.0.0.1 --port 8000
```

另外，Windows-MCP 自带 `PowerShell`、`Registry` 这类工具。调用方已经有 shell 的话，它们等于第二条不受外层工具管控的路径，可以用 `--exclude-tools "PowerShell,Registry"` 在服务端去掉。这次我没有去掉，只是约定不用。

## Electron 的无障碍树，冷启动时几乎是空的

应用刚启动时，第一次探测只拿到 14 个节点：1 个窗口、11 个 Pane、2 个 Document，没有任何可交互控件。6 秒之后再查，是 764 个节点，其中 299 个可交互、296 个有名字，按钮、链接、开关状态都能读到。

Chromium 只在检测到辅助技术时才构建无障碍树，所以第一次查询本身就是唤醒动作。原本我打算用 `--force-renderer-accessibility` 启动应用，实测不需要：回放用例的第一步（preheat）对主窗口做一次完整遍历，然后轮询节点数，到 200 以上才继续。把应用彻底关掉再启动，连续 3 次，第一次 preheat 都在约 1.1 秒内拿到 402 个节点。

## 回放用例

用例走一遍最常见的路径，每一步都用 UIA 属性定位和断言，截图只在结束时保存，留作人工复核：

| 步骤 | 定位与断言 | 中位耗时 |
|---|---|---|
| preheat | 完整遍历一次，节点数 ≥ 200 | 203 ms |
| new_chat | 点「新对话」，输入框（Edit）出现 | 642 ms |
| compose | 输入带唯一 token 的探针文字 | 1420 ms |
| enable_send | 「发送」按钮从不可用变为可用 | 83 ms |
| send | 点「发送」，记录此前的回复数 | 658 ms |
| echo | 消息列表里出现含 token 的文字 | 21 ms |
| reply | 出现新回复：去掉句末标点后以「收到」开头，总长不超过 8 | 5283 ms |
| cleanup | 只删含本轮 token 的会话，最多两次尝试 | 5676 ms |

「发送」按钮的可用状态是少数能直接断言的 UI 状态。除去模型等待，整轮约 9.1 秒，其中清理占 5.7 秒。表里的耗时来自最后一批 5 轮。

## 几个只有跑起来才会遇到的问题

### 窗口标题会随会话改变

第一版按窗口名查找主窗口。会话有了标题之后，Electron 把窗口标题改成会话标题，查找就失败了，前面几轮都是「新对话」，所以没暴露。改成用 Win32 枚举窗口，按进程的可执行文件路径匹配，再对这些窗口调 `ElementFromHandle`：

```python
def app_hwnds() -> list[int]:
    user32 = ctypes.windll.user32
    hits: list[int] = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    def visit(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            pid = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                if APP_EXE_MARK in psutil.Process(pid.value).exe():
                    hits.append(hwnd)
            except (psutil.Error, OSError):
                pass
        return True

    user32.EnumWindows(visit, 0)
    return hits
```

这是节选，改了名字。

### 别遍历桌面上所有窗口

最早的版本从 UIA 根节点往下找顶层窗口，有一轮卡了 63 秒，还有两轮根节点查询返回了 0 个窗口。我怀疑是碰到了某个无响应的窗口，没有验证。改成只对目标应用自己的窗口操作之后，这个问题没有再出现。

同样的思路也解决了清理慢的问题。菜单和确认框是目标应用自己的弹出窗口，但我一开始是在整个桌面上找它们：扫 9 个顶层窗口要 5.3 秒，限定到应用自己的窗口之后是 0.02 秒，清理的中位耗时从 29.6 秒降到 5.7 秒。多半是别的应用（浏览器之类）的大树拖慢了，我没有逐个窗口量。

### 菜单没关，下一轮的树只剩 20 个节点

有一轮清理失败，「会话操作」的下拉菜单留在了屏幕上。下一轮 preheat 等了 30 秒，无障碍树只有 20 个节点，后面一轮也一样。现在每轮开始前、清理失败后都先按一次 Esc。

### 菜单项刚出现就点，点击没生效

清理失败有两种现象：点了「删除」但确认框没出现，或者确认框出现了却找不到确认按钮。我的判断是菜单还在展开动画，点得太早被吞掉了。菜单项出现后等 0.6 秒再重新定位、点击，清理的首次失败从 20 轮里的 4 次降到 2 次，没有消失，所以又加了一次重试，两次都失败的情况在后面的批次里没有再出现。根因我没有完全查清。

### UIA 的瞬时 COM 错误

第一批 20 轮里有 3 轮在等回复时抛出 `COMError -2147220991`（`EVENT_E_ALL_SUBSCRIBERS_FAILED`，中文系统里显示为「事件无法调用任何订户」）。对 UIA 查询做最多 3 次重试之后，后面 45 轮没有再出现。

### 坐标要用物理像素

这台机器的缩放是 200%。进程不声明 DPI 感知时，UIA 返回的是逻辑坐标，和输入注入用的物理坐标差了一倍，点击会落到别处。脚本开头调用 `SetProcessDpiAwarenessContext(-4)`（per-monitor v2）之后两边对齐。

## 测试数据

| 批次 | 轮数 | 测试步骤通过 | 清理最终成功 | 改动 |
|---|---|---|---|---|
| A | 20 | 17 | 16 | 初版，3 轮失败都是上面那个 COM 错误 |
| B | 20 | 20 | 16 | UIA 查询加重试 |
| C | 20 | 20 | 20 | 菜单项等待 0.6 秒，清理最多两次 |
| D | 5 | 5 | 5 | 弹出窗口只在应用自己的窗口里找 |
| 冷启动 | 3 | 3 | 3 | 每轮先彻底关掉应用再启动 |

B 到 D 一共 45 轮，测试步骤没有失败。调试过程中还有几轮零散的运行，没有计入。

## 对前端的要求

这套回放能跑，靠的是 UIA 里按名字和控件类型找得到东西。看下来有几处值得前端补：

- 764 个元素里只有 11 个带 AutomationId。从 `root`、`DndLiveRegion-0` 这些值看，HTML 的 `id` 会被映射成 AutomationId；但现有的基本是框架生成的（比如 React 生成的 `radix-_r_9_`），依赖渲染顺序，不适合当选择器。关键控件可以加稳定的 `id`。
- 会话列表里每一行都有同名的「重命名」「删除」按钮，同名元素各有 60 个，行内按钮的 `aria-label` 带上会话名才能区分。
- 同一个输入框，空会话里是 Edit，进入会话后换了控件类型，定位时只能按几种类型依次找。

## 对 SealDesk 意味着什么

回头看这一圈，SealDesk 一行代码都没有用上。AI 助手到这台机器靠的是已有的远程 shell 通道，操作靠 UIA 语义树而不是像素，有人在用机器时让出控制权也是 Windows-MCP 自带的。

SealDesk 能补的是语义树够不到的场合：自绘界面、游戏和 CAD、远端虚拟机里的桌面，还有需要人亲眼看着画面、低延迟接手的时候；另外就是机器上没有现成通道时的那一段连接。这些场合有多常见，值不值得为它往 SealDesk 里加 agent 能力，我现在还没有答案。

## 限制

- 每一轮都会在账号里新建一个会话并调用一次模型，测试结束后删除。
- 只测了一个应用、一条流程。
- 没有和基于截图的方案做过对比，只能说语义树够用，不能说它更快或更稳。
- 界面文案是写死的中文字面量，界面改版要同步改。
- 回复断言只检查以「收到」开头且不超过 8 个字符，模型换种说法会被判失败。
- 桌面会话断开（比如 RDP 断开）时，Windows-MCP 返回 `CONTROL_UNAVAILABLE`，脚本会直接失败，不会误报通过。

回放脚本绑定了具体应用的界面，这里只贴了通用的部分。Windows-MCP 在 [GitHub](https://github.com/CursorTouch/Windows-MCP) 和 [PyPI](https://pypi.org/project/windows-mcp/) 上都有。
