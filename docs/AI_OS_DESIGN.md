# AI OS DESIGN

## 1. 전체 구조

외고반장의 AI OS는 사용자의 자연어 요청을 받아 업무 의도를 분류하고, 필요한 전문 에이전트를 실행한 뒤, 안전한 다음 행동과 근거를 생성한다.

```txt
User Request
→ Intent Router
→ Planner
→ State Loader
→ Agent Execution
→ Risk / Human Approval
→ Evidence Log
→ Final Response