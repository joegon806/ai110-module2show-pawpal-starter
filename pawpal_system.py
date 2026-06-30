"""PawPal+ domain model.

Skeleton generated from diagrams/uml.mmd — attributes and empty method
stubs only. Fill in the logic incrementally (see README workflow step 4).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from enum import IntEnum


class Priority(IntEnum):
    """Task priority. IntEnum so tasks sort high -> low naturally."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass(kw_only=True)
class AllocatedTime:
    """Base for anything that occupies a span on the day's timeline."""

    title: str
    start_time: time | None = None
    end_time: time | None = None

    def overlaps(self, other: "AllocatedTime") -> bool:
        """Return True if this span overlaps `other`'s span."""
        raise NotImplementedError


@dataclass(kw_only=True)
class TimeConstraint(AllocatedTime):
    """A fixed, immovable block the scheduler must work around."""

    @classmethod
    def create_time_constraint(cls, title: str, start_time: time, end_time: time) -> "TimeConstraint":
        raise NotImplementedError

    def edit_time_constraint(self) -> None:
        raise NotImplementedError


@dataclass(kw_only=True)
class Task(AllocatedTime):
    """A care task. duration + priority are user inputs; the placed span is
    stored in the inherited start_time/end_time, set by Scheduler."""

    duration: int  # minutes
    priority: Priority
    preferred_time: time | None = None
    # start_time / end_time inherited from AllocatedTime; None until scheduled.
    pets: list["Pet"] = field(default_factory=list)

    @property
    def is_scheduled(self) -> bool:
        return self.start_time is not None

    @classmethod
    def create_task(cls, title: str, duration: int, priority: Priority) -> "Task":
        raise NotImplementedError

    def edit_task_info(self) -> None:
        raise NotImplementedError


@dataclass
class Pet:
    name: str
    owner: "Owner | None" = None
    # A pet's tasks are derived from Scheduler.tasks_for(pet), not stored here,
    # so there is a single source of truth for what gets scheduled.

    @classmethod
    def create_pet(cls, name: str) -> "Pet":
        raise NotImplementedError

    def edit_info(self) -> None:
        raise NotImplementedError


@dataclass
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list)

    @classmethod
    def create_owner(cls, name: str) -> "Owner":
        raise NotImplementedError

    def edit_info(self) -> None:
        raise NotImplementedError

    def add_pet(self, pet: Pet) -> None:
        raise NotImplementedError


@dataclass
class DailyPlan:
    """Result of generate_plan() — what got scheduled, what didn't, and why."""

    scheduled_tasks: list[Task] = field(default_factory=list)
    unscheduled_tasks: list[Task] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class Scheduler:
    """Scheduling engine: holds tasks + constraints and builds a DailyPlan.

    One schedule serves all pets; tasks are attributed to pets via Task.pets.
    day_start/day_end bound the window find_slot() searches within.
    """

    day_start: time = time(7, 0)
    day_end: time = time(22, 0)
    tasks: list[Task] = field(default_factory=list)
    constraints: list[TimeConstraint] = field(default_factory=list)

    def generate_plan(self) -> DailyPlan:
        raise NotImplementedError

    def tasks_for(self, pet: Pet) -> list[Task]:
        """All tasks assigned to `pet` (derived view, not a stored list)."""
        raise NotImplementedError

    def add_task(self, task: Task) -> None:
        raise NotImplementedError

    def remove_task(self, task: Task) -> None:
        raise NotImplementedError

    def has_conflict(self, task: Task) -> bool:
        """True if `task`'s assigned span collides with a constraint or another task."""
        raise NotImplementedError

    def find_slot(self, task: Task) -> time | None:
        """Find a start time for an unscheduled task, or None if no room."""
        raise NotImplementedError

    def add_constraint(self, constraint: TimeConstraint) -> None:
        raise NotImplementedError

    def remove_constraint(self, constraint: TimeConstraint) -> None:
        raise NotImplementedError
