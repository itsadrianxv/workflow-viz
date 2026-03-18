import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "workflow_viz.py"


def load_workflow_viz():
    spec = importlib.util.spec_from_file_location("workflow_viz", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


workflow_viz = load_workflow_viz()


def make_result():
    fn = workflow_viz.FunctionMetrics(
        name="handle_request",
        complexity=12,
        max_nesting=4,
        decisions=6,
        early_exits=1,
        exception_handlers=2,
        distinct_calls=7,
        call_count=8,
        async_markers=4,
        start_line=10,
        end_line=48,
    )
    metrics = workflow_viz.FileMetrics(
        path=REPO_ROOT / "src" / "sample_service.py",
        relative_path=Path("src/sample_service.py"),
        language="python",
        loc=120,
        functions=[fn],
        import_count=5,
        cross_module_refs=4,
        async_categories={"async-await", "events"},
        async_coordination=True,
        async_marker_total=5,
        state_count=3,
        transition_count=4,
        exception_paths=3,
        role_hints={"workflow", "handler"},
        data_flow_markers=4,
        entrypoint="handle_request",
        explicit_target=False,
    )
    return workflow_viz.evaluate_file(metrics)


class WorkflowVizTests(unittest.TestCase):
    def test_default_docs_root_moves_to_workflow_viz_directory(self):
        self.assertEqual(workflow_viz.DEFAULT_DOCS_ROOT, Path("docs/workflow-viz"))

    def test_recommended_diagrams_prioritize_architecture_pack(self):
        result = make_result()

        self.assertEqual(
            result.recommended_diagrams[:5],
            [
                "architecture-context",
                "architecture-modules",
                "architecture-dependencies",
                "activity",
                "sequence",
            ],
        )

    def test_build_plantuml_uses_default_theme_and_chinese_labels(self):
        result = make_result()

        architecture = workflow_viz.build_plantuml(result, "architecture-context", theme="materia")
        sequence = workflow_viz.build_plantuml(result, "sequence", theme="materia")

        self.assertTrue(architecture.startswith("@startuml\n!theme materia\n"))
        self.assertIn("架构总览图", architecture)
        self.assertIn("外部调用方", architecture)
        self.assertIn("handle_request", architecture)
        self.assertNotIn("TODO collaborator", architecture)
        self.assertNotIn("coordinates", architecture)

        self.assertTrue(sequence.startswith("@startuml\n!theme materia\n"))
        self.assertIn("协作顺序图", sequence)
        self.assertIn("发起方", sequence)
        self.assertIn("handle_request", sequence)
        self.assertNotIn("invoke", sequence)
        self.assertNotIn("complete", sequence)

    def test_build_plantuml_supports_theme_override_and_disable(self):
        result = make_result()

        custom = workflow_viz.build_plantuml(result, "activity", theme="plain")
        disabled = workflow_viz.build_plantuml(result, "activity", theme="none")

        self.assertTrue(custom.startswith("@startuml\n!theme plain\n"))
        self.assertTrue(disabled.startswith("@startuml\n"))
        self.assertNotIn("!theme", disabled)

    def test_build_plantuml_injects_dark_mode_foreground_skinparams(self):
        result = make_result()

        activity = workflow_viz.build_plantuml(result, "activity", theme="materia")

        self.assertIn("skinparam defaultFontColor #FFFFFF", activity)
        self.assertIn("skinparam ArrowColor #FFFFFF", activity)
        self.assertIn("skinparam LineColor #FFFFFF", activity)

    def test_build_markdown_is_image_first_and_architecture_focused(self):
        result = make_result()
        slug = workflow_viz.slug_for_path(result.metrics.relative_path)

        markdown = workflow_viz.build_markdown(result, slug)

        self.assertIn("## 架构图组", markdown)
        self.assertIn("### 架构总览图", markdown)
        self.assertIn("### 模块拆解图", markdown)
        self.assertIn("### 依赖职责图", markdown)
        self.assertIn("图前说明", markdown)
        self.assertIn("图后解读", markdown)
        self.assertIn(f"../charts/{slug}-architecture-context.svg", markdown)
        self.assertNotIn("## 职责说明", markdown)
        self.assertNotIn("## 复杂度证据", markdown)
        self.assertNotIn("## 关键结论", markdown)

    def test_generate_docs_writes_markdown_and_assets_to_separate_directories(self):
        result = make_result()
        slug = workflow_viz.slug_for_path(result.metrics.relative_path)

        with tempfile.TemporaryDirectory() as temp_dir:
            docs_root = Path(temp_dir) / "docs" / "workflow-viz"
            insights_dir = docs_root / "insights"
            code_dir = docs_root / "code"
            charts_dir = docs_root / "charts"
            code_dir.mkdir(parents=True, exist_ok=True)
            charts_dir.mkdir(parents=True, exist_ok=True)

            legacy_code = code_dir / f"{slug}-architecture.puml"
            legacy_chart = charts_dir / f"{slug}-architecture.svg"
            legacy_code.write_text("legacy", encoding="utf-8")
            legacy_chart.write_text("legacy", encoding="utf-8")

            exit_code = workflow_viz.generate_docs(
                REPO_ROOT,
                docs_root,
                [result],
                render=False,
                theme="materia",
            )

            self.assertEqual(exit_code, 0)
            self.assertFalse(legacy_code.exists())
            self.assertFalse(legacy_chart.exists())
            self.assertTrue((insights_dir / f"{slug}.md").exists())
            self.assertTrue((insights_dir / "index.md").exists())
            self.assertTrue((code_dir / f"{slug}-architecture-context.puml").exists())
            self.assertTrue((code_dir / f"{slug}-architecture-modules.puml").exists())
            self.assertTrue((code_dir / f"{slug}-architecture-dependencies.puml").exists())
            self.assertFalse((insights_dir / "code").exists())
            self.assertFalse((insights_dir / "charts").exists())

    def test_force_dark_svg_foreground_recolors_dark_text_and_strokes(self):
        svg = (
            '<svg>'
            '<text fill="#222222">handle_request()</text>'
            '<path style="stroke:#333333;fill:none;" />'
            '<rect fill="#FEFECE" stroke="#181818" />'
            "</svg>"
        )

        normalized = workflow_viz.force_dark_svg_foreground(svg)

        self.assertIn('fill="#FFFFFF">handle_request()</text>', normalized)
        self.assertIn('style="stroke:#FFFFFF;fill:none;"', normalized)
        self.assertIn('fill="#FEFECE"', normalized)
        self.assertIn('stroke="#FFFFFF"', normalized)

    def test_documentation_files_describe_new_defaults(self):
        skill = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        readme_en = (REPO_ROOT / "README_EN.md").read_text(encoding="utf-8")
        template = (REPO_ROOT / "references" / "markdown-template.md").read_text(encoding="utf-8")
        selection = (REPO_ROOT / "references" / "diagram-selection.md").read_text(encoding="utf-8")
        runtime = (REPO_ROOT / "references" / "runtime-setup.md").read_text(encoding="utf-8")

        self.assertIn("!theme materia", skill)
        self.assertIn("architecture-context", skill)
        self.assertIn("architecture-modules", skill)
        self.assertIn("architecture-dependencies", skill)
        self.assertIn("docs/workflow-viz/code", skill)
        self.assertIn("docs/workflow-viz/charts", skill)
        self.assertIn("docs/workflow-viz/insights", skill)
        self.assertIn("docs/workflow-viz/code", readme)
        self.assertIn("docs/workflow-viz/charts", readme)
        self.assertIn("docs/workflow-viz/insights", readme)
        self.assertIn("docs/workflow-viz/code", readme_en)
        self.assertIn("docs/workflow-viz/charts", readme_en)
        self.assertIn("docs/workflow-viz/insights", readme_en)
        self.assertIn("图前说明", template)
        self.assertIn("图后解读", template)
        self.assertIn("../charts/<slug>-architecture-context.svg", template)
        self.assertIn("专属名词保留代码命名", skill)
        self.assertIn("暗色环境", skill)
        self.assertIn("白色", skill)
        self.assertIn("专属名词保留代码命名", readme)
        self.assertIn("暗色环境", readme)
        self.assertIn("white foreground", readme_en)
        self.assertNotIn("先给结论，再给图", template)
        self.assertIn("架构总览图", selection)
        self.assertIn("模块拆解图", selection)
        self.assertIn("依赖职责图", selection)
        self.assertIn("!theme materia", runtime)
        self.assertIn("docs/workflow-viz/code", runtime)
        self.assertIn("docs/workflow-viz/charts", runtime)
        self.assertIn("docs/workflow-viz/insights", runtime)


if __name__ == "__main__":
    unittest.main()
