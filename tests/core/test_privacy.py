"""Who a log row is about, and what is left of it (SPEC §10.4).

The arithmetic only. What the database does with it is tests/ha's; the point
of these is that the rules can be read and checked without a Home Assistant
instance, like everything else in core/.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from custom_components.foyer.core.models import ArmingDevice, Contact, DeviceKind
from custom_components.foyer.core.privacy import (
    ERASED_COLUMNS,
    NAMED_CATEGORIES,
    REDACTED,
    SHORT_RETENTION_DAYS,
    PersonRef,
    cutoff,
    new_pseudonym,
    person_ref,
    redact_detail,
)

from .helpers import make_house, user

NOW = datetime(2026, 9, 20, 22, 0, tzinfo=UTC)


def _house():
    return replace(
        make_house(),
        users=(user("luca", "Luca"), user("ana", "Ana Cleaner")),
        devices=(
            ArmingDevice(
                id="tag_ana",
                name="Ana's tag",
                kind=DeviceKind.TAG,
                entity_id="tag.ana",
                user_id="ana",
            ),
            ArmingDevice(
                id="hall", name="Hall keypad", kind=DeviceKind.KEYPAD, ref="hall"
            ),
        ),
        contacts=(
            Contact(id="c_ana", name="Ana", linked_user_id="ana"),
            Contact(id="c_luca", name="Luca"),
        ),
    )


def test_person_ref_gathers_every_pointer_at_one_person():
    """A subject access request is about personal data, not about the rows
    whose user_id column matches (part 2 decision 7)."""
    ref = person_ref(_house(), "ana")
    assert ref is not None
    assert ref.user_id == "ana"
    assert ref.names == ("Ana Cleaner",)
    # Her tag, and not the shared keypad in the hall.
    assert ref.device_ids == ("tag_ana",)
    # The address-book entry linked to her, and not the one that is not.
    assert ref.contact_ids == ("c_ana",)
    assert not ref.empty


def test_person_ref_of_somebody_who_is_not_a_user():
    assert person_ref(_house(), "nobody") is None


def test_erasure_empties_every_identifying_column():
    """Decision 6: not two columns but four. Which keypad, and by which
    route, is as much "who" as the name once you know the household. The
    store erases exactly these (store/log_store.py reads this tuple)."""
    assert set(ERASED_COLUMNS) == {"user_id", "user_name", "channel", "device_id"}


def test_redaction_reaches_a_name_inside_a_configuration_diff():
    """Names get into `detail` by the side door: a configuration row
    summarises what changed by the *name* of the thing it changed."""
    detail = {
        "kind": "device",
        "changes": {
            "devices": {
                "added": ["Ana Cleaner's tag"],
                "changed": {"Hall keypad": {"enabled": [True, False]}},
            }
        },
    }
    out = redact_detail(detail, ("Ana Cleaner",))
    assert out["changes"]["devices"]["added"] == [REDACTED]
    # Everything that is not about her is untouched.
    assert out["changes"]["devices"]["changed"] == {
        "Hall keypad": {"enabled": [True, False]}
    }
    assert out["kind"] == "device"


def test_redaction_matches_a_name_used_as_a_key():
    out = redact_detail(
        {"changed": {"Ana Cleaner": {"enabled": [True, False]}}}, ("ana cleaner",)
    )
    assert list(out["changed"]) == [REDACTED]


def test_redaction_without_a_name_changes_nothing():
    detail = {"changes": {"areas": {"added": ["Garage"]}}}
    assert redact_detail(detail, ()) == detail


def test_a_pseudonym_is_opaque_and_stable_for_its_token():
    assert new_pseudonym("0123456789abcdef") == new_pseudonym("0123456789abcdef")
    assert new_pseudonym("0123456789abcdef") != new_pseudonym("fedcba9876543210")
    # It says nothing about anybody: no name goes into it, so no list of
    # names gets it back out (part 2 decision 4).
    assert "Ana" not in new_pseudonym("0123456789abcdef")


def test_cutoff_is_the_moment_rows_become_old_enough():
    assert cutoff(NOW, 30) == NOW - timedelta(days=30)
    # A delay below the floor is raised to it: the sweep runs daily and
    # anything shorter would promise a precision it does not have.
    assert cutoff(NOW, 0) == NOW - timedelta(days=1)


def test_the_short_preset_touches_only_what_names_people():
    """§10.4's preset for installations with domestic staff (decision 8)."""
    assert SHORT_RETENTION_DAYS == 7
    # `action` names who acknowledged (third review).
    assert set(NAMED_CATEGORIES) == {"arming", "alarm", "action", "security", "config"}
    # The diagnostic categories are left alone: they name nobody, and they
    # are what somebody reads when a sensor did not react three weeks ago.
    assert "system" not in NAMED_CATEGORIES
    assert "zone_armed" not in NAMED_CATEGORIES
    assert "zone_disarmed" not in NAMED_CATEGORIES


def test_an_empty_reference_matches_nothing():
    assert PersonRef(user_id=None).empty


def test_redaction_matches_whole_words_and_not_substrings():
    """A person called Ed must not erase `added`, `changed` and `enabled`.

    Found in review: substring matching turned an erasure into the
    destruction of the "what happened" §10.4 says must survive, in an UPDATE
    with nothing behind it.
    """
    detail = {
        "kind": "device",
        "item_id": "abc",
        "changes": {"devices": {"added": ["Hall keypad"], "changed": {"a": 1}}},
        "enabled": True,
    }
    assert redact_detail(detail, ("Ed",)) == detail
    assert redact_detail({"area_id": "a", "zone_id": "z"}, ("Id",)) == {
        "area_id": "a",
        "zone_id": "z",
    }
    # And the name still comes out when it is a word, including in a
    # possessive, which is how a person's name gets into a device's name.
    assert redact_detail({"added": ["Ed's tag"]}, ("Ed",)) == {"added": [REDACTED]}


def test_two_redacted_keys_stay_two_entries():
    """A dict comprehension would collapse them into one, losing a row's
    content with no error and no count (found in review)."""
    out = redact_detail({"Ana Smith": {"a": 1}, "Ana Smith ": {"b": 2}}, ("Ana Smith",))
    assert len(out) == 2


def test_unlink_removes_the_id_that_points_back_at_the_account():
    from custom_components.foyer.core.privacy import unlink_detail

    assert unlink_detail({"kind": "user", "item_id": "ana"}, "ana") == {"kind": "user"}
    # Somebody else's row is left alone.
    assert unlink_detail({"item_id": "luca"}, "ana") == {"item_id": "luca"}
