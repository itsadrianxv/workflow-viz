#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


DEFAULT_DOCS_ROOT = Path("docs/workflow-viz/insights")
DEFAULT_TOP = 5
DEFAULT_THEME = "materia"
MAX_FILE_BYTES = 350_000

ARCHITECTURE_DIAGRAMS = [
    "architecture-context",
    "architecture-modules",
    "architecture-dependencies",
]
CORE_DIAGRAMS = [*ARCHITECTURE_DIAGRAMS, "activity", "sequence"]
LEGACY_ARCHITECTURE_KEYS = ("architecture",)

CHART_TITLES = {
    "architecture-context": "架构总览图",
    "architecture-modules": "模块拆解图",
    "architecture-dependencies": "依赖职责图",
    "activity": "主流程活动图",
    "sequence": "协作顺序图",
    "branch-decision": "分支判定图",
    "state": "状态图",
    "async-concurrency": "异步/并发图",
    "data-flow": "数据/依赖流图",
}

CHART_INTROS = {
    "architecture-context": "图前说明：先看这个文件位于哪一层、被谁触发、向哪些外部角色发起协作。",
    "architecture-modules": "图前说明：这张图把文件内部的关键职责分成几个稳定模块，帮助快速识别边界。",
    "architecture-dependencies": "图前说明：重点看入口如何把职责分派给不同依赖，以及每个依赖承担什么角色。",
    "activity": "图前说明：沿着主入口顺序阅读，先建立正常路径的执行心智模型。",
    "sequence": "图前说明：这张图强调调用时序，适合定位谁先发起、谁后响应、哪里容易串线。",
    "branch-decision": "图前说明：把主要分支和守卫条件单独抽出来，便于区分正常路径与特殊路径。",
    "state": "图前说明：当文件存在状态切换时，优先看清每个阶段之间如何流转。",
    "async-concurrency": "图前说明：这张图专门突出异步触发、并发协作和等待回收的关系。",
    "data-flow": "图前说明：按数据从输入到输出的流向阅读，能更快看清中间变换链路。",
}

CHART_OUTROS = {
    "architecture-context": "图后解读：补全真实调用方、外部系统和边界约束后，这张图应能回答“它在整体架构中的位置”。",
    "architecture-modules": "图后解读：补齐真实模块名称后，这张图应能回答“内部职责如何拆分，哪些模块不要混改”。",
    "architecture-dependencies": "图后解读：补齐真实依赖职责后，这张图应能回答“入口是如何协调多个依赖完成任务的”。",
    "activity": "图后解读：把真实输入、关键判定和产出补进去后，这张图应能回答“正常流程到底怎么走”。",
    "sequence": "图后解读：把真实协作者和消息名补进去后，这张图应能回答“关键协作顺序是否符合预期”。",
    "branch-decision": "图后解读：把真实条件替换进去后，这张图应能回答“哪些条件最容易引发路径分叉”。",
    "state": "图后解读：把真实状态和值守条件补齐后，这张图应能回答“状态变更的触发器和退出点是什么”。",
    "async-concurrency": "图后解读：把真实队列、回调和等待点补进去后，这张图应能回答“并发协调风险集中在哪”。",
    "data-flow": "图后解读：把真实数据对象补齐后，这张图应能回答“数据在各协作者之间怎样被加工和交付”。",
}

LANGUAGE_BY_EXTENSION = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".java": "java",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".kt": "kotlin",
    ".rs": "rust",
    ".swift": "swift",
}

EXCLUDED_DIRS = {
    ".agents",
    ".claude",
    ".codex",
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".next",
    ".nuxt",
    ".turbo",
    ".cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "coverage",
    "tmp",
    "temp",
    "__pycache__",
}

EXCLUDED_FILE_PATTERNS = (
    re.compile(r".*\.min\.(js|css)$", re.IGNORECASE),
    re.compile(r".*\.bundle\.(js|css)$", re.IGNORECASE),
    re.compile(r".*\.lock$", re.IGNORECASE),
    re.compile(r".*package-lock\.json$", re.IGNORECASE),
    re.compile(r".*pnpm-lock\.yaml$", re.IGNORECASE),
    re.compile(r".*yarn\.lock$", re.IGNORECASE),
    re.compile(r".*Cargo\.lock$", re.IGNORECASE),
    re.compile(r".*poetry\.lock$", re.IGNORECASE),
    re.compile(r".*\.snap$", re.IGNORECASE),
    re.compile(r".*generated.*", re.IGNORECASE),
    re.compile(r".*\.pb\.(go|py|ts|js|java)$", re.IGNORECASE),
)

FUNCTION_PATTERNS = (
    re.compile(r"^\s*(?:async\s+)?function\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE),
    re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_]\w*)\s*=\s*(?:async\s*)?\(", re.MULTILINE),
    re.compile(r"^\s*(?:export\s+default\s+)?(?:async\s+)?([A-Za-z_]\w*)\s*=\s*\(", re.MULTILINE),
    re.compile(r"^\s*func\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE),
    re.compile(r"^\s*def\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE),
    re.compile(
        r"^\s*(?:public|private|protected|internal|static|final|async|\s)+"
        r"(?:[A-Za-z_<>\[\],?]+\s+)+([A-Za-z_]\w*)\s*\(",
        re.MULTILINE,
    ),
)

DECISION_RE = re.compile(
    r"\b(if|elif|else\s+if|for|while|switch|case|catch|except|when|match)\b",
    re.IGNORECASE,
)
CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([A-Za-z0-9_./]+)\s+import|import\s+([A-Za-z0-9_., ]+)|"
    r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)|use\s+([A-Za-z0-9_.:]+))",
    re.MULTILINE,
)
STRING_LITERAL_RE = re.compile(r"['\"]([A-Za-z][A-Za-z0-9_-]{1,30})['\"]")
STATE_VAR_RE = re.compile(r"\b(state|status|phase|mode|stage|lifecycle)\b", re.IGNORECASE)
TRANSITION_RE = re.compile(
    r"\b(transition|advance|enter|leave|activate|deactivate|pause|resume|expire|"
    r"expired|start|stop|rollback|switch|promote|demote|restore|shutdown)\b",
    re.IGNORECASE,
)
DATA_FLOW_RE = re.compile(
    r"\b(map|reduce|filter|transform|serialize|deserialize|parse|build|merge|join|"
    r"aggregate|collect|normalize|convert|emit|publish)\b",
    re.IGNORECASE,
)

