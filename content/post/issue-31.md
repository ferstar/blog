---
title: "给SQLAlchemy declarative_base加个基类"
date: "2020-12-11T22:39:38+08:00"
tags: ['Python']
comments: true
---

作为CRUD仔，经常这样的套路用ORM，想加个`to_dict`的方法来把ORM对象转换成json给前端返回，但已有的项目都是在各自的子类里写个`to_dict`的方法，太累了，放到基类可好？是可以的。
```python
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(String(20), primary_key=True)
    name = Column(String(20))

    def to_dict(self):
        ...

class School(Base):
    __tablename__ = 'school'
    id = ...
    name = ...

    def to_dict(self):
        ...
...

engine = create_engine('mysql+mysqlconnector://root:password@localhost:3306/test')
DBSession = sessionmaker(bind=engine)
```
看`declarative_base`源码发现可以给塞个自定义的class进去作为基类，所以以上代码可以这样改进

```python
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base

class _Base:
    __banned_cols__: List[str] = ['deleted_utc']
    __extra_cols__: List[str] = []

    def to_dict(self, **kwargs):
        cols = self.__extra_cols__ + [c.name for c in inspect(self.__class__).c]
        ret_dict = {col: getattr(self, col) for col in cols if hasattr(self, col) and col not in self.__banned_cols__}
        for func in self.custom_funcs():
            if callable(func):
                ret_dict.update(func(ret_dict, **kwargs))
        return ret_dict

    def custom_funcs(self) -> List[FunctionType]:
        return []

Base = declarative_base(cls=_Base)
...
```

这样子类model class就没必要去再写一遍`to_dict`方法了

```
# NOTE: I am not responsible for any expired content.
created_date: 2020-12-11T22:39:38+08:00
update_date: 2021-02-12T22:14:58+08:00
comment_url: https://github.com/ferstar/blog/issues/31
