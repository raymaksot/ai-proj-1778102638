import pytest
from main import StateMachine, InvalidTransitionError

class TestStateMachine:

    def test_init(self):
        fsm = StateMachine(initial_state="idle")
        assert fsm.current_state == "idle"
        assert fsm._transitions == {}
        assert fsm._on_enter == {}
        assert fsm._on_exit == {}

    def test_add_state_registers_states_and_callbacks(self):
        fsm = StateMachine("start")
        called = []
        fsm.add_state("start", on_enter=lambda: called.append("enter_start"),
                       on_exit=lambda: called.append("exit_start"))
        fsm.add_state("end", on_enter=lambda: called.append("enter_end"))
        assert "start" in fsm._transitions
        assert fsm._transitions["start"] == set()
        assert fsm._on_enter["start"] is not None
        assert fsm._on_exit["start"] is not None
        assert "end" in fsm._transitions
        assert fsm._on_enter["end"] is not None
        # callbacks not called until transition
        assert called == []

    def test_add_transition_creates_allowed_paths(self):
        fsm = StateMachine("A")
        fsm.add_state("A")
        fsm.add_state("B")
        fsm.add_transition("A", "B")
        fsm.add_transition("A", "C")  # target C will be auto-created in transitions map
        assert "B" in fsm._transitions["A"]
        assert "C" in fsm._transitions["A"]
        assert "C" in fsm._transitions  # auto-created
        assert fsm._transitions["C"] == set()

    def test_can_transition_to_existing_path(self):
        fsm = StateMachine("draft")
        fsm.add_transition("draft", "review")
        assert fsm.can_transition_to("review")  # current_state "draft" is in transitions?
        # "draft" was not explicitly added, but add_transition auto-added "draft" to transitions map.
        # So it should have "review" in its set.
        assert fsm.can_transition_to("review") == True
        assert not fsm.can_transition_to("approved")

    def test_can_transition_to_when_current_state_not_in_map(self):
        fsm = StateMachine("orphan")  # not added anywhere
        # no transitions defined, so _transitions is empty
        assert not fsm.can_transition_to("any")
        fsm.add_transition("draft", "review")
        # still current_state "orphan" not in map
        assert not fsm.can_transition_to("review")

    def test_transition_to_success_returns_true_and_changes_state(self):
        fsm = StateMachine("A")
        fsm.add_transition("A", "B")
        success = fsm.transition_to("B")
        assert success is True
        assert fsm.current_state == "B"

    def test_transition_to_calls_exit_and_enter_callbacks(self):
        log = []
        fsm = StateMachine("init")
        fsm.add_state("init", on_exit=lambda: log.append("exit_init"))
        fsm.add_state("next", on_enter=lambda: log.append("enter_next"))
        fsm.add_transition("init", "next")
        fsm.transition_to("next")
        assert log == ["exit_init", "enter_next"]

    def test_transition_to_raises_error_on_invalid_move(self):
        fsm = StateMachine("locked")
        with pytest.raises(InvalidTransitionError) as excinfo:
            fsm.transition_to("open")
        assert "Cannot transition from 'locked' to 'open'" in str(excinfo.value)

    def test_duplicate_state_add_overwrites_callbacks_only_when_provided(self):
        fsm = StateMachine("s")
        fsm.add_state("s", on_enter=lambda: None)
        assert "s" in fsm._on_enter
        # add again without callbacks – callbacks should remain unchanged (existing ones not cleared)
        fsm.add_state("s")
        assert "s" in fsm._on_enter  # must not be removed
        # add again with new exit callback
        fsm.add_state("s", on_exit=lambda: None)
        assert "s" in fsm._on_exit

    def test_edge_case_transition_from_state_with_no_exits_defined(self):
        fsm = StateMachine("A")
        fsm.add_state("A")  # no callbacks
        fsm.add_state("B")
        fsm.add_transition("A", "B")
        # should not raise, no callbacks called
        assert fsm.transition_to("B") is True
        assert fsm.current_state == "B"

    def test_multiple_transitions_across_paths(self):
        fsm = StateMachine("draft")
        fsm.add_transition("draft", "review")
        fsm.add_transition("review", "approved")
        fsm.add_transition("review", "draft")
        fsm.add_transition("approved", "published")
        fsm.transition_to("review")
        assert fsm.current_state == "review"
        fsm.transition_to("draft")
        assert fsm.current_state == "draft"
        fsm.transition_to("review")
        fsm.transition_to("approved")
        fsm.transition_to("published")
        assert fsm.current_state == "published"
        # published has no outgoing transitions
        assert not fsm.can_transition_to("draft")

    def test_callbacks_receive_no_arguments(self):
        # verify that callbacks are called without arguments (they are Callable[[], None])
        called = []
        fsm = StateMachine("start")
        fsm.add_state("start", on_exit=lambda: called.append(True))
        fsm.add_state("end", on_enter=lambda: called.append(True))
        fsm.add_transition("start", "end")
        fsm.transition_to("end")
        assert len(called) == 2