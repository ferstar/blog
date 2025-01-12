---
title: "AI codereview实践"
date: "2025-01-06T14:55:44+08:00"
tags: ['Linux', 'Snippet']
comments: true
---

最近在公司内网 CI 工作流里加入了 AI Codereview 的功能，效果确实不错，能发现一些常规 Review 很难发现的问题。废话不多说直接上步骤&代码。

1. 按 author 拆分 commit，获取 diff codes

```Python
@dataclass
class CommitCache:
    path: Path = Path(tempfile.gettempdir()) / "commits_cache.txt"
    max_size: int = 100
    ids: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.path.exists():
            self.ids = [i.strip() for i in self.path.read_text().split("\n") if i.strip()]

    def add(self, *ids):
        self.ids = (self.ids + [i for i in ids if i not in self.ids])[-self.max_size :]
        self.path.write_text("\n".join(self.ids))


@dataclass
class CommitDiff:
    rev: str
    author: str
    content: str
    parent_rev: str = field(init=False)

    def __post_init__(self):
        self.parent_rev = run(f"git rev-parse {self.rev}^", hide=True).stdout.strip()

    @property
    def changes(self):
        return f"""```
{run(f"git diff --name-only {self.rev}^!", hide=True).stdout.strip()}
```"""

    @property
    def need_review(self):
        return any(i.startswith("diff --git") and i.endswith((".py", ".sh")) for i in self.content.split("\n"))

def prepare_commit_diff(log_range: int = 10, commit_range: int = 3) -> Iterable[CommitDiff]:
    """从指定(默认为最近10次)的提交中提取各 author 最近(默认为最近3次)的修改内容"""
    result = run(f'git log -n {log_range} --pretty=format:"%an" | sort | uniq', hide=True)
    commit_cache = CommitCache()
    for author in result.stdout.split("\n"):
        if not author:
            continue
        result = run(f"""git log --author="{author}" --pretty=format:'%H' -n {commit_range}""", hide=True).stdout
        for commit_id in (i for i in result.split("\n") if i):
            if commit_id not in commit_cache.ids:
                # 避免重复检查
                commit_cache.add(commit_id)
                diff = CommitDiff(
                    author=author,
                    rev=commit_id,
                    content=run(
                        f"git diff --ignore-all-space --diff-algorithm=minimal --function-context --no-ext-diff --no-color {commit_id}^!",
                        hide=True,
                    ).stdout,
                )
                if diff.need_review:
                    yield diff
```

2. 调整提示词，携带 git diff 调用 GPT

```Python

system_instruction = """你是一位资深的 IT 编程专家，精通 `Python 3.12`、`FastAPI`、`Pydantic`、`Shell` 和 `SQL`。你的任务是**严格审查**给定的 `diff` 内容，并找出其中存在的**重大问题**。

**重大问题** 定义如下：

*   **安全漏洞：** 例如 SQL 注入、跨站脚本 (XSS)、未授权访问等。
*   **关键功能缺失：** 例如核心业务逻辑的缺失或错误实现。
*   **语法/编译/运行时错误：** 导致代码无法运行或崩溃的错误。
*   **性能瓶颈：**  导致程序运行缓慢或占用过多资源的瓶颈。
*   **资源泄露：** 例如内存泄漏、文件句柄未关闭等。
*   **关键逻辑错误：** 导致程序产生错误结果或行为的关键性错误。

**请忽略**以下类型的问题：

*   **一般问题：** 代码结构、可读性、潜在性能问题、代码风格、注释、未使用变量等不影响代码功能的因素。
*   **存疑问题：**  需要更多上下文才能确认的问题。
*   **`import` 语句相关的更改或缺失:** 例如新增、删除或修改 `import` 语句。

**请仅按以下格式回复：**

1. 重大问题：

    <重大问题列表，如果没有则回复“无”>

2. 建议：

    <针对重大问题的具体建议，如果没有则回复“无”>

**重要：** 严格按照上述格式输出，只关注重大问题和建议，不要包含任何其他内容。
"""

quality_prompt = """
__insert_diff__
"""


def init_openai_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=get_config("ai.openai.api_key"),
        base_url=get_config("ai.openai.base_url"),
        default_headers={"Accept": "text/event-stream"},
    )


async def openai_chat_iter(
    messages: list[dict[str, str]], *, client: AsyncOpenAI = None, model: str = None, **options
) -> AsyncIterator[str]:
    client = client or init_openai_client()
    stream = client.chat.completions.create(
        messages=messages,
        model=model or get_config("ai.openai.model"),
        **{
            "temperature": get_config("ai.openai.temperature"),
            "timeout": get_config("ai.openai.timeout") or 10,
            "stream": True,
            **options,
        },
    )
    async for chunk in await stream:
        if chunk.choices and (content := chunk.choices[0].delta.content):
            yield content


async def openai_chat(messages: list[dict[str, str]]) -> str:
    reply = []
    async for chunk in openai_chat_iter(messages):
        reply.append(chunk)
    return "".join(reply)

@lru_cache(maxsize=1)
def get_repository_name():
    return run(r"git remote get-url origin | xargs basename | sed 's/\.git$//'", hide=True).stdout.strip()

async def quality_check(diff: CommitDiff):
    """质量检查&发送通知"""
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": quality_prompt.replace("__insert_diff__", diff.content)},
    ]
    try:
        reply = await openai_chat(messages)
    except Exception as e:
        reply = f"Error: {e}"

    changes = f"xxx.git.com/{get_repository_name()}/-/compare/{diff.parent_rev}...{diff.rev}"
    content = f"""@{diff.author} [Show changes]({changes})

{diff.changes}

{reply}"""
    # 发送 review 通知
    send_notify(xxx)

```

这玩意其实缺点也很明显，受限于上下文，基本上偏业务逻辑都是瞎点评，但总体作用是积极的，能实际提高 codereview 的效率。



---

```js
NOTE: I am not responsible for any expired content.
Created at: 2025-01-06T14:55:44+08:00
Updated at: 2025-01-12T15:56:57+08:00
Origin issue: https://github.com/ferstar/blog/issues/81
```
