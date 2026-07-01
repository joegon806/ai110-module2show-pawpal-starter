"""PawPal+ domain model.

Skeleton generated from diagrams/uml.mmd — attributes and empty method
stubs only. Fill in the logic incrementally (see README workflow step 4).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import IntEnum


class Priority(IntEnum):
    """Task priority. IntEnum so tasks sort high -> low naturally."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


def _shift(start: time, minutes: int) -> time:
    """Return the clock time ``minutes`` after ``start`` (same day)."""
    return (datetime.combine(date.min, start) + timedelta(minutes=minutes)).time()


@dataclass(kw_only=True)
class AllocatedTime:
    """Base for anything that occupies a span on the day's timeline.

    Spans are treated as half-open intervals [start_time, end_time): a block
    that ends exactly when another begins does NOT overlap it, so back-to-back
    tasks (08:00-08:30 and 08:30-09:00) are allowed.
    """

    title: str
    description: str = ""
    start_time: time | None = None
    end_time: time | None = None

    @property
    def is_placed(self) -> bool:
        """True once both ends of the span are set."""
        return self.start_time is not None and self.end_time is not None

    def overlaps(self, other: "AllocatedTime") -> bool:
        """Return True if this span overlaps ``other``'s span.

        An unplaced span (missing either end) occupies no time, so it can
        never overlap anything.
        """
        if not self.is_placed or not other.is_placed:
            return False
        # Half-open overlap: a starts before b ends AND b starts before a ends.
        return self.start_time < other.end_time and other.start_time < self.end_time

    def contains(self, moment: time) -> bool:
        """True if ``moment`` falls within this span, [start, end)."""
        if not self.is_placed:
            return False
        return self.start_time <= moment < self.end_time


@dataclass(kw_only=True)
class TimeConstraint(AllocatedTime):
    """A fixed, immovable block the scheduler must work around (e.g. work
    hours, a vet appointment).

    Unlike a Task, a constraint is always placed: it has concrete start/end
    times from the moment it is created. Construct it directly, e.g.
    ``TimeConstraint(title="work", start_time=time(9), end_time=time(17))``;
    the span is validated so it is never empty or inverted.
    """

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not self.is_placed:
            raise ValueError(
                f"TimeConstraint '{self.title}' needs both a start_time and an end_time."
            )
        if self.start_time >= self.end_time:
            raise ValueError(
                f"TimeConstraint '{self.title}' end_time ({self.end_time}) must be "
                f"after start_time ({self.start_time})."
            )

    def edit_time_constraint(
        self,
        *,
        title: str | None = None,
        description: str | None = None,
        start_time: time | None = None,
        end_time: time | None = None,
    ) -> None:
        """Update any of the fields in place; re-validates the resulting span."""
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if start_time is not None:
            self.start_time = start_time
        if end_time is not None:
            self.end_time = end_time
        self._validate()


