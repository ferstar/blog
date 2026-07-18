# {{ .Title | plainify }}

Source: {{ .Permalink }}

{{ $content := .RawContent }}
{{ $content = replaceRE `(?m)^[\t ]*\{\{[<%][\t ]*mermaid[\t ]*[>%]\}\}[\t ]*$` "```mermaid" $content }}
{{ $content = replaceRE `(?m)^[\t ]*\{\{[<%][\t ]*/mermaid[\t ]*[>%]\}\}[\t ]*$` "```" $content }}
{{ $content }}
