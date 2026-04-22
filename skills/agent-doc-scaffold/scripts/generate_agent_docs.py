#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

IGNORED_DIRS = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    ".gradle",
    ".mvn",
    ".next",
    ".turbo",
    ".venv",
    "build",
    "coverage",
    "dist",
    "doc",
    "docs",
    "node_modules",
    "out",
    "target",
    "tmp",
    "vendor",
}

COMMON_MODULE_ROOTS = (
    "packages",
    "apps",
    "services",
    "modules",
    "libs",
    "crates",
    "components",
)

MANIFEST_FILES = (
    "package.json",
    "pnpm-workspace.yaml",
    "turbo.json",
    "nx.json",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "go.mod",
    "Cargo.toml",
    "Makefile",
    "makefile",
    "justfile",
)

COMMAND_ORDER = ("Install", "Build", "Test", "Lint", "Typecheck", "Format", "Dev")
COMMAND_LABELS_ZH = {
    "Install": "安装",
    "Build": "构建",
    "Test": "测试",
    "Lint": "检查",
    "Typecheck": "类型检查",
    "Format": "格式化",
    "Dev": "开发",
}


@dataclass(frozen=True)
class ProjectFacts:
    name: str
    root_manifests: list[str]
    likely_stacks: list[str]
    root_commands: list[tuple[str, str]]
    module_roots: list[str]
    read_first: list[str]
    key_dirs: list[str]


