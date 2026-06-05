"""FastAPI application exposing the NexusAI engines as a JSON API."""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
    RewardScenarioBuilder,
    SyntheticDatasetGenerator,
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
