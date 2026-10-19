# 当前应用模型登记卡

## 模型身份

- 状态：已选定并导出；本地预测服务、容器及 CI 分环境镜像构建已验证，尚未部署云端服务
- 注册模型名：AutoMPG_LinearRegression
- 注册版本：6
- 实验名称：AutoMPG_Regression
- Run 名称：improved-v2-linear-export
- Run ID：e550bf0a8ae24948a08ed1a66d6c33be
- MLflow 模型 URI：models:/m-25e284869407462bbc4cddaf3e52ec1a
- 导出文件：app/model/linear_regression.pkl
- 文件 SHA256：31d31c4d8e200cc426f9bc7e79458e1cfbdb6304be63dbb58e367c8ab3716435

## 模型结构与输入

模型结构：

SimpleImputer(strategy="median") → StandardScaler → LinearRegression

输入是带列名的 pandas DataFrame，列顺序为：

1. cylinders
2. displacement
3. horsepower
4. weight
5. acceleration
6. model_year
7. origin_1
8. origin_2
9. origin_3

原始 origin 必须先转换成上述三个 one-hot 列。
导出的 Pipeline 包含填补、标准化和回归器，不包含原始 origin 编码。
horsepower 的问号应先转换为数值缺失值 NaN。

输出为预测 mpg，单位是英里/加仑。

## 训练与评价

- 训练输入：data/auto_mpg_v1.csv
- DVC MD5：4f2321b47a64d9849f9325d64ceb5361
- 训练代码提交：9f28b8a8ed157835131dad7045b34c994d6d859c
- 训练记录：319 条
- 独立测试记录：79 条
- 训练集马力中位数：95.0
- 训练集 5 折 CV RMSE：3.367225
- 测试 RMSE：3.269054
- 测试 MAE：2.489024
- 测试 R²：0.790624

缺失值填补和标准化在 Pipeline 内拟合。
交叉验证时，每一折单独拟合预处理参数。
测试集不参与预处理参数学习或模型选型。

## 导出验证

模型导出后已重新加载，在同一测试输入上的预测通过
numpy.testing.assert_allclose 检查。

导出的是本次训练、评价的同一个模型，没有加入测试集重新训练。