@dataclass(kw_only=True)
class Task(AllocatedTime):
    """A care task. duration + priority are user inputs; the placed span is
    stored in the inherited start_time/end_time, set by Scheduler."""

    duration: int  # minutes
    priority: Priority
    preferred_time: time | None = None
    # title, description, start_time, end_time inherited from AllocatedTime.
    # start_time / end_time are None until the task is scheduled.
    pets: list["Pet"] = field(default_factory=list)
    completed: bool = False

    def __post_init__(self) -> None:
        if self.duration <= 0:
            raise ValueError(
                f"Task '{self.title}' duration must be positive, got {self.duration}."
            )

    @property
    def is_scheduled(self) -> bool:
        """True once the scheduler has placed this task on the timeline."""
        return self.is_placed

    def schedule_at(self, start: time) -> None:
        """Place the task at ``start``; its end is start + duration."""
        self.start_time = start
        self.end_time = _shift(start, self.duration)

    def unschedule(self) -> None:
        """Remove the task from the timeline so it can be re-placed."""
        self.start_time = None
        self.end_time = None

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Reset this task to not-yet-done."""
        self.completed = False

    def edit_task_info(
        self,
        *,
        title: str | None = None,
        description: str | None = None,
        duration: int | None = None,
        priority: Priority | None = None,
        preferred_time: time | None = None,
        pets: list["Pet"] | None = None,
    ) -> None:
        """Update any subset of fields by keyword. Changing the duration of an
        already-scheduled task re-derives its end time from its current start."""
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if duration is not None:
            if duration <= 0:
                raise ValueError(f"duration must be positive, got {duration}.")
            self.duration = duration
            if self.is_scheduled:
                self.schedule_at(self.start_time)
        if priority is not None:
            self.priority = priority
        if preferred_time is not None:
            self.preferred_time = preferred_time
        if pets is not None:
            self.pets = pets


@dataclass
class Pet:
    # Identifying info
    name: str
    species: str = ""
    breed: str = ""
    notes: str = ""
    owner: "Owner | None" = None
    # The pet's own care tasks. Kept in sync with each Task.pets back-reference
    # via add_task/remove_task.
    tasks: list[Task] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Pet name must not be empty.")

    def edit_info(
        self,
        *,
        name: str | None = None,
        species: str | None = None,
        breed: str | None = None,
        notes: str | None = None,
    ) -> None:
        """Update identifying info. Ownership is managed via Owner.add_pet."""
        if name is not None:
            if not name.strip():
                raise ValueError("Pet name must not be empty.")
            self.name = name
        if species is not None:
            self.species = species
        if breed is not None:
            self.breed = breed
        if notes is not None:
            self.notes = notes

    # --- task management (keeps both sides of the Pet<->Task link in sync) ---

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet. Idempotent."""
        if all(t is not task for t in self.tasks):
            self.tasks.append(task)
        if all(p is not self for p in task.pets):
            task.pets.append(self)

    def remove_task(self, task: Task) -> None:
        """Detach a task from this pet, clearing the back-reference."""
        self.tasks = [t for t in self.tasks if t is not task]
        task.pets = [p for p in task.pets if p is not self]

    def list_tasks(self, *, include_completed: bool = True) -> list[Task]:
        """Return this pet's tasks; set include_completed=False for pending only."""
        if include_completed:
            return list(self.tasks)
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Owner name must not be empty.")

    def edit_info(self, *, name: str | None = None) -> None:
        """Rename the owner."""
        if name is not None:
            if not name.strip():
                raise ValueError("Owner name must not be empty.")
            self.name = name

    def add_pet(self, pet: Pet) -> None:
        """Add a pet and keep both sides of the relationship in sync.

        Idempotent: adding the same pet twice is a no-op rather than a
        duplicate. Also rehomes the pet if it currently belongs elsewhere.
        """
        if pet in self.pets:
            return
        if pet.owner is not None and pet.owner is not self:
            pet.owner.remove_pet(pet)
        self.pets.append(pet)
        pet.owner = self

    def remove_pet(self, pet: Pet) -> None:
        """Detach a pet, clearing the back-reference if it pointed here."""
        if pet in self.pets:
            self.pets.remove(pet)
        if pet.owner is self:
            pet.owner = None


@dataclass
class DailyPlan:
    """Result of generate_plan() — what got scheduled, what didn't, and why.

    The scheduler builds a plan incrementally with schedule()/skip(); note()
    records a line of reasoning. summary() renders it for the CLI/Streamlit UI.
    """

    scheduled_tasks: list[Task] = field(default_factory=list)
    unscheduled_tasks: list[Task] = field(default_factory=list)
    reasoning: str = ""

    @property
    def is_complete(self) -> bool:
        """True if every task found a slot (nothing was skipped)."""
        return not self.unscheduled_tasks

    def note(self, message: str) -> None:
        """Append a line of human-readable reasoning."""
        self.reasoning += message if not self.reasoning else "\n" + message

    def schedule(self, task: Task) -> None:
        """Record a task as placed and note where it landed."""
        self.scheduled_tasks.append(task)
        self.note(
            f"Scheduled '{task.title}' at {task.start_time.strftime('%H:%M')} "
            f"({task.duration} min, {task.priority.name.lower()} priority)."
        )

    def skip(self, task: Task, reason: str) -> None:
        """Record a task that could not be placed, with the reason why."""
        self.unscheduled_tasks.append(task)
        self.note(f"Skipped '{task.title}': {reason}")

    def summary(self) -> str:
        """Render the plan as plain text, scheduled tasks in time order."""
        lines: list[str] = []
        for t in sorted(self.scheduled_tasks, key=lambda t: t.start_time):
            lines.append(
                f"{t.start_time.strftime('%H:%M')} — {t.title} "
                f"({t.duration} min) [priority: {t.priority.name.lower()}]"
            )
        for t in self.unscheduled_tasks:
            lines.append(
                f"(unscheduled) {t.title} ({t.duration} min) "
                f"[priority: {t.priority.name.lower()}]"
            )
        if self.reasoning:
            lines += ["", "Reasoning:", self.reasoning]
        return "\n".join(lines)


