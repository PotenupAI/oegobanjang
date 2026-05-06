# WorkBridge 제품화 하드닝 실행 계획

> **agent 작업자 필수 지침:** 이 계획을 실행할 때는 `superpowers:subagent-driven-development` 또는 `superpowers:executing-plans`를 사용한다. 각 항목은 체크박스 단위로 진행 상태를 추적한다.

**목표:** 현재 skeleton/MVP 상태인 WorkBridge를 실제 제품에 가까운 backend/frontend로 끌어올린다. 핵심은 실제 LLM provider 호출, Approval/Evidence/Document 영속 저장, 공식 문서 심화 수집, 실제 Next.js build 검증이다.

**아키텍처:** 기존 `route -> plan -> execute -> approval -> evidence -> final` 흐름은 유지한다. 새 기능은 feature flag와 adapter 뒤에 붙여서 기존 deterministic 테스트가 깨지지 않게 한다. Persistence, source collection, frontend compile은 서로 다른 mission으로 분리한다.

**기술 스택:** FastAPI, Pydantic, OpenAI Python SDK Responses API structured outputs, SQLAlchemy 2, SQLite/PostgreSQL 호환 persistence, 기존 RAG JSONL pipeline, Next.js.

---

## 이 계획이 닫는 현재 빈틈

현재 PR/branch 기준으로 남은 제품화 gap은 아래 네 가지다.

1. `backend/app/agent_runtime/llm/client.py`에는 `RealProviderJudgmentClient`가 있지만, 실제 OpenAI SDK 호출은 하지 않고 `ProviderError`를 발생시킨다.
2. Approval, Evidence, Document 상태는 DB 영속 저장이 아니라 in-memory dict 또는 payload 기반이다.
3. HiKorea/KOSHA 일부 raw source는 공식 URL 응답 원문은 확보했지만, 상세 PDF/자료/하위 리소스 단위까지 깊게 수집한 수준은 아니다.
4. `frontend/package.json`의 `build`와 `test`는 실제 Next compile이 아니라 `validate-frontend.mjs` skeleton 검증이다.

---

## Mission 분리

구현 전에 아래 mission 파일을 새로 만든다.

- `missions/active/014-real-openai-structured-provider.md`
- `missions/active/015-persistent-approval-evidence-document-state.md`
- `missions/active/016-official-source-depth-collection.md`
- `missions/active/017-real-next-frontend-build.md`

권장 구현 순서는 아래와 같다.

1. **Mission 015: persistence 먼저**
   - Approval/Evidence/Document 상태가 process memory에만 있으면 LLM provider error나 frontend API 상태를 안정적으로 추적하기 어렵다.
2. **Mission 014: real LLM provider**
   - provider 호출 결과, 오류, refusal, timeout을 evidence/persistence에 남길 수 있어야 한다.
3. **Mission 016: official source depth**
   - 더 깊은 공식 source가 있어야 RAG와 LLM 판단 report의 근거 품질이 올라간다.
4. **Mission 017: real frontend build**
   - API contract가 안정된 뒤 실제 Next compile로 전환한다.

---

## Task 1. 신규 Mission 파일 작성

**대상 파일**

- 생성: `missions/active/014-real-openai-structured-provider.md`
- 생성: `missions/active/015-persistent-approval-evidence-document-state.md`
- 생성: `missions/active/016-official-source-depth-collection.md`
- 생성: `missions/active/017-real-next-frontend-build.md`
- 수정: `missions/README.md`
- 수정: `FOLDER_STRUCTURE.md`

### 1-1. Mission 015 작성

`missions/active/015-persistent-approval-evidence-document-state.md`를 만든다.

