# Auto MPG Regression

使用 UCI Auto MPG 数据集训练回归模型，通过 FastAPI 提供油耗预测服务。

## 开发流程

feature/* → dev → staging → main

## 当前进度

- 阶段零：项目结构与开发环境完成。
- 阶段一：DVC 数据版本管理及 Azure 远程存储完成。
- 阶段二：模型训练、MLflow 实验对比与模型导出完成。
- 阶段三：FastAPI 预测接口和网页表单完成本地验证。
- 阶段四：模型契约、接口边界和应用调用流程测试完成，71 项测试通过。
- GitHub Actions、Docker 和云端部署尚未完成。

## 本地启动

以下命令在项目根目录的 Git Bash 中执行，使用已有虚拟环境：

```bash
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

- 网页表单：http://127.0.0.1:8001/
- 接口文档：http://127.0.0.1:8001/docs
- 健康检查：http://127.0.0.1:8001/health
- 模型信息：http://127.0.0.1:8001/model-info

预测服务直接加载本地模型，不需要启动 MLflow。
MLflow 页面使用 5000 端口，与预测服务独立运行。

## 预测接口

POST /predict 接受以下七个字段：

| 字段 | 含义与单位 |
|---|---|
| cylinders | 气缸数 |
| displacement | 排量，立方英寸 |
| horsepower | 马力，hp |
| weight | 车重，磅 |
| acceleration | 加速时间，秒 |
| model_year | 四位车型年份，1970—1982 |
| origin | 1：美国，2：欧洲，3：日本 |

示例请求：

```json
{
  "cylinders": 4,
  "displacement": 120,
  "horsepower": 79,
  "weight": 2625,
  "acceleration": 18.6,
  "model_year": 1982,
  "origin": 1
}
```

当前模型预测约为 29.16 mpg。

合法输入返回 200，响应包含 mpg、unit、model_version 和 app_env。
越界、缺字段或多余字段返回 422。

mpg 表示每加仑燃油可行驶的英里数，越高越省油。
输入通过校验不代表预测一定准确。

## 特征转换与模型

服务把四位年份转换为两位数，将 origin 展开为三个 one-hot 列，
按固定顺序生成九列 DataFrame，然后交给导出的 Pipeline。

Pipeline 包含缺失值填补、标准化和线性回归。
服务只执行预测，不重新训练，也不重复标准化。

默认模型文件：app/model/linear_regression.pkl

服务启动时加载模型并检查特征列。
模型文件缺失或特征列不匹配时，启动失败。

模型来源和评价结果：
- ml/registry/current_model.md
- ml/README_experiments.md
- ml/PROVENANCE.md

## 环境配置

应用读取以下进程环境变量：

| 变量 | 默认行为 |
|---|---|
| APP_ENV | development |
| MODEL_VERSION | 6 |
| MODEL_PATH | 未设置时使用应用目录下的 model/linear_regression.pkl |

MODEL_VERSION 是返回给调用方的版本标识，改变它不会下载或切换模型。
实际加载的模型由 MODEL_PATH 决定；相对路径以启动目录为基准。

当前应用不会自动读取 .env 文件。
例如，在 Git Bash 中可以这样设置环境变量：

```bash
export APP_ENV=development
export MODEL_VERSION=6
```

修改环境变量后，需要从该终端重新启动服务才能生效。

## 检查与测试

在项目根目录执行：

```bash
./.venv/Scripts/python.exe -m ruff check app ml tests
./.venv/Scripts/python.exe -m pytest tests -q
```

接口测试使用 TestClient，加载真实导出模型。
不需要先启动 Uvicorn，也不占用网络端口。

本阶段验证结果：
- 网页默认示例预测为 29.16 mpg。
- 健康检查和模型信息接口正常。
- 负车重请求返回 422，错误位置指向 weight。
- 模型文件缺失时启动失败。
- 71 项自动化测试通过。

目前测试输出有一条测试客户端依赖的弃用警告，不影响测试通过。

## 阶段四测试覆盖

| 测试范围 | 用例数 | 主要验证内容 |
|---|---:|---|
| 原有数据处理、划分和建模测试 | 14 | 数据转换、划分可复现、训练预处理及 Ridge 行为 |
| 模型与特征契约测试 | 17 | 列顺序、产地编码、年份转换、训练与服务转换一致性、固定样本预测 |
| 接口测试 | 36 | 正常响应、数值越界、错误类型、缺字段、多余字段、年份边界、错误 JSON、模型缺失 |
| 应用调用流程测试 | 4 | 多接口信息一致性，以及非法请求后服务仍可正常预测 |
| 合计 | 71 | 本地运行全部通过 |

测试使用真实导出模型，不重新训练。
车重和年份的方向测试用于检查当前模型的行为，不代表通用物理规律。

接口和集成测试使用 TestClient，在进程内执行应用启动及请求处理，
不覆盖真实网络、浏览器 JavaScript、Docker 或云端部署。
网页表单提交与结果展示已完成本地手动验证。

测试通过说明上述检查范围内的行为符合预期，不代表不存在其他缺陷，
也不代表模型对任意车辆都能准确预测。

测试输出仍有一条测试客户端依赖的弃用警告，未造成失败。