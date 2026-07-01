from datetime import time

from pawpal_system import Owner, Pet, Priority, Scheduler, TimeConstraint, Task

dino = Pet("Dino")
baby_puss = Pet("Baby Puss")

owner = Owner("Fred")
owner.add_pet(dino)
owner.add_pet(baby_puss)

work = TimeConstraint(title="Work", start_time=time(8,0), end_time=time(18,0))

walk = Task(title="Walk", duration=60, priority=Priority.HIGH)
put_out = Task(title="Put out", duration=10, priority=Priority.MEDIUM,
               preferred_time=time(21, 0))
feed = Task(title="Feed", duration=60, priority=Priority.HIGH,
            preferred_time=time(18, 0))

# Pet is the source of truth for tasks: attach them to pets.
dino.add_task(walk)
baby_puss.add_task(put_out)
dino.add_task(feed)
baby_puss.add_task(feed)  # feed is shared; add_task de-dupes it

# The scheduler plans the tasks of the pets it serves.
scheduler = Scheduler(pets=[dino, baby_puss])
scheduler.add_constraint(work)

plan = scheduler.generate_plan()
print(plan.summary())