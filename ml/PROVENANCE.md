# 模型溯源说明

## 数据来源与版本

来源：UCI Auto MPG
DOI：https://doi.org/10.24432/C5859H

v1：
- 标签：data-v1
- 文件：data/auto_mpg_v1.csv
- 行数：398
- DVC MD5：4f2321b47a64d9849f9325d64ceb5361

v2：
- 标签：data-v2
- 文件：data/auto_mpg_v2.csv
- 行数：397
- DVC MD5：3e4175cf1366fa913048bf2678166b78

v2 是数据清洗与版本管理制品。
正式训练从 v1 固定划分，不照搬 v2 的全数据中位数与 IQR 删行。

## 代码到模型的对应关系

- 训练代码提交：9f28b8a8ed157835131dad7045b34c994d6d859c
- Run 名称：improved-v2-linear-export
- Run ID：e550bf0a8ae24948a08ed1a66d6c33be
- 注册模型：AutoMPG_LinearRegression
- 注册版本：6
- MLflow 模型 URI：models:/m-25e284869407462bbc4cddaf3e52ec1a
- 导出文件：app/model/linear_regression.pkl
- 文件 SHA256：31d31c4d8e200cc426f9bc7e79458e1cfbdb6304be63dbb58e367c8ab3716435

训练代码提交定位生成模型的代码。
DVC MD5 定位训练输入数据。
Run ID 定位实验记录。
模型 SHA256 定位导出文件内容。

后续将模型文件和文档加入 Git 的提交，会晚于上述训练代码提交；
这不会改变模型实际使用的代码版本。

## 训练和验证流程

1. 将 6 条缺失马力记录放入训练集。
2. 将 392 条完整记录固定划分为 313 条训练、79 条测试。
3. improved 使用全部 319 条训练记录。
4. 在训练集上进行 5 折交叉验证，预处理参数按折拟合。
5. 使用全部训练集拟合最终 Pipeline，在固定测试集上评价。
6. 导出该模型，重新加载并验证预测一致性。

MLflow 制品 split_and_features.json 保存划分索引及特征顺序。
export_manifest.json 保存导出文件与代码、数据、实验的对应关系。

## 复现命令

在独立的复现副本中检出训练代码提交，配置本机 DVC 凭证后执行：

~~~bash
git switch --detach 9f28b8a8ed157835131dad7045b34c994d6d859c
./.venv/Scripts/dvc.exe pull
./.venv/Scripts/python.exe -m ml.train --data data/auto_mpg_v1.csv --run-name improved-v2-linear-export --stage improved --model-type linear --export app/model/linear_regression.pkl
~~~

运行前应安装项目依赖并保持 Git 工作区干净。
Azure 凭证仅存放在被忽略的 .dvc/config.local。

重新运行会产生新的 Run ID，注册版本号取决于本地 Registry 的已有记录。
本说明中的编号代表本次已经完成的实验，不能假定复现时编号相同。