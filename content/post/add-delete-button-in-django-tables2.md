---
title: "Add Delete Button in Django-tables2"
date: 2018-06-29T11:09:59+08:00
tags: ['DJANGO', 'PYTHON']
comments: true
---

这是用 [django-tables2](https://django-tables2.readthedocs.io/en/latest/) 的另一个坑：如何给每行条目添加删除功能？

还是直接上解决方案：在`tables.py`加一列，用来放删除按钮，本来是打算直接给`href`加个`DELETE`的`method`，然而发现`HTML5`并不支持这样做，没办法只好捏造一个`form`表单来做这事情了。

```python
# samples/tables.py
import django_tables2 as tables

from .models import Sample


class SampleTable(tables.Table):    
    # 塞一个form进去，POST方法，加一个隐藏输入，命名为_method，通过这货的值来冒充DELETE方法
    # 实际上还是一个POST请求，不过干的是DELETE的事情
    delete = tables.TemplateColumn(
        '<form action="/samples/{{record.id}}/" method="post">{% csrf_token %}<input type="hidden" name="_method" value="delete"><button data-toggle="tooltip" title="Please note that deletion cannot be undone" type="submit" class="btn btn-danger btn-xs">delete</button></form>',
        orderable=False,
        verbose_name=''
    )

    class Meta:
        model = Sample
        fields = ('name', '...', 'delete', '...')  # 这里控制要显示的字段
        template_name = 'django_tables2/bootstrap.html'
```

`DELETE`方法有了，自然需要搞个路由

```python
# samples/urls.py
from django.urls import path

from . import views

app_name = 'samples'
urlpatterns = [
    path('', views.index, name='index'),
    path('<uuid:sample_id>/', views.detail, name='detail'),
]
```

视图部分：

```python
# samples/views.py
# 略去各种 import
def index(request):
    # 各种验证（是否登录、合法）后，返回当前用户真正可以看到的数据（未标记为归档的部分）
    return render(request, 'samples/index.html', locals())

def detail(request, sample_id):
    if request.method == "POST":
        # 找不到不处理
        try:
            sample = Sample.objects.get(id=sample_id)
        except:
            return HttpResponse(status=404)
        data = request.POST
        method = data.get('_method', '').lower()
        
        if method == 'delete':
            sample.has_archived = True  # 只添加归档标记，真的删除是不可能的，万一有用呢
            sample.save()
            return redirect('samples:index')
```

效果如图：

![add-delete-button](https://blog-1253877569.cos.ap-chengdu.myqcloud.com/ext/jpg/2018/6/45e42b6a890cafda88510a096f8cf526.jpg)

