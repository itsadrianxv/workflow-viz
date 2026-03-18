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


def make_metrics(
    relative_path: str = "src/application/services/order_service.py",
    *,
    role_hints: set[str] | None = None,
    entrypoint: str = "handle_order",
    complexity: int = 12,
    max_nesting: int = 4,
    decisions: int = 6,
    early_exits: int = 1,
    exception_handlers: int = 1,
    distinct_calls: int = 7,
    call_count: int = 8,
    async_categories: set[str] | None = None,
    async_coordination: bool = False,
    async_marker_total: int = 0,
    state_count: int = 1,
    transition_count: int = 1,
    exception_paths: int = 1,
    cross_module_refs: int = 4,
    data_flow_markers: int = 1,
    import_count: int = 5,
    explicit_target: bool = True,
):
    fn = workflow_viz.FunctionMetrics(
        name=entrypoint,
        complexity=complexity,
        max_nesting=max_nesting,
        decisions=decisions,
        early_exits=early_exits,
        exception_handlers=exception_handlers,
        distinct_calls=distinct_calls,
        call_count=call_count,
        async_markers=async_marker_total,
        start_line=10,
        end_line=48,
    )
    relative = Path(relative_path)
    return workflow_viz.FileMetrics(
        path=REPO_ROOT / relative,
        relative_path=relative,
        language="python",
        loc=120,
        functions=[fn],
        import_count=import_count,
        cross_module_refs=cross_module_refs,
        async_categories=async_categories or set(),
        async_coordination=async_coordination,
        async_marker_total=async_marker_total,
        state_count=state_count,
        transition_count=transition_count,
        exception_paths=max(exception_paths, exception_handlers),
        role_hints=role_hints or set(),
        data_flow_markers=data_flow_markers,
        entrypoint=entrypoint,
        explicit_target=explicit_target,
    )


def make_result(relative_path: str = "src/application/services/order_service.py", **kwargs):
    return workflow_viz.evaluate_file(make_metrics(relative_path, **kwargs))