```markdown
# Mission 015: Persistent Approval, Evidence, And Document State

## 목표

Approval 요청, Evidence event, worker, worker document 상태를 process memory 밖에 저장한다.

## 범위

- in-memory approval/evidence store를 repository 기반 persistence로 교체한다.
- 테스트 DB fixture에서 seed workers/documents를 읽을 수 있게 한다.
- PII masking은 저장 경계에서 유지한다.
- destructive production migration은 아직 구현하지 않는다.

## Acceptance Criteria

- API로 생성한 approval을 새 service instance에서도 조회할 수 있다.
- Evidence event는 masked payload만 저장한다.
- document gap check가 `worker_documents.csv` 또는 DB-backed document state를 읽을 수 있다.
- SQLite temporary test DB 기준 테스트가 통과한다.
- 기존 deterministic workflow 테스트가 계속 통과한다.

## Verification

- `uv run pytest backend/tests/test_persistence_approval.py backend/tests/test_persistence_evidence.py backend/tests/test_document_check_tool.py`
- `uv run pytest backend/tests/test_agent_workflow.py backend/tests/test_evidence.py`
```

### 1-2. Mission 014 작성

`missions/active/014-real-openai-structured-provider.md`를 만든다.

```markdown
# Mission 014: Real OpenAI Structured Provider

## 목표

fake provider를 기본값으로 유지하면서, feature flag로만 켜지는 실제 OpenAI structured judgment provider를 추가한다.

## 범위

- OpenAI Responses API structured outputs를 사용한다.
- `REAL_LLM_ENABLED=true`와 `OPENAI_API_KEY`가 있을 때만 실제 호출한다.
- 테스트에서는 실제 network 호출을 하지 않는다.
- provider error는 workflow를 자동 완료하지 않고 안전하게 block/pending 처리한다.

## Acceptance Criteria

- fake provider가 기본값이다.
- real provider는 feature flag가 켜졌을 때만 호출된다.
- OpenAI 요청 메시지는 PII masking 이후 전달된다.
- provider output은 기존 judgment schema로 parse된다.
- provider timeout, invalid schema, refusal, missing key가 테스트된다.

## Verification

- `uv run pytest backend/tests/test_llm_judgment_chain.py backend/tests/test_real_provider_client.py`
- `uv run pytest backend/tests/test_agent_workflow.py backend/tests/test_guardrails.py`
```

### 1-3. Mission 016 작성

`missions/active/016-official-source-depth-collection.md`를 만든다.

```markdown
# Mission 016: Official Source Depth Collection

## 목표

공식 source 수집을 landing page snapshot 수준에서 PDF, guide, form, resource page 단위로 깊게 확장한다.

## 범위

- `data-pipeline/raw/source_manifest.json`에 child source row를 추가한다.
- official URL, retrieval date, source type, document type, evidence grade를 보존한다.
- child source metadata 테스트를 추가한다.
- 수집된 source로 법률 해석이나 가능 여부 확정 문구를 만들지 않는다.

## Acceptance Criteria

- HiKorea/KOSHA row가 landing page, guide page, PDF/form, resource index를 구분한다.
- collected source row가 최소 30개 이상이다.
- RAG ingest가 source hierarchy metadata를 유지한다.
- retrieval eval에 deep source case가 포함된다.

## Verification

- `uv run python scripts/ingest_rag_docs.py`
- `uv run pytest backend/tests/test_rag_source_manifest.py backend/tests/test_rag_indexing.py`
- `uv run python scripts/run_evals.py --dataset rag_retrieval_cases`
```

### 1-4. Mission 017 작성

`missions/active/017-real-next-frontend-build.md`를 만든다.

```markdown
# Mission 017: Real Next Frontend Build

## 목표

frontend skeleton validation을 실제 Next.js compile과 기본 test path로 교체한다.

## 범위

- Next, React, TypeScript, lint/build script를 추가한다.
- 현재 dashboard routes와 backend fallback 동작은 유지한다.
- `npm run build`가 실제 compile을 수행하게 한다.
- auth/deployment는 아직 추가하지 않는다.

## Acceptance Criteria

- `npm run build`가 `next build`를 실행한다.
- `npm run validate:skeleton`은 기존 구조/PII validation을 계속 수행한다.
- dashboard pages가 server component로 compile된다.
- API fallback code가 strict TypeScript에서 compile된다.

## Verification

- `npm run validate:skeleton`
- `npm run build`
```

