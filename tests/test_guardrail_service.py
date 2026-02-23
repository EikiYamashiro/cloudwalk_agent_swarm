from services.guardrail_service import (
    validate_input_message,
    validate_transfer_payload,
)


def test_validate_input_message_blocks_empty():
    blocked, reason = validate_input_message("   ")
    assert blocked is True
    assert reason == "Empty message."


def test_validate_input_message_allows_normal_text():
    blocked, reason = validate_input_message("How can I use tap to pay?")
    assert blocked is False
    assert reason is None


def test_validate_transfer_payload_blocks_invalid_amount():
    blocked, reason = validate_transfer_payload(amount=0, counterparty_name="Maria")
    assert blocked is True
    assert reason == "Transfer amount must be greater than zero."


def test_validate_transfer_payload_blocks_empty_counterparty_name():
    blocked, reason = validate_transfer_payload(amount=10, counterparty_name=" ")
    assert blocked is True
    assert reason == "Counterparty name is required."
