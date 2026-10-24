# SPDX-FileCopyrightText: 2026 CESNET.
# SPDX-License-Identifier: MIT

"""Tests for the marshmallow 4 strict context fixture (active in these tests too)."""

import pytest
from marshmallow import Schema, fields


class Inner(Schema):
    """Nested schema."""

    name = fields.String()


class Wrapper(Schema):
    """Schema with a nested field."""

    inner = fields.Nested(Inner)


class Unguarded(Schema):
    """Schema reading ``self.context`` directly."""

    value = fields.Method("get_value")

    def get_value(self, obj):
        """Read context without a guard."""
        return self.context.get("value")


class Guarded(Schema):
    """Schema reading ``self.context`` guarded."""

    value = fields.Method("get_value")

    def get_value(self, obj):
        """Read context with a guard."""
        return (getattr(self, "context", None) or {}).get("value", "default")


def test_unguarded_schema_context():
    """Reading ``Schema.context`` fails like on marshmallow 4."""
    with pytest.raises(AttributeError):
        Unguarded().dump({})


def test_unguarded_field_context():
    """Reading ``Field.context`` fails like on marshmallow 4."""
    with pytest.raises(AttributeError):
        Unguarded().fields["value"].context


def test_guarded():
    """Guarded reads fall back to the default."""
    assert Guarded().dump({}) == {"value": "default"}


def test_nested():
    """marshmallow's own nested context propagation keeps working."""
    assert Wrapper().dump({"inner": {"name": "a"}}) == {"inner": {"name": "a"}}