@dataclass(frozen=True)
class ModuleFacts:
    relative_path: str
    manifests: list[str]
    likely_stacks: list[str]
    commands: list[tuple[str, str]]
    key_dirs: list[str]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "为目标仓库生成根 AGENTS.md、精简根 CLAUDE.md、doc/ 下的索引文档，"
            "以及可选的模块级 AGENTS.md。"
        )
    )
    parser.add_argument("project_root", help="目标仓库根目录路径")
    parser.add_argument(
        "--module",
        action="append",
        default=[],
        help="需要生成独立 AGENTS.md 的模块相对路径，可重复传入",
    )
    parser.add_argument(
        "--no-submodules",
        action="store_true",
        help="只生成根级文件，不生成模块级 AGENTS.md",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="覆盖已有文件，而不是跳过",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印将要写入的结果，不实际修改目标仓库",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.is_dir():
        raise SystemExit(f"目标仓库不存在，或给定路径不是目录：{project_root}")

    project = inspect_project(project_root)
    module_paths = resolve_modules(project_root, explicit=args.module, auto=not args.no_submodules)
    modules = [inspect_module(project_root, module_path) for module_path in module_paths]

    writes: list[tuple[Path, str]] = [
        (project_root / "AGENTS.md", render_root_agents(project)),
        (project_root / "CLAUDE.md", render_root_claude()),
        (project_root / "doc" / "agent-doc-index.md", render_index(project, modules)),
    ]

    for module in modules:
        writes.append((project_root / module.relative_path / "AGENTS.md", render_module_agents(module)))

    written: list[Path] = []
    skipped: list[Path] = []
    for path, content in writes:
        did_write = write_file(path=path, content=content, force=args.force, dry_run=args.dry_run)
        (written if did_write else skipped).append(path)

    print(f"目标仓库：{project_root}")
    print(f"模式：{'dry-run' if args.dry_run else 'write'}")
    print("")
    if written:
        print("已生成：")
        for path in written:
            print(f"  - {path.relative_to(project_root)}")
    if skipped:
        print("已跳过现有文件：")
        for path in skipped:
            print(f"  - {path.relative_to(project_root)}")

    return 0


def inspect_project(project_root: Path) -> ProjectFacts:
    root_manifests = detect_manifest_names(project_root)
    likely_stacks = detect_stacks(project_root)
    root_commands = collect_commands(project_root, project_root)
    module_roots = [name for name in COMMON_MODULE_ROOTS if (project_root / name).is_dir()]
    read_first = root_manifests[:]
    key_dirs = top_level_dirs(project_root)
    return ProjectFacts(
        name=project_root.name,
        root_manifests=root_manifests,
        likely_stacks=likely_stacks,
        root_commands=root_commands,
        module_roots=module_roots,
        read_first=read_first,
        key_dirs=key_dirs,
    )


def inspect_module(project_root: Path, module_path: Path) -> ModuleFacts:
    relative_path = module_path.relative_to(project_root).as_posix()
    manifests = detect_manifest_names(module_path)
    likely_stacks = detect_stacks(module_path)
    commands = collect_commands(module_path, project_root)
    key_dirs = top_level_dirs(module_path)
    return ModuleFacts(
        relative_path=relative_path,
        manifests=manifests,
        likely_stacks=likely_stacks,
        commands=commands,
        key_dirs=key_dirs,
    )


def resolve_modules(project_root: Path, explicit: list[str], auto: bool) -> list[Path]:
    modules: set[Path] = set()
    for item in explicit:
        candidate = (project_root / item).resolve()
        if candidate.is_dir():
            modules.add(candidate)
    if auto:
        modules.update(discover_modules(project_root))
    return sorted(modules, key=lambda path: path.relative_to(project_root).as_posix())


def discover_modules(project_root: Path) -> set[Path]:
    discovered: set[Path] = set()
    discovered.update(parse_package_workspaces(project_root))
    discovered.update(parse_pnpm_workspaces(project_root))
    discovered.update(parse_maven_modules(project_root))
    discovered.update(parse_gradle_modules(project_root))

    for root_name in COMMON_MODULE_ROOTS:
        root = project_root / root_name
        if not root.is_dir():
            continue
        for child in root.iterdir():
            if is_candidate_module_dir(child):
                discovered.add(child.resolve())

    for child in project_root.iterdir():
        if is_candidate_module_dir(child):
            discovered.add(child.resolve())

    filtered: set[Path] = set()
    for path in discovered:
        if path == project_root:
            continue
        if any(part in IGNORED_DIRS for part in path.relative_to(project_root).parts):
            continue
        if detect_manifest_names(path):
            filtered.add(path)
    return filtered


def parse_package_workspaces(project_root: Path) -> set[Path]:
    package_json = project_root / "package.json"
    data = load_json(package_json)
    if not data:
        return set()

    workspaces = data.get("workspaces")
    patterns: list[str] = []
    if isinstance(workspaces, list):
        patterns = [item for item in workspaces if isinstance(item, str)]
    elif isinstance(workspaces, dict):
        packages = workspaces.get("packages")
        if isinstance(packages, list):
            patterns = [item for item in packages if isinstance(item, str)]
    return expand_workspace_patterns(project_root, patterns)


def parse_pnpm_workspaces(project_root: Path) -> set[Path]:
    workspace_file = project_root / "pnpm-workspace.yaml"
    if not workspace_file.is_file():
        return set()
    patterns: list[str] = []
    for line in safe_read_text(workspace_file).splitlines():
        match = re.match(r"\s*-\s*['\"]?([^'\"]+)['\"]?\s*$", line)
        if match:
            patterns.append(match.group(1))
    return expand_workspace_patterns(project_root, patterns)


def parse_maven_modules(project_root: Path) -> set[Path]:
    pom_file = project_root / "pom.xml"
    if not pom_file.is_file():
        return set()
    text = safe_read_text(pom_file)
    return {
        (project_root / module.strip()).resolve()
        for module in re.findall(r"<module>\s*([^<]+?)\s*</module>", text)
        if (project_root / module.strip()).is_dir()
    }


def parse_gradle_modules(project_root: Path) -> set[Path]:
    module_paths: set[Path] = set()
    for name in ("settings.gradle", "settings.gradle.kts"):
        settings_file = project_root / name
        if not settings_file.is_file():
            continue
        text = safe_read_text(settings_file)
        for line in text.splitlines():
            if "include" not in line:
                continue
            for token in re.findall(r"['\"]([^'\"]+)['\"]", line):
                normalized = token.strip(":").replace(":", "/")
                candidate = project_root / normalized
                if candidate.is_dir():
                    module_paths.add(candidate.resolve())
    return module_paths


def expand_workspace_patterns(project_root: Path, patterns: Iterable[str]) -> set[Path]:
    resolved: set[Path] = set()
    for pattern in patterns:
        for candidate in project_root.glob(pattern):
            if candidate.is_dir():
                resolved.add(candidate.resolve())
    return resolved


def is_candidate_module_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    if path.name.startswith(".") or path.name in IGNORED_DIRS:
        return False
    return bool(detect_manifest_names(path))


def detect_manifest_names(directory: Path) -> list[str]:
    return [name for name in MANIFEST_FILES if (directory / name).is_file()]


def detect_stacks(directory: Path) -> list[str]:
    stacks: list[str] = []
    manifests = set(detect_manifest_names(directory))
    if "package.json" in manifests:
        stacks.append("Node.js / JavaScript or TypeScript")
    if "pom.xml" in manifests or "build.gradle" in manifests or "build.gradle.kts" in manifests:
        stacks.append("Java / JVM")
    if "pyproject.toml" in manifests or "requirements.txt" in manifests or "setup.py" in manifests:
        stacks.append("Python")
    if "go.mod" in manifests:
        stacks.append("Go")
    if "Cargo.toml" in manifests:
        stacks.append("Rust")
    if "turbo.json" in manifests or "nx.json" in manifests or "pnpm-workspace.yaml" in manifests:
        stacks.append("Workspace / Monorepo")
    return stacks or ["Unknown from top-level manifests"]


def collect_commands(directory: Path, project_root: Path) -> list[tuple[str, str]]:
    candidates: dict[str, tuple[int, str]] = {}

    def add(label: str, command: str, priority: int) -> None:
        current = candidates.get(label)
        if current is None or priority > current[0]:
            candidates[label] = (priority, command)

    make_targets = parse_make_targets(directory / "Makefile")
    make_targets.update(parse_make_targets(directory / "makefile"))
    just_targets = parse_make_targets(directory / "justfile")

    for label, target_names in {
        "Build": ("build", "compile"),
        "Test": ("test", "check"),
        "Lint": ("lint",),
        "Format": ("format", "fmt"),
        "Dev": ("dev", "start", "serve"),
        "Install": ("install", "bootstrap"),
    }.items():
        target = first_target(make_targets, target_names)
        if target:
            add(label, f"make {target}", 110)
        target = first_target(just_targets, target_names)
        if target:
            add(label, f"just {target}", 105)

    package_json = directory / "package.json"
    package_data = load_json(package_json)
    if package_data:
        package_manager = infer_package_manager(directory, project_root)
        scripts = package_data.get("scripts", {})
        if isinstance(scripts, dict):
            if scripts:
                add("Install", install_command(package_manager), 90)
            for script_name, label in {
                "build": "Build",
                "test": "Test",
                "lint": "Lint",
                "typecheck": "Typecheck",
                "format": "Format",
                "dev": "Dev",
                "start": "Dev",
            }.items():
                if script_name in scripts:
                    add(label, run_script_command(package_manager, script_name), 90)

    mvn_wrapper = directory / "mvnw"
    if (directory / "pom.xml").is_file():
        mvn_cmd = "./mvnw" if mvn_wrapper.is_file() else "mvn"
        add("Build", f"{mvn_cmd} -DskipTests package", 80)
        add("Test", f"{mvn_cmd} test", 80)

    gradle_wrapper = directory / "gradlew"
    if (directory / "build.gradle").is_file() or (directory / "build.gradle.kts").is_file():
        gradle_cmd = "./gradlew" if gradle_wrapper.is_file() else "gradle"
        add("Build", f"{gradle_cmd} build", 80)
        add("Test", f"{gradle_cmd} test", 80)

    pyproject = directory / "pyproject.toml"
    if pyproject.is_file() or (directory / "requirements.txt").is_file() or (directory / "setup.py").is_file():
        if (directory / "tests").is_dir() or "pytest" in safe_read_text(pyproject):
            add("Test", "pytest", 70)
        pyproject_text = safe_read_text(pyproject)
        if "ruff" in pyproject_text:
            add("Lint", "ruff check .", 70)
            add("Format", "ruff format .", 70)
        elif "black" in pyproject_text:
            add("Format", "black .", 65)

    if (directory / "go.mod").is_file():
        add("Build", "go build ./...", 70)
        add("Test", "go test ./...", 70)

    if (directory / "Cargo.toml").is_file():
        add("Build", "cargo build", 70)
        add("Test", "cargo test", 70)
        add("Lint", "cargo clippy --all-targets --all-features", 70)
        add("Format", "cargo fmt --all", 70)

    ordered = []
    for label in COMMAND_ORDER:
        current = candidates.get(label)
        if current:
            ordered.append((label, current[1]))
    return ordered


def parse_make_targets(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    targets: set[str] = set()
    for line in safe_read_text(path).splitlines():
        match = re.match(r"^([A-Za-z0-9][A-Za-z0-9_.-]+):(?:\s|$)", line)
        if match and not match.group(1).startswith("."):
            targets.add(match.group(1))
    return targets


def first_target(targets: set[str], names: Iterable[str]) -> str | None:
    for name in names:
        if name in targets:
            return name
    return None


def infer_package_manager(directory: Path, project_root: Path) -> str:
    for current in (directory, project_root):
        package_data = load_json(current / "package.json")
        if package_data:
            package_manager = package_data.get("packageManager")
            if isinstance(package_manager, str):
                normalized = package_manager.split("@", 1)[0].strip()
                if normalized in {"pnpm", "yarn", "npm", "bun"}:
                    return normalized
        if (current / "pnpm-workspace.yaml").is_file():
            return "pnpm"
        if (current / "pnpm-lock.yaml").is_file():
            return "pnpm"
        if (current / "yarn.lock").is_file():
            return "yarn"
        if (current / "bun.lockb").is_file() or (current / "bun.lock").is_file():
            return "bun"
        if (current / "package-lock.json").is_file():
            return "npm"
    return "npm"


def install_command(package_manager: str) -> str:
    return {
        "pnpm": "pnpm install",
        "yarn": "yarn install",
        "bun": "bun install",
    }.get(package_manager, "npm install")


def run_script_command(package_manager: str, script_name: str) -> str:
    return {
        "pnpm": f"pnpm run {script_name}",
        "yarn": f"yarn {script_name}",
        "bun": f"bun run {script_name}",
    }.get(package_manager, f"npm run {script_name}")


def top_level_dirs(directory: Path, limit: int = 6) -> list[str]:
    names = [
        child.name
        for child in sorted(directory.iterdir(), key=lambda item: item.name)
        if child.is_dir() and not child.name.startswith(".") and child.name not in IGNORED_DIRS
    ]
    return names[:limit]


def render_root_agents(project: ProjectFacts) -> str:
    commands = render_commands(project.root_commands)
    read_first = ", ".join(f"`{item}`" for item in project.read_first) or "先检查根目录 manifest 和 README。"
    module_roots = ", ".join(f"`{item}/`" for item in project.module_roots) or "未检测到常见模块根目录。"
    key_dirs = ", ".join(f"`{item}/`" for item in project.key_dirs) or "未检测到明显的顶层目录。"
    manifests = ", ".join(f"`{item}`" for item in project.root_manifests) or "未检测到可识别的根目录 manifest。"
    stacks = ", ".join(project.likely_stacks)
    return (
        f"# {project.name} AGENTS\n\n"
        "这是当前仓库面向编码代理的仓库级规范文件。"
        "共享规则统一维护在这里，`CLAUDE.md` 保持精简，子级 `AGENTS.md` 仅用于补充局部范围说明。\n\n"
        "请将本文件视为活文档：当构建命令、架构、工作流或操作约束发生变化时，应同步更新。\n\n"
        "## 作用域解析\n\n"
        "1. 本文件默认适用于整个仓库。\n"
        "2. 如果更深层目录存在自己的 `AGENTS.md`，则将最近的那份视为额外的局部规范。\n"
        "3. 使用 `doc/agent-doc-index.md` 查找已生成的代理文档及其作用域。\n\n"
        "## 工作规则\n\n"
        "1. 修改前先检查仓库上下文，从 manifest、workspace 配置、入口点和已有测试开始。\n"
        "2. 优先做最小且足够的修改，保持与现有技术栈、命名方式和依赖选择一致。\n"
        "3. 除非任务明确要求调整职责边界，否则不要破坏既有架构分层。\n"
        "4. 对外 API、配置、Schema 和持久化数据默认保持兼容，除非任务允许破坏性变更。\n"
        "5. 完成前使用最小且相关的命令验证被修改的表面。\n\n"
        "## 仓库快照\n\n"
        f"- 优先阅读：{read_first}\n"
        f"- 检测到的 manifest：{manifests}\n"
        f"- 推测技术栈：{stacks}\n"
        f"- 常见模块根目录：{module_roots}\n"
        f"- 顶层关键目录：{key_dirs}\n"
        "- 生成的索引文档：`doc/agent-doc-index.md`\n\n"
        "## 建议命令\n\n"
        f"{commands}\n\n"
        "## 协作方式\n\n"
        "- 修改某个子树前，先阅读最近的 `README`、设计说明和 `AGENTS.md`。\n"
        "- 当项目同时存在本地包装命令和裸工具链命令时，优先使用项目定义的包装命令或 workspace 命令。\n"
        "- 若行为变更涉及同一表面，应同步更新测试、文档和配置。\n"
        "- 避免顺手做与任务无关的重构；相邻问题可单独记录，但不要混进当前改动。\n\n"
        "## 安全要求\n\n"
        "- 除非用户明确要求，否则避免执行破坏性的 git 或文件操作。\n"
        "- 不要直接覆盖用户手写的代理文档；先审阅其意图，再有意识地合并。\n"
        "- 在提示词、日志和生成文档中，避免暴露密钥、凭据和环境特定敏感信息。\n\n"
        "## 完成检查\n\n"
        "- 修改前确认受影响的模块或表面范围。\n"
        "- 加载最近的局部指令文件。\n"
        "- 运行最相关的验证命令，或说明为何未运行。\n"
        "- 总结修改内容、已完成验证以及剩余风险。\n"
    )


def render_root_claude() -> str:
    return (
        "# Claude Instructions\n\n"
        "当前项目的规范主文档位于 `./AGENTS.md`。\n\n"
        "1. 在本仓库内进行规划、编辑或验证之前，先阅读 `./AGENTS.md`。\n"
        "2. 如果你正在编辑的目录下存在更近的 `AGENTS.md`，将其视为额外的局部规范。\n"
        "3. 使用 `doc/agent-doc-index.md` 查找模块级指令文档和相关代理文档。\n"
        "4. 本文件保持精简；共享规则应更新到 `AGENTS.md`，不要在此重复维护。\n"
    )


def render_index(project: ProjectFacts, modules: list[ModuleFacts]) -> str:
    module_lines = (
        "\n".join(
            f"- `{module.relative_path}/AGENTS.md` - 作用域 `{module.relative_path}/`；"
            f"技术栈：{', '.join(module.likely_stacks)}"
            for module in modules
        )
        or "- 未生成模块级 `AGENTS.md` 文件。"
    )
    manifests = ", ".join(f"`{item}`" for item in project.root_manifests) or "未检测到可识别的根目录 manifest。"
    stacks = ", ".join(project.likely_stacks)
    module_roots = ", ".join(f"`{item}/`" for item in project.module_roots) or "未检测到常见模块根目录。"
    return (
        f"# Agent Documentation Index\n\n"
        f"为 `{project.name}` 生成，日期：{date.today().isoformat()}。\n\n"
        "## 核心文件\n\n"
        "- `AGENTS.md` - 编码代理共享的仓库级规范。\n"
        "- `CLAUDE.md` - 面向 Anthropic 生态的精简包装文件，回指 `AGENTS.md`。\n"
        "- `doc/agent-doc-index.md` - 当前索引文档。\n\n"
        "## 作用域解析\n\n"
        "1. 从根 `AGENTS.md` 开始阅读。\n"
        "2. 如果更深层目录存在自己的 `AGENTS.md`，则将最近的那份视为额外的局部规范。\n"
        "3. 共享规则放在根文件，局部规则尽量贴近对应模块。\n\n"
        "## 检测到的仓库事实\n\n"
        f"- 根目录 manifest：{manifests}\n"
        f"- 推测技术栈：{stacks}\n"
        f"- 常见模块根目录：{module_roots}\n\n"
        "## 已生成的模块文件\n\n"
        f"{module_lines}\n\n"
        "## 维护说明\n\n"
        "- 这些文件应保持简洁、直接，并纳入版本控制。\n"
        "- 当命令、架构或操作约束变化时，应同步更新。\n"
        "- 优先在生成的 starter 基础上收紧和修订，而不是把同样的规则复制到多个文件里。\n"
    )


def render_module_agents(module: ModuleFacts) -> str:
    manifests = ", ".join(f"`{item}`" for item in module.manifests) or "未检测到可识别的 manifest。"
    stacks = ", ".join(module.likely_stacks)
    key_dirs = ", ".join(f"`{item}/`" for item in module.key_dirs) or "未检测到明显的子目录。"
    commands = render_commands(module.commands, empty_message="先检查模块 manifest；若缺少明确命令，再回退到仓库根目录命令。")
    return (
        f"# {module.relative_path} AGENTS\n\n"
        f"本文件补充说明 `{module.relative_path}/` 范围内的局部规范。"
        "请先应用根 `AGENTS.md`，再结合本文件理解模块特定上下文。\n\n"
        "## 模块快照\n\n"
        f"- 作用域：`{module.relative_path}/`\n"
        f"- 检测到的 manifest：{manifests}\n"
        f"- 推测技术栈：{stacks}\n"
        f"- 关键目录：{key_dirs}\n\n"
        "## 模块规则\n\n"
        "- 修改尽量限制在当前模块范围内；只有共享接口确实要求联动时，才扩散到其他模块。\n"
        "- 变更导出 API、Schema、事件或配置前，先检查调用方、消费方和共享契约。\n"
        "- 保持与当前模块既有的测试、日志、配置和错误处理模式一致。\n\n"
        "## 建议命令\n\n"
        f"{commands}\n\n"
        "## 验证要求\n\n"
        "- 修改后运行最小且相关的模块级校验命令。\n"
        "- 如果缺少可靠的模块本地命令，则使用仓库根目录的验证流程，并明确说明这一限制。\n"
    )


def render_commands(commands: list[tuple[str, str]], empty_message: str = "先检查仓库自定义脚本或 README，再决定具体命令。") -> str:
    if not commands:
        return f"- {empty_message}"
    return "\n".join(f"- {COMMAND_LABELS_ZH.get(label, label)}: `{command}`" for label, command in commands)


def write_file(path: Path, content: str, force: bool, dry_run: bool) -> bool:
    if path.exists() and not force:
        return False
    if dry_run:
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return True


def safe_read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(safe_read_text(path))
    except json.JSONDecodeError:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