@dataclass
class Scheduler:
    """Scheduling engine: plans the tasks of the pets it serves, around a set
    of constraints, into a DailyPlan.

    Pet is the single source of truth for tasks: `tasks` is derived from the
    scheduled pets, never stored separately. day_start/day_end bound the window
    find_slot() searches within.
    """

    day_start: time = time(7, 0)
    day_end: time = time(22, 0)
    pets: list[Pet] = field(default_factory=list)
    constraints: list[TimeConstraint] = field(default_factory=list)

    @property
    def tasks(self) -> list[Task]:
        """Every task across the scheduled pets, de-duplicated by identity
        (a task shared by two pets still appears once)."""
        collected: list[Task] = []
        for pet in self.pets:
            for task in pet.tasks:
                if all(t is not task for t in collected):
                    collected.append(task)
        return collected

    # --- membership ---

    def add_pet(self, pet: Pet) -> None:
        """Bring a pet (and therefore its tasks) under this scheduler."""
        if all(p is not pet for p in self.pets):
            self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        self.pets = [p for p in self.pets if p is not pet]

    def add_constraint(self, constraint: TimeConstraint) -> None:
        if all(c is not constraint for c in self.constraints):
            self.constraints.append(constraint)

    def remove_constraint(self, constraint: TimeConstraint) -> None:
        self.constraints = [c for c in self.constraints if c is not constraint]

    def tasks_for(self, pet: Pet) -> list[Task]:
        """The tasks belonging to `pet` (a thin pass-through to pet.tasks)."""
        return [t for t in self.tasks if any(p is pet for p in t.pets)]

    # --- conflict detection & slot finding ---

    def has_conflict(self, task: Task) -> bool:
        """True if `task`'s placed span collides with a constraint or another
        scheduled task. The task itself is excluded from the comparison."""
        if not task.is_scheduled:
            return False
        if any(task.overlaps(c) for c in self.constraints):
            return True
        return any(
            other is not task and other.is_scheduled and task.overlaps(other)
            for other in self.tasks
        )

    def _is_free(self, start: time, duration: int, ignore: Task | None = None) -> bool:
        """True if a `duration`-minute block starting at `start` fits inside the
        day window and overlaps no constraint or other scheduled task."""
        end = _shift(start, duration)
        if start < self.day_start or end > self.day_end or end <= start:
            return False  # out of bounds, or wrapped past midnight
        busy = list(self.constraints) + [
            t for t in self.tasks if t is not ignore and t.is_scheduled
        ]
        return all(not (start < b.end_time and b.start_time < end) for b in busy)

    def find_slot(self, task: Task) -> time | None:
        """Earliest start time where `task` fits, or None if there's no room.

        Honors `task.preferred_time` as a soft target when that exact slot is
        free; otherwise returns the earliest gap in the day.
        """
        if task.preferred_time is not None and self._is_free(
            task.preferred_time, task.duration, ignore=task
        ):
            return task.preferred_time
        # The earliest feasible start is day_start or right after a busy block.
        candidates = {self.day_start}
        candidates.update(c.end_time for c in self.constraints)
        candidates.update(t.end_time for t in self.tasks if t is not task and t.is_scheduled)
        for start in sorted(candidates):
            if start >= self.day_start and self._is_free(start, task.duration, ignore=task):
                return start
        return None

    # --- planning ---

    def generate_plan(self) -> DailyPlan:
        """Greedily place tasks highest-priority-first into the day window,
        recording each decision (and the reason for any skip) in the plan."""
        plan = DailyPlan()
        for t in self.tasks:
            t.unschedule()  # start fresh so re-running is idempotent

        def order_key(t: Task) -> tuple:
            preferred = t.preferred_time if t.preferred_time is not None else time.max
            return (-int(t.priority), preferred, t.title)

        for task in sorted(self.tasks, key=order_key):
            slot = self.find_slot(task)
            if slot is None:
                plan.skip(
                    task,
                    f"no free {task.duration}-min slot between "
                    f"{self.day_start:%H:%M} and {self.day_end:%H:%M}",
                )
                continue
            task.schedule_at(slot)
            plan.schedule(task)
        return plan

    def start_new_day(self) -> DailyPlan:
        """Begin a fresh day: clear every task's completion status, then
        rebuild the schedule. Returns the new plan."""
        for task in self.tasks:
            task.mark_incomplete()
        return self.generate_plan()
