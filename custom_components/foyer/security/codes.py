"""Codes: hashing them, and recognising the person who typed one (SPEC §8.1).

This is the only module in the integration that ever holds a code in the
clear, and it holds one for as long as it takes to compare it. Nothing here
returns a hash to a caller that could send it anywhere, no hash reaches the
API, the log or a diagnostic, and ``core/`` is told only what the comparison
concluded (INV-2, core/authz).

It deliberately imports nothing from ``homeassistant``: bcrypt blocks for tens
of milliseconds and belongs in an executor thread, which is the caller's
business, and this way the whole of it is testable without Home Assistant.

**Cost of a check.** Codes are unique across users (§8.1), so a code typed at
a shared keypad identifies exactly one person — but finding them means trying
each stored hash in turn, and a bcrypt comparison is deliberately slow. The
scan stops at the first match, and a channel that already knows who is asking
(the panel, a per-user tag) passes that user and costs one comparison. An
installation with a great many users and a shared keypad pays for all of them;
that is the price of storing codes the way they must be stored.
"""

from __future__ import annotations

from dataclasses import dataclass
import secrets

import bcrypt

from ..core.models import MAX_CODE_LENGTH, MIN_CODE_LENGTH, CodeResult, User

# What a new hash costs, and the one number here worth arguing about.
#
# Home Assistant hashes account passwords at twelve. An alarm code is checked
# on the path of somebody standing at a keypad with an entry delay running,
# and a WRONG code costs the whole scan — every stored hash, twice. At twelve
# that is roughly half a second per comparison on the small machines this runs
# on, so five users make a rejected code take seconds, on the one path that
# must not hesitate.
#
# Ten keeps a comparison in the tens of milliseconds and still puts an offline
# guess at a six-digit code many hours away. And the person who can mount that
# guess is the one who can read .storage — a Home Assistant administrator, who
# INV-6 already says these codes do not protect against. What protects a code
# against guessing from outside is the lockout of §8.4, not the work factor.
ROUNDS = 10


class CodeError(ValueError):
    """A code that cannot be stored: wrong length, or not digits."""


@dataclass(frozen=True, slots=True)
class Credential:
    """What arrived, once it has been compared with what is stored.

    ``user`` is the person recognised, if any. ``result`` is what ``core/``
    is told: nothing was supplied, something was and it matched, something
    was and it did not. ``duress`` means the match was on the duress code,
    which acts exactly as the ordinary one does wherever it is used, and
    says so to nobody except the log and the default profile (§8.1).
    """

    result: CodeResult = CodeResult.NONE
    user: User | None = None
    duress: bool = False

    @property
    def user_id(self) -> str | None:
        return self.user.id if self.user else None


def validate(code: str, length: int) -> str:
    """Check a code before it is hashed, and return it.

    The length is global (§8.1) because a keypad has to know how many digits
    to collect before it validates anything. Digits only, for the same reason:
    a keypad has no letters.
    """
    # ASCII digits only: `isdigit` also accepts superscripts and the digits
    # of other scripts, which no keypad can type, so a code made of them is
    # one nobody could ever enter.
    if not (code.isascii() and code.isdigit()):
        raise CodeError("a code is digits only")
    if len(code) != length:
        raise CodeError(f"a code must be exactly {length} digits")
    if not MIN_CODE_LENGTH <= length <= MAX_CODE_LENGTH:
        raise CodeError("the configured code length is out of bounds")
    return code


def hash_code(code: str) -> str:
    """One bcrypt hash. The only direction this module travels in."""
    return bcrypt.hashpw(code.encode(), bcrypt.gensalt(rounds=ROUNDS)).decode()


def matches(code: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(code.encode(), hashed.encode())
    except ValueError:
        # A stored value that is not a bcrypt hash at all. It matches nothing,
        # and saying so is better than raising in the middle of a disarm.
        return False


def identify(
    users: tuple[User, ...], code: str | None, *, user_id: str | None = None
) -> Credential:
    """Which of these people typed this code, if any.

    ``user_id`` narrows the search to one person, for a channel that already
    knows who is asking; the code still has to match, so this is a shortcut
    through the work and never through the check.
    """
    if not code:
        return Credential()
    candidates = [u for u in users if user_id is None or u.id == user_id]
    for user in candidates:
        if matches(code, user.code_hash):
            return Credential(CodeResult.VALID, user)
        if matches(code, user.duress_code_hash):
            return Credential(CodeResult.VALID, user, duress=True)
    return Credential(CodeResult.INVALID)


def collides(
    users: tuple[User, ...], code: str, *, ignore_user_id: str | None = None
) -> bool:
    """Does this code already belong to somebody?

    Uniqueness is what keeps the log honest (§8.1): with a shared code the
    first matching hash wins and the log attributes the action to the wrong
    person. Duress codes are part of the same space — a duress code that is
    also somebody's ordinary code would disarm with a silent alarm attached.

    The caller must refuse the save without saying *whose* code it collided
    with, which would otherwise turn this check into a way of testing codes.
    """
    return any(
        matches(code, user.code_hash) or matches(code, user.duress_code_hash)
        for user in users
        if user.id != ignore_user_id
    )


def random_code(length: int) -> str:
    """A suggestion for the panel, so nobody has to invent 1234 themselves."""
    return "".join(secrets.choice("0123456789") for _ in range(length))
