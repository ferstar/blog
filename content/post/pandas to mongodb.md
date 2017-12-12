---
title: "pandas to mongodb"
date: "2017-07-13T13:02:00+08:00"
tags: ['PYTHON']
comments: true
---


最近项目需要, 把所有历史资料(Excel格式)汇总分析, 于是祭出pandas神器, 上万份Excel表格轻松搞定.

先放一段Excel转入MongoDB的代码

```python
import os
import sys
import time
from functools import reduce, wraps
from shutil import copy2

import pandas as pd
import pymongo
from bson.json_util import loads

g_set = {'A', 'C', 'T', 'G'}
gg_set = {'AC', 'AG', 'AT', 'CG', 'CT', 'GT'}
summary = {
    "ok": 0,
    "skip": 0,
    "error": 0,
    "tmp": 0
}
db_name = "test"
collection_name = "snp_info"
index_name = "Sample_ID"


def bak_file(fp, ds="tmp", ext="bak", rename=True):
    fn = os.path.basename(fp)
    if not os.path.exists(ds):
        os.mkdir(ds)
    # 复制到临时目录
    copy2(fp, os.path.join(ds, fn))
    # 原路径加.bak后缀名
    if rename:
        os.rename(fp, "{}.{}".format(fp, ext))


def pick_rules(fp):
    # 文件名中包含LH-R及LH-I的均为其他项目, 跳过不处理
    fp_base = os.path.basename(fp)
    if "LH-R" in fp_base or "LH-I" in fp_base:
        bak_file(fp, "skip")
        summary["skip"] += 1
        print("{}\t0\t0\tskip".format(fp_base))
        return False
    elif fp_base.startswith("~"):  # 跳过office临时文件
        bak_file(fp, rename=False)
        summary["tmp"] += 1
        print("{}\t0\t0\ttmp".format(fp_base))
        return False
    else:
        return True


def get_files(dp, ext="xlsx"):
    """
    获取目标目录下指定后缀名文件列表
    :param dp: 目标目录
    :param ext: 后缀名, 默认为xlsx
    :return: 指定后缀名文件路径列表
    """
    # 绝对路径中有空格的情况会有bug, 所以暂时还是用相对路径
    # abspath = os.path.abspath(dp)
    lst = []
    for root, dirs, files in os.walk(dp):
        for file in files:
            if file.endswith(".{}".format(ext)):
                lst.append(os.path.join(root, file))
    return lst


def xlsx2df(fp, sn="Sample_ID"):
    """
    将xlsx内带有检测信息的结果转化为dataframe返回
    可以处理以下四种情况
    1. Sample_ID在首行, 紧接着是样本信息, 中间没有空行
    2. Sample_ID在首行, 紧接着两行首行为空, 第四行开始才是正常样本信息
    3. 1, 2两行首列为空, Sample_ID在第三行, 后面才是样本信息
    4. 没有Sample_ID, 首行首列为空, 紧接着就是样本信息
    :param fp: Excel文件路径
    :param sn: header name默认是Sample_ID
    :return: 整理后的dataframe
    """
    df = pd.read_excel(fp, header=None)
    # 添加header name
    is_format_ok = False
    for i in range(df.shape[0]):
        _t = str(df.iloc[i, 0])
        if _t == sn:
            # Sample_ID在首行的情况(大多数情况)
            df.columns = [i for i in df.iloc[i].values]
            df = df.iloc[(i + 1):]  # 跳过Sample_ID行
            is_format_ok = True
            break
        if _t.startswith("B"):
            # 没有Sample_ID的情况(极少)
            # 以B开头即表示正常ID, 则取上一行内容为header name, 第一个应该是sn即Sample_ID
            df.columns = [sn] + [i for i in df.iloc[i - 1].values][1:]
            is_format_ok = True
            break
    if not is_format_ok:
        # 文件无法识别, 备份源文件并返回空df
        print("{}:\t0\t0\terror".format(os.path.basename(fp)))
        bak_file(fp, "error")
        summary["error"] += 1
        return pd.DataFrame()
    # 删除Sample_ID为空的行
    df = df[pd.notnull(df[sn])]

    # 删除空列
    df = df.dropna(axis=1, how="all")

    # 删除重复rs号
    df = df.loc[:, ~df.columns.duplicated()]

    rows, cols = df.shape
    for i in range(rows):
        for j in range(1, cols):  # 跳过第一列Sample_ID不作处理
            v = df.iloc[i, j]
            if isinstance(v, str):
                v = v.strip().upper()  # 去空格&转大写
                if v in g_set:
                    # 纯合子加倍
                    df.iloc[i, j] = v * 2
                elif len(v) == 2:
                    # 杂合子排序
                    _v = "".join(sorted(v))
                    df.iloc[i, j] = _v if _v in gg_set else None
                elif v == "DEL":
                    # 单个碱基缺失, 用DD表示
                    df.iloc[i, j] = "DD"
                elif "." in v:
                    # 杂合缺失, 将DEL替换为D
                    _s = sorted(v.split("."), key=lambda x: len(x))[0]  # 提取出单个碱基
                    df.iloc[i, j] = "".join(sorted((_s, "D"))) if _s in g_set else None
                else:
                    # 空值或者超长字符, 填Nan
                    df.iloc[i, j] = None
            else:
                # 非string值填Nan
                df.iloc[i, j] = None
    summary["ok"] += 1
    print("{}\t{}\t{}\tok".format(os.path.basename(fp), rows, cols))
    return df


def insert_many(collection, docs=None, update=True):
    if not docs:
        return
    # $set 的时候, 会更新数据, setOnInsert只插入不更新
    update_key = "$set" if update else "$setOnInsert"
    bulk = pymongo.bulk.BulkOperationBuilder(collection, ordered=False)
    for i in docs:
        if i.get(index_name):
            bulk.find({index_name: i[index_name]}).upsert().update_one({update_key: i})
        else:
            bulk.insert(i)
    result = bulk.execute()
    return result


def df2db(df):
    # 写入数据库
    client = pymongo.MongoClient()
    db = client[db_name]
    collection = db[collection_name]
    try:
        collection.index_information()
    except pymongo.errors.OperationFailure:
        # 索引Sample_ID
        collection.create_index(index_name, unique=True)
    data = loads(df.T.to_json()).values()
    rs = insert_many(collection, data)
    # collection.insert_many(loads(df.T.to_json()).values())
    print("-" * 30)
    print("summary(files):")
    print("\tok:\t\t{}".format(summary['ok']))
    print("\terror:\t\t{}".format(summary['error']))
    print("\ttmp:\t\t{}".format(summary['tmp']))
    print("\tskip:\t\t{}".format(summary['skip']))
    print("\ttotal:\t\t{}".format(sum(summary.values())))
    print("-" * 30)
    print("summary(samples):")
    print("\tupdate:\t\t{}".format(rs.get("nModified")))
    print("\tinsert:\t\t{}".format(rs.get("nUpserted") + rs.get("nInserted")))
    print("\ttotal:\t\t{}".format(collection.count()))
    client.close()


def time_it(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t1 = time.time()
        rt = func(*args, **kwargs)
        print("cost: {}s".format(round((time.time() - t1), 2)))
        return rt

    return wrapper


@time_it
def main(dp):
    # 读入Excel, 处理后合并输出到df
    df = reduce(
        lambda df1, df2: df1.append(df2, ignore_index=True),
        map(
            xlsx2df, filter(
                pick_rules,
                get_files(dp)
            )
        )
    )
    # 删除重复ID
    df = df.drop_duplicates(subset="Sample_ID")
    # 删除空列
    df = df.dropna(axis=1, how="all")
    df2db(df)
    print("-" * 30)
    print("data importing complete!")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: {} <samples_dir>".format(os.path.basename(sys.argv[0])))
    main(sys.argv[1])

```
运行结果:
```shell
------------------------------
summary(files):
        ok:             7
        error:          0
        tmp:            0
        skip:           0
        total:          7
------------------------------
summary(samples):
        update:         0
        insert:         0
        total:          7272
------------------------------
data importing complete!
cost: 1.26s
```