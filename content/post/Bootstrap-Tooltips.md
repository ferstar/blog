---
title: "Bootstrap Tooltips"
date: 2018-06-29T10:06:55+08:00
tags: ['DJANGO', 'PYTHON', 'BOOTSTRAP']
comments: true
---

最近用 Django 写一个内部项目，选用 [django-tables2](https://django-tables2.readthedocs.io/en/latest/) 做数据库表单页面展示非常方便，不过再方便，踩坑也是必不可少的。其中遇到的一个问题是有的列表内文字不能写太多，但需要给出比较详细的提示（鼠标悬停即显示详细提示内容）。虽然直接给加`title`就行，但原生效果略丑，我需要跟 Bootstrap 主题样式一致，所以需要额外的一点工作。

直接上解决方案：

```python
# samples/tables.py
import django_tables2 as tables

from .models import Sample


class SampleTable(tables.Table):
	# 添加报告链接
    # 这个链接是根据样本完成状态与否自动生成
    # 加个data-toggle的属性，将title内容变成提示框
    report = tables.TemplateColumn(
        '{% if record.has_completed %}<a data-toggle="tooltip" title="It will take a few seconds to load the data, please be patient" href="/samples/{{record.id}}/" target="_blank">Result link</a> {% else %}<i class="fa fa-ellipsis-h"></i>{% endif %}',
        verbose_name='View Result',  # 这个可以控制显示的列名，默认是数据库对应字段名
        orderable=False)  # 拒绝排序
    
    class Meta:
        model = Sample
        fields = ('name', '...', 'report', '...')  # 这里控制要显示的字段
        template_name = 'django_tables2/bootstrap.html'
```

模板要加个自定义 js 的 block

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en-US">
    <body>
    ...
    {% block js %}{% endblock %}
    </body>
</html>
```

对应app(samples)的模板文件

```html
{% extends 'base.html' %}
{% load staticfiles %}
{% block title %}我爱北京天安门{% endblock %}
{% load render_table from django_tables2 %}
{% block content %}
	<div class="container-fluid">
        {% render_table table %}
	</div>
{% endblock %}
{% block js %}
    <script src="{% static 'samples/js/index.js' %}"></script>
{% endblock %}
```

在当前app(samples)目录下新建`static/samples/js`目录，写入自定义js

```javascript
// samples/static/samples/js/index.js
$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
})
```

效果如图：

![tooltips](http://7xivdp.com1.z0.glb.clouddn.com/jpg/2018/6/5c72ddc40df1977100b2b6b6440df9dd.jpg)

咦，怎么还能加按钮？这个下回再说~