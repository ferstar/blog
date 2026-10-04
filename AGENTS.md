## 1) 内容（强制）
- **双语对齐**：`content/` 的新文章必须在 `content.en/` 提供高保真翻译；仅面向国内日常、与英语读者无关的主题可不译（如 `homework-print-prep`）。
- **内容一致**：代码块、命令行、Mermaid 图、表格两端保持一致。
- **图示优先**：能用 Mermaid 的示意图优先用 Mermaid，避免字符画。
- **Front Matter 必填**：新文章必须包含 `title`、`slug`、`date`、`tags`、`description`；
  中英字段名一致；`slug`/`date`/`tags` 必须相同，`title`/`description` 可翻译；
  `series` 可选，但中英文必须一致。
- **降低 AI 味**：语言自然、具体，避免模板化措辞、口号式小节名与冗余铺垫。
- **英文声明**：每篇英文文章必须包含：
  `> I am not a native English speaker; this article was translated by AI.`

## 2) SEO 与重定向（不得回退）
- **重定向**：`static/_redirects` 只允许显式规则，禁止 `/post/*` 这类模糊通配。
- **描述规范**：所有文章都必须写 description，尽量 SEO 友好；description 使用 `[痛点] + [方案] + [结果]`。
- **系列聚合**：相关内容用 Hugo `series` 做内链。

## 3) 多语言站点设置（保持）
- `contentDir` 保持拆分：`content/`（zh-cn）与 `content.en/`（en）。
- 导航链接使用 Hugo `pageRef` 保证多语言安全跳转。

## 4) 格式（强制）
- 中英版本均禁止连续空行超过 2 行。
- **主题短代码**：Blowfish 主题功能必须用短代码而非裸 Markdown——流程图用 `{{</* mermaid */>}}...{{< /mermaid >}}`（禁止 ```mermaid 代码块），提示块用 `{{</* alert */>}}`。写新文章前先看站内已有文章的用法对齐。
- **发布时间**：front matter 的 `date` 不允许是未来时间——Hugo 默认不构建未来日期的文章，页面会静默缺失。新文章写当前时间或更早。

