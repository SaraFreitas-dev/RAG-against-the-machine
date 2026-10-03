<div align="center">

# 🗂️ 06 — Inverted index and persistence

**How a search over thousands of chunks takes milliseconds, and what to keep on disk**

`📚 Concepts` · `⏱️ ~20 min read` · `🎯 Prerequisite: 05 — BM25`

</div>

---

> [!IMPORTANT]
> **TL;DR** — Scoring every chunk for every question is wasteful: most chunks share **no term** with the question and score 0 anyway. An **inverted index** flips the data around, from *chunk → its terms* to **term → the chunks that contain it**, so a search only touches the few chunks that can actually score. 🎯
>
> The `index` command builds this structure **once** and **saves it to disk** (`data/processed/`). The `search` commands **load it** and answer quickly. Two budgets from the subject frame everything:
> - ⏱️ **Indexing:** whole corpus in **≤ 5 minutes**;
> - ⚡ **Retrieval:** **200 questions in ≤ 90 seconds**.

---

## 📑 Contents

1. [🐢 The brute-force approach, and why it's wasteful](#-1-the-brute-force-approach-and-why-its-wasteful)
2. [🔄 Flipping it around: the inverted index](#-2-flipping-it-around-the-inverted-index)
3. [🧱 The pieces of an index](#-3-the-pieces-of-an-index)
4. [✏️ Worked example: build it by hand](#️-4-worked-example-build-it-by-hand)
5. [🔍 Searching with an inverted index](#-5-searching-with-an-inverted-index)
6. [🧮 Precompute now or compute later?](#-6-precompute-now-or-compute-later)
7. [💾 Persistence: saving and loading](#-7-persistence-saving-and-loading)
8. [⏱️ The 5-minute indexing budget](#️-8-the-5-minute-indexing-budget)
9. [⚡ The 90-second search budget](#-9-the-90-second-search-budget)
10. [🛡️ Keeping index and code in sync](#️-10-keeping-index-and-code-in-sync)
11. [🚫 Common misconceptions](#-11-common-misconceptions)
12. [✅ Check your understanding](#-12-check-your-understanding)

---

## 🐢 1. The brute-force approach, and why it's wasteful

The most direct way to search:

```text
for each question:
    for each chunk in the corpus:          ← every single chunk
        compute score(question, chunk)
    keep the k best
```

With the subject's example numbers (about **13,000 chunks**) and **200 questions**, that's **2.6 million** score computations, and each one has to look at the chunk's terms. 😩

But look at what the scores actually are:

```text
question: "default port"

chunk 1:  0       ← no "default", no "port"
chunk 2:  0
chunk 3:  0
...
chunk 4127: 2.05  ← contains both
...
chunk 9810: 0.74  ← contains "port"
...
chunk 13000: 0
```

> [!NOTE]
> 🕳️ In lexical search, a chunk that shares **no term** with the question scores **exactly 0** (docs 04–05). For a typical question, that's the **vast majority** of chunks. Brute force spends almost all its time computing zeros.

---

## 🔄 2. Flipping it around: the inverted index

A book index is the perfect analogy 📘. You don't read the whole book to find "garbage collection": you look it up at the back and get **page numbers**.

| | Forward index 📄 → 🔤 | Inverted index 🔤 → 📄 |
|---|---|---|
| **Maps** | chunk → its terms | term → chunks containing it |
| **Question it answers** | "What's in chunk 42?" | "Which chunks contain `port`?" |
| **Book analogy** | The pages themselves | The index at the back |

```text
FORWARD                              INVERTED
C1 → port, server, port, default     default → C1
C2 → server, start, model     ──►    model   → C2, C3, C4
C3 → model, config, port             port    → C1, C3
                                     server  → C1, C2
                                     ...
```

The list of chunks for a term is called its **postings list** 📮 (each entry is a "posting").

> [!TIP]
> ⚡ With an inverted index, a search reads only the postings lists of the **question's terms**. A question with 5 terms touches 5 lists, however big the corpus is. Rare terms have tiny lists, and those are exactly the terms that matter most (high IDF). 💎

---

## 🧱 3. The pieces of an index

To compute BM25 (doc 05) you need several kinds of information. They naturally fall into four groups:

| Piece | Contains | Used for |
|---|---|---|
| 📮 **Postings** | For each term: the chunks containing it, with **tf** in each | Finding candidate chunks · `tf(t, d)` · `df(t)` = length of the list |
| 📦 **Chunk store** | For each chunk: its **address** (`file_path`, `first`, `last`) and its **length in terms** `\|d\|` (and maybe its text) | Building the output · BM25 length normalization · giving text to the LLM |
| 📊 **Global statistics** | `N` (number of chunks), `avgdl` (average length) | IDF · length normalization |
| ⚙️ **Configuration** | How the index was built: tokenizer settings, max chunk size, corpus location… | Checking the index matches the current code (Section 10) |

> [!NOTE]
> 🧮 Notice `df(t)` doesn't need to be stored separately: it's simply **how many entries** the term's postings list has.

> [!TIP]
> 🆔 Postings usually refer to chunks by a small **ID** (their position in the chunk store: 0, 1, 2…) rather than repeating the full address in every list. One address per chunk, stored once.

---

## ✏️ 4. Worked example: build it by hand

The same tiny corpus as docs 04 and 05:

| ID | Chunk terms | \|d\| |
|:-:|---|:-:|
| 0 | port · server · port · default | 4 |
| 1 | server · start · model | 3 |
| 2 | model · config · port | 3 |
| 3 | model · load · model · weights | 4 |

### 📮 Postings (term → list of (chunk ID, tf))

| Term | Postings | df |
|---|---|:-:|
| config | (2, 1) | 1 |
| default | (0, 1) | 1 |
| load | (3, 1) | 1 |
| model | (1, 1) · (2, 1) · (3, **2**) | 3 |
| port | (0, **2**) · (2, 1) | 2 |
| server | (0, 1) · (1, 1) | 2 |
| start | (1, 1) | 1 |
| weights | (3, 1) | 1 |

### 📦 Chunk store

| ID | file_path | first | last | \|d\| |
|:-:|---|:-:|:-:|:-:|
| 0 | data/raw/vllm-0.10.1/docs/… | … | … | 4 |
| 1 | … | … | … | 3 |
| 2 | … | … | … | 3 |
| 3 | … | … | … | 4 |

### 📊 Global statistics

```text
N      = 4
avgdl  = (4 + 3 + 3 + 4) / 4 = 3.5
```

> [!TIP]
> 🔨 Building the postings means going through every chunk **once**, and for each term, appending `(chunk ID, tf)` to that term's list. One pass over the corpus: that's what makes indexing feasible in minutes. ⏱️

---

## 🔍 5. Searching with an inverted index

**Question:** *"default port"* (`k1 = 1.2`, `b = 0.75`, as in doc 05)

### 1️⃣ Tokenize the question

Same tokenizer as the index (doc 03, golden rule 🪞) → `["default", "port"]`

### 2️⃣ Walk the postings, accumulating scores

Keep a small table of **accumulators**: one running score per chunk **that appears in at least one list**.

| Step | Posting read | BM25 contribution | Accumulators after |
|:-:|---|:-:|---|
| 1 | default → (0, tf 1) | 1.137 | {0: 1.137} |
| 2 | port → (0, tf 2) | 0.916 | {0: 2.054} |
| 3 | port → (2, tf 1) | 0.736 | {0: 2.054, 2: 0.736} |

📏 Only **3 postings** were read. Chunks 1 and 3 were **never touched**.

### 3️⃣ Keep the top-k

```text
sort accumulators by score → [0: 2.054, 2: 0.736]
keep the first k
```

> [!TIP]
> 🏔️ When there are many candidates, fully sorting all of them just to keep 5 is wasteful. A **heap** keeps the best *k* as you go. Python's standard library has `heapq` for exactly this. 🐍

### 4️⃣ Turn IDs back into addresses

Look up chunks 0 and 2 in the chunk store → `file_path`, `first_character_index`, `last_character_index` → `MinimalSource` objects → output JSON. ✅

### 📉 Brute force vs inverted index

| | Brute force | Inverted index |
|---|---|---|
| Work per question | Every chunk × question terms | Only the question terms' postings |
| On a big corpus | ~13,000 chunk evaluations | Often a few hundred postings |
| Rare-term questions | Same cost | 🚀 Very cheap: rare terms have short lists |
| Common-term questions | Same cost | 🐢 Slower: e.g. `vllm` or `self` may have thousands of postings |

> [!NOTE]
> 🤔 Very common terms are both **expensive** (long postings lists) and **nearly worthless** for ranking (low IDF). Doc 03's stopword discussion has a performance side too.

---

## 🧮 6. Precompute now or compute later?

Some parts of the score never change between questions. Doing them at indexing time saves search time, but freezes some choices:

| What | When it can be computed | Precompute? |
|---|---|---|
| `N`, `avgdl` | Index time | ✅ Obviously |
| `df(t)` / `idf(t)` | Index time (don't depend on the question) | ✅ Cheap to store |
| `\|d\|` per chunk | Index time | ✅ Needed anyway |
| The full BM25 TF part for each posting | Index time, **if** `k1` and `b` are fixed | 🤔 Faster search, but `k1`/`b` are **baked in** |
| The final score | Only at search time (depends on the question) | ❌ |

> [!WARNING]
> ⚖️ If you bake `k1` and `b` into the stored values, **tuning them** (doc 05, Section 8) means **re-indexing** for every combination. If you store raw `tf` and `|d|`, you can try new values instantly. Neither is wrong, but know which one you chose and why. 🎛️

---

## 💾 7. Persistence: saving and loading

The subject requires the index to be **persisted** under `data/processed/` by the `index` command, and reused by `search`, `search_dataset`, `answer`…

### 📦 What to save

| Save | Why |
|---|---|
| 📮 Postings | The heart of search |
| 📦 Chunk store (addresses + lengths) | To build outputs and compute BM25 |
| 📝 Chunk texts? | Needed by the **answer** stage. Store them, or re-read files from addresses (doc 01, Section 6): speed vs size |
| 📊 Global statistics | So they're not recomputed at every load |
| ⚙️ Configuration / version | To detect a stale or incompatible index (Section 10) |

### 🗄️ Formats: trade-offs

| Format | ✅ | ❌ |
|---|---|---|
| 📄 **JSON** | Human-readable, portable, easy to inspect and debug | Big on disk, slow to load for large structures, keys are always strings |
| 🥒 **pickle** | Saves almost any Python object as-is, fast to load | Python-only, tied to your class definitions, ⚠️ **unsafe to load from untrusted sources** |
| 🔢 **NumPy / SciPy arrays** (`.npy`, `.npz`) | Compact, very fast for numeric data and sparse matrices | Needs restructuring data into arrays |
| 🗃️ **SQLite** | Query from disk without loading everything | More setup, slower per lookup than in-memory dicts |

> [!CAUTION]
> 🥒 `pickle` can execute arbitrary code when loading. Fine for files **your own program** wrote, never for files from elsewhere. Worth mentioning if you use it and are asked at the defense. 🛡️

> [!TIP]
> 🔍 Whatever the main format, having **one small human-readable file** (stats + config in JSON, say) makes debugging much easier: you can open it and immediately see what the index thinks it contains.

### ⏳ Loading is part of search time

```text
search_dataset (200 questions):
    load index      ← once!
    for each question:
        search
    save results
```

> [!WARNING]
> 🐢 Load the index **once** per command, never once per question. Loading a large structure 200 times can blow the 90-second budget by itself.

---

## ⏱️ 8. The 5-minute indexing budget

`index` must process the **whole corpus** in **≤ 5 minutes**. Where does the time go?

| Stage | Typical cost | Watch out for |
|---|---|---|
| 📂 Reading files | Disk I/O | Slow filesystems (WSL on `/mnt/c` is much slower than the Linux filesystem), reading files you'll skip anyway |
| ✂️ Chunking | CPU | Parsing every Python file (doc 02), expensive patterns |
| 🔤 Tokenizing | CPU, the biggest loop | Complex regexes, stemming, recomputing things per term |
| 📮 Building postings | CPU + memory | Inefficient structures (see below) |
| 💾 Saving | Disk I/O | Slow formats for large data (JSON with many small objects) |

### 🐌 Hidden slow patterns

Things that look innocent but hide a loop inside a loop:

| Pattern | Problem |
|---|---|
| `term in some_list` inside a loop | Searching a list is slow. Sets and dicts answer this instantly |
| `some_list.count(term)` for every term of a chunk | Recounts the whole chunk each time. Count once per chunk |
| Recomputing `avgdl` or `N` inside the chunk loop | Compute once at the end |
| Re-reading the same file for each of its chunks | Read once, chunk from memory |
| Building huge strings with `+=` in a loop | Can get slow for big texts |

> [!TIP]
> 📊 `tqdm` (required by the subject) shows items per second for each stage. If one stage is far slower than the others, start there. And measure on the **real** corpus: a tiny test folder hides everything. ⏱️

---

## ⚡ 9. The 90-second search budget

**200 questions in ≤ 90 s** means about **0.45 s per question**, including everything: loading the index (once), tokenizing, scoring, top-k, and writing JSON.

| Usually fast ✅ | Can be slow ❌ |
|---|---|
| Looking up a few postings lists | Loading the index once per question |
| Accumulating a few hundred scores | Brute-force scoring of every chunk |
| Picking top-k with a heap | Re-tokenizing chunk texts at search time |
| | Re-reading corpus files during search when the needed data could be in the index |

> [!NOTE]
> 🤖 The 90-second budget is for **retrieval**. Generating answers with Qwen (doc 08) is much slower per question, and it's a separate command (`answer_dataset`).

---

## 🛡️ 10. Keeping index and code in sync

The index is a **snapshot** of your code's choices at the moment `index` ran. If the code changes afterwards, the saved index can silently stop matching it:

| You changed… | Old index… |
|---|---|
| 🔤 Tokenizer (doc 03) | ❌ Terms don't match new query terms (golden rule broken) |
| ✂️ Chunking / max size (doc 02) | ❌ Addresses and lengths are from the old chunking |
| 🎛️ `k1` / `b` (if baked in) | ❌ Scores use the old values |
| 📂 Corpus | ❌ Missing or outdated files |

> [!TIP]
> ⚙️ Saving the **configuration** used to build the index lets the search commands check it at load time and print a clear message ("index built with different settings, run `index` again") instead of quietly giving bad results.

### 🧯 Degenerate cases (the subject tests these!)

| Situation | Graceful behaviour |
|---|---|
| `search` runs but no index exists | Clear error message suggesting `index`, no traceback |
| Index files are corrupted or from an old version | Clear error, no traceback |
| Question has **no** term in the index | Valid output with **no** sources (or as your design decides), no crash |
| `k = 0` / `k` larger than the number of matches | Defined behaviour, no crash |

> [!NOTE]
> 🎁 Two bonuses build directly on this doc: **incremental indexing** (re-index only changed files, which needs a way to remove a file's postings) and **caching** (faster cold start and repeated queries). If you design the index cleanly now, they're much easier later.

---

## 🚫 11. Common misconceptions

| ❌ Myth | ✅ Reality |
|---|---|
| "Search has to look at every chunk." | Only chunks containing a query term can score above 0. The inverted index finds them directly. |
| "df must be stored separately." | It's the length of the term's postings list. |
| "The index is just the BM25 scores." | Scores depend on the question. The index stores the **ingredients**: postings, lengths, statistics. |
| "Persisting means pickling everything." | It's one option among several, each with trade-offs (size, speed, safety, readability). |
| "Load time doesn't count." | It's part of the command's run time. Load once per command, never per question. |
| "Once built, the index stays valid." | It's tied to the tokenizer, chunking and parameters that built it. |
| "Common words are cheap to search." | They have the **longest** postings lists and contribute the least. |

---

## ✅ 12. Check your understanding

Try first, then open the hints. 🧩

**1.** In the worked example, add a fifth chunk (ID 4): `port · start · port`. Update the postings for `port` and `start`, and the values of `N` and `avgdl`.
<details><summary>💡 Hint</summary>Append (4, tf) to each term's list. N becomes 5. Recompute the average length with the new |d| = 3. (Section 4)</details>

**2.** For the question *"server model"*, which postings would a search read? Which chunks get an accumulator, and which are never touched?
<details><summary>💡 Hint</summary>Read only the lists for <code>server</code> and <code>model</code>. (Section 5)</details>

**3.** Why does the inverted index make searches with **rare** terms especially cheap, and why is that a happy coincidence for ranking quality?
<details><summary>💡 Hint</summary>How long is a rare term's postings list? What's its IDF? (Sections 2 and 5)</details>

**4.** You store the final BM25 TF part (with `k1 = 1.2`, `b = 0.75` baked in) in each posting. What happens when you want to try `b = 0.5`?
<details><summary>💡 Hint</summary>Which stored values depend on b? (Section 6)</details>

**5.** `search_dataset` takes 3 minutes for 200 questions, but a single `search` takes 0.8 s. What's the most likely culprit?
<details><summary>💡 Hint</summary>0.8 s × 200 ≈ 160 s. What might a single search spend most of its time on? (Sections 7 and 9)</details>

**6.** You changed your tokenizer to split camelCase, but forgot to re-run `index`. Recall drops on code questions. Explain why, and how your program could have warned you.
<details><summary>💡 Hint</summary>Golden rule of doc 03, and the configuration piece of the index. (Section 10)</details>

**7.** Name two reasons why storing chunk **texts** in the index might be worth it, and one reason against.
<details><summary>💡 Hint</summary>Who needs the text later? What does re-reading files cost? What does storing it cost? (Section 7)</details>

---

## 📚 Further reading

- 📘 Manning, Raghavan & Schütze, *Introduction to Information Retrieval*, ch. 1 (inverted index), ch. 4 (index construction) and ch. 7 (efficient scoring, top-k): <https://nlp.stanford.edu/IR-book/>
- 🏔️ Python `heapq` (keeping the k best items efficiently): <https://docs.python.org/3/library/heapq.html>
- 🥒 Python `pickle`, including its security warning: <https://docs.python.org/3/library/pickle.html>

---

<div align="center">

**← Previous** [05 — BM25 🏆](05-bm25.md) · [🏠 Docs index](README.md) · **Next →** [07 — Evaluation: recall@k and IoU 🎯](07-evaluation.md)

</div>