ASYNC_CATEGORY_PATTERNS = {
    "async-await": (
        re.compile(r"\basync\b", re.IGNORECASE),
        re.compile(r"\bawait\b", re.IGNORECASE),
    ),
    "promise": (
        re.compile(r"\bPromise\b", re.IGNORECASE),
        re.compile(r"\.then\s*\(", re.IGNORECASE),
        re.compile(r"\.catch\s*\(", re.IGNORECASE),
        re.compile(r"\.finally\s*\(", re.IGNORECASE),
    ),
    "events": (
        re.compile(r"\b(event|emit|listener|subscribe|publish|dispatchEvent|addEventListener)\b", re.IGNORECASE),
    ),
    "queue-worker": (
        re.compile(r"\b(queue|worker|scheduler|cron|job|task\s*queue)\b", re.IGNORECASE),
    ),
    "thread-lock": (
        re.compile(r"\b(thread|mutex|lock|semaphore|channel|goroutine|parallel)\b", re.IGNORECASE),
    ),
    "timers-retry": (
        re.compile(r"\b(timeout|timer|interval|retry|backoff|sleep|delay)\b", re.IGNORECASE),
    ),
    "fan-in-out": (
        re.compile(r"\b(gather|race|fan[- ]?out|fan[- ]?in|concurrent|parallel)\b", re.IGNORECASE),
        re.compile(r"\bPromise\.all\b", re.IGNORECASE),
        re.compile(r"\bPromise\.race\b", re.IGNORECASE),
    ),
}

COORDINATION_PATTERNS = (
    re.compile(r"\b(gather|wait|join|race|mutex|lock|semaphore|channel|queue|worker)\b", re.IGNORECASE),
    re.compile(r"\b(retry|backoff|timeout|cancel|throttle|debounce)\b", re.IGNORECASE),
    re.compile(r"\b(subscribe|publish|emit|listener|dispatcher)\b", re.IGNORECASE),
)

ROLE_HINT_TOKENS = (
    "workflow",
    "orchestrator",
    "pipeline",
    "controller",
    "handler",
    "dispatch",
    "execute",
    "process",
    "run",
)

ENTRYPOINT_HINTS = (
    "run",
    "execute",
    "process",
    "handle",
    "main",
    "dispatch",
    "orchestrate",
)

MARKDOWN_TEMPLATE_HINT = """\
这是一份以图为主的脚手架文档。请先补齐图中的真实角色、依赖和路径，再在每张图两侧补充贴图解释。
"""


@dataclass
class FunctionMetrics:
    name: str
    complexity: int
    max_nesting: int
    decisions: int
    early_exits: int
    exception_handlers: int
    distinct_calls: int
    call_count: int
    async_markers: int
    start_line: int
    end_line: int

    def summary(self) -> str:
        return (
            f"{self.name} (cc={self.complexity}, nest={self.max_nesting}, "
            f"decisions={self.decisions}, calls={self.distinct_calls})"
        )


@dataclass
class FileMetrics:
    path: Path
    relative_path: Path
    language: str
    loc: int
    functions: list[FunctionMetrics]
    import_count: int
    cross_module_refs: int
    async_categories: set[str]
    async_coordination: bool
    async_marker_total: int
    state_count: int
    transition_count: int
    exception_paths: int
    role_hints: set[str]
    data_flow_markers: int
    entrypoint: str
    explicit_target: bool = False


@dataclass
class AnalysisResult:
    metrics: FileMetrics
    strong_signals: list[str]
    medium_signals: list[str]
    gate_passed: bool
    score: int
    score_breakdown: dict[str, int]
    recommended_diagrams: list[str]
    top_functions: list[FunctionMetrics]
    watchlist: bool
    selected: bool
    selection_reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.metrics.relative_path.as_posix(),
            "language": self.metrics.language,
            "loc": self.metrics.loc,
            "score": self.score,
            "watchlist": self.watchlist,
            "selected": self.selected,
            "selection_reason": self.selection_reason,
            "gate_passed": self.gate_passed,
            "strong_signals": self.strong_signals,
            "medium_signals": self.medium_signals,
            "recommended_diagrams": self.recommended_diagrams,
            "entrypoint": self.metrics.entrypoint,
            "top_functions": [fn.summary() for fn in self.top_functions],
            "score_breakdown": self.score_breakdown,
        }


