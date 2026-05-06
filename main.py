from __future__ import annotations
from typing import Dict, Set, Optional, Callable, Any
from dataclasses import dataclass, field

class InvalidTransitionError(Exception):
    """Raised when a requested state transition is not allowed."""
    pass

class StateMachine:
    """
    A tiny state machine framework with transition validation.
    Supports entering/exiting state callbacks and optional guard conditions.
    """

    def __init__(self, initial_state: str):
        self.current_state: str = initial_state
        self._transitions: Dict[str, Set[str]] = {}
        self._on_enter: Dict[str, Callable[[], None]] = {}
        self._on_exit: Dict[str, Callable[[], None]] = {}

    def add_state(self, state: str,
                  on_enter: Optional[Callable[[], None]] = None,
                  on_exit: Optional[Callable[[], None]] = None) -> None:
        """Register a state with optional callbacks. Creates entry in transitions map."""
        if state not in self._transitions:
            self._transitions[state] = set()
        if on_enter:
            self._on_enter[state] = on_enter
        if on_exit:
            self._on_exit[state] = on_exit

    def add_transition(self, from_state: str, to_state: str) -> None:
        """Define an allowed transition."""
        self._transitions.setdefault(from_state, set()).add(to_state)
        # Ensure the target state exists in the map
        if to_state not in self._transitions:
            self._transitions[to_state] = set()

    def can_transition_to(self, to_state: str) -> bool:
        """Check whether moving from current state to `to_state` is allowed."""
        return to_state in self._transitions.get(self.current_state, set())

    def transition_to(self, to_state: str) -> bool:
        """
        Attempt to move to `to_state`. Returns True if succeeded,
        raises InvalidTransitionError otherwise.
        """
        if not self.can_transition_to(to_state):
            raise InvalidTransitionError(
                f"Cannot transition from '{self.current_state}' to '{to_state}'"
            )
        # Exit old state
        if self.current_state in self._on_exit:
            self._on_exit[self.current_state]()
        # Change state
        old_state = self.current_state
        self.current_state = to_state
        # Enter new state
        if to_state in self._on_enter:
            self._on_enter[to_state]()
        return True

def main() -> None:
    # Build a simple document lifecycle state machine
    fsm = StateMachine(initial_state="draft")

    # Register states with optional side effects
    fsm.add_state("draft", on_enter=lambda: print("Entered draft mode."))
    fsm.add_state("review", on_exit=lambda: print("Leaving review."))
    fsm.add_state("approved", on_enter=lambda: print("Approved!"))
    fsm.add_state("published", on_enter=lambda: print("Published!"))

    # Allowed transitions
    fsm.add_transition("draft", "review")
    fsm.add_transition("review", "approved")
    fsm.add_transition("approved", "published")
    fsm.add_transition("review", "draft")   # back to draft
    # No transition from published to anything else

    print(f"Initial state: {fsm.current_state}")

    # Demonstrate valid transitions
    for next_state in ["review", "approved", "published"]:
        print(f"Transitioning to '{next_state}'...")
        try:
            fsm.transition_to(next_state)
            print(f"Now in state: {fsm.current_state}")
        except InvalidTransitionError as e:
            print(f"Error: {e}")

    # Try an invalid transition
    print("Attempting invalid transition to 'draft' from 'published'...")
    try:
        fsm.transition_to("draft")
    except InvalidTransitionError as e:
        print(f"Error: {e}")

    # Back to review and then to draft to show multi-step
    print("\nResetting: moving to review then draft...")
    # We need to go from published? can't - so demonstrate on a new instance.
    fsm2 = StateMachine(initial_state="approved")
    fsm2.add_transition("approved", "review")
    fsm2.add_transition("review", "draft")
    fsm2.add_state("draft")
    fsm2.add_state("review")
    fsm2.transition_to("review")
    print(f"fsm2 state: {fsm2.current_state}")
    fsm2.transition_to("draft")
    print(f"fsm2 state: {fsm2.current_state}")

    # Show validation: check if transition is possible
    print(f"\nCan 'draft' -> 'review'? {fsm.can_transition_to('review')}")

if __name__ == "__main__":
    main()