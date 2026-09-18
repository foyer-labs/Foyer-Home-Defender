"""Hashing and recognising codes (SPEC §8.1). Needs bcrypt, not Home Assistant."""

from __future__ import annotations

from dataclasses import replace

import pytest

from custom_components.foyer.core.models import CodeResult
from custom_components.foyer.security import codes

from .helpers import user


def person(user_id: str, code: str, duress: str | None = None):
    return user(
        user_id,
        user_id.capitalize(),
        code_hash=codes.hash_code(code),
        duress_code_hash=codes.hash_code(duress) if duress else None,
    )


def test_a_code_is_stored_as_a_hash_and_never_as_itself():
    hashed = codes.hash_code("123456")
    assert "123456" not in hashed
    assert hashed.startswith("$2b$")
    assert codes.matches("123456", hashed)
    assert not codes.matches("123457", hashed)


def test_the_same_code_hashes_differently_every_time():
    assert codes.hash_code("123456") != codes.hash_code("123456")


def test_a_code_must_be_digits_of_the_configured_length():
    assert codes.validate("123456", 6) == "123456"
    with pytest.raises(codes.CodeError):
        codes.validate("12345", 6)
    with pytest.raises(codes.CodeError):
        codes.validate("abcdef", 6)


def test_a_code_identifies_exactly_one_person():
    users = (person("luca", "111111"), person("anna", "222222"))
    found = codes.identify(users, "222222")

    assert found.result is CodeResult.VALID
    assert found.user_id == "anna"
    assert not found.duress


def test_a_code_nobody_holds_is_invalid_and_names_nobody():
    users = (person("luca", "111111"),)
    found = codes.identify(users, "999999")

    assert found.result is CodeResult.INVALID
    assert found.user is None


def test_no_code_at_all_is_not_a_failed_attempt():
    assert codes.identify((person("luca", "111111"),), None).result is CodeResult.NONE
    assert codes.identify((), "").result is CodeResult.NONE


def test_the_duress_code_identifies_the_same_person_and_says_so():
    users = (person("luca", "111111", duress="999999"),)
    found = codes.identify(users, "999999")

    assert found.result is CodeResult.VALID
    assert found.user_id == "luca"
    assert found.duress


def test_a_known_user_shortens_the_search_but_not_the_check():
    users = (person("luca", "111111"), person("anna", "222222"))

    assert codes.identify(users, "222222", user_id="anna").user_id == "anna"
    # Anna's code is not Luca's, even when the channel says it is Luca asking.
    assert codes.identify(users, "222222", user_id="luca").result is CodeResult.INVALID


def test_a_code_that_already_belongs_to_somebody_collides():
    users = (person("luca", "111111", duress="999999"),)

    assert codes.collides(users, "111111")
    assert codes.collides(users, "999999")  # against a duress code too
    assert not codes.collides(users, "222222")
    # Editing that same user is not a collision with themselves.
    assert not codes.collides(users, "111111", ignore_user_id="luca")


def test_a_user_whose_stored_hash_is_rubbish_matches_nothing():
    """It must answer, not raise: this runs in the middle of a disarm."""
    broken = replace(person("luca", "111111"), code_hash="not a hash")
    assert codes.identify((broken,), "111111").result is CodeResult.INVALID


def test_a_suggested_code_has_the_length_asked_for():
    suggested = codes.random_code(8)
    assert len(suggested) == 8
    assert suggested.isdigit()
