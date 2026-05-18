"""FastAPI application exposing the NexusAI engines as a JSON API."""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from ..engines import (
    AgentOrchestrator,
    ChainBuilder,
    EvolutionEngine,
    PromptAnalyzer,
    PromptEngine,
    PromptOptimizer,
    SafetyEngine,
    SafetyViolation,
    TemplateLibrary,
)
from ..training import (
    EvalSuiteBuilder,
    ExportConfig,
    FineTuneDataExporter,
    RewardScenarioBuilder,
    SyntheticDatasetGenerator,
    teacher_is_available,
)
from ..types import Domain, Platform, Prompt, SkillLevel
from . import schemas


def create_app() -> FastAPI:
    app = FastAPI(
        title="NexusAI",
        description="Autonomous prompt-engineering ecosystem.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Single shared engine instance (in-memory state lives here).
    engine = PromptEngine()
    evolution = EvolutionEngine(analyzer=engine.analyzer, optimizer=engine.optimizer)
    chain_builder = ChainBuilder(engine=engine)
    orchestrator = AgentOrchestrator(engine=engine, evolution=evolution)
    templates = TemplateLibrary()
    dataset_gen = SyntheticDatasetGenerator()
    eval_builder = EvalSuiteBuilder()
    reward_builder = RewardScenarioBuilder()
    safety = SafetyEngine()
    optimizer = PromptOptimizer()
    analyzer = PromptAnalyzer()

    # ------------------------------------------------------------------ meta
    @app.get("/health")
    def health() -> Dict[str, Any]:
        return {"status": "ok", "memory": engine.memory.snapshot()}

    @app.get("/meta/domains")
    def list_domains() -> List[str]:
        return [d.value for d in Domain]

    @app.get("/meta/platforms")
    def list_platforms() -> List[str]:
        return [p.value for p in Platform]

    @app.get("/meta/skills")
    def list_skills() -> List[str]:
        return [s.value for s in SkillLevel]

    # ------------------------------------------------------------------ intent
    @app.post("/intent")
    def predict_intent(req: schemas.IntentRequest) -> Dict[str, Any]:
        intent = engine.intent.predict(
            req.raw_idea, hint_domain=req.domain, hint_platform=req.platform
        )
        return intent.to_dict()

    # ----------------------------------------------------------------- prompt
    @app.post("/generate")
    def generate(req: schemas.GenerateRequest) -> Dict[str, Any]:
        try:
            prompt = engine.generate(
                req.raw_idea,
                skill_level=req.skill_level,
                domain=req.domain,
                platform=req.platform,
                include_negative=req.include_negative,
            )
        except SafetyViolation as e:
            raise HTTPException(status_code=400, detail=str(e))
        return prompt.to_dict()

    @app.post("/generate/tiered")
    def generate_tiered(req: schemas.GenerateTieredRequest) -> List[Dict[str, Any]]:
        try:
            prompts = engine.generate_tiered(
                req.raw_idea, domain=req.domain, platform=req.platform
            )
        except SafetyViolation as e:
            raise HTTPException(status_code=400, detail=str(e))
        return [p.to_dict() for p in prompts]

    # ---------------------------------------------------------------- analysis
    @app.post("/analyze")
    def analyze(req: schemas.AnalyzeRequest) -> Dict[str, Any]:
        return analyzer.analyze(req.text, req.platform).to_dict()

    @app.post("/optimize")
    def optimize(req: schemas.OptimizeRequest) -> Dict[str, Any]:
        improved = optimizer.optimize(req.text, req.domain, req.platform)
        score = analyzer.analyze(improved, req.platform)
        return {"text": improved, "score": score.to_dict()}

    # --------------------------------------------------------------- evolution
    @app.post("/evolve")
    def evolve(req: schemas.EvolveRequest) -> Dict[str, Any]:
        seed = Prompt(
            id=Prompt.new_id(),
            text=req.text,
            domain=req.domain,
            platform=req.platform,
            skill_level=req.skill_level,
            score=analyzer.analyze(req.text, req.platform),
        )
        result = evolution.evolve(seed, generations=req.generations,
                                  feedback_score=req.feedback_score)
        return result.to_dict()

    # ------------------------------------------------------------------ chain
    @app.post("/chain")
    def build_chain(req: schemas.ChainRequest) -> Dict[str, Any]:
        chain = chain_builder.build_chain(
            req.raw_idea, skill_level=req.skill_level, platform=req.platform
        )
        return chain.to_dict()

    # ----------------------------------------------------------------- agents
    @app.post("/agents/run")
    def run_agents(req: schemas.AgentsRequest) -> Dict[str, Any]:
        try:
            result = orchestrator.run(req.raw_idea, skill_level=req.skill_level)
        except SafetyViolation as e:
            raise HTTPException(status_code=400, detail=str(e))
        return result.to_dict()

    # ---------------------------------------------------------------- feedback
    @app.post("/feedback")
    def submit_feedback(req: schemas.FeedbackRequest) -> Dict[str, Any]:
        prompt = engine.memory.get(req.prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="prompt not found")
        engine.memory.record_feedback(req.prompt_id, req.score)
        return {
            "prompt_id": req.prompt_id,
            "score": req.score,
            "average": engine.memory.average_score(req.prompt_id),
        }

    # --------------------------------------------------------------- templates
    @app.get("/templates")
    def list_templates() -> List[Dict[str, Any]]:
        return [t.to_dict() for t in templates.all()]

    @app.post("/templates/render")
    def render_template(req: schemas.TemplateRenderRequest) -> Dict[str, Any]:
        template = templates.get(req.template_id)
        if not template:
            raise HTTPException(status_code=404, detail="template not found")
        try:
            text = template.render(**req.variables)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"text": text, "score": analyzer.analyze(text).to_dict()}

    # ----------------------------------------------------------------- safety
    @app.post("/safety/review")
    def safety_review(req: schemas.SafetyRequest) -> Dict[str, Any]:
        return safety.review(req.text).to_dict()

    # --------------------------------------------------------------- training
    @app.post("/training/dataset")
    def synth_dataset(req: schemas.DatasetRequest) -> Dict[str, Any]:
        examples = dataset_gen.generate(
            req.task, req.input_schema, req.output_schema,
            n_per_difficulty=req.n_per_difficulty,
        )
        return {"task": req.task, "examples": [e.to_dict() for e in examples]}

    @app.post("/training/eval")
    def synth_eval(req: schemas.EvalRequest) -> Dict[str, Any]:
        tasks = eval_builder.build(req.task_type, req.custom_thresholds)
        return {"task_type": req.task_type, "tasks": [t.to_dict() for t in tasks]}

    @app.post("/training/reward")
    def synth_reward(req: schemas.RewardRequest) -> Dict[str, Any]:
        scenario = reward_builder.build(req.task)
        return scenario.to_dict()

    # ----------------------------------------------------- fine-tuning export
    finetune_exporter = FineTuneDataExporter(engine=engine)

    def _build_export_cfg(req: schemas.FineTuneExportRequest) -> ExportConfig:
        # Validate `fmt` here (we keep schemas free of enums to avoid breaking
        # existing clients that send strings).
        if req.fmt not in ("llama", "chatml", "alpaca", "openai"):
            raise HTTPException(
                status_code=400,
                detail=f"Unknown format '{req.fmt}'. Use one of: llama, chatml, alpaca, openai.",
            )
        if req.use_teacher and not teacher_is_available():
            # Don't 500; just tell the caller why polish will be skipped.
            # The exporter's silent fallback will keep the run working.
            pass
        return ExportConfig(
            n_examples=req.n_examples,
            domains=req.domains,
            fmt=req.fmt,  # type: ignore[arg-type]
            min_score=req.min_score,
            seed=req.seed,
            edge_case_ratio=req.edge_case_ratio,
            include_system_prompt=req.include_system_prompt,
            use_teacher=req.use_teacher,
            teacher_model=req.teacher_model,
            teacher_temperature=req.teacher_temperature,
        )

    @app.get("/training/finetune/teacher-status")
    def teacher_status() -> Dict[str, Any]:
        """Tell the UI whether the GPT-4 teacher is wired up.

        Used by the dashboard to decide whether to show the 'use teacher'
        toggle as enabled or disabled.
        """
        return {"available": teacher_is_available()}

    @app.post("/training/finetune/export")
    def finetune_export(req: schemas.FineTuneExportRequest) -> Dict[str, Any]:
        """Generate a JSONL fine-tuning dataset and return it inline.

        Best for moderate sizes (n_examples <= ~1000). For larger runs prefer
        /training/finetune/stream which streams NDJSON as it generates.
        """
        cfg = _build_export_cfg(req)
        try:
            records, stats = finetune_exporter.export(cfg)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"records": records, "stats": stats.to_dict()}

    @app.post("/training/finetune/stream")
    def finetune_stream(req: schemas.FineTuneExportRequest) -> StreamingResponse:
        """Stream the dataset as newline-delimited JSON.

        First line is a `meta` record (config, started_at). Then one JSON
        line per kept training example. Final line is a `summary` record
        with full stats. Clients can save the body as `dataset.jsonl` after
        stripping the meta/summary lines, or process them live.
        """
        import json
        import time

        cfg = _build_export_cfg(req)

        def _gen():
            yield json.dumps({
                "type": "meta",
                "format": cfg.fmt,
                "n_examples": cfg.n_examples,
                "domains": [d.value for d in cfg.domains] if cfg.domains else None,
                "use_teacher": cfg.use_teacher and teacher_is_available(),
                "started_at": time.time(),
            }) + "\n"

            count = 0
            for record in finetune_exporter.export_iter(cfg):
                count += 1
                yield json.dumps(record, ensure_ascii=False) + "\n"

            yield json.dumps({
                "type": "summary",
                "kept": count,
                "requested": cfg.n_examples,
                "finished_at": time.time(),
            }) + "\n"

        return StreamingResponse(_gen(), media_type="application/x-ndjson")

    @app.post("/training/finetune/download")
    def finetune_download(req: schemas.FineTuneExportRequest) -> StreamingResponse:
        """Same as /export but returns a downloadable .jsonl file.

        Note: this is not streaming; we collect first, then send. Use this
        from the UI to give the user a 'Download dataset' button.
        """
        import json

        cfg = _build_export_cfg(req)
        try:
            records, _ = finetune_exporter.export(cfg)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        def _iter_lines():
            for r in records:
                yield json.dumps(r, ensure_ascii=False) + "\n"

        filename = f"nexusai_train_{cfg.fmt}_{cfg.n_examples}.jsonl"
        return StreamingResponse(
            _iter_lines(),
            media_type="application/x-ndjson",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # ------------------------------------------------------------------ memory
    @app.get("/memory/snapshot")
    def memory_snapshot() -> Dict[str, Any]:
        return {
            **engine.memory.snapshot(),
            "top_patterns": engine.memory.top_success_patterns(10),
        }

    @app.get("/memory/recall")
    def memory_recall(query: str, k: int = 5) -> List[Dict[str, Any]]:
        results = engine.memory.recall(query, k=k)
        return [{"prompt": p.to_dict(), "similarity": round(s, 3)} for p, s in results]

    return app


app = create_app()
