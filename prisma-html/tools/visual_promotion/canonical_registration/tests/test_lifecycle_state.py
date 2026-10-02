from __future__ import annotations

import unittest

from visual_promotion.canonical_registration.lifecycle_state import (
    assert_transition,
    normalize_lifecycle,
)


def status(state: str) -> dict[str, object]:
    return {
        "state": state,
        "statusIsAuthority": False,
        "statusMayAuthorizeMutation": False,
        "blockerCodes": [],
    }


class LifecycleStateTests(unittest.TestCase):
    def test_superseded_uses_existing_canonical_state(self) -> None:
        normalized = normalize_lifecycle(status("SUPERSEDED"))
        self.assertEqual(normalized.canonical_state, "SUPERSEDED")
        self.assertFalse(normalized.mutation_authorized)

    def test_closed_lifecycle_can_be_superseded(self) -> None:
        assert_transition(status("DONE"), status("SUPERSEDED"))

    def test_superseded_lifecycle_cannot_reopen(self) -> None:
        with self.assertRaisesRegex(ValueError, "SUPERSEDED_LIFECYCLE_REOPEN_FORBIDDEN"):
            assert_transition(status("SUPERSEDED"), status("IN_PROGRESS"))


if __name__ == "__main__":
    unittest.main()
