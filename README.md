# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🛠️ Implementation Summary

The logic layer lives in `pawpal_system.py` and is made of four classes:

- **`Task`**: one care activity (title, category, duration, priority, preferred time, frequency, completed). It validates its own data on creation and can mark itself complete or apply edits.
- **`Pet`**: a pet's profile plus its list of tasks. `add_task` tags each task with the pet's name so the plan can say who a task is for.
- **`Owner`**: the user's name, daily time budget (`available_minutes`), preferred categories, and pets. `get_all_tasks()` returns every pet's tasks in one list.
- **`Scheduler`**: the planner. `generate_plan()` reads tasks from `Owner.get_all_tasks()` (so it covers every pet), drops completed ones, picks tasks by priority (ties go to preferred categories, then earlier time, then shorter tasks) until the time budget runs out, and returns the chosen tasks in time order. `explain_plan()` says why each task was scheduled or skipped.

`main.py` is a CLI demo that builds an owner with two pets and prints today's schedule. Run it with `python main.py`.

## 🖥️ Sample Output

Output of `python main.py`:

```
Daily plan for Mochi (Dog):
  07:30 — Morning walk (30 min) [priority: high]
  18:00 — Evening walk (30 min) [priority: medium]

Daily plan for Luna (Cat):
  08:00 — Breakfast (10 min) [priority: high]
  12:00 — Litter box (10 min) [priority: medium]
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
collected 10 items

tests\test_pawpal.py ..........                                          [100%]

============================== 10 passed in 0.03s ==============================
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Orders tasks by due date, then preferred time, using `sorted()` with a lambda key. Tasks with no preferred time go last. `generate_plan()` uses it to show the final plan in time order. |
| Priority selection | `Scheduler.generate_plan()` | Picks pending tasks due today (or overdue) by priority. Ties go to the owner's preferred categories, then earlier time, then shorter duration. Tasks that don't fit in the remaining minutes are skipped and explained. |
| Filtering | `Scheduler.filter_tasks(pet_name=, completed=, due_on=)` | Returns tasks that match every filter given. Leave a filter out to ignore it, e.g. `filter_tasks(pet_name="Luna", completed=False)`. |
| Conflict handling | `Scheduler.detect_conflicts()` | Groups pending tasks by (due date, start time) and returns one warning string per shared slot instead of raising an error. Only exact start-time matches count, not overlapping durations. The app shows these as warnings above the schedule. |
| Recurring tasks | `Scheduler.mark_task_complete()`, `Task.next_occurrence()` | Completing a `daily` or `weekly` task adds a fresh copy to the same pet, due `timedelta(days=1)` or `timedelta(weeks=1)` later. `once` tasks don't recur. Future occurrences stay out of today's plan. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
