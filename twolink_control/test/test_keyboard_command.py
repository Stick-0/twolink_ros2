"""Verify keyboard startup cannot publish a joint-mode command on its own."""

from types import MethodType, SimpleNamespace
from unittest.mock import Mock

import pytest

from twolink_control.keyboard_command import PosPublisher


def keyboard_with_feedback():
    keyboard = SimpleNamespace(
        q1_curr=3.099, q2_curr=-2.6409, q1des=3.0, q2des=-2.5,
        delta=0.1, command_active=False, publisher=Mock())
    for name in ('handle_key', 'publish_message'):
        setattr(keyboard, name, MethodType(getattr(PosPublisher, name), keyboard))
    return keyboard


@pytest.mark.parametrize('key', [-1, ord('x'), ord(' '), ord('\n')])
def test_feedback_and_nonmovement_keys_do_not_start_joint_control(key):
    keyboard = keyboard_with_feedback()
    keyboard.handle_key(key)
    keyboard.publish_message()
    assert not keyboard.command_active
    keyboard.publisher.publish.assert_not_called()


def test_movement_key_requires_feedback():
    keyboard = keyboard_with_feedback()
    keyboard.q1des = keyboard.q2des = None
    keyboard.handle_key(ord('e'))
    keyboard.publish_message()
    assert not keyboard.command_active
    keyboard.publisher.publish.assert_not_called()


def test_first_movement_key_uses_latest_feedback_for_both_joints():
    keyboard = keyboard_with_feedback()
    keyboard.handle_key(ord('e'))
    keyboard.publish_message()
    assert keyboard.command_active
    keyboard.publisher.publish.assert_called_once()
    command = keyboard.publisher.publish.call_args.args[0]
    assert command.q1des == pytest.approx(3.199)
    assert command.q2des == pytest.approx(-2.6409)
