# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> Unit 3 is implemented: the tools run independently and the agent branches
> on search results. Unit 4 sections below remain for the next unit.
>
> **Submission repository:** [manasmaddi/ai201-project2-fitfindr-starter-v2026](https://github.com/manasmaddi/ai201-project2-fitfindr-starter-v2026). Keep this same URL for the next unit.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr takes a thrift-shopping request such as “vintage graphic tee under $30, size M” and searches 40 local mock listings. It filters by size and budget, selects the best keyword match, suggests outfits using saved wardrobe pieces, and writes a short fit-card caption through Gemini. With an empty wardrobe it gives general styling ideas; with no matching listing it stops and suggests changes to the search. This Unit 3 build runs locally from the terminal.


---

## Tool Inventory

### `search_listings`

- **What it does:** Load listings through `load_listings()`, filter size and budget, and rank by case-insensitive keyword overlap across title, description, category, style tags, colors, and brand. Whole words match; ties retain dataset order.
- **Inputs:** `description: str`, `size: str | None = None`, `max_price: float | None = None`.
- **Returns:** Up to `config.SEARCH_RESULT_LIMIT` listing dictionaries, best match first, containing `id`, `title`, `description`, `category`, `style_tags: list[str]`, `size`, `condition`, `price: float`, `colors: list[str]`, `brand: str | None`, and `platform`. Price is an inclusive ceiling. Size tokens match case-insensitively: `M` matches `S/M`; `S` does not match `US 9`; `L` does not match `XL`; `8` matches `US 8` but not `US 8.5`; `W30` matches `W30 L30`. Parenthetical fit notes are ignored. Compound requested sizes must have all their tokens present. `One Size` is matched explicitly, not treated as every size.
- **When it has nothing:** Return `[]`, including a blank description or zero keyword matches.

### `suggest_outfit`

- **What it does:** Ask the model through the starter's `generate()` adapter for one or two outfits using the selected thrift item and named wardrobe pieces.
- **Inputs:** `new_item: dict` (a listing), `wardrobe: dict` with `items: list[dict]`.
- **Returns:** A non-empty string naming the new item and specific pieces the user owns. A missing brand does not prevent styling.
- **When it has nothing:** An empty wardrobe requests general styling advice without claiming the user owns suggested pieces. If the model returns blank text, return brief general styling advice.

### `create_fit_card`

- **What it does:** Ask the model through `generate()` for a social caption about the find and outfit.
- **Inputs:** `outfit: str`, `new_item: dict` (a listing).
- **Returns:** A two-to-four sentence caption with a specific vibe, mentioning the item's title, price, and platform once each. If the model returns blank text, return a short caption using the supplied facts.
- **When it has nothing:** For an empty or whitespace-only outfit, return `No outfit suggestion was provided. Add an outfit before creating a fit card.` without calling the model.

---

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, store a message naming changes to keywords, size, or budget in `session["error"]` and stop; otherwise select the first result, suggest an outfit, and create a fit card.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regular expressions extract an optional `size` (including `US 8`, `W30 L30`, or `S/M`) and inclusive price ceiling such as `under $30` or `max $30`. Those phrases and conversational filler are removed from the keyword description. Unsupported phrasing is not interpreted semantically.

**What moves through the session:** `query` → `parsed` → `search_results` → `selected_item` → `outfit_suggestion` → `fit_card`. `wardrobe` is stored when the session starts. Each tool result is saved before the next tool reads its inputs from the session. `trace.check_iterations()` enforces `config.MAX_ITERATIONS`. Empty search leaves the selected item, outfit, and fit card as `None`.

---

## Sample Run

Commands below use the project's Python 3.13 virtual environment. After activating it, `python` can replace `.venv/bin/python`. Outputs are real terminal output; model wording can vary.

**One full query**

```text
$ .venv/bin/python app.py ask 'vintage graphic tee under $30, size M'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Outfit 1: Y2K Streetwear Contrast
- Top: Y2K Baby Tee — Butterfly Print
- Bottoms: Baggy straight-leg jeans, dark wash
- Shoes: Chunky white sneakers
- Accessories: Black crossbody bag

Why it works: This pairing plays on the classic Y2K silhouette contrast. The fitted, cropped length of the baby tee balances out the voluminous, high-waisted fit of the baggy dark wash jeans, while the white sneakers tie in the white tones of the butterfly graphic.


Outfit 2: Edgy Casual Mix
- Top: Y2K Baby Tee — Butterfly Print
- Outerwear: Vintage black denim jacket
- Bottoms: Wide-leg khaki trousers
- Shoes: Black combat boots
- Accessories: Brown leather belt

Why it works: The fitted pastel and white butterfly tee adds a soft touch against the structured earth tones of the wide-leg khaki trousers. Layering the slightly cropped black denim jacket and finishing with black combat boots grounds the sweeter Y2K print with an effortless, grunge-leaning edge.

  Fit card: Channeling total 2000s mall energy with this Y2K Baby Tee — Butterfly Print, especially paired with wide-leg khaki trousers and chunky boots for that perfect grunge-leaning edge. I spotted it on depop for $18.00 and can't get over how good the pastel graphic looks with earth tones. Such an easy piece to throw on and instantly make the outfit.

1 model calls this session, 1 served from cache, 464 prompt + 83 output tokens
```

**The three tools, tested one at a time**

Each command prints one line, including the empty case. Embedded `\n` sequences in outfit text are literal escapes in that printed dictionary. These standalone calls were checked before wiring the loop.

```text
$ .venv/bin/python -c 'from tools import search_listings; print({"matches": [(x["id"], x["size"], x["price"]) for x in search_listings("graphic tee", size="M", max_price=18)], "empty": search_listings("unicorn spacesuit", size="XXS", max_price=0)})'
{'matches': [('lst_002', 'S/M', 18.0), ('lst_017', 'S/M', 15.0)], 'empty': []}
```

```text
$ .venv/bin/python -c 'from tools import suggest_outfit; from utils.data_loader import load_listings, get_example_wardrobe, get_empty_wardrobe; item=load_listings()[1]; print({"wardrobe": suggest_outfit(item, get_example_wardrobe()), "empty_wardrobe": suggest_outfit(item, get_empty_wardrobe())})'
{'wardrobe': 'Outfit 1: Y2K Streetwear Contrast\n- Top: Y2K Baby Tee — Butterfly Print\n- Bottoms: Baggy straight-leg jeans, dark wash\n- Shoes: Chunky white sneakers\n- Accessories: Black crossbody bag\n\nWhy it works: This pairing plays on the classic Y2K silhouette contrast. The fitted, cropped length of the baby tee balances out the voluminous, high-waisted fit of the baggy dark wash jeans, while the white sneakers tie in the white tones of the butterfly graphic.\n\n\nOutfit 2: Edgy Casual Mix\n- Top: Y2K Baby Tee — Butterfly Print\n- Outerwear: Vintage black denim jacket\n- Bottoms: Wide-leg khaki trousers\n- Shoes: Black combat boots\n- Accessories: Brown leather belt\n\nWhy it works: The fitted pastel and white butterfly tee adds a soft touch against the structured earth tones of the wide-leg khaki trousers. Layering the slightly cropped black denim jacket and finishing with black combat boots grounds the sweeter Y2K print with an effortless, grunge-leaning edge.', 'empty_wardrobe': '1. Pair the baby tee with low-rise baggy cargo pants and chunky platform sneakers for an authentic Y2K streetwear look.\n2. Layer it under a slip dress or pair it with a pleated mini skirt and shoulder bag for a sweet, nostalgic aesthetic.'}
```

```text
$ AI201_CACHE=0 .venv/bin/python -c 'from tools import create_fit_card; from utils.data_loader import load_listings; item=load_listings()[1]; outfit="Baggy dark wash jeans and chunky white sneakers for a relaxed Y2K vibe"; print({"cards": [create_fit_card(outfit, item) for _ in range(3)], "empty_outfit": create_fit_card("   ", item)})'
{'cards': ['Scored this Y2K Baby Tee — Butterfly Print on depop for $18.00 and I am obsessed. It has the absolute cutest early 2000s graphic and fits like a dream. Throwing it on with baggy dark wash jeans and chunky white sneakers gives it that perfect effortless, relaxed Y2K vibe.', 'Paired this Y2K Baby Tee — Butterfly Print with some baggy dark wash jeans and chunky white sneakers for the ultimate relaxed Y2K vibe. Found it on depop for just $18.00 and I am low-key obsessed with the pastel graphic.', "Found this Y2K Baby Tee — Butterfly Print on depop for $18.00 and I am obsessed. I'd style it with baggy dark wash jeans and chunky white sneakers for a relaxed Y2K vibe. It’s giving total early 2000s mall goth energy in the best way possible."], 'empty_outfit': 'No outfit suggestion was provided. Add an outfit before creating a fit card.'}
```

The three uncached captions above were read and are different from each other. `TEMPERATURE` remains `0.9`; `AI201_CACHE=0` disables the default response cache for that command, so all three captions came from fresh model calls. The outfit output names saved pieces when the wardrobe is populated and offers general ideas when it is empty. No tool is hardcoded in place of its implementation; the model tools include fallbacks only for blank model text.

**Empty-search branch**

```text
$ .venv/bin/python app.py ask 'designer ballgown size XXS under $5'

  No listings matched this search. Try broader keywords (for example, 'tee'), change or remove the size filter, or raise the price ceiling.

0 model calls this session
```

That message gives a reader three concrete next attempts: use a broader term such as `tee`, change or omit `size XXS`, or raise `under $5`. It has not yet received a breakout-group or external Claude review.

**Session and state checks**

I printed the completed happy-path and impossible-query sessions from the terminal. The happy path stored `lst_002` in `selected_item`, along with a non-empty outfit and fit card. Wrapping the real `suggest_outfit` call confirmed `outfit.call_args.args[0] is session["selected_item"]` printed `True`. The impossible query stored `{"description": "designer ballgown", "size": "XXS", "max_price": 5.0}` in `parsed`, `[]` in `search_results`, and left `selected_item`, `outfit_suggestion`, and `fit_card` as `None`.

Focused local checks also assert the exact tool arguments against stored session values, verify that neither model tool runs after an empty search, and exercise size boundaries, an inclusive price ceiling, a zero budget, blank inputs, empty-wardrobe prompt selection, and the iteration limit. These checks use mocks for model responses and do not measure model quality over five tries; that evaluation belongs to Unit 4.

```text
$ .venv/bin/python -m unittest test_unit3 -v
Ran 14 tests
OK
```

---

## How I Used AI

**Moment 1 — implementing search from the spec**

- *What I asked for:* I asked Codex to inspect this repository and complete the Unit 3 milestones, including the three tools and their empty cases.
- *What came back:* It found my unfinished search tested whether an entire listing description appeared inside the query, and pointed out that substring size matching could confuse `S` with `US 9` and `L` with `XL`.
- *What I changed:* With Codex's help, I replaced the unfinished search with whole-word keyword scoring, independent size and inclusive price filters, token-based size matching, and an explicit `[]` for no matches. The terminal test found the two medium-compatible tees at or below $18 and returned `[]` for the impossible search.

**Moment 2 — checking the branch and state**

- *What I asked for:* In the same request, I asked Codex to wire the loop so each tool stores its result in the session and an impossible query stops early.
- *What came back:* It implemented a loop that branches on the stored search results, plus focused checks comparing the actual arguments sent to the next tool with the session. It also found that my criterion 3 covered an empty wardrobe but omitted the required state check.
- *What I changed:* With Codex's help, I added observable state requirements to criterion 3, stored every result before the next call, and used an empty-search message that names keywords, size, and price changes. The happy path passed the stored selected item to styling; the impossible query made zero model calls and left its fit card as `None`.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [x] criteria.md has five numbered criteria, each with a target
       [x] Each criterion has a reason underneath it
       [x] All five unit 3 sections above have real content
       [x] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [x] Planning Loop names the branch rule and agent.py::run_agent
       [x] Sample Run: one full query plus the three per-tool tests, as text
       [x] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
