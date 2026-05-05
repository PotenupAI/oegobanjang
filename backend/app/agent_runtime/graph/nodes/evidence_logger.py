from app.agent_runtime.schemas import ForeignHiringState, EvidenceEvent, EventType


def log_event(state: ForeignHiringState, event: EvidenceEvent) -> ForeignHiringState:
    state.evidence_events.append(event)
    return state


def make_event(
    event_type: EventType,
    request_id: str,
    summary: str,
    agent_name: str | None = None,
    step_name: str | None = None,
    citation_ids: list[str] | None = None,
    risk_level: str = "LOW",
) -> EvidenceEvent:
    return EvidenceEvent(
        event_type=event_type,
        request_id=request_id,
        agent_name=agent_name,
        step_name=step_name,
        summary=summary,
        citation_ids=citation_ids or [],
        risk_level=risk_level,
    )
