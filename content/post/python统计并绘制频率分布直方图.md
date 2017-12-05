+++
date = "2017-07-27T15:30:00+08:00"
title = "python统计并绘制频率分布直方图"
tags = ['PYTHON']

+++

为了统计xx数据分布情况, 需要从`csv`文件中读出数据, 转换成`int`后绘制出频率直方图

代码如下

```python
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import numpy as np

lst = []
with open("123.csv", 'r', encoding='utf8') as fh:
    while 1:
        line = fh.readline()
        if not line: break
        try:
            lst.append(int(line.strip()))
        except:
            pass

mu = np.mean(lst)  # 样本均值
sigma = np.std(lst)  # 样本标准差
num_bins = 50  # 区间数量(实际样本值是从100到150, 所以分成50份)
n, bins, patches = plt.hist(lst, num_bins, normed=1, facecolor='blue', alpha=0.5)
# 添加一个理想的正态分布拟合曲线
y = mlab.normpdf(bins, mu, sigma)
plt.plot(bins, y, 'r--')
plt.xlabel('Values')
plt.ylabel('Probability')
plt.title(r'$\mu={}$, $\sigma={}$'.format(round(mu, 2), round(sigma, 2)))
plt.subplots_adjust(left=0.15)
plt.show()

```

实际在`jupyter-notebook`中, 上述代码输出并未内嵌, 而是新弹出了一个窗口绘图

![](~/15-43-38.jpg)

我们希望能够将图标内嵌到`notebook`的网页当中, 所以需要额外的操作

```python
%matplotlib inline
from IPython.display import HTML
```

这样就可以了

![](~/15-44-12.jpg)



## 参考

1. [hist的使用](http://blog.csdn.net/u013571243/article/details/48998619)
2. [python统计并绘制频率分布直方图](http://blog.csdn.net/baidu_31508279/article/details/52329688)

