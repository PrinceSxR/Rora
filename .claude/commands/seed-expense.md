---
description: Seed random dummy expenses for a user
allowed-tools: Read, Bash(python3:*)
argument-hint: [user_id] [count]
---

Read database/db.py to understand the expenses table schema,
the CATEGORIES list, and the get_db() helper.

Then write and run a Python script using Bash that:

1. Uses user_id = first argument in "$ARGUMENTS" (default: the most
   recently created user) and count = second argument (default: 10).
   Abort with a clear message if the user does not exist.

2. Generates `count` realistic expenses for an Indian user:
   - amount: realistic INR values per category
     (e.g. Food 80–1500, Transport 20–800, Bills 300–5000)
   - category: only values from CATEGORIES
   - date: random dates within the last 60 days (YYYY-MM-DD)
   - description: realistic (e.g. "Swiggy order", "Ola ride",
     "Jio recharge", "Apollo Pharmacy")

3. Inserts all rows in a single transaction with parameterized
   queries via get_db().

4. Prints a confirmation: the user, the number inserted, the total
   amount, and a per-category breakdown.