### 1-5. Mission 파일 commit

```powershell
git add missions/active/014-real-openai-structured-provider.md missions/active/015-persistent-approval-evidence-document-state.md missions/active/016-official-source-depth-collection.md missions/active/017-real-next-frontend-build.md missions/README.md FOLDER_STRUCTURE.md
git commit -m "docs: add productization hardening missions"
```

---

## Task 2. Approval/Evidence/Document 영속 저장

**대상 파일**

- 수정: `pyproject.toml`
- 수정: `.env.example`
- 수정: `backend/app/config.py`
- 교체: `backend/app/db/session.py`
- 생성: `backend/app/db/repositories.py`
- 수정: `backend/app/models/approval.py`
- 수정: `backend/app/models/evidence.py`
- 수정: `backend/app/models/document.py`
- 수정: `backend/app/services/approval_service.py`
- 수정: `backend/app/services/evidence_service.py`
- 수정: `backend/app/services/document_service.py`
- 수정: `backend/app/agent_runtime/tools/document_check_tool.py`
- 생성: `backend/tests/test_persistence_approval.py`
- 생성: `backend/tests/test_persistence_evidence.py`
- 생성: `backend/tests/test_document_state_repository.py`

### 2-1. persistence dependency 추가

```powershell
uv add -U sqlalchemy psycopg[binary]
```

예상 결과:

- `pyproject.toml`에 SQLAlchemy와 psycopg가 추가된다.
- `uv.lock`이 갱신된다.

### 2-2. DB 설정 추가

`backend/app/config.py`에 추가한다.

```python
test_database_url: str = "sqlite+pysqlite:///:memory:"
use_persistent_stores: bool = False
```

`.env.example`에 추가한다.

```env
USE_PERSISTENT_STORES=false
DATABASE_URL=postgresql+psycopg://oegobanjang:oegobanjang@localhost:5432/oegobanjang
TEST_DATABASE_URL=sqlite+pysqlite:///:memory:
```

### 2-3. DB session 구현

현재 `SessionPlaceholder`를 SQLAlchemy session factory로 교체한다.

`backend/app/db/session.py`:

```python
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str | None = None):
    url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, future=True)


engine = build_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)


@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

### 2-4. persistence 테스트 작성

`backend/tests/test_persistence_approval.py`:

```python
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, build_engine
from app.db.repositories import ApprovalRepository
from app.schemas.approval import ApprovalCreate, ApprovalDecision


def test_approval_persists_across_repository_instances() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    with SessionLocal() as session:
        repo = ApprovalRepository(session)
        created = repo.create(
            ApprovalCreate(
                request_id="req_1",
                action_type="send_message",
                reason="needs approval",
            )
        )
        approval_id = created.approval_id
        session.commit()

    with SessionLocal() as session:
        repo = ApprovalRepository(session)
        found = repo.get(approval_id)
        assert found is not None
        assert found.status == "PENDING"
        decided = repo.decide(approval_id, ApprovalDecision(status="APPROVED"))
        assert decided is not None
        assert decided.status == "APPROVED"
```

`backend/tests/test_persistence_evidence.py`:

```python
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, build_engine
from app.db.repositories import EvidenceRepository
from app.schemas.evidence import EvidenceCreate
from app.services.evidence_service import contains_raw_pii


def test_evidence_persists_masked_payload_only() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    with SessionLocal() as session:
        repo = EvidenceRepository(session)
        record = repo.append(
            EvidenceCreate(
                request_id="req_pii",
                event_type="tool_executed",
                agent_id="executor",
                action_type="execute_tool",
                payload={"alien_number": "900101-1234567", "passport": "M12345678"},
            )
        )
        session.commit()

    with SessionLocal() as session:
        repo = EvidenceRepository(session)
        events = repo.list_by_request("req_pii")
        assert len(events) == 1
        assert events[0].event_id == record.event_id
        assert not contains_raw_pii(events[0].payload)