class WorkflowVizTests(unittest.TestCase):
    def test_default_docs_root_moves_to_workflow_viz_directory(self):
        self.assertEqual(workflow_viz.DEFAULT_DOCS_ROOT, Path("docs/workflow-viz"))

    def test_detect_file_role_from_representative_paths(self):
        cases = [
            (
                "src/application/services/order_service.py",
                {"application", "service"},
                "handle_order",
                "application-service",
            ),
            (
                "src/domain/services/pricing_service.py",
                {"domain", "service"},
                "price_order",
                "domain-service",
            ),
            (
                "src/domain/entities/order.py",
                {"entity", "domain"},
                "recalculate_total",
                "entity",
            ),
            (
                "src/domain/aggregates/order_aggregate.py",
                {"aggregate", "root"},
                "advance_status",
                "aggregate-root",
            ),
            (
                "src/infrastructure/repositories/order_repository.py",
                {"repository", "storage"},
                "save",
                "repository",
            ),
            (
                "src/infrastructure/adapters/payment_gateway_adapter.py",
                {"adapter", "gateway"},
                "send_payment",
                "infrastructure-adapter",
            ),
            (
                "src/workflows/order_workflow.py",
                {"workflow", "orchestrator"},
                "run_order_workflow",
                "workflow-orchestrator",
            ),
        ]

        for relative_path, role_hints, entrypoint, expected in cases:
            metrics = make_metrics(relative_path, role_hints=role_hints, entrypoint=entrypoint)
            self.assertEqual(workflow_viz.detect_file_role(metrics), expected)

    def test_recommended_diagrams_follow_role_templates(self):
        cases = [
            (
                "src/application/services/order_service.py",
                {"application", "service"},
                "application-service",
                ["sequence", "activity", "boundary-context"],
            ),
            (
                "src/domain/services/pricing_service.py",
                {"domain", "service"},
                "domain-service",
                ["domain-structure", "boundary-context", "activity"],
            ),
            (
                "src/domain/entities/order.py",
                {"entity", "domain"},
                "entity",
                ["domain-structure", "boundary-context", "state"],
            ),
            (
                "src/domain/aggregates/order_aggregate.py",
                {"aggregate", "root"},
                "aggregate-root",
                ["state", "boundary-context", "domain-structure"],
            ),
            (
                "src/infrastructure/repositories/order_repository.py",
                {"repository", "storage"},
                "repository",
                ["boundary-context", "data-flow", "sequence"],
            ),
            (
                "src/infrastructure/adapters/payment_gateway_adapter.py",
                {"adapter", "gateway"},
                "infrastructure-adapter",
                ["sequence", "boundary-context", "data-flow"],
            ),
            (
                "src/workflows/order_workflow.py",
                {"workflow", "orchestrator"},
                "workflow-orchestrator",
                ["sequence", "activity", "boundary-context"],
            ),
        ]

        for relative_path, role_hints, expected_role, expected_diagrams in cases:
            result = make_result(relative_path, role_hints=role_hints)
            self.assertEqual(result.file_role, expected_role)
            self.assertEqual(result.recommended_diagrams[:3], expected_diagrams)

    def test_entity_state_signal_promotes_state_to_first_diagram(self):
        result = make_result(
            "src/domain/entities/order.py",
            role_hints={"entity", "domain"},
            state_count=5,
            transition_count=7,
            complexity=6,
            max_nesting=2,
            decisions=3,
            distinct_calls=3,
            call_count=3,
            cross_module_refs=2,
            data_flow_markers=0,
        )

        self.assertEqual(result.file_role, "entity")
        self.assertEqual(result.recommended_diagrams[:3], ["state", "domain-structure", "boundary-context"])

    def test_build_plantuml_uses_default_theme_and_code_names(self):
        result = make_result()

        boundary = workflow_viz.build_plantuml(result, "boundary-context", theme="materia")
        structure = workflow_viz.build_plantuml(result, "domain-structure", theme="materia")

        self.assertTrue(boundary.startswith("@startuml\n!theme materia\n"))
        self.assertIn("handle_order", boundary)
        self.assertNotIn("TODO collaborator", boundary)
        self.assertNotIn("coordinates", boundary)

        self.assertTrue(structure.startswith("@startuml\n!theme materia\n"))
        self.assertIn("handle_order", structure)
        self.assertNotIn("invoke", structure)
        self.assertNotIn("complete", structure)

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

    def test_build_markdown_is_image_first_and_uses_role_based_intro(self):
        result = make_result()
        slug = workflow_viz.slug_for_path(result.metrics.relative_path)

        markdown = workflow_viz.build_markdown(result, slug, "../../charts")

        self.assertIn("## ", markdown)
        self.assertIn("### ", markdown)
        self.assertIn(f"../../charts/{slug}-sequence.svg", markdown)
        self.assertIn("文件角色", markdown)
        self.assertIn("推荐阅读顺序", markdown)
        self.assertNotIn("架构图组", markdown)
        self.assertNotIn("先看下面这组架构图", markdown)

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
            markdown_dir = insights_dir / "order-service"
            markdown_path = markdown_dir / "analysis.md"
            self.assertTrue(markdown_path.exists())
            self.assertFalse((insights_dir / f"{slug}.md").exists())
            self.assertFalse((insights_dir / "index.md").exists())
            self.assertIn(f"../../charts/{slug}-sequence.svg", markdown_path.read_text(encoding="utf-8"))
            self.assertTrue((code_dir / f"{slug}-sequence.puml").exists())
            self.assertTrue((code_dir / f"{slug}-activity.puml").exists())
            self.assertTrue((code_dir / f"{slug}-boundary-context.puml").exists())
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

    def test_documentation_files_describe_role_based_diagram_defaults(self):
        skill = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        readme_en = (REPO_ROOT / "README_EN.md").read_text(encoding="utf-8")
        template = (REPO_ROOT / "references" / "markdown-template.md").read_text(encoding="utf-8")
        selection = (REPO_ROOT / "references" / "diagram-selection.md").read_text(encoding="utf-8")
        heuristics = (REPO_ROOT / "references" / "heuristics.md").read_text(encoding="utf-8")
        runtime = (REPO_ROOT / "references" / "runtime-setup.md").read_text(encoding="utf-8")

        self.assertIn("domain-structure", skill)
        self.assertIn("boundary-context", skill)
        self.assertIn("object-snapshot", skill)
        self.assertIn("工作流编排", skill)
        self.assertNotIn("架构图是默认重点", skill)

        self.assertIn("domain-structure", readme)
        self.assertIn("boundary-context", readme)
        self.assertIn("role-based", readme_en)
        self.assertIn("domain-structure", readme_en)
        self.assertIn("../../charts/<slug>-sequence.svg", template)
        self.assertIn("domain-structure", selection)
        self.assertIn("boundary-context", selection)
        self.assertIn("aggregate root", heuristics.lower())
        self.assertIn("domain-structure", runtime)


if __name__ == "__main__":
    unittest.main()
