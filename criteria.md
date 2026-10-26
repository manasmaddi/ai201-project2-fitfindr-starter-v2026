# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
The search uses keyword overlap rather than semantic matching, so alternate
phrasings can miss a listing even when it is relevant. Four of five allows one
such miss while still requiring the full three-tool path to work consistently.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
An empty result list gives the loop a deterministic stopping condition that
does not depend on model wording. Every run should take this branch and tell
the user to change the keywords, size, or price ceiling.

---

## 3. The selected item moves through the session, including with an empty wardrobe

For five matching queries, the listing dictionary passed to `suggest_outfit`
must equal `session["selected_item"]`, and the outfit and item passed to
`create_fit_card` must equal their stored session values, in 5 of 5 tries.
Given a matching listing and a wardrobe with an empty `items` list,
`suggest_outfit` also returns non-empty general styling advice without claiming the
user owns any suggested pieces — in 5 of 5 tries.

**Why this target:**
State transfer is deterministic: the next tool must receive the exact item
stored in the session. An empty wardrobe is a supported input, so it should
always select the general styling prompt. The exact advice can vary, but requiring one particular outfit
would be too strict for a model-generated response.

---

## 4. The fit card mentions the price

I would be unhappy to see a caption that never mentions the price, especially
when `suggest_outfit` gives general advice. The fit card should mention the
selected item's correct price in at least 4 of 5 tries.

**Why this target:**

Because it is the final step in the loop, it is crucial to contain the price
information. Four of five allows an occasional omission from the model while
still requiring the caption to include the price consistently.

---

## 5. Search respects the user's budget

For five searches with explicit price ceilings, every returned listing has a
price less than or equal to the requested ceiling. A listing priced exactly at
the ceiling remains eligible when its keywords and size match.

**Why this target:**
Price filtering compares numeric listing prices and does not call the model,
so zero over-budget results is a reasonable target. Including the boundary
checks that the filter honors the tool's inclusive maximum rather than
discarding an affordable item.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