```

### 2-5. repository 구현

`backend/app/db/repositories.py`를 만든다.

핵심 repository:

- `ApprovalRepository`
- `EvidenceRepository`
- `WorkerDocumentRepository`

기본 원칙:

- 저장 전 `mask_payload()`를 적용한다.
- 같은 `(request_id, event_type, agent_id, action_type)` evidence는 중복 저장하지 않는다.
- 같은 `(request_id, action_type)` approval은 중복 생성하지 않는다.
- document state는 `worker_id`, `document_type`, `status` 기준으로 조회할 수 있게 한다.

### 2-6. service에 feature flag 적용

`approval_service.py`, `evidence_service.py`, `document_service.py`는 아래 방식으로 분기한다.

```python
if get_settings().use_persistent_stores:
    with get_session() as session:
        return ApprovalRepository(session).create(payload)
```

`USE_PERSISTENT_STORES=false`일 때는 기존 in-memory 동작을 유지한다.

### 2-7. 검증 및 commit

```powershell
uv run pytest backend/tests/test_persistence_approval.py backend/tests/test_persistence_evidence.py backend/tests/test_document_state_repository.py backend/tests/test_agent_workflow.py backend/tests/test_evidence.py
git add pyproject.toml uv.lock .env.example backend/app backend/tests
git commit -m "feat(persistence): add repository-backed approval evidence and document state"
```

---

## Task 3. 실제 OpenAI structured provider 연결

**대상 파일**

- 수정: `pyproject.toml`
- 수정: `.env.example`
- 수정: `backend/app/config.py`
- 수정: `backend/app/agent_runtime/llm/client.py`
- 수정: `backend/app/agent_runtime/llm/judgment_chain.py`
- 생성: `backend/tests/test_real_provider_client.py`

### 3-1. OpenAI dependency 추가

```powershell
uv add -U openai
```

### 3-2. LLM 설정 추가

`backend/app/config.py`:

```python
llm_model: str = "gpt-4o-mini"
llm_max_output_tokens: int = 1200
```

`.env.example`:

```env
REAL_LLM_ENABLED=false
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=30
LLM_MAX_OUTPUT_TOKENS=1200
OPENAI_API_KEY=
```

### 3-3. provider 테스트 작성

`backend/tests/test_real_provider_client.py`:

```python
import json

import pytest

from app.agent_runtime.llm.client import ProviderError, RealProviderJudgmentClient


class FakeParsedResponse:
    output_parsed = {
        "status": "draft",
        "request_id": "req_1",
        "case_type": "new_hiring",
        "detected_intents": ["HIRING"],
        "summary": "근거 기반 초안입니다.",
        "evidence_summary": [],
        "risk_flags": [],
        "readiness_status": "needs_review",
        "missing_inputs": [],
        "follow_up_questions": [],
        "approval_required": True,
        "blocked": False,
        "guardrail_notes": [],
        "prohibited_actions": [],
        "next_actions": ["담당자 검토"],
    }


class FakeResponses:
    def parse(self, **kwargs):
        assert kwargs["model"] == "gpt-4o-mini"
        assert "text_format" in kwargs
        assert "900101-1234567" not in str(kwargs["input"])
        return FakeParsedResponse()


class FakeOpenAI:
    def __init__(self, api_key: str, timeout: float):
        self.api_key = api_key
        self.timeout = timeout
        self.responses = FakeResponses()


