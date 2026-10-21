# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

Three core actions a user should be able to perform:

1. **Enter owner and pet information.** The user sets up a basic profile for themselves (name, how much time they have available each day, any preferences) and for their pet (name, species/breed, and any care needs). Everything else in the app hangs off this profile.
2. **Add and edit care tasks.** The user can create tasks such as walks, feeding, medication, enrichment, or grooming, giving each one at least a duration and a priority. They can also change or remove a task later as the pet's needs change.
3. **Generate and view a daily plan.** The user asks the app to build today's schedule from their tasks, given their available time and priorities. The app displays the plan clearly and explains why it included, ordered, or left out each task.

My initial UML has four classes, kept deliberately small:

- **Task** (dataclass): one unit of care, such as a walk, feeding, or medication. It holds a title, category, duration, priority, an optional preferred time, and a completed flag. It is responsible for its own state: marking itself complete and applying edits.
- **Pet** (dataclass): a pet's profile (name, species, age) plus the list of tasks that pet needs. It is responsible for managing that list: adding and removing tasks and reporting which ones are still pending.
- **Owner**: the user, with their name, how many minutes they have available per day, and their preferences. It owns the list of pets and is responsible for adding and removing them. It also gathers every task across all pets so the scheduler has a single place to look.
- **Scheduler**: the "brain". It takes an Owner, reads the pending tasks and the owner's time limit, and builds the daily plan by selecting and ordering tasks by priority. It also records and returns an explanation of why each task was included, ordered, or dropped.

Relationships: an Owner has many Pets, a Pet has many Tasks, and the Scheduler depends on the Owner (and, through it, the Tasks) without owning them. Keeping the scheduling logic in its own class means the data classes stay simple and the planning rules can change without touching them.

**b. Design changes**

Yes. After reviewing the skeleton for missing relationships and bottlenecks, I made three changes before writing any scheduling logic:

1. **Priority is now an `IntEnum` (`LOW=1, MEDIUM=2, HIGH=3`) instead of a string.** Sorting strings alphabetically puts "low" before "medium" and only puts "high" first by luck. Numeric values make "highest priority first" a plain sort and prevent typos like `"hgih"`.
2. **`Task` gained a `pet_name` field, set by `Pet.add_task`.** `Owner.get_all_tasks()` flattens every pet's tasks into one list, and with two pets a plan entry like "Walk" would have no way to say which pet it is for. Tagging the task fixes this without adding a new class.
3. **`Task.__post_init__` validation and a "rebuild from scratch" rule for `Scheduler.generate_plan()`.** Validation (positive duration, valid priority) keeps bad data out of the scheduler. Rebuilding `plan` and `explanations` on every call stops a stored plan from going stale when tasks change.

I considered adding a `ScheduledItem` class (task, start time, reason) but held off. It would add a fifth class before I know I need start times, and I can introduce it later if the plan display needs it. I also left `Owner.preferences` as plain strings until the scheduler actually uses them.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

I used an AI coding assistant (Claude Code) to turn my class skeleton into a working implementation, write a CLI demo (`main.py`), draft the first pytest tests, and add docstrings. The most helpful prompts were specific about requirements: for example, telling it the `Scheduler` had to read tasks through `Owner.get_all_tasks()` rather than from a single pet, and pasting the exact output format I wanted from the README.

**b. Judgment and verification**

- **What it suggested:** a `Scheduler` that selects pending tasks by priority (using owner preferences, time, and duration as tie-breakers) until the time budget runs out, then lists them in time order. It also added a `frequency` field to `Task`, because the assignment asks for one and my skeleton didn't have it.
- **What I accepted:** the scheduling approach and the `frequency` field (I updated the UML to match).
- **What I rejected or changed:** the first version of `main.py` printed a single table of all tasks followed by a "Why this plan" list. That wasn't the format I wanted, so I asked for the per-pet "Daily plan for ..." layout shown in the README instead. The em dash in that format also came out garbled in the Windows terminal, which led to a fix that forces UTF-8 output.
- **How I verified it:** I ran `python main.py` and checked that the plan made sense by hand. The 90-minute budget fit four tasks (80 minutes), and the 20-minute low-priority "Brush coat" was correctly skipped. I also ran `python -m pytest` and confirmed both tests pass.

---

## 4. Testing and Verification

**a. What you tested**

- `mark_complete()` changes a task's `completed` flag from `False` to `True`.
- `Pet.add_task()` increases the pet's task count and tags the task with the pet's name.

These are the building blocks the scheduler relies on: it filters out completed tasks and uses `pet_name` to show which pet each task belongs to.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
