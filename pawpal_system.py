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
    """A care task. duration + priority are user inputs; scheduled_* are
    assigned by DaySchedule."""

    duration: int  # minutes
    priority: Priority
    preferred_time: time | None = None
    scheduled_start: time | None = None
    scheduled_end: time | None = None
    pets: list["PetProfile"] = field(default_factory=list)

    @classmethod
    def create_task(cls, title: str, duration: int, priority: Priority) -> "Task":
        raise NotImplementedError

    def edit_task_info(self) -> None:
        raise NotImplementedError


@dataclass
class PetProfile:
    name: str
    tasks: list[Task] = field(default_factory=list)
    owner: "UserProfile | None" = None

    @classmethod
    def create_pet_profile(cls, name: str) -> "PetProfile":
        raise NotImplementedError

    def edit_info(self) -> None:
        raise NotImplementedError


@dataclass
class UserProfile:
    name: str
    pets: list[PetProfile] = field(default_factory=list)

    @classmethod
    def create_user_profile(cls, name: str) -> "UserProfile":
        raise NotImplementedError

    def edit_info(self) -> None:
        raise NotImplementedError

    def add_pet(self, pet: PetProfile) -> None:
        raise NotImplementedError


@dataclass
class DailyPlan:
    """Result of generate_plan() — what got scheduled, what didn't, and why."""

    scheduled_tasks: list[Task] = field(default_factory=list)
    unscheduled_tasks: list[Task] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class DaySchedule:
    """Scheduling engine: holds tasks + constraints and builds a DailyPlan."""

    tasks: list[Task] = field(default_factory=list)
    constraints: list[TimeConstraint] = field(default_factory=list)

    def generate_plan(self) -> DailyPlan:
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

    def assign_tasks_to_pet(self, pet: PetProfile) -> None:
        raise NotImplementedError
