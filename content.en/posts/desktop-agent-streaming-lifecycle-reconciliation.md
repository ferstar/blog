---
title: "Decoupling Heavy IO from UI Finalization: Eliminating Input Freezes in Desktop Agents"
slug: "desktop-agent-streaming-lifecycle-reconciliation"
date: "2026-08-31T23:40:00+08:00"
tags: ['AI', 'Agent', 'Electron', 'Frontend']
description: "Desktop agents often lock the chat input in a frozen loading state after generation completes; decouple disk IO from UI lifecycles via bypass emission channels, optimistic unlocking, and periodic stale reconciliation; completely eliminate input freezes while maintaining deterministic state consistency."
series: ['AI Coding']
---

> I am not a native English speaker; this article was translated by AI.

When building desktop or web-based agent clients, there is a recurring, annoying UX friction:

> **The model has finished streaming its last token on screen, but the input box stays disabled with a "Task in progress..." placeholder. You cannot focus the cursor. It takes several seconds to unlock, and switching away from the window mid-stream can sometimes freeze it in a loading state permanently.**

This looks like a simple frontend state bug, but tracing through the stack reveals an issue of asynchronous disk persistence blocking the event dispatch pipeline.

{{< mermaid >}}
flowchart TD
  subgraph Backend[Agent Host Process / Runtime]
    M[Receive Final Text Chunk] --> MC[Emit MessageComplete]
    MC --> P[Heavy Async Persistence: SQLite & Archiving]
    P --> AE[Emit AgentEnd Terminal Event]
  end

  subgraph Legacy[Legacy Serial Pattern]
    L1[Wait for Persistence to Finish] --> L2[Notify Frontend via Long IPC Queue]
    L2 --> L3[Clear isStreaming / Noticeable UI Freeze]
  end

  subgraph Optimized[Decoupled & Reconciled Pattern]
    MC -->|Optimistic: No Pending Tools| UI1[Unlock Input Box Instantly]
    AE -->|Bypass Fast Channel| UI1
    T[10s Periodic Stale Reconciliation] -.->|Handles Dropouts & Blur Edge Cases| UI1
  end
{{< /mermaid >}}

---

## 1. Why Does the Input Lock Up?

From model output to disk storage, messages pass through three layers:
1. **Sampling Runtime**: Consumes the SSE stream, producing text deltas and `MessageComplete`.
2. **Host Process (Node.js / IPC Layer)**: Manages cross-process communication, SQLite writes, image materialization, and JSONL archiving.
3. **Renderer Process (Frontend UI)**: Manages reactive states like `isStreaming` and input enablement in React/Vue.

Tracing the logs revealed three main bottlenecks:

### Culprit 1: Terminal Events Blocked Behind Heavy I/O

The legacy implementation waited for all disk writes in the turn to finish before sending `agent_end` to the UI:
```typescript
// Legacy flow: Heavy I/O blocks terminal notifications
await persistTurnToSqlite(turnData);      // 50~200ms
await materializeImagesToDisk(images);    // 500ms~2s
await appendSessionJsonl(largePayload);   // 100~500ms

// Only now is the UI notified
emitToRenderer('agent_end', session);
```
While the user is already reading the final response, the host process is still grinding through disk writes. In large sessions, this easily introduces noticeable delays.

### Culprit 2: Head-of-Line Blocking in IPC Queues

To preserve message ordering, events pass through an ordered queue (Emit Chain). If the model emits diagnostic logs during finalization, `agent_end` gets queued behind them.

### Culprit 3: Window Defocus Drops

When a user switches windows mid-stream, Chromium throttles background timers. If a cross-process packet drops during that transition, the UI permanently misses `agent_end`, leaving the input locked.

---

## 2. The Solution

We updated the IPC and frontend state management across three areas:

### 1. Optimistic Unlocking

Input availability should not wait on disk writes. Once the frontend receives `MessageComplete` and verifies:
- The reply is a genuine terminal turn (`EndTurn`);
- No background tools are currently executing;
- The user has not requested a stop.

It **unlocks the input box immediately**, dropping perceived recovery latency to zero.

### 2. Bypass Channel for Terminal Events

Lifecycle events (`agent_end`, `error`, `cancelled`) have higher priority than regular stream deltas. We introduced a fast-track bypass in the IPC bridge:
- Terminal events skip the standard ordered queue and dispatch directly to the renderer.
- Even if SQLite writes or archiving queues are backed up, the UI lifecycle updates without delay.

### 3. 10-Second Low-Overhead Reconciliation Loop

To handle orphaned states from window blur or dropped packets, the frontend runs a 10-second reconciliation check:

```typescript
useEffect(() => {
  const timer = setInterval(() => {
    // Check for sessions with no activity for >10s still marked as streaming
    reconcileStaleStreamingSessions();
  }, 10_000);
  return () => clearInterval(timer);
}, []);
```

Any stuck sessions are idempotently cleaned up and synchronized.

---

## 3. Takeaway

With these changes in place, the input box is ready the moment generation finishes, and focus freezes from window switching are gone.

In rich-client apps, keep user interactions optimistic and fast, run heavy persistence asynchronously in the background, and use periodic reconciliation to ensure eventual consistency.
