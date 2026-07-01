# EduMind Git/GitHub 协作指南

本项目使用 GitHub 进行多人协作开发。Git 中只保存源代码、配置模板、部署脚本、测试与必要资源；不要提交完整运行环境、密钥、本地数据、日志、IDE 配置或生成产物。

## 当前仓库配置

- GitHub 账号：`XXXXXQ-0206`
- 远程仓库：`https://github.com/XXXXXQ-0206/EduMind.git`
- 本地 Git 用户名：`XXXXXQ-0206`
- 本地 Git 邮箱：`145568156+XXXXXQ-0206@users.noreply.github.com`
- 默认主分支：`main`
- 集成开发分支：`develop`
- 功能分支格式：`feature/<short-name>`
- 项目级 hooks：`.githooks/`

## 必备工具

- Git 2.40+
- Git LFS 3+
- Docker Desktop 与 Docker Compose
- Node.js 22+
- Python 3.11+
- 可选：GitHub CLI (`gh`)

## 首次配置

登录 GitHub：

```powershell
git lfs install
git credential-manager github login --username "XXXXXQ-0206" --device --force --no-ui
```

命令会输出 `https://github.com/login/device` 和一次性 code。用任意正常浏览器打开该地址，输入 code，并确认登录的是 `XXXXXQ-0206`。

配置本仓库：

```powershell
.\scripts\configure-github-collaboration.ps1 `
  -GitUserName "XXXXXQ-0206" `
  -GitUserEmail "145568156+XXXXXQ-0206@users.noreply.github.com" `
  -RepositoryUrl "https://github.com/XXXXXQ-0206/EduMind.git"
```

如果同伴使用自己的 GitHub 账号，应把 `GitUserName` 和 `GitUserEmail` 换成自己的 GitHub 信息，但 `RepositoryUrl` 保持为本项目仓库地址。

## 分支策略

- `main`：稳定分支，保持可演示、可部署状态。
- `develop`：日常集成分支，功能开发完成后先合入这里。
- `feature/<short-name>`：功能或修复分支，从 `develop` 创建。

规则：

- 不直接在 `main` 上开发。
- 功能变更通过 Pull Request 合入 `develop`。
- `develop` 通过测试和验收后，再合入 `main`。
- 分支名应清晰，例如 `feature/github-collaboration`、`feature/paper-export`、`feature/auth-hardening`。

## 常用协作命令

克隆仓库：

```powershell
git clone https://github.com/XXXXXQ-0206/EduMind.git
cd EduMind
git lfs install
git config core.hooksPath .githooks
git switch develop
```

拉取更新：

```powershell
git switch develop
git pull origin develop
```

创建功能分支：

```powershell
git switch develop
git pull origin develop
git switch -c feature/<short-name>
```

提交更改：

```powershell
git status
git add <files>
git commit -m "feat: concise change summary"
```

推送功能分支：

```powershell
git push -u origin feature/<short-name>
```

合并已审核分支：

```powershell
git switch develop
git pull origin develop
git merge --no-ff feature/<short-name>
git push origin develop
```

让功能分支同步最新 `develop`：

```powershell
git switch feature/<short-name>
git fetch origin
git merge origin/develop
```

解决冲突：

```powershell
git status
# 打开冲突文件，保留正确内容，并删除 <<<<<<<、=======、>>>>>>> 标记。
git add <resolved-files>
git commit
```

放弃一次冲突合并：

```powershell
git merge --abort
```

## 提交质量检查

版本化 hooks 位于 `.githooks/`：

- `pre-commit`：阻止提交 `.env`、依赖目录、运行数据、IDE 配置、日志和未走 LFS 的大文件。
- `pre-commit`：执行 Python 编译检查和 `docker compose config` 校验。
- `pre-commit`：如果本机存在 `frontend/node_modules`，会执行前端 lint。
- `commit-msg`：要求 Conventional Commit 格式，例如 `feat: add paper export`。
- `pre-push`：执行 Git LFS 检查，并阻止直接推送到已有的 `main` / `master`。

启用 hooks：

```powershell
git config core.hooksPath .githooks
```

只有首次初始化空仓库或紧急修复时才考虑 `--no-verify`，并应尽快补齐检查。

## 应提交与不应提交的内容

应提交：

- `backend/`、`frontend/`、`services/`
- `deploy/`、`docs/`、`scripts/`、`tests/`
- `package.json`、lock 文件、`requirements.txt`
- `.env.example`、`.gitattributes`、`.gitignore`、`.dockerignore`
- 必要产品资源，例如 logo、字体、图片、短视频；二进制资源通过 Git LFS 管理

不应提交：

- `.env` 或任何包含密钥的文件
- `node_modules/`、`.venv/`、`venv/`、`dist/`
- `storage/`、`models/`、`logs/`、`screenshots/`
- `.idea/`、`.cursor/`、`.codex/`、`.shared/`、`.claude/`、`.agents/`
- `.DS_Store`、`Thumbs.db`

如果这些文件曾被历史提交跟踪过，使用下面命令从 Git 索引移除但保留本地文件：

```powershell
git rm -r --cached --ignore-unmatch .claude .github/prompts .agents .shared .cursor .idea .codex
git commit -m "chore: remove local tool files from git"
```

## 远程验证

登录并配置完成后：

```powershell
git remote -v
git ls-remote --heads origin
git push -u origin main
git push -u origin develop
```

如果 GitHub 提示无权限，确认当前登录账号是 `XXXXXQ-0206`，并检查仓库地址是否为 `https://github.com/XXXXXQ-0206/EduMind.git`。
