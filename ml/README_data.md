# Auto MPG 数据集说明

## 1. 数据来源

- 数据集：Auto MPG
- 来源：UCI Machine Learning Repository
- 数据页面：https://archive.ics.uci.edu/dataset/9/auto+mpg
- DOI：https://doi.org/10.24432/C5859H
- 引用：Quinlan, R. (1993). Auto MPG [Dataset]. UCI Machine Learning Repository.
- 原始文件：`data/auto-mpg.data`
- 原始规模：398 行、9 列
- 原始格式：无表头、空白分隔
- 预测目标：`mpg`，表示每加仑燃油行驶的英里数

原始字段包括：

- `mpg`
- `cylinders`
- `displacement`
- `horsepower`
- `weight`
- `acceleration`
- `model_year`
- `origin`
- `car_name`

## 2. v1 数据版本

v1 是将 UCI 原始文本转换成带表头的规范 CSV，没有进行数据清洗。

文件：

- `data/auto_mpg_v1.csv`
- `data/auto_mpg_v1.csv.dvc`

v1 的主要特征：

- 398 行、9 列
- `horsepower` 中保留了 6 个 `?`
- `origin` 仍然使用整数 1、2、3
- 保留 `car_name`
- CSV 本体由 DVC 管理，Git 只保存 `.dvc` 指针

## 3. v1 到 v2 的变化

v2 完全由 `ml/data_pipeline.py` 从 v1 自动生成，没有手工修改 CSV。

| 变化 | 处理方式 |
|---|---|
| 缺失值 | 将 `horsepower` 中的 6 个 `?` 转换为缺失值，再使用中位数 93.5 填补 |
| 类别编码 | 将 `origin` 展开为 `origin_1`、`origin_2`、`origin_3` 三个 one-hot 列 |
| 异常值 | 使用 IQR 区间 `[0.25, 46.25]`，删除 1 行 `mpg=46.6` 的异常记录 |
| 无关字段 | 删除不用于模型训练的 `car_name` |
| 行数 | 从 398 行变为 397 行 |
| 列数 | 从 9 列变为 10 个模型字段 |
| 缺失值数量 | 清洗后为 0 |

v2 文件：

- `data/auto_mpg_v2.csv`
- `data/auto_mpg_v2.csv.dvc`

v2 最终字段：

- `mpg`
- `cylinders`
- `displacement`
- `horsepower`
- `weight`
- `acceleration`
- `model_year`
- `origin_1`
- `origin_2`
- `origin_3`

## 4. Git 与 DVC 版本对应关系

| 版本 | Git 标签 | Git 提交 SHA | 数据文件 | DVC MD5 |
|---|---|---|---|---|
| v1 | `data-v1` | `824875105af0d9963086b3eca444ee6ec56c4abe` | `data/auto_mpg_v1.csv` | `4f2321b47a64d9849f9325d64ceb5361` |
| v2 | `data-v2` | `a375cdaa352ab1a0045ca69afc6a2d108750675b` | `data/auto_mpg_v2.csv` | `3e4175cf1366fa913048bf2678166b78` |

`data-v1` 标签指向包含 v1 数据指针和 Azure 公共配置的提交，因此从该标签切换后可以使用 DVC 从 Azure 恢复数据。

Git 提交 SHA 和 DVC MD5 是两种不同的指纹：

- Git SHA 定位代码、测试和 `.dvc` 指针的版本。
- DVC MD5 定位真实 CSV 的内容。
- 两者结合，可以准确回答某次实验使用了哪一版代码和哪一版数据。

## 5. 数据版本复现方法

恢复 v1：

~~~bash
git switch --detach data-v1
dvc pull
~~~

返回之前的开发分支并恢复 v2：

~~~bash
git switch -
dvc pull
~~~

检查本地数据与 Azure 是否一致：

~~~bash
dvc status
dvc status --cloud
~~~

真实 CSV 不提交到 GitHub。GitHub 保存代码、测试和 `.dvc` 指针，CSV 数据本体保存在 DVC 本地缓存和 Azure Blob Storage 中。

Azure SAS Token 只保存在被 Git 忽略的 `.dvc/config.local`，不能写入代码、README 或 Git 提交。