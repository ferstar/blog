---
title: "Find common substring between two strings"
date: "2021-11-23T06:56:34+08:00"
tags: ['Default']
comments: true
---

有一段损失了定位信息的文字: `plain_text = '我爱北京天安门, 天安门上放鞭炮'`, 要求还原这段文字在给定段落中尽可能相近的位置

这个段落数据结构大概长这样: `paragraph = {'text': '佛曰 我爱北京天安门, 天安门上太阳升...', chars': [{'text': '佛', 'box': [1, 2, 3, 4]}, {'text': '曰', 'box': [1, 2, 3, 4]}, ..., {'text': '我', 'box': [1, 2, 3, 4]}, ..., {'text': '门', 'box': [1, 2, 3, 4]}, ]}`

其实这就是一个`求最长公共子串`的问题, 先简单粗暴实现了一发:

1. 找出最大公共子串

```python
def find_longest_sub_str(string1, string2):
    answer = ''
    len1, len2 = len(string1), len(string2)
    for i in range(len1):
        for j in range(len2):
            lcs_temp = 0
            match = ''
            while (i + lcs_temp < len1) and (j + lcs_temp < len2) and string1[i + lcs_temp] == string2[j + lcs_temp]:
                match += string2[j + lcs_temp]
                lcs_temp += 1
            if len(match) > len(answer):
                answer = match
    return answer


if __name__ == '__main__':
    str_a = '我爱北京天安门, 天安门上放鞭炮'
    str_b = '佛曰 我爱北京天安门, 天安门上太阳升...'
    print(find_longest_sub_str(str_a, str_b))

```

2. 按index取对应的box信息

```python
def find_longest_sub_str(string1, string2):
    answer = []
    len1, len2 = len(string1), len(string2)
    for i in range(len1):
        for j in range(len2):
            lcs_temp = 0
            match = []
            while (i + lcs_temp < len1) and (j + lcs_temp < len2) and string1[i + lcs_temp] == string2[j + lcs_temp]:
                match.append(j + lcs_temp)
                lcs_temp += 1
            if len(match) > len(answer):
                answer = match[:]
    return answer


if __name__ == '__main__':
    str_a = '我爱北京天安门, 天安门上放鞭炮'
    str_b = '佛曰 我爱北京天安门, 天安门上太阳升...'
    indexes = find_longest_sub_str(str_a, str_b)
    # 这里拦头去尾就可以从段落中拿到对应字的位置信息了

```

粗看起来貌似能交差, 但实际上很坑, 这玩意是`O(N^2)`, 段落文字如果略长的话, 会慢到怀疑人生, 所以必须优化之, 放狗一搜, 发现标准库就有对应实现, 果断抄之

```python
def find_longest_sub_str1(str_a, str_b):
    return SequenceMatcher(None, str_a, str_b).find_longest_match(0, len(str_a), 0, len(str_b))
```

跑了个分, 当字符串长度过长时, 人比人得死了...

![image](https://user-images.githubusercontent.com/2854276/142982012-cf3d0cc4-58f2-4094-9ef0-cbf7223fcd21.png)



```
# NOTE: I am not responsible for any expired content.
create@2021-11-23T06:56:34+08:00
update@2021-11-23T06:56:34+08:00
comment@https://github.com/ferstar/blog/issues/51
```