@dataclass
class PlantUMLRuntime:
    mode: str
    command: str | None = None
    jar_path: Path | None = None
    source: str = ""

    def version(self) -> str:
        if self.mode == "command":
            result = subprocess.run(
                f'{self.command} -version',
                shell=True,
                check=True,
                capture_output=True,
                text=True,
            )
        else:
            result = subprocess.run(
                ["java", "-jar", str(self.jar_path), "-version"],
                check=True,
                capture_output=True,
                text=True,
            )
        return (result.stdout or result.stderr).strip()

    def render(self, source_file: Path, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        if self.mode == "command":
            subprocess.run(
                f'{self.command} -tsvg -o "{output_dir}" "{source_file}"',
                shell=True,
                check=True,
                capture_output=True,
                text=True,
            )
            return
        subprocess.run(
            ["java", "-jar", str(self.jar_path), "-tsvg", "-o", str(output_dir), str(source_file)],
            check=True,
            capture_output=True,
            text=True,
        )


class PythonFunctionAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.decisions = 0
        self.early_exits = 0
        self.exception_handlers = 0
        self.call_names: set[str] = set()
        self.call_count = 0
        self.async_markers = 0
        self.max_nesting = 0
        self._nesting = 0

    def visit_If(self, node: ast.If) -> None:
        self.decisions += 1
        self._visit_nested(node)

    def visit_For(self, node: ast.For) -> None:
        self.decisions += 1
        self._visit_nested(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.decisions += 1
        self.async_markers += 1
        self._visit_nested(node)

    def visit_While(self, node: ast.While) -> None:
        self.decisions += 1
        self._visit_nested(node)

    def visit_Match(self, node: ast.Match) -> None:
        self.decisions += max(len(node.cases), 1)
        self._visit_nested(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self.decisions += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self.decisions += max(len(node.values) - 1, 0)
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        self.decisions += len(node.ifs)
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        self.exception_handlers += len(node.handlers)
        self._visit_nested(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.exception_handlers += 1
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        self.early_exits += 1
        self.generic_visit(node)

    def visit_Break(self, node: ast.Break) -> None:
        self.early_exits += 1

    def visit_Continue(self, node: ast.Continue) -> None:
        self.early_exits += 1

    def visit_Raise(self, node: ast.Raise) -> None:
        self.early_exits += 1
        self.generic_visit(node)

    def visit_Await(self, node: ast.Await) -> None:
        self.async_markers += 1
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self.async_markers += 1
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        call_name = get_call_name(node.func)
        if call_name:
            self.call_names.add(call_name)
        self.call_count += 1
        self.generic_visit(node)

    def _visit_nested(self, node: ast.AST) -> None:
        self._nesting += 1
        self.max_nesting = max(self.max_nesting, self._nesting)
        self.generic_visit(node)
        self._nesting -= 1


class PythonFunctionCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.current_class: list[str] = []
        self.functions: list[tuple[str, ast.AST]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.current_class.append(node.name)
        self.generic_visit(node)
        self.current_class.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.append((self._qualify(node.name), node))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.functions.append((self._qualify(node.name), node))
        self.generic_visit(node)

    def _qualify(self, name: str) -> str:
        if self.current_class:
            return ".".join([*self.current_class, name])
        return name


def clamp01(value: float) -> float:
    return max(0.0, min(value, 1.0))


def normalize(value: float, target: float) -> float:
    if target <= 0:
        return 0.0
    return clamp01(value / target)


def count_non_empty_loc(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def language_for_path(path: Path) -> str:
    return LANGUAGE_BY_EXTENSION.get(path.suffix.lower(), "generic")


def is_supported_source(path: Path) -> bool:
    return path.suffix.lower() in LANGUAGE_BY_EXTENSION


def path_is_excluded(path: Path, repo_root: Path) -> bool:
    lowered_parts = {part.lower() for part in path.relative_to(repo_root).parts[:-1]}
    if lowered_parts & EXCLUDED_DIRS:
        return True
    relative_str = path.relative_to(repo_root).as_posix().lower()
    if relative_str.startswith("docs/workflow-viz/"):
        return True
    return any(pattern.match(path.name) for pattern in EXCLUDED_FILE_PATTERNS)


def discover_candidate_files(repo_root: Path, explicit_paths: Sequence[str] | None = None) -> list[Path]:
    resolved: list[Path] = []
    seen: set[Path] = set()

    def add_candidate(path: Path, explicit: bool = False) -> None:
        candidate = path.resolve()
        if candidate in seen or not candidate.is_file():
            return
        if candidate.stat().st_size > MAX_FILE_BYTES:
            return
        if explicit:
            if is_supported_source(candidate):
                seen.add(candidate)
                resolved.append(candidate)
            return
        if is_supported_source(candidate) and not path_is_excluded(candidate, repo_root):
            seen.add(candidate)
            resolved.append(candidate)

    if explicit_paths:
        for raw in explicit_paths:
            candidate = Path(raw)
            if not candidate.is_absolute():
                candidate = repo_root / candidate
            candidate = candidate.resolve()
            if candidate.is_dir():
                for nested in candidate.rglob("*"):
                    if nested.is_file():
                        add_candidate(nested, explicit=False)
                continue
            add_candidate(candidate, explicit=True)
        return sorted(resolved)

    for path in repo_root.rglob("*"):
        if path.is_file():
            add_candidate(path)
    return sorted(resolved)


def get_call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = get_call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return get_call_name(node.func)
    return ""


def analyze_python(text: str, relative_path: Path) -> tuple[list[FunctionMetrics], int, int, str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return analyze_generic_functions(text, relative_path.stem)

    collector = PythonFunctionCollector()
    collector.visit(tree)

    functions: list[FunctionMetrics] = []
    imported_modules: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module.split(".")[0])

    for name, node in collector.functions:
        analyzer = PythonFunctionAnalyzer()
        analyzer.visit(node)
        functions.append(
            FunctionMetrics(
                name=name,
                complexity=1 + analyzer.decisions,
                max_nesting=analyzer.max_nesting,
                decisions=analyzer.decisions,
                early_exits=analyzer.early_exits,
                exception_handlers=analyzer.exception_handlers,
                distinct_calls=len(analyzer.call_names),
                call_count=analyzer.call_count,
                async_markers=analyzer.async_markers,
                start_line=getattr(node, "lineno", 1),
                end_line=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
            )
        )

    entrypoint = choose_entrypoint(functions, relative_path.stem)
    return functions, len(imported_modules), len(imported_modules), entrypoint


def analyze_generic_functions(text: str, fallback_name: str) -> tuple[list[FunctionMetrics], int, int, str]:
    line_starts: list[tuple[int, str]] = []
    lines = text.splitlines()
    for index, line in enumerate(lines, start=1):
        for pattern in FUNCTION_PATTERNS:
            match = pattern.match(line)
            if match:
                line_starts.append((index, match.group(1)))
                break

    if not line_starts:
        snippet_metrics = analyze_generic_snippet(text, fallback_name, 1, len(lines) or 1)
        imports = estimate_imports(text)
        return [snippet_metrics], imports, imports, snippet_metrics.name

    functions: list[FunctionMetrics] = []
    for idx, (start_line, name) in enumerate(line_starts):
        end_line = (line_starts[idx + 1][0] - 1) if idx + 1 < len(line_starts) else len(lines)
        snippet = "\n".join(lines[start_line - 1 : end_line])
        functions.append(analyze_generic_snippet(snippet, name, start_line, end_line))
    entrypoint = choose_entrypoint(functions, fallback_name)
    imports = estimate_imports(text)
    return functions, imports, imports, entrypoint


def analyze_generic_snippet(text: str, name: str, start_line: int, end_line: int) -> FunctionMetrics:
    decisions = len(DECISION_RE.findall(text))
    decisions += text.count("&&") + text.count("||")
    decisions += len(re.findall(r"\band\b|\bor\b", text, re.IGNORECASE))
    call_names = {
        match.group(1)
        for match in CALL_RE.finditer(text)
        if match.group(1).lower() not in {"if", "for", "while", "switch", "catch", "return"}
    }
    return FunctionMetrics(
        name=name,
        complexity=1 + decisions,
        max_nesting=estimate_brace_nesting(text),
        decisions=decisions,
        early_exits=len(re.findall(r"\b(return|break|continue|throw|raise)\b", text, re.IGNORECASE)),
        exception_handlers=len(
            re.findall(r"\b(catch|except|retry|fallback|degrad|recover|timeout)\b", text, re.IGNORECASE)
        ),
        distinct_calls=len(call_names),
        call_count=len(list(CALL_RE.finditer(text))),
        async_markers=len(
            re.findall(
                r"\b(async|await|Promise|event|listener|queue|worker|scheduler|thread|lock|"
                r"mutex|semaphore|channel|timeout|retry|backoff|gather|race)\b",
                text,
                re.IGNORECASE,
            )
        ),
        start_line=start_line,
        end_line=end_line,
    )


def estimate_imports(text: str) -> int:
    modules: set[str] = set()
    for match in IMPORT_RE.finditer(text):
        raw = next((group for group in match.groups() if group), "")
        for piece in re.split(r"[, ]+", raw):
            piece = piece.strip().strip("\"'")
            if piece:
                modules.add(piece.split(".")[0].split("/")[0])
    return len(modules)


def estimate_brace_nesting(text: str) -> int:
    depth = 0
    maximum = 0
    for char in text:
        if char == "{":
            depth += 1
            maximum = max(maximum, depth)
        elif char == "}":
            depth = max(depth - 1, 0)
    if maximum:
        return maximum
    indent_depth = 0
    for line in text.splitlines():
        stripped = line.lstrip()
        if not stripped:
            continue
        if re.match(r"(if|elif|for|while|else|case|catch|except)\b", stripped):
            indent_depth = max(indent_depth, (len(line) - len(stripped)) // 4 + 1)
    return indent_depth


def choose_entrypoint(functions: Sequence[FunctionMetrics], fallback: str) -> str:
    if not functions:
        return fallback
    for hint in ENTRYPOINT_HINTS:
        for function in functions:
            if function.name.lower().endswith(hint):
                return function.name
    for function in functions:
        if not function.name.split(".")[-1].startswith("_"):
            return function.name
    return functions[0].name


def detect_async_categories(text: str) -> tuple[set[str], bool]:
    categories = {
        name
        for name, patterns in ASYNC_CATEGORY_PATTERNS.items()
        if any(pattern.search(text) for pattern in patterns)
    }
    coordination = any(pattern.search(text) for pattern in COORDINATION_PATTERNS)
    return categories, coordination


def detect_state_metrics(text: str) -> tuple[int, int]:
    states: set[str] = set()
    transitions = 0
    for line in text.splitlines():
        if not STATE_VAR_RE.search(line):
            continue
        for match in STRING_LITERAL_RE.finditer(line):
            states.add(match.group(1).lower())
        if TRANSITION_RE.search(line):
            transitions += 1
        if re.search(r"(==|!=|=|:=|=>)", line):
            transitions += 1
    return len(states), transitions


def detect_exception_paths(text: str) -> int:
    categories = 0
    if re.search(r"\b(except|catch)\b", text, re.IGNORECASE):
        categories += 1
    if re.search(r"\b(retry|backoff)\b", text, re.IGNORECASE):
        categories += 1
    if re.search(r"\b(fallback|degrad|recover|graceful)\b", text, re.IGNORECASE):
        categories += 1
    if re.search(r"\b(timeout|cancel|abort)\b", text, re.IGNORECASE):
        categories += 1
    if re.search(r"\b(raise|throw)\b", text, re.IGNORECASE):
        categories += 1
    return categories


def detect_role_hints(text: str, relative_path: Path, entrypoint: str) -> set[str]:
    haystack = f"{relative_path.as_posix()} {entrypoint} {text[:2000]}".lower()
    return {token for token in ROLE_HINT_TOKENS if token in haystack}


def analyze_file(path: Path, repo_root: Path, explicit_target: bool = False) -> FileMetrics:
    text = read_text(path)
    language = language_for_path(path)
    relative_path = path.relative_to(repo_root)
    if language == "python":
        functions, import_count, cross_module_refs, entrypoint = analyze_python(text, relative_path)
    else:
        functions, import_count, cross_module_refs, entrypoint = analyze_generic_functions(text, relative_path.stem)

    async_categories, async_coordination = detect_async_categories(text)
    state_count, transition_count = detect_state_metrics(text)
    return FileMetrics(
        path=path,
        relative_path=relative_path,
        language=language,
        loc=count_non_empty_loc(text),
        functions=functions,
        import_count=import_count,
        cross_module_refs=cross_module_refs,
        async_categories=async_categories,
        async_coordination=async_coordination,
        async_marker_total=sum(function.async_markers for function in functions),
        state_count=state_count,
        transition_count=transition_count,
        exception_paths=max(detect_exception_paths(text), max((fn.exception_handlers for fn in functions), default=0)),
        role_hints=detect_role_hints(text, relative_path, entrypoint),
        data_flow_markers=len(DATA_FLOW_RE.findall(text)),
        entrypoint=entrypoint,
        explicit_target=explicit_target,
    )


def evaluate_file(metrics: FileMetrics) -> AnalysisResult:
    top_functions = sorted(
        metrics.functions,
        key=lambda item: (item.complexity, item.max_nesting, item.decisions, item.distinct_calls),
        reverse=True,
    )[:3]
    peak = top_functions[0] if top_functions else FunctionMetrics("<module>", 1, 0, 0, 0, 0, 0, 0, 0, 1, 1)

    strong_signals: list[str] = []
    medium_signals: list[str] = []

    if peak.complexity >= 10:
        strong_signals.append(f"峰值函数圈复杂度 >= 10 ({peak.name}={peak.complexity})")
    elif peak.complexity >= 7:
        medium_signals.append(f"峰值函数圈复杂度 >= 7 ({peak.name}={peak.complexity})")

    if peak.max_nesting >= 4 and peak.decisions >= 6:
        strong_signals.append(
            f"嵌套深度 >= 4 且判定点 >= 6 ({peak.name}: nesting={peak.max_nesting}, decisions={peak.decisions})"
        )
    elif peak.max_nesting >= 3 and peak.decisions >= 4:
        medium_signals.append(
            f"嵌套深度 >= 3 且判定点 >= 4 ({peak.name}: nesting={peak.max_nesting}, decisions={peak.decisions})"
        )

    if metrics.state_count >= 4 or metrics.transition_count >= 6:
        strong_signals.append(
            f"显式状态/生命周期复杂 ({metrics.state_count} states, {metrics.transition_count} transitions)"
        )
    elif metrics.state_count >= 3 or metrics.transition_count >= 4:
        medium_signals.append(
            f"存在状态/阶段切换 ({metrics.state_count} states, {metrics.transition_count} transitions)"
        )

    if metrics.exception_paths >= 3:
        strong_signals.append(f"异常/重试/降级路径 >= 3 ({metrics.exception_paths})")
    elif metrics.exception_paths >= 2:
        medium_signals.append(f"异常/重试/降级路径 >= 2 ({metrics.exception_paths})")

    if peak.call_count >= 5 and peak.decisions >= 2:
        strong_signals.append(f"主编排函数存在 >= 5 个顺序步骤 ({peak.name} calls={peak.call_count})")
    elif peak.call_count >= 4 and peak.early_exits >= 1:
        medium_signals.append(f"主编排函数存在 >= 4 个顺序步骤且有提前退出 ({peak.name})")

    if len(metrics.async_categories) >= 3 and metrics.async_coordination:
        strong_signals.append(f"异步/并发模式极强（类别数={len(metrics.async_categories)}，且存在协调控制）")

    if peak.distinct_calls >= 6 and metrics.cross_module_refs >= 3:
        strong_signals.append(
            f"单入口协调 >= 6 个协作者且跨 >= 3 模块 ({peak.name}: 协作者={peak.distinct_calls}, 模块={metrics.cross_module_refs})"
        )

    gate_passed = bool(strong_signals or len(medium_signals) >= 2 or metrics.explicit_target)

    structure_raw = (
        normalize(peak.complexity, 10) * 0.24
        + normalize(peak.max_nesting, 4) * 0.16
        + normalize(peak.decisions, 6) * 0.16
        + normalize(metrics.exception_paths, 3) * 0.14
        + normalize(max(metrics.state_count / 4.0, metrics.transition_count / 6.0), 1) * 0.15
        + normalize(peak.call_count, 5) * 0.15
    )
    collaboration_raw = (
        normalize(peak.distinct_calls, 6) * 0.45
        + normalize(metrics.cross_module_refs, 3) * 0.30
        + normalize(metrics.import_count, 6) * 0.10
        + normalize(metrics.data_flow_markers, 4) * 0.15
    )
    async_raw = (
        normalize(len(metrics.async_categories), 3) * 0.5
        + (0.25 if metrics.async_coordination else 0.0)
        + normalize(metrics.async_marker_total, 6) * 0.25
    )
    role_raw = normalize(len(metrics.role_hints), 3)

    breakdown = {
        "structure": int(round(structure_raw * 45)),
        "collaboration": int(round(collaboration_raw * 20)),
        "async": int(round(async_raw * 20)),
        "role_hint": int(round(role_raw * 15)),
    }
    score = sum(breakdown.values())
    watchlist = score >= 50
    selected = score >= 60 or metrics.explicit_target
    if metrics.explicit_target and score < 60:
        selection_reason = "explicit"
    elif score >= 60:
        selection_reason = "hotspot"
    elif score >= 50:
        selection_reason = "watchlist"
    else:
        selection_reason = "below-threshold"

    recommended_diagrams = [*CORE_DIAGRAMS]
    if peak.decisions >= 4 or peak.max_nesting >= 3 or metrics.exception_paths >= 2:
        recommended_diagrams.append("branch-decision")
    if metrics.state_count >= 3 or metrics.transition_count >= 4:
        recommended_diagrams.append("state")
    if len(metrics.async_categories) >= 2 or metrics.async_coordination:
        recommended_diagrams.append("async-concurrency")
    if metrics.cross_module_refs >= 3 or metrics.data_flow_markers >= 3:
        recommended_diagrams.append("data-flow")

    return AnalysisResult(
        metrics=metrics,
        strong_signals=strong_signals,
        medium_signals=medium_signals,
        gate_passed=gate_passed,
        score=score,
        score_breakdown=breakdown,
        recommended_diagrams=recommended_diagrams,
        top_functions=top_functions,
        watchlist=watchlist,
        selected=selected,
        selection_reason=selection_reason,
    )


def analyze_repository(repo_root: Path, explicit_paths: Sequence[str] | None = None) -> list[AnalysisResult]:
    explicit_resolved: set[Path] = set()
    if explicit_paths:
        for raw in explicit_paths:
            candidate = Path(raw)
            if not candidate.is_absolute():
                candidate = repo_root / candidate
            if candidate.exists():
                explicit_resolved.add(candidate.resolve())

    results: list[AnalysisResult] = []
    for path in discover_candidate_files(repo_root, explicit_paths):
        metrics = analyze_file(path, repo_root, explicit_target=path.resolve() in explicit_resolved)
        results.append(evaluate_file(metrics))
    results.sort(
        key=lambda item: (item.selected, item.watchlist, item.gate_passed, item.score, -item.metrics.loc),
        reverse=True,
    )
    return results


def resolve_runtime(repo_root: Path) -> tuple[PlantUMLRuntime | None, list[str]]:
    notes: list[str] = []
    plantuml_command = os.environ.get("PLANTUML_COMMAND", "").strip()
    if plantuml_command:
        runtime = PlantUMLRuntime(mode="command", command=plantuml_command, source="PLANTUML_COMMAND")
        try:
            runtime.version()
            return runtime, notes
        except Exception as exc:  # noqa: BLE001
            notes.append(f"PLANTUML_COMMAND exists but failed: {exc}")

    plantuml_jar = os.environ.get("PLANTUML_JAR", "").strip()
    if plantuml_jar:
        jar_path = Path(plantuml_jar)
        if jar_path.exists():
            runtime = PlantUMLRuntime(mode="jar", jar_path=jar_path, source="PLANTUML_JAR")
            try:
                runtime.version()
                return runtime, notes
            except Exception as exc:  # noqa: BLE001
                notes.append(f"PLANTUML_JAR exists but failed: {exc}")
        else:
            notes.append(f"PLANTUML_JAR not found: {jar_path}")

    command_path = shutil.which("plantuml")
    if command_path:
        runtime = PlantUMLRuntime(mode="command", command=command_path, source="PATH")
        try:
            runtime.version()
            return runtime, notes
        except Exception as exc:  # noqa: BLE001
            notes.append(f"plantuml on PATH failed: {exc}")

    common_jars = [
        Path.home() / "tools" / "plantuml" / "plantuml.jar",
        repo_root / ".tools" / "plantuml" / "plantuml.jar",
        repo_root / "tools" / "plantuml" / "plantuml.jar",
    ]
    for jar_path in common_jars:
        if not jar_path.exists():
            continue
        runtime = PlantUMLRuntime(mode="jar", jar_path=jar_path, source=str(jar_path))
        try:
            runtime.version()
            return runtime, notes
        except Exception as exc:  # noqa: BLE001
            notes.append(f"PlantUML jar at {jar_path} failed: {exc}")

    return None, notes


def run_doctor(repo_root: Path) -> int:
    print(f"Repo root: {repo_root}")
    java_path = shutil.which("java")
    print(f"Java: {'found at ' + java_path if java_path else 'missing'}")

    runtime, notes = resolve_runtime(repo_root)
    if notes:
        print("Notes:")
        for note in notes:
            print(f"- {note}")

    if runtime is None:
        print("PlantUML runtime: missing")
        print("Fix suggestions:")
        print("- Set PLANTUML_COMMAND to a working plantuml executable or wrapper.")
        print("- Or set PLANTUML_JAR to a PlantUML jar file path.")
        print("- Or install plantuml on PATH.")
        return 1

    print(f"PlantUML runtime: {runtime.source}")
    try:
        print(runtime.version().splitlines()[0])
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to query PlantUML version: {exc}")
        return 1

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "doctor-diagram.puml"
            output_dir = temp_path / "charts"
            source.write_text("@startuml\nAlice -> Bob : health check\n@enduml\n", encoding="utf-8")
            runtime.render(source, output_dir)
            expected = output_dir / "doctor-diagram.svg"
            if not expected.exists():
                print(f"Render test failed: expected {expected}")
                return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Render test failed: {exc}")
        print("Check Java, PlantUML, and Graphviz configuration, then rerun doctor.")
        return 1

    print("Render test: OK")
    return 0


def render_scan_text(results: Sequence[AnalysisResult], top: int) -> str:
    shown = list(results[:top])
    if not shown:
        return "没有找到候选文件。"

    lines: list[str] = []
    for index, result in enumerate(shown, start=1):
        status = "热点" if result.score >= 60 else "观察名单" if result.watchlist else "候选"
        if result.metrics.explicit_target and result.score < 60:
            status = "显式指定"
        lines.extend(
            [
                f"{index}. {result.metrics.relative_path.as_posix()}",
                f"   分数={result.score} 状态={status} 门控={'通过' if result.gate_passed else '未过'}",
                f"   主入口={result.metrics.entrypoint}",
                f"   推荐图={', '.join(chart_title(key) for key in result.recommended_diagrams)}",
                f"   关键函数={'; '.join(fn.summary() for fn in result.top_functions)}",
            ]
        )
        if result.strong_signals:
            lines.append(f"   强信号={'; '.join(result.strong_signals)}")
        if result.medium_signals:
            lines.append(f"   中信号={'; '.join(result.medium_signals)}")
    return "\n".join(lines)


def render_scan_json(results: Sequence[AnalysisResult], top: int) -> str:
    return json.dumps([result.to_dict() for result in results[:top]], ensure_ascii=False, indent=2)


def slug_for_path(relative_path: Path) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", relative_path.as_posix().lower()).strip("-")
    digest = hashlib.sha1(relative_path.as_posix().encode("utf-8")).hexdigest()[:8]
    return f"{base}-{digest}" if base else digest


def chart_title(diagram_key: str) -> str:
    return CHART_TITLES[diagram_key]


def chart_intro(diagram_key: str) -> str:
    return CHART_INTROS[diagram_key]


def chart_outro(diagram_key: str) -> str:
    return CHART_OUTROS[diagram_key]


def emit_theme(theme: str) -> str:
    if theme.lower() == "none":
        return ""
    return f"!theme {theme}\n"


def write_if_changed(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    path.write_text(content, encoding="utf-8")


def build_markdown(result: AnalysisResult, slug: str) -> str:
    reasons = result.strong_signals or result.medium_signals or ["用户显式指定"]
    highlights = "；".join(reasons[:3])

    def image_block(diagram_key: str, heading_level: str) -> list[str]:
        return [
            f"{heading_level} {chart_title(diagram_key)}",
            "",
            chart_intro(diagram_key),
            "",
            f"![{chart_title(diagram_key)}](./charts/{slug}-{diagram_key}.svg)",
            "",
            chart_outro(diagram_key),
            "",
        ]

    lines = [
        f"# 热点洞察：{result.metrics.relative_path.name}",
        "",
        f"- 源文件: `{result.metrics.relative_path.as_posix()}`",
        f"- 热点分数: `{result.score}`",
        f"- 主入口: `{result.metrics.entrypoint}`",
        f"- 触发原因: `{highlights}`",
        "",
        MARKDOWN_TEMPLATE_HINT.strip(),
        "",
        "开头引导：先看下面这组架构图，建立这个热点文件所在位置、内部拆分和依赖职责的整体轮廓，再进入流程细节。",
        "",
        "## 架构图组",
        "",
        "这一组图默认优先生成，用来回答“它在系统哪里、内部怎么分、依赖如何协作”。",
        "",
    ]
    for diagram_key in ARCHITECTURE_DIAGRAMS:
        if diagram_key in result.recommended_diagrams:
            lines.extend(image_block(diagram_key, "###"))

    for diagram_key in result.recommended_diagrams:
        if diagram_key in ARCHITECTURE_DIAGRAMS:
            continue
        lines.extend(
            [
                f"## {chart_title(diagram_key)}",
                "",
            ]
        )
        lines.extend(image_block(diagram_key, "###"))

    lines.extend(
        [
            "结尾总结：补齐真实角色名称、关键条件和产出物后，这一页应能让人先通过图建立心智模型，再回到源码核对细节。",
            "",
        ]
    )
    return "\n".join(lines)


def build_plantuml(result: AnalysisResult, diagram_key: str, theme: str = DEFAULT_THEME) -> str:
    del result
    title = chart_title(diagram_key)
    header = f"@startuml\n{emit_theme(theme)}title {title}\n"

    if diagram_key == "architecture-context":
        return header + """skinparam shadowing false
skinparam componentStyle rectangle

rectangle "外部调用方" as caller
rectangle "热点文件入口" as entrypoint
rectangle "上游上下文" as upstream
rectangle "下游协作者" as downstream
rectangle "外部资源" as external

caller --> entrypoint : 发起请求
upstream --> entrypoint : 提供上下文
entrypoint --> downstream : 分派关键动作
entrypoint --> external : 读写外部资源
entrypoint --> caller : 返回结果
@enduml
"""

    if diagram_key == "architecture-modules":
        return header + """skinparam shadowing false
skinparam componentStyle rectangle

package "热点文件内部模块" {
  component "入口协调层" as entry
  component "规则判定层" as rules
  component "协作编排层" as orchestration
  component "结果收束层" as result
}

entry --> rules : 读取输入
rules --> orchestration : 选择路径
orchestration --> result : 汇总结果
result --> entry : 回传结论
@enduml
"""

    if diagram_key == "architecture-dependencies":
        return header + """skinparam shadowing false
skinparam componentStyle rectangle

rectangle "主入口" as entry
rectangle "输入校验依赖" as validate
rectangle "流程编排依赖" as orchestrate
rectangle "状态记录依赖" as state
rectangle "输出组装依赖" as output

entry --> validate : 校验输入
entry --> orchestrate : 触发主流程
entry --> state : 记录状态
entry --> output : 组装输出
orchestrate --> state : 同步进度
output --> entry : 返回结果
@enduml
"""

    if diagram_key == "activity":
        return header + """start
:进入主入口;
:准备输入与上下文;
:执行主流程编排;
if (是否命中关键分支?) then (是)
  :进入条件路径;
else (否)
  :继续主线路径;
endif
:汇总输出并返回;
stop
@enduml
"""

    if diagram_key == "sequence":
        return header + """autonumber

actor "发起方" as Caller
participant "热点文件入口" as Entry
participant "关键协作者甲" as DepA
participant "关键协作者乙" as DepB

Caller -> Entry : 发起调用
Entry -> DepA : 请求步骤一
DepA --> Entry : 返回阶段结果
Entry -> DepB : 请求步骤二
DepB --> Entry : 返回阶段结果
Entry --> Caller : 返回完成结果
@enduml
"""

    if diagram_key == "branch-decision":
        return header + """start
:进入判定入口;
if (是否满足主守卫条件?) then (满足)
  :执行主分支;
elseif (是否满足降级条件?)
  :执行降级分支;
else
  :执行默认路径或提前结束;
endif
stop
@enduml
"""

    if diagram_key == "state":
        return header + """[*] --> 待开始
待开始 --> 处理中 : 启动
处理中 --> 等待中 : 暂停或等待
等待中 --> 处理中 : 恢复或重试
处理中 --> 已完成 : 完成
已完成 --> [*]
@enduml
"""

    if diagram_key == "async-concurrency":
        return header + """autonumber

participant "触发方" as Trigger
participant "热点文件入口" as Workflow
participant "异步执行单元" as Worker

Trigger -> Workflow : 发起异步任务
activate Workflow
Workflow -> Worker : 分派并发动作
activate Worker
Worker --> Workflow : 回传结果或信号
deactivate Worker
Workflow --> Trigger : 返回确认结果
deactivate Workflow
@enduml
"""

    if diagram_key == "data-flow":
        return header + """skinparam shadowing false

rectangle "输入数据" as Input
rectangle "入口处理" as Core
rectangle "中间变换" as Mid
rectangle "输出结果" as Output

Input --> Core : 接收
Core --> Mid : 转换
Mid --> Output : 产出
@enduml
"""

    raise ValueError(f"Unsupported diagram key: {diagram_key}")


def build_index(results: Sequence[AnalysisResult]) -> str:
    lines = [
        "# Workflow Viz 洞察总览",
        "",
        "本页汇总当前仓库里最值得补图的热点文件，默认优先展示架构图组三连。",
        "",
        "| 文件 | 分数 | 状态 | 默认图组 | 文档 |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for result in results:
        slug = slug_for_path(result.metrics.relative_path)
        status = "热点" if result.score >= 60 else "观察名单" if result.watchlist else "候选"
        if result.metrics.explicit_target and result.score < 60:
            status = "显式指定"
        lines.append(
            "| "
            + f"`{result.metrics.relative_path.as_posix()}` | {result.score} | {status} | "
            + f"{'、'.join(chart_title(key) for key in result.recommended_diagrams)} | [打开](./{slug}.md) |"
        )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- `热点`：达到默认可视化建议阈值。",
            "- `观察名单`：接近阈值，建议在当前任务强相关时补图。",
            "- `显式指定`：分数未达阈值，但被用户明确点名。",
            "",
        ]
    )
    return "\n".join(lines)


def cleanup_legacy_architecture_artifacts(slug: str, code_dir: Path, charts_dir: Path) -> None:
    for diagram_key in LEGACY_ARCHITECTURE_KEYS:
        legacy_code = code_dir / f"{slug}-{diagram_key}.puml"
        legacy_chart = charts_dir / f"{slug}-{diagram_key}.svg"
        if legacy_code.exists():
            legacy_code.unlink()
        if legacy_chart.exists():
            legacy_chart.unlink()


def generate_docs(
    repo_root: Path,
    docs_root: Path,
    results: Sequence[AnalysisResult],
    render: bool,
    theme: str = DEFAULT_THEME,
) -> int:
    selected = [result for result in results if result.selected]
    if not selected:
        print("没有可生成文档的热点文件。")
        return 1

    code_dir = docs_root / "code"
    charts_dir = docs_root / "charts"
    docs_root.mkdir(parents=True, exist_ok=True)
    code_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)

    runtime: PlantUMLRuntime | None = None
    if render:
        runtime, _ = resolve_runtime(repo_root)
        if runtime is None:
            print("请求渲染 SVG，但未找到可用的 PlantUML 运行时。请先执行 doctor。")
            return 1

    for result in selected:
        slug = slug_for_path(result.metrics.relative_path)
        cleanup_legacy_architecture_artifacts(slug, code_dir, charts_dir)
        write_if_changed(docs_root / f"{slug}.md", build_markdown(result, slug))
        for diagram_key in result.recommended_diagrams:
            plantuml_path = code_dir / f"{slug}-{diagram_key}.puml"
            write_if_changed(plantuml_path, build_plantuml(result, diagram_key, theme=theme))
            if render and runtime is not None:
                runtime.render(plantuml_path, charts_dir)

    write_if_changed(docs_root / "index.md", build_index(selected))
    print(f"已在 {docs_root} 下生成 {len(selected)} 个热点文件的洞察文档。")
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan code understanding hotspots and scaffold workflow docs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Validate PlantUML rendering runtime.")
    doctor.add_argument("--repo-root", required=True, help="Repository root to inspect.")

    scan = subparsers.add_parser("scan", help="Scan a repository for high-comprehension-cost code.")
    scan.add_argument("--repo-root", required=True, help="Repository root to inspect.")
    scan.add_argument("--paths", nargs="+", help="Explicit files or directories to scan.")
    scan.add_argument("--top", type=int, default=DEFAULT_TOP, help="Number of results to print.")
    scan.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")

    generate = subparsers.add_parser("generate", help="Generate Markdown, PlantUML, and optionally SVG charts.")
    generate.add_argument("--repo-root", required=True, help="Repository root to inspect.")
    generate.add_argument("--paths", nargs="+", help="Explicit files or directories to generate docs for.")
    generate.add_argument("--top", type=int, default=DEFAULT_TOP, help="When scanning the full repo, only keep top N.")
    generate.add_argument(
        "--docs-root",
        default=str(DEFAULT_DOCS_ROOT),
        help="Documentation root relative to repo root. Default: docs/workflow-viz/insights",
    )
    generate.add_argument(
        "--theme",
        default=DEFAULT_THEME,
        help='PlantUML theme name. Use "none" to disable theme injection.',
    )
    generate.add_argument("--render", action="store_true", help="Render PlantUML to SVG.")

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        print(f"Repository root not found: {repo_root}", file=sys.stderr)
        return 1

    if args.command == "doctor":
        return run_doctor(repo_root)

    results = analyze_repository(repo_root, getattr(args, "paths", None))
    if args.command == "scan":
        top = max(1, args.top)
        renderer = render_scan_json if args.format == "json" else render_scan_text
        print(renderer(results, top))
        return 0

    if args.command == "generate":
        top = max(1, args.top)
        docs_root = Path(args.docs_root)
        if not docs_root.is_absolute():
            docs_root = repo_root / docs_root
        chosen = results if args.paths else results[:top]
        return generate_docs(repo_root, docs_root, chosen, render=args.render, theme=args.theme)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
