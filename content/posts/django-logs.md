---
title: "Django2.0 踩坑记"
slug: "django-2-logging-pitfalls"
date: 2018-02-26T09:01:41+08:00
tags: ['LINUX', 'DJANGO']
comments: true
---

## 坑一：?: (2_0.W001) Your URL pattern '^ has...

因为是新项目，没有历史包袱，所以直接上了 Django 2.0 的方案，于是照着老司机经验教程爬就掉到了这个坑，全提示是：

```
WARNINGS:
?: (2_0.W001) Your URL pattern '^$' has a route that contains '(?P<', begins with a '^', or ends with a '$'. This was likely an oversight when migrating to django.urls.path().
```

解决很简单，Google 大法

<https://stackoverflow.com/a/47661654>

抄一下原答案：

```shell


The new path() syntax in Django 2.0 does not use regular expressions. You want something like:

path('<int:album_id>/', views.detail, name='detail'),

If you want to use a regular expression, you can use re_path().

re_path(r'^(?P<album_id>[0-9])/$', views.detail, name='detail'),

The old url() still works and is now an alias to re_path, but it is likely to be deprecated in future.

url(r'^(?P<album_id>[0-9])/$', views.detail, name='detail'),
```

意思是新的 path() 方法不认正则表达式，如果在 urls 中想用正则，需要用 re_path()，旧的 url() 方法在 Django 2.0 中依然支持，等同于 re_path()，未来可能会 deprecated，所以就用 re_path() 吧
