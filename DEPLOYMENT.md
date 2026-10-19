# 构建与交付说明

## 交付边界

本项目课程交付到镜像构建为止。已完成本地服务与容器验证，以及 GitHub Actions
的 staging / production 镜像构建。没有配置镜像仓库登录、docker push、镜像归档上传
或云端部署；Actions 运行环境中的镜像未作为可下载交付物保留。
任务名称中的 production 表示构建配置，不表示已有线上生产服务。

## 分环境构建

以 [.github/workflows/ci.yml](.github/workflows/ci.yml) 为准：

| 项目 | staging | production |
|---|---|---|
| 触发条件 | push 到 staging | push 到 main |
| 任务 ID | build-staging | build-production |
| 页面显示名称 | Build staging image | Build production image |
| 前置条件 | needs: ci 成功 | needs: ci 成功 |
| APP_ENV | staging | production |
| Repository Secret | STAGING_MODEL_VERSION | PRODUCTION_MODEL_VERSION |
| 镜像标签 | mpg-app:staging | mpg-app:production |

PR 目标为 dev、staging、main 时执行 ci，两个环境构建任务跳过。
ci 安装 requirements-dev.txt，执行 Ruff、全部 pytest 测试及 Docker 构建。
每个任务在独立运行环境中执行，因此环境构建任务会重新检出并构建镜像。

在 GitHub Settings → Secrets and variables → Actions 中配置上述两项 Repository
Secrets。当前对应模型版本为 6；页面只能确认名称存在，不能读取已保存值。
工作流通过 env 注入 MODEL_VERSION，先检查非空，再使用带引号的 shell 变量传给
docker build 的 APP_ENV 和 MODEL_VERSION 构建参数。不生成、不读取 .env 文件。

MODEL_VERSION 仅为服务返回的版本标签，不会从 MLflow 下载或自动切换模型。
实际模型来自随 app/ 复制进镜像的 app/model/linear_regression.pkl。
更新模型时，必须同时核对导出文件、模型登记卡、测试和环境版本配置。
不要把访问令牌等真正的凭证传入 Docker ARG/ENV；这里传递的是环境名与版本标识。

## 已有验收证据

以下记录来自本项目操作过程的 GitHub 页面及终端结果，属于指定提交的历史证据。

| 项目 | 提交或 PR | 结果 |
|---|---|---|
| CI 工作流合并到 dev | [PR #6](https://github.com/490047748-design/auto-mpg-regression/pull/6)，9e3df74 | PR 检查及 dev push 检查成功 |
| 推进到 staging | [PR #7](https://github.com/490047748-design/auto-mpg-regression/pull/7)，8a822fb | ci 成功；staging 构建执行成功，52 秒；production 跳过 |
| 推进到 main | [PR #8](https://github.com/490047748-design/auto-mpg-regression/pull/8)，5e14e10 | ci 成功；production 构建执行成功，50 秒；staging 跳过 |
| 本地模型与接口 | 版本 6 | 固定样本约 29.16 mpg；非法输入返回 422 |
| 本地容器 | mpg-app:local | 网页、health、model-info、predict 验证通过；运行用户 uid=10001 |

全部 71 项测试通过；测试客户端仍有一条弃用警告，未抑制、未导致失败。
API 与集成测试使用进程内 TestClient，不能代替真实网络、浏览器或云部署验证。
分支保护已配置；检查等待时阻止合并已观察到，未额外进行人为失败演练。
Actions 出现 ubuntu-latest 迁移通知；这里没有固定 runner OS 版本，未来运行环境可能变化。

## 本地复核

需要 Docker Linux 引擎。以下命令在项目根目录的 Git Bash 执行，使用单独名称，
避免覆盖之前的 mpg-app 容器：

```bash
docker build --build-arg APP_ENV=production --build-arg MODEL_VERSION=6 -t mpg-app:production .
docker run -d --name mpg-app-production-check -p 127.0.0.1:8003:8000 mpg-app:production
curl -sS http://127.0.0.1:8003/health
curl -sS http://127.0.0.1:8003/model-info
curl -sS -w '\nHTTP %{http_code}\n' \
  http://127.0.0.1:8003/predict \
  -H 'Content-Type: application/json' \
  -d '{"cylinders":4,"displacement":120,"horsepower":79,"weight":2625,"acceleration":18.6,"model_year":1982,"origin":1}'
docker exec mpg-app-production-check id
```

预期健康状态 ok，模型版本 6，app_env 为 production，预测约 29.16 mpg、HTTP 200，
用户 uid=10001。浏览器访问 http://127.0.0.1:8003/ 可以验证网页表单。
此处为可复核步骤，不表示本轮文档整理已重新执行这些命令。
如已有同名容器，可使用 docker start 再启动；新镜像不会自动替换旧容器。
复核结束后可执行 docker stop mpg-app-production-check 停止该复核容器。

## 安全与复现边界

- .env、.dvc/config.local、原始 CSV、虚拟环境与 MLflow 本地记录不应进入 Git。
- DVC 数据恢复需要自行配置忽略的本地凭证；文档不记录访问令牌。
- .dockerignore 排除数据、测试、开发元数据及 .env 配置，模型文件保留在 app/ 中。
- 已有容器文件检查只覆盖 /app 中列明的文件与目录，不等同于完整镜像安全审计。
- python:3.12-slim 与 ubuntu-latest 为可变化标签；当前结果不是逐字节可复现保证。
- 镜像沿用现有依赖清单，尚未拆分最小推理依赖。

## 文档变更的交付流程

feature/docs → PR 到 dev → ci 成功后合并 → PR 到 staging → 合并后验证 staging 构建
→ PR 到 main → 合并后验证 production 构建。保留 merge commit 历史。
若目标分支保护要求更新源分支，应将目标分支合并回源分支并重新等待检查，不能绕过规则。
文档修改不会自动更新 GitHub 保护规则或 Secrets；这些是独立的仓库设置。