def test_real_provider_uses_structured_parse_and_masks_pii(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.agent_runtime.llm.client.OpenAI", FakeOpenAI)
    client = RealProviderJudgmentClient(
        provider="openai",
        model="gpt-4o-mini",
        api_key="key",
        timeout_seconds=30,
    )

    raw = client.generate_json([{"role": "user", "content": "외국인등록번호 900101-1234567 확인"}])

    parsed = json.loads(raw)
    assert parsed["approval_required"] is True
    assert "900101-1234567" not in str(client.last_messages)


def test_real_provider_requires_api_key() -> None:
    client = RealProviderJudgmentClient(
        provider="openai",
        model="gpt-4o-mini",
        api_key=None,
        timeout_seconds=30,
    )
    with pytest.raises(ProviderError, match="API key is missing"):
        client.generate_json([{"role": "user", "content": "test"}])
```

### 3-4. provider 구현

`backend/app/agent_runtime/llm/client.py`에 optional import를 둔다.

```python
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
```

`RealProviderJudgmentClient.generate_json()`은 아래 흐름으로 바꾼다.

```python
if OpenAI is None:
    raise ProviderError("openai package is not installed")

client = OpenAI(api_key=self.api_key, timeout=self.timeout_seconds)
response = client.responses.parse(
    model=self.model,
    input=self.last_messages,
    text_format=WorkBridgeJudgmentPayload,
)
return json.dumps(response.output_parsed, ensure_ascii=False, sort_keys=True)
```

주의:

- 테스트에서는 `OpenAI`를 monkeypatch한다.
- `REAL_LLM_ENABLED=false`면 절대 실제 provider를 호출하지 않는다.
- provider output도 기존 guardrail을 반드시 통과해야 한다.

### 3-5. 검증 및 commit

```powershell
uv run pytest backend/tests/test_real_provider_client.py backend/tests/test_llm_judgment_chain.py backend/tests/test_agent_workflow.py backend/tests/test_guardrails.py
git add pyproject.toml uv.lock .env.example backend/app/config.py backend/app/agent_runtime/llm backend/tests/test_real_provider_client.py
git commit -m "feat(llm): call OpenAI structured provider behind feature flag"
```

---

## Task 4. 공식 source 심화 수집

**대상 파일**

- 수정: `data-pipeline/raw/source_manifest.json`
- 추가: `data-pipeline/raw/*`
- 수정: `scripts/ingest_rag_docs.py`
- 수정: `backend/tests/test_rag_source_manifest.py`
- 수정: `evals/datasets/rag_retrieval_cases.jsonl`

### 4-1. source hierarchy 필드 추가

manifest row는 아래 필드를 지원해야 한다.

```json
{
  "source_id": "hikorea_stay_guide_pdf_001",
  "parent_source_id": "hikorea_stay_guide_001",
  "title": "HiKorea stay guide PDF",
  "official_url": "https://...",
  "saved_path": "data-pipeline/raw/hikorea_stay_guide_pdf_001.pdf",
  "downloaded_format": "pdf",
  "collection_status": "collected",
  "publisher": "HiKorea",
  "source_type": "official_procedure",
  "doc_type": "procedure",
  "evidence_grade": "A"
}
```

### 4-2. manifest 테스트 추가

`backend/tests/test_rag_source_manifest.py`에 추가한다.

```python
def test_collected_sources_include_deep_child_sources() -> None:
    manifest = _load_manifest()
    collected = [row for row in manifest["sources"] if row["collection_status"] == "collected"]
    child_rows = [row for row in collected if row.get("parent_source_id")]

    assert len(collected) >= 30
    assert any(row["publisher"] == "HiKorea" for row in child_rows)
    assert any(row["publisher"] == "안전보건공단" for row in child_rows)
    assert all(row["saved_path"] for row in child_rows)
```

### 4-3. ingest metadata 보존

`scripts/ingest_rag_docs.py`에서 chunk metadata에 아래 값을 포함한다.

```python
"parent_source_id": record.get("parent_source_id"),
"official_url": record.get("official_url") or record.get("url"),
"collection_status": record.get("collection_status", "unknown"),
```

### 4-4. retrieval eval case 추가

`evals/datasets/rag_retrieval_cases.jsonl`에 deep source case를 추가한다.

```jsonl
{"id":"rag-021","input":"HiKorea 체류 안내 세부 자료 근거 찾아줘","expected_source_ids":["hikorea_stay_guide_pdf_001"],"answer_evidence_only":true}
{"id":"rag-022","input":"KOSHA 외국인 근로자 안전표지 자료 찾아줘","expected_source_ids":["kosha_safety_signs_pdf_001"],"answer_evidence_only":true}
{"id":"rag-023","input":"체류기간 연장 신청서류 상세 PDF 근거 찾아줘","expected_source_ids":["gov24_stay_extension_001"],"answer_evidence_only":true}
```

### 4-5. 검증 및 commit

```powershell
uv run python scripts/ingest_rag_docs.py
uv run pytest backend/tests/test_rag_source_manifest.py backend/tests/test_rag_indexing.py
uv run python scripts/run_evals.py --dataset rag_retrieval_cases
git add data-pipeline/raw/source_manifest.json data-pipeline/raw data-pipeline/processed/chunks scripts/ingest_rag_docs.py backend/tests/test_rag_source_manifest.py evals/datasets/rag_retrieval_cases.jsonl
git commit -m "feat(rag): deepen official source collection"
```

---

## Task 5. 실제 Next.js frontend build

**대상 파일**

- 수정: `frontend/package.json`
- 수정: `frontend/app/layout.tsx`
- 수정: `frontend/app/page.tsx`
- 수정: `frontend/lib/api.ts`
- 생성: `frontend/next.config.mjs`
- 생성: `frontend/tsconfig.json`
- 생성: `frontend/.eslintrc.json`

### 5-1. frontend dependency 추가

`frontend/`에서 실행한다.

```powershell
npm install next react react-dom typescript @types/react @types/node eslint eslint-config-next
```

### 5-2. script 변경

`frontend/package.json`:

```json
{
  "scripts": {
    "validate:skeleton": "node scripts/validate-frontend.mjs",
    "lint": "next lint",
    "test": "node scripts/validate-frontend.mjs",
    "build": "next build"
  }
}
```

### 5-3. Next 설정 추가

`frontend/next.config.mjs`:

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
};

export default nextConfig;
```

`frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "es2022"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{"name": "next"}]
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### 5-4. strict TypeScript 대응

`frontend/lib/api.ts`에서 backend 응답 배열이 없을 때도 compile되도록 방어한다.

```ts
const safeEvents = Array.isArray(response.evidence_events)
  ? response.evidence_events
  : [];
```

### 5-5. 검증 및 commit

```powershell
npm run validate:skeleton
npm run build
git add frontend/package.json frontend/package-lock.json frontend/next.config.mjs frontend/tsconfig.json frontend/.eslintrc.json frontend/app frontend/lib frontend/types
git commit -m "feat(frontend): replace skeleton validation with real Next build"
```

---

## 최종 검증

repo root에서 실행한다.

```powershell
uv run pytest backend/tests
uv run python scripts/run_evals.py --dataset safety_guardrail_cases
uv run python scripts/run_evals.py --dataset rag_retrieval_cases
uv run python scripts/run_evals.py --dataset langchain_judgment_cases
```

`frontend/`에서 실행한다.

```powershell
npm run validate:skeleton
npm run build
```

기대 결과:

- backend tests 통과
- safety eval이 자동 제출/법률 판단/가치 판단 요청을 계속 차단
- RAG eval `0 issues`
- LLM judgment eval은 `REAL_LLM_ENABLED=false`에서 network-free
- frontend는 실제 `next build` 통과

---

## 참고 원칙

- OpenAI provider는 가능한 경우 Responses API structured outputs를 사용한다.
- CI/test에서는 실제 OpenAI API를 호출하지 않는다.
- 실제 provider smoke test는 `REAL_LLM_ENABLED=true`를 켠 로컬 수동 명령으로 분리한다.
- AI는 비자 가능 여부 확정, 법률/노무 자문, 정부 포털 자동 제출, 국적 선호, 이탈 예측을 하지 않는다.
