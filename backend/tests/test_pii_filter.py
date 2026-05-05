from app.agent_runtime.middleware.pii_filter import mask, mask_payload, mask_text, restore


def test_mask_text_masks_alien_registration_number_passport_number_and_phone() -> None:
    text = "외국인등록번호 900101-1234567, 여권번호 M12345678, 전화번호 010-1234-5678"

    masked = mask_text(text)

    assert "900101-*******" not in masked
    assert "900101-▲▲▲▲▲▲▲" in masked
    assert "M1234****" in masked
    assert "010-****-5678" in masked


def test_mask_returns_restore_map_and_restore_recovers_original_text() -> None:
    text = "외국인등록번호 900101-1234567, 여권번호 M12345678, 전화번호 010-1234-5678"

    masked, restore_map = mask(text)

    assert masked == "외국인등록번호 900101-▲▲▲▲▲▲▲, 여권번호 M1234****, 전화번호 010-****-5678"
    assert restore(masked, restore_map) == text


def test_mask_payload_recursively_masks_nested_strings() -> None:
    payload = {
        "worker": {
            "alien_number": "900101-1234567",
            "passport_number": "M12345678",
        },
        "phones": ["010-1234-5678"],
    }

    masked = mask_payload(payload)

    assert masked["worker"]["alien_number"] == "900101-▲▲▲▲▲▲▲"
    assert masked["worker"]["passport_number"] == "M1234****"
    assert masked["phones"][0] == "010-****-5678"
