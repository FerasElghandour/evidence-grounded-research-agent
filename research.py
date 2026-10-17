"""Provider-neutral evidence workflow. Author: Feras Elghandour."""
from dataclasses import dataclass
from typing import Callable
import math

@dataclass(frozen=True)
class Evidence:
    key: str
    title: str
    url: str
    text: str

@dataclass(frozen=True)
class Assessment:
    sufficient: bool
    confidence: float
    reason: str

    def __post_init__(self):
        if not math.isfinite(self.confidence) or not 0 <= self.confidence <= 1:
            raise ValueError('Confidence must be finite and within [0, 1]')

@dataclass(frozen=True)
class Answer:
    text: str
    citations: tuple[str, ...]
    limitations: tuple[str, ...] = ()

class ResearchAgent:
    """Inject retrieval, assessment, search, resolution, and generation adapters.

    Citation membership is enforced; factual entailment still needs evaluation.
    Instances hold session-local memory and are not a multi-user persistence layer.
    """
    def __init__(self, retrieve: Callable, assess: Callable, search: Callable,
                 answer: Callable, resolve: Callable, threshold=0.7, history_limit=4):
        if not 0 <= threshold <= 1 or history_limit < 1:
            raise ValueError('Invalid routing or memory configuration')
        self.retrieve, self.assess, self.search = retrieve, assess, search
        self.answer, self.resolve = answer, resolve
        self.threshold, self.history_limit = threshold, history_limit
        self._sessions = {}

    def history(self, session):
        return tuple(self._sessions.get(session, ()))

    def invoke(self, question, session):
        if not question.strip() or not session.strip():
            raise ValueError('Question and session are required')
        prior = self.history(session)
        resolved = self.resolve(question, prior) if prior else question
        if not isinstance(resolved, str) or not resolved.strip():
            raise ValueError('Resolver must return a question')
        docs = tuple(self.retrieve(resolved))
        judgement = self.assess(resolved, docs)
        trace = ['retrieve', 'assess']
        limits = []
        if not docs or not judgement.sufficient or judgement.confidence < self.threshold:
            trace.append('web_search')
            try:
                docs = tuple(self.search(resolved))
                judgement = self.assess(resolved, docs)
                trace.append('assess_web')
            except Exception:
                docs = ()
                limits.append('External search was unavailable.')
        if not docs or not judgement.sufficient or judgement.confidence < self.threshold:
            result = Answer('The available evidence does not support a verified answer.', (),
                            tuple(limits) + ('Additional evidence is required.',))
        else:
            keys = [d.key for d in docs]
            if len(keys) != len(set(keys)):
                raise ValueError('Evidence identifiers must be unique')
            result = self.answer(resolved, docs)
            if not result.citations or not set(result.citations) <= set(keys):
                raise ValueError('Answer must cite supplied evidence identifiers')
        self._sessions[session] = (*prior, (question, result))[-self.history_limit:]
        return {'question': question, 'resolved_question': resolved,
                'answer': result, 'trace': tuple(trace)}
