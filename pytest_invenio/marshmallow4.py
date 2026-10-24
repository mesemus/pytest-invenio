# SPDX-FileCopyrightText: 2026 CESNET.
# SPDX-License-Identifier: MIT

"""Helpers to make marshmallow 3 behave like marshmallow 4 regarding ``context``.

marshmallow 4 removed ``Schema.context`` (and ``Field.context``). Reading it
raises ``AttributeError``. On marshmallow 3 the attribute still exists, so code
relying on it passes the tests silently. The helpers in this module replace the
attribute by a property which raises :class:`Marshmallow4ContextError` (a
subclass of ``AttributeError``) on read, so that such code is detected while
still running on marshmallow 3.

Code guarded with ``getattr(obj, "context", None)`` keeps working, exactly as
on marshmallow 4.
"""

import sys
from contextlib import contextmanager

import pytest


class Marshmallow4ContextError(AttributeError):
    """Raised on reading ``.context`` of a marshmallow schema or field."""


def _raise(owner):
    raise Marshmallow4ContextError(
        f"{type(owner).__name__}.context was removed in marshmallow 4; use "
        "marshmallow_utils.context:context_schema or a constructor argument "
        "instead."
    )


@contextmanager
def strict_context():
    """Make reading ``Schema.context`` and ``Field.context`` raise an error.

    Does nothing if marshmallow is not installed (it is not a dependency of
    pytest-invenio) or has no ``context`` any more (marshmallow 4+).
    """
    try:
        from marshmallow import fields
        from marshmallow.schema import Schema
    except ImportError:
        yield
        return

    if not hasattr(fields.Field, "context"):
        yield
        return

    # marshmallow itself copies the parent context into nested schemas
    allowed = {fields.Nested.schema.fget.__code__}

    def schema_get(self):
        if sys._getframe(1).f_code in allowed:
            # instances created before patching store it as plain "context"
            return self.__dict__.get("_mm3_context", self.__dict__.get("context", {}))
        _raise(self)

    def schema_set(self, value):
        # Schema.__init__ still assigns ``self.context``
        self.__dict__["_mm3_context"] = value

    def field_get(self):
        _raise(self)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(Schema, "context", property(schema_get, schema_set), raising=False)
        mp.setattr(fields.Field, "context", property(field_get))
        yield
