from __future__ import annotations


def issue_local_token(user_id: str) -> dict[str, str]:
    return {"access_token": f"local-{user_id}", "token_type": "bearer"}
