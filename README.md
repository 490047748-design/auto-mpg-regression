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
- 阶段五：Docker 镜像构建与本地容器运行验证完成。
- 阶段六：GitHub Actions CI、分支保护及 staging / production 镜像构建验证完成。
- 阶段七：交付文档与本地验收已完成，分支发布状态以对应 PR 和 Actions 记录为准。

课程交付范围到镜像构建为止。目前没有发布镜像或部署云端服务。
完整环境说明与验收证据见 [DEPLOYMENT.md](DEPLOYMENT.md)。

## 新环境安装

需要 Python 3.12；以下为 Windows Git Bash 命令。在项目根目录执行：

```bash
py -3.12 -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
```

已有虚拟环境时无需重复创建。导出模型已进入 Git，运行预测和现有测试不要求
下载 DVC 数据或连接 MLflow；重新训练需要恢复数据并配置相应工具，见下方数据文档。

## CI 与代码流转

工作流定义：[.github/workflows/ci.yml](.github/workflows/ci.yml)。

| 事件 | 实际执行的任务 | 内容 |
|---|---|---|
| PR 目标为 dev / staging / main | ci | Ruff、全部测试、构建 mpg-app:ci |
| push 到 dev | ci | 同上 |
| push 到 staging | ci → build-staging | ci 成功后构建 mpg-app:staging |
| push 到 main | ci → build-production | ci 成功后构建 mpg-app:production |
| push 到 feature/*，没有关联 PR | 无 | 当前工作流不监听功能分支 push |

向已开 PR 的功能分支推送提交，会触发该 PR 的更新检查。
PR 中两个环境构建任务按条件跳过；环境任务设置 needs: ci，必须等待 ci 成功。

```text
feature/* 提交并推送
  → PR 到 dev → ci: lint → test → Docker build → 合并 dev
  → PR: dev 到 staging → ci 通过 → 合并 staging
  → push staging: ci → staging 镜像构建
  → PR: staging 到 main → ci 通过 → 合并 main
  → push main: ci → production 镜像构建
```

dev、staging、main 均已配置分支保护：要求 PR、必需检查 ci、分支保持最新，
管理员也不得绕过；当前单人流程不要求人工批准，不要求线性历史。
这些设置位于 GitHub 仓库设置中，不由 YAML 自动创建，复制仓库时需要重新配置。
已观察到检查等待期间合并被阻止；未额外执行故意失败的 CI 演练。

## 数据、模型与目录导航

数据来自 UCI Auto MPG。DVC 管理原始 v1 与清洗 v2，远程存储为 Azure；
训练使用 v1，填补和标准化在训练数据或交叉验证训练折内部拟合，避免预处理泄漏。
当前模型为 AutoMPG_LinearRegression 版本 6，测试 RMSE 约 3.2691 mpg，
MAE 约 2.4890 mpg，R² 约 0.7906。

| 路径 | 用途 |
|---|---|
| app/ | FastAPI、请求校验、特征转换、网页及导出模型 |
| ml/ | 数据处理、训练、划分、实验与溯源文档 |
| data/*.dvc | 两版数据的 DVC 指针，实际 CSV 不进入 Git |
| tests/unit/ | 数据处理、划分、建模及模型契约测试 |
| tests/api/test_api.py | HTTP 接口与输入边界测试 |
| tests/integration/test_flow.py | 应用调用流程测试 |
| .github/workflows/ci.yml | CI 与分环境镜像构建 |
| Dockerfile / .dockerignore | 镜像构建与上下文排除规则 |
| .env.example | 配置说明模板，不包含凭证 |

- [数据版本说明](ml/README_data.md)
- [实验对比与选型](ml/README_experiments.md)
- [当前模型登记卡](ml/registry/current_model.md)
- [数据—代码—模型溯源](ml/PROVENANCE.md)
- [构建与交付说明](DEPLOYMENT.md)

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

## Docker 构建与运行

以下命令在项目根目录执行，需要 Docker 引擎已启动并使用 Linux 容器。

### 构建镜像

```bash
docker build --build-arg APP_ENV=development --build-arg MODEL_VERSION=6 -t mpg-app:local .
```

镜像基于 python:3.12-slim，先安装依赖，再复制应用代码。
使用现有 requirements.txt，包含训练相关依赖，尚未拆分最小推理依赖。

模型文件随 app/ 目录一起进入镜像。
启动时不需要连接 MLflow、Azure 或下载训练数据。

### 首次创建并启动容器

```bash
docker run -d --name mpg-app -p 127.0.0.1:8002:8000 mpg-app:local
```

本机 8002 端口映射到容器内部 8000 端口。
容器内部监听 0.0.0.0，对外映射仅绑定本机 127.0.0.1。

访问地址：
- 网页：http://127.0.0.1:8002/
- 接口文档：http://127.0.0.1:8002/docs
- 健康检查：http://127.0.0.1:8002/health
- 模型信息：http://127.0.0.1:8002/model-info

/predict 只接受 POST。直接在浏览器地址栏访问会发送 GET，
因此可能返回 Method Not Allowed。可通过网页表单或 /docs 发起预测。

### 查看状态和日志

```bash
docker ps --filter name=mpg-app
docker logs mpg-app
docker exec mpg-app id
```

运行用户应为 uid=10001(appuser)，不是 root。

### 停止和再次启动已有容器

```bash
docker stop mpg-app
docker start mpg-app
```

已有同名容器时，使用 docker start，不重复执行 docker run。
重新构建镜像不会自动更新已有容器；应用新镜像需要重新创建容器。

### 已完成的本地验证

- Docker 镜像构建成功。
- /health 返回正常状态。
- /model-info 返回 model_version=6、app_env=development。
- 固定样本预测返回 HTTP 200，约为 29.16 mpg。
- 网页表单能够提交并展示相同预测结果。
- weight=-5 返回 422，错误位置指向 weight。
- model_year=2082 返回 422，错误位置指向 model_year。
- 容器以 uid=10001 运行。
- 容器 /app 中存在模型文件。
- 容器 /app 下未发现 data、tests、.git、.dvc、.venv、
  mlruns、mlflow.db，也未发现 .env 配置文件。

.dockerignore 排除本地数据、虚拟环境、实验记录和配置文件。
上述文件检查针对容器中的项目目录，不代表完成了全面安全审计。

本阶段完成本地容器验证，尚未发布镜像或部署到云端。
