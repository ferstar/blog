---
title: "Driving an Electron Desktop App Through UIA: A Windows-MCP Field Test"
slug: "ai-agent-drives-electron-app-windows-mcp-uia"
date: "2026-10-18T18:00:00+08:00"
tags: ["AI Agent", "Windows", "UI Automation", "MCP", "Electron", "Testing"]
description: "Having an AI acceptance-test an Electron desktop app is awkward: the accessibility tree is nearly empty on a cold start, and window titles, leftover popups and transient UIA errors make replays flaky; this post reads the UIA semantic tree through Windows-MCP, finds windows by process path, narrows every search scope and retries cleanup; after the fixes, 45 consecutive runs had zero failing test steps, about 9 seconds of UI overhead per run excluding the model wait, and SealDesk was not needed anywhere in the chain."
---

> I am not a native English speaker; this article was translated by AI.

After [the last post]({{< relref "yet-another-remote-desktop-application-sealdesk.md" >}}) open-sourced SealDesk, I started wondering what it should gain next. Putting AI control on top of remote desktop sounds like a natural step, but plenty of ready-made options already cover that combination, so instead of changing SealDesk I first ran the existing tools to see whether they were enough.

This time an AI assistant (Claude), working through a remote shell tool, used Windows-MCP on my Windows machine to drive an Electron desktop client: open a new chat, type, send, wait for the reply, assert the result, and finally delete the session the test created. The AI assistant ran the experiments and did the debugging under my direction; I did not track these problems down by hand. The numbers below come from the logs it produced.

The conclusion first: this route works. After a few fixes, 45 consecutive runs had no failing test step, and SealDesk was not used anywhere in the chain.

## The chain

The AI assistant only has a remote shell tool and cannot see Windows-MCP's tool list, so we wrote a small command-line bridge, `wmcp.py`, with three commands, `ping`, `tools` and `call`, that turns MCP tool calls into shell commands.

{{< mermaid >}}
flowchart LR
    A["AI assistant"] --> B["Remote shell tool"]
    B --> C["wmcp.py"]
    C --> D["Windows-MCP<br/>127.0.0.1:8000 + bearer key"]
    D --> E["UIA semantic tree / input injection"]
    E --> F["Electron desktop app"]
    H["Person using the machine"] -.->|"USER_CONTROL: yield control"| D
{{< /mermaid >}}

Windows-MCP binds to `127.0.0.1` only and requires a bearer key. Install it with `uv tool install`, not `uvx`: uvx keeps its environment in the uv cache, and once the cache is cleaned the resident service can no longer start.

Screenshots exceed the MCP Python SDK's default 1 MiB limit on a single SSE event, so the bridge uses the lower-level `streamable_http_client` and turns that limit off. When a person is using the machine, Windows-MCP returns `USER_CONTROL`; the bridge retries for the wait time it gives and exits on timeout rather than taking control.

## Deal with telemetry before installing

This is based on the 0.8.8 source. The upstream README says usage data is collected; the details are:

- It is turned off only when the environment variable `ANONYMIZED_TELEMETRY` equals `false`; it is on by default.
- The client is PostHog, initialized without disabling geoip and with exception autocapture enabled.
- Each tool call reports the tool name, duration, success flag, client name and version, plus an anonymous ID persisted under `~/.windows-mcp/`. The call arguments are not part of that event.
- On errors it reports the original error message and a traceback; what they contain depends on the error.

The startup script that `windows-mcp install` generates does not set this variable, so add one line yourself:

```bat
@echo off
setlocal
set ANONYMIZED_TELEMETRY=false
"<uv tool dir>\windows-mcp\Scripts\python.exe" -m windows_mcp serve --transport streamable-http --host 127.0.0.1 --port 8000
```

Windows-MCP also ships tools such as `PowerShell` and `Registry`. If the caller already has a shell, they amount to a second path that the outer tool does not govern, and `--exclude-tools "PowerShell,Registry"` removes them on the server side. I did not remove them this time; we simply agreed not to use them.

## On a cold start, Electron's accessibility tree is nearly empty

Right after the app starts, the first probe returns only 14 nodes: 1 window, 11 Panes and 2 Documents, with no interactive controls at all. Six seconds later the same query returns 764 nodes, 299 of them interactive and 296 with names; buttons, links and toggle states are all readable.

Chromium builds the accessibility tree only when it detects assistive technology, so the first query is itself the wake-up. I had planned to launch the app with `--force-renderer-accessibility`, but in practice it is not needed: the first step of the replay (preheat) does one full walk of the main window and then polls the node count until it exceeds 200. I fully closed the app and restarted it three times in a row; each time the first preheat reached 402 nodes within about 1.1 seconds.

## The replay case

The case walks the most common path. Every step is located and asserted through UIA properties; a screenshot is saved only at the end, for manual review:

| Step | Locator and assertion | Median time |
|---|---|---|
| preheat | One full walk, node count ≥ 200 | 203 ms |
| new_chat | Click "New chat", the input box (Edit) appears | 642 ms |
| compose | Type a probe text with a unique token | 1420 ms |
| enable_send | The "Send" button goes from disabled to enabled | 83 ms |
| send | Click "Send", recording the earlier reply count | 658 ms |
| echo | Text containing the token appears in the message list | 21 ms |
| reply | A new reply appears: after stripping trailing punctuation it starts with the expected word and is at most 8 characters long | 5283 ms |
| cleanup | Delete only the session that contains this run's token, with up to two attempts | 5676 ms |

The enabled state of the "Send" button is one of the few UI states that can be asserted directly. Excluding the model wait, a whole run takes about 9.1 seconds, of which cleanup is 5.7 seconds. The timings in the table come from the last batch of 5 runs.

## Problems you only meet once it runs

### The window title changes with the session

The first version found the main window by name. Once a session had a title, Electron renamed the window to that title and the lookup failed; the earlier runs all showed "New chat", so it stayed hidden. The fix is to enumerate windows with Win32, match on the process's executable path, and call `ElementFromHandle` on those windows:

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

This is an excerpt with the names changed.

### Don't walk every window on the desktop

The earliest version looked for top-level windows by going down from the UIA root. One run stalled for 63 seconds, and in two others the root query returned 0 windows. I suspect it hit an unresponsive window but did not verify that. After switching to touching only the target app's own windows, the problem did not recur.

The same idea fixed the slow cleanup. The menu and the confirmation dialog are popup windows of the target app, but I first searched for them across the whole desktop: scanning 9 top-level windows took 5.3 seconds, and limiting the search to the app's own windows took 0.02 seconds. The median cleanup time dropped from 29.6 seconds to 5.7 seconds. Most likely the large trees of other applications (browsers and the like) were slowing it down; I did not measure window by window.

### A menu left open leaves the next run with a 20-node tree

In one run the cleanup failed and the "session actions" dropdown stayed on screen. The next run's preheat waited 30 seconds and saw an accessibility tree of only 20 nodes, and the run after it did the same. Now Esc is pressed once before each run and after a failed cleanup.

### Clicking a menu item as soon as it appears doesn't register

Cleanup failed in two ways: the click on "Delete" happened but no confirmation dialog appeared, or the dialog appeared but its confirm button could not be found. My judgment is that the menu was still animating open and the early click got swallowed. Waiting 0.6 seconds after the item appears, then locating and clicking it again, cut first-attempt cleanup failures from 4 in 20 runs to 2. They did not go away, so I added one retry; in later batches no run failed both attempts. I have not fully pinned down the root cause.

### Transient UIA COM errors

In the first batch of 20 runs, 3 runs raised `COMError -2147220991` (`EVENT_E_ALL_SUBSCRIBERS_FAILED`) while waiting for the reply. After adding up to 3 retries to UIA queries, it did not appear again in the next 45 runs.

### Coordinates must be in physical pixels

This machine runs at 200% scaling. If the process does not declare DPI awareness, UIA returns logical coordinates, which are half the physical coordinates used for input injection, and clicks land in the wrong place. Calling `SetProcessDpiAwarenessContext(-4)` (per-monitor v2) at the top of the script makes the two agree.

## Test results

| Batch | Runs | Test steps passed | Cleanup eventually succeeded | Change |
|---|---|---|---|---|
| A | 20 | 17 | 16 | First version; the 3 failing runs were the COM error above |
| B | 20 | 20 | 16 | Retries added to UIA queries |
| C | 20 | 20 | 20 | 0.6-second wait for the menu item, up to two cleanup attempts |
| D | 5 | 5 | 5 | Popups searched only within the app's own windows |
| Cold start | 3 | 3 | 3 | App fully closed and relaunched before each run |

Across B to D, 45 runs in total, no test step failed. A few scattered runs during debugging are not counted.

## What this asks of the front end

The replay works because UIA can find things by name and control type. A few things are worth fixing in the front end:

- Only 11 of 764 elements carry an AutomationId. Values such as `root` and `DndLiveRegion-0` show that an HTML `id` is mapped to AutomationId; but the existing ones are mostly framework-generated (for example React's `radix-_r_9_`), depend on render order, and are not suitable as selectors. Key controls could get stable `id` values.
- Every row in the session list has "Rename" and "Delete" buttons with the same names, 60 elements each; the buttons' `aria-label` needs to include the session name to tell rows apart.
- The same input box is an Edit in an empty chat and changes control type once a conversation is open, so the locator can only try several types in turn.

## What this means for SealDesk

Looking back over the whole exercise, SealDesk was not used for a single line of code. The AI assistant reached this machine through an existing remote shell channel, it operated through the UIA semantic tree rather than pixels, and yielding control when a person is using the machine is built into Windows-MCP.

Where SealDesk can add something is where the semantic tree cannot reach: custom-drawn interfaces, games and CAD, desktops inside remote virtual machines, and the moments when a person needs to watch the actual picture and take over with low latency; also the connection leg itself when the machine has no ready-made channel. How common those cases are, and whether they justify adding agent capabilities to SealDesk, I don't have an answer yet.

## Limitations

- Every run creates a session in the account and makes one model call; the session is deleted when the test ends.
- Only one app and one flow were tested.
- It was not compared with a screenshot-based approach, so I can only say the semantic tree is sufficient, not that it is faster or more stable.
- The UI strings are hard-coded Chinese literals and need updating whenever the interface changes.
- The reply assertion only checks that the reply starts with the expected word and is at most 8 characters long; if the model phrases it differently, the run is judged a failure.
- When the desktop session is disconnected (an RDP disconnect, for example), Windows-MCP returns `CONTROL_UNAVAILABLE` and the script fails outright instead of reporting a false pass.

The replay script is tied to a specific app's interface, so only the generic parts are shown here. Windows-MCP is available on [GitHub](https://github.com/CursorTouch/Windows-MCP) and [PyPI](https://pypi.org/project/windows-mcp/).
