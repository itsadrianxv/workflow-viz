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


def make_result(
    relative_path: str = "src/sample_service.py",
    *,
    role_hints: set[str] | None = None,
    entrypoint: str = "handle_request",
):
    fn = workflow_viz.FunctionMetrics(
        name=entrypoint,
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
    relative = Path(relative_path)
    metrics = workflow_viz.FileMetrics(
        path=REPO_ROOT / relative,
        relative_path=relative,
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
        role_hints=role_hints or {"workflow", "handler"},
        data_flow_markers=4,
        entrypoint=entrypoint,
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

    def test_build_plantuml_uses_default_theme_and_code_names(self):
        result = make_result()

        architecture = workflow_viz.build_plantuml(result, "architecture-context", theme="materia")
        sequence = workflow_viz.build_plantuml(result, "sequence", theme="materia")

        self.assertTrue(architecture.startswith("@startuml\n!theme materia\n"))
        self.assertIn("handle_request", architecture)
        self.assertNotIn("TODO collaborator", architecture)
        self.assertNotIn("coordinates", architecture)

        self.assertTrue(sequence.startswith("@startuml\n!theme materia\n"))
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

    def test_build_markdown_is_image_first_and_supports_nested_chart_paths(self):
        result = make_result()
        slug = workflow_viz.slug_for_path(result.metrics.relative_path)

        markdown = workflow_viz.build_markdown(result, slug, "../../charts")

        self.assertIn("## ", markdown)
        self.assertIn("### ", markdown)
        self.assertIn("![](", markdown.replace(f"![{workflow_viz.chart_title('architecture-context')}]", "![]"))
        self.assertIn(f"../../charts/{slug}-architecture-context.svg", markdown)
        self.assertNotIn("## Responsibilities", markdown)

    def test_plan_markdown_outputs_uses_shared_module_directory_for_related_files(self):
        handler = make_result("src/payment/handler.py", role_hints={"payment", "workflow", "handler"})
        rules = make_result("src/payment/rules.py", role_hints={"payment", "rules"})

        plan = workflow_viz.plan_markdown_outputs([handler, rules])

        self.assertEqual(len(plan.groups), 1)
        self.assertEqual(plan.groups[0].directory_name, "payment")
        self.assertEqual(
            sorted(item.markdown_name for item in plan.groups[0].items),
            ["handler.md", "rules.md"],
        )

    def test_plan_markdown_outputs_splits_unrelated_files(self):
        payment = make_result("src/payment/handler.py", role_hints={"payment", "workflow", "handler"})
        auth = make_result("src/auth/token.py", role_hints={"auth", "token"})

        plan = workflow_viz.plan_markdown_outputs([payment, auth])

        self.assertEqual(sorted(group.directory_name for group in plan.groups), ["auth-token", "payment-handler"])
        self.assertEqual(
            sorted(item.markdown_name for group in plan.groups for item in group.items),
            ["auth-token.md", "payment-handler.md"],
        )

    def test_generate_docs_single_file_writes_analysis_markdown_in_group_directory(self):
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
            markdown_dir = insights_dir / "sample-service"
            markdown_path = markdown_dir / "analysis.md"
            self.assertTrue(markdown_path.exists())
            self.assertFalse((insights_dir / f"{slug}.md").exists())
            self.assertFalse((insights_dir / "index.md").exists())
            self.assertIn(f"../../charts/{slug}-architecture-context.svg", markdown_path.read_text(encoding="utf-8"))
            self.assertTrue((code_dir / f"{slug}-architecture-context.puml").exists())
            self.assertTrue((code_dir / f"{slug}-architecture-modules.puml").exists())
            self.assertTrue((code_dir / f"{slug}-architecture-dependencies.puml").exists())
            self.assertFalse((insights_dir / "code").exists())
            self.assertFalse((insights_dir / "charts").exists())

    def test_generate_docs_related_files_share_a_group_directory(self):
        handler = make_result("src/payment/handler.py", role_hints={"payment", "workflow", "handler"})
        rules = make_result("src/payment/rules.py", role_hints={"payment", "rules"})

        with tempfile.TemporaryDirectory() as temp_dir:
            docs_root = Path(temp_dir) / "docs" / "workflow-viz"

            exit_code = workflow_viz.generate_docs(
                REPO_ROOT,
                docs_root,
                [handler, rules],
                render=False,
                theme="materia",
            )

            self.assertEqual(exit_code, 0)
            payment_dir = docs_root / "insights" / "payment"
            self.assertTrue((payment_dir / "handler.md").exists())
            self.assertTrue((payment_dir / "rules.md").exists())
            self.assertFalse((payment_dir / "analysis.md").exists())
            self.assertFalse((docs_root / "insights" / "index.md").exists())

    def test_generate_docs_unrelated_files_use_separate_group_directories(self):
        payment = make_result("src/payment/handler.py", role_hints={"payment", "workflow", "handler"})
        auth = make_result("src/auth/token.py", role_hints={"auth", "token"})

        with tempfile.TemporaryDirectory() as temp_dir:
            docs_root = Path(temp_dir) / "docs" / "workflow-viz"

            exit_code = workflow_viz.generate_docs(
                REPO_ROOT,
                docs_root,
                [payment, auth],
                render=False,
                theme="materia",
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue((docs_root / "insights" / "payment-handler" / "payment-handler.md").exists())
            self.assertTrue((docs_root / "insights" / "auth-token" / "auth-token.md").exists())
            self.assertFalse((docs_root / "insights" / "payment-handler" / "analysis.md").exists())
            self.assertFalse((docs_root / "insights" / "index.md").exists())

    def test_generate_docs_cleans_legacy_flat_markdown_outputs_conservatively(self):
        result = make_result()
        slug = workflow_viz.slug_for_path(result.metrics.relative_path)

        with tempfile.TemporaryDirectory() as temp_dir:
            docs_root = Path(temp_dir) / "docs" / "workflow-viz"
            insights_dir = docs_root / "insights"
            insights_dir.mkdir(parents=True, exist_ok=True)
            (insights_dir / "index.md").write_text("legacy index", encoding="utf-8")
            (insights_dir / f"{slug}.md").write_text("legacy flat markdown", encoding="utf-8")
            (insights_dir / "notes.md").write_text("keep me", encoding="utf-8")

            exit_code = workflow_viz.generate_docs(
                REPO_ROOT,
                docs_root,
                [result],
                render=False,
                theme="materia",
            )

            self.assertEqual(exit_code, 0)
            self.assertFalse((insights_dir / "index.md").exists())
            self.assertFalse((insights_dir / f"{slug}.md").exists())
            self.assertTrue((insights_dir / "notes.md").exists())

    def test_force_dark_svg_foreground_keeps_text_on_light_shapes_dark(self):
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<rect fill="#FEFECE" stroke="#181818" x="0" y="0" width="120" height="40" />'
            '<text fill="#222222" x="12" y="24">inside_box</text>'
            '<text fill="#222222" x="12" y="84">between_boxes</text>'
            '<path style="stroke:#333333;fill:none;" />'
            "</svg>"
        )

        normalized = workflow_viz.force_dark_svg_foreground(svg)

        self.assertIn('fill="#222222" x="12" y="24">inside_box</text>', normalized)
        self.assertIn('fill="#FFFFFF" x="12" y="84">between_boxes</text>', normalized)
        self.assertIn('style="stroke:#FFFFFF;fill:none;"', normalized)
        self.assertIn('fill="#FEFECE"', normalized)
        self.assertIn('stroke="#FFFFFF"', normalized)

    def test_force_dark_svg_foreground_treats_light_gradients_as_text_background(self):
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<defs>'
            '<linearGradient id="light-fill" x1="50%" x2="50%" y1="0%" y2="100%">'
            '<stop offset="0%" stop-color="#FFFFFF" />'
            '<stop offset="100%" stop-color="#F8F8F8" />'
            "</linearGradient>"
            "</defs>"
            '<polygon fill="url(#light-fill)" points="0,0 120,0 120,50 0,50" />'
            '<text fill="#222222" x="16" y="28">gradient_box</text>'
            "</svg>"
        )

        normalized = workflow_viz.force_dark_svg_foreground(svg)

        self.assertIn('fill="#222222" x="16" y="28">gradient_box</text>', normalized)

    def test_documentation_files_describe_grouped_markdown_defaults(self):
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
        self.assertIn("docs/workflow-viz/insights/<group>/analysis.md", skill)
        self.assertIn("docs/workflow-viz/insights/<group>/<file>.md", skill)
        self.assertNotIn("docs/workflow-viz/insights/index.md", skill)
        self.assertIn("docs/workflow-viz/code", readme)
        self.assertIn("docs/workflow-viz/charts", readme)
        self.assertIn("docs/workflow-viz/insights", readme)
        self.assertIn("analysis.md", readme)
        self.assertIn("insights/<group>/", readme)
        self.assertIn("docs/workflow-viz/code", readme_en)
        self.assertIn("docs/workflow-viz/charts", readme_en)
        self.assertIn("docs/workflow-viz/insights", readme_en)
        self.assertIn("analysis.md", readme_en)
        self.assertIn("insights/<group>/", readme_en)
        self.assertIn("../../charts/<slug>-architecture-context.svg", template)
        self.assertNotIn("](../charts/<slug>-architecture-context.svg)", template)
        self.assertIn("free-floating labels white", readme_en)
        self.assertIn("light-filled shapes stay dark", readme_en)
        self.assertIn("浅色图形里的文字保留深色", skill)
        self.assertIn("architecture-context", selection)
        self.assertIn("architecture-modules", selection)
        self.assertIn("architecture-dependencies", selection)
        self.assertIn("!theme materia", runtime)
        self.assertIn("docs/workflow-viz/code", runtime)
        self.assertIn("docs/workflow-viz/charts", runtime)
        self.assertIn("docs/workflow-viz/insights", runtime)
        self.assertIn("analysis.md", runtime)


if __name__ == "__main__":
    unittest.main()
