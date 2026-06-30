from datetime import time

from pawpal_system import Owner, Pet, Priority, Scheduler, TimeConstraint, Task

dino = Pet("Dino")
baby_puss = Pet("Baby Puss")

owner = Owner("Fred")
owner.add_pet(dino)
owner.add_pet(baby_puss)

work = TimeConstraint(title="Work", start_time=time(8,0), end_time=time(18,0))

walk = Task(title="Walk", duration=60, priority=Priority.HIGH, pets=[dino])
put_out = Task(title="Put out", duration=10, priority=Priority.MEDIUM,
               preferred_time=time(21, 0), pets=[baby_puss])
feed = Task(title="Feed", duration=60, priority=Priority.HIGH,
            preferred_time=time(18, 0), pets=[dino, baby_puss])

scheduler = Scheduler()
scheduler.add_task(walk)
scheduler.add_task(put_out)
scheduler.add_task(feed)

plan = scheduler.generate_plan()
print(plan.summary())