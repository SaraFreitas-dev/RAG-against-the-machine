<div align="center">

# ✂️ 02 — Chunking

**How to cut files into pieces that can be found, and why the cuts matter so much**

`📚 Concepts` · `⏱️ ~20 min read` · `🎯 Prerequisite: 01 — The corpus and character offsets`

</div>

---

> [!IMPORTANT]
> **TL;DR** — Before you can search, every file must be cut into **chunks**: slices with an address (`file_path` + character range) and a text. Chunking looks like a boring preprocessing step, but it decides **what can ever be found**:
> - 📏 **size** decides how precise a result is and whether it passes the grader's overlap test;
> - 🔁 **overlap** decides what happens to information sitting on a boundary;
> - 🧱 **boundaries** decide whether a chunk is a meaningful unit (a section, a function) or a random cut.
>
> The subject requires **two different strategies**: one for 🐍 Python code and one for 📝 Markdown/text.

---

## 📑 Contents

1. [🤔 Why chunk at all?](#-1-why-chunk-at-all)
2. [🧩 What a chunk is](#-2-what-a-chunk-is)
3. [📏 Chunk size: the central trade-off](#-3-chunk-size-the-central-trade-off)
4. [🔁 Overlap](#-4-overlap)
5. [🧱 Where to cut: fixed vs structure-aware](#-5-where-to-cut-fixed-vs-structure-aware)
6. [📝 Strategy 1: Markdown and text](#-6-strategy-1-markdown-and-text)
7. [🐍 Strategy 2: Python code](#-7-strategy-2-python-code)
8. [🧭 The lost-context problem](#-8-the-lost-context-problem)
9. [🧪 Invariants: what must always be true](#-9-invariants-what-must-always-be-true)
10. [📊 Measuring the effect of your choices](#-10-measuring-the-effect-of-your-choices)
11. [🚫 Common misconceptions](#-11-common-misconceptions)
12. [✅ Check your understanding](#-12-check-your-understanding)

---

## 🤔 1. Why chunk at all?

Why not index whole files and return whole files? Four reasons, each coming from a different part of the project:

| | Reason | Comes from |
|:-:|---|---|
| 📏 | **The grader forbids it.** Any source wider than **2000 characters** makes the whole output invalid. Most files are much longer. | The moulinette |
| 🎯 | **Precision.** A 40,000-character file "about the scheduler" is not an answer. The question is about **one paragraph** or **one function** in it. | Recall@k / IoU |
| 🔍 | **Search quality.** In a huge text, the question's words are drowned among thousands of unrelated words. Ranking functions like BM25 even **penalise** long texts on purpose (doc 05). | Retrieval |
| 🤖 | **The model's budget.** The retrieved text is pasted into Qwen's prompt. Small, focused pieces leave room for several sources; whole files would not fit. | Generation |

> [!TIP]
> 💡 A good chunk is like a good **index card** 🗂️: small enough to be about **one thing**, big enough to **make sense on its own**.

---

## 🧩 2. What a chunk is

Recall doc 01: a chunk is an **address** plus the **text** at that address.

```text
📁 file_path              data/raw/vllm-0.10.1/docs/serving/env_vars.md
🔢 first_character_index  4210
🔢 last_character_index   5530
📝 text                   "## VLLM_PORT\nThe port used by ..."   (= file_text[4210:5530])
```

Chunking a file means producing a **list of such ranges** over the file's text.

```text
file:   |──────────────────────────── 0 … 9000 ────────────────────────────|
chunks: |── 1 ──|──── 2 ────|── 3 ──|────── 4 ──────|─── 5 ───|── 6 ──|─ 7 ─|
```

> [!IMPORTANT]
> 🔑 Every part of the file that is **not inside any chunk** can **never** be returned. If the answer to a question lives in a gap, your recall for that question is 0, no matter how good your search is. 🕳️

---

## 📏 3. Chunk size: the central trade-off

### ⚖️ Small vs large

| | 🐜 Small chunks (e.g. 300 chars) | 🐘 Large chunks (e.g. 2000 chars) |
|---|---|---|
| **Precision** | ✅ Each chunk is about one thing | ❌ Mixes several topics |
| **Context** | ❌ A sentence may be cut away from what it refers to | ✅ Keeps explanations together |
| **Search signal** | ❌ Few words → the question's words may not all be there | ✅ More words to match |
| **Number of chunks** | ❌ Many → bigger index, slower indexing and search | ✅ Fewer |
| **Grader overlap (IoU)** | ✅ Easy to beat 0.05 with a small reference | ❌ May fail against a **small** reference (below) |
| **For the LLM** | ❌ Fragments without context | ❌ Fewer sources fit in the prompt |

There's no universally right size. The subject makes it a CLI parameter (`--max_chunk_size`, default 2000) and asks you to **report its effect on recall**.

### 🎯 The IoU ceiling: a constraint you can compute

From doc 01: a result counts if its **IoU** with the reference range is above **0.05**.

Suppose your chunk **fully contains** the reference (the best case). Then:

```text
intersection = reference width
union        = chunk width

IoU = reference width ÷ chunk width
```

So even a **perfect** hit fails if the chunk is more than **20×** wider than the reference:

| Reference width | Chunk width | IoU (chunk contains reference) | Counts? |
|:-:|:-:|:-:|:-:|
| 200 | 2000 | 0.100 | ✅ |
| 100 | 2000 | 0.050 | ⚠️ right on the edge |
| 60 | 2000 | 0.030 | ❌ |
| 60 | 1000 | 0.060 | ✅ |
| 60 | 1200 | 0.050 | ⚠️ right on the edge |

> [!CAUTION]
> 🤯 With big chunks, you can retrieve **exactly the right place** and still score 0 for it, if the reference is narrow. How wide are the references in the real datasets? That's an **empirical question**: go measure it (doc 01, Section 9). Your answer should influence your chunk size. 📐

<sub>Whether the grader's comparison is strictly "greater than" or "greater or equal" at exactly 0.05 doesn't matter much in practice: don't design for the edge.</sub>

### 🔢 Size is a maximum, not a target

`--max_chunk_size` is a **ceiling**. Structure-aware strategies (Section 5) naturally produce chunks of different sizes: a short section might be 300 characters, a long function 1900. That's fine, as long as **none** exceeds the maximum.

> [!WARNING]
> 📏 The maximum must hold **after** everything, including overlap and any merging of small pieces. One chunk at 2001 characters invalidates the whole output file. 💣

---

## 🔁 4. Overlap

**Overlap** means consecutive chunks share some characters: each new chunk starts **before** the previous one ends.

```text
No overlap (size 1000):
|───── A: 0–1000 ─────|───── B: 1000–2000 ─────|───── C: 2000–3000 ─────|

Overlap 200 (size 1000, step 800):
|───── A: 0–1000 ─────|
                 |───── B: 800–1800 ─────|
                                    |───── C: 1600–2600 ─────|
                                                       |── D: 2400–3000 ──|
```

### 🎯 Why it helps: the boundary problem

Imagine the reference is a short paragraph at **[950 : 1050]**, exactly on a boundary.

**Without overlap**, it's split in two:

| Chunk | Range | Intersection | Union | IoU | |
|:-:|---|:-:|:-:|:-:|:-:|
| A | 0–1000 | 50 | 1050 | ≈ 0.048 | ❌ |
| B | 1000–2000 | 50 | 1050 | ≈ 0.048 | ❌ |

Neither half counts. 😱 Worse for search: the paragraph's words are **split** between two chunks, so neither matches the question well.

**With overlap 200**, chunk B (800–1800) contains the whole paragraph:

| Chunk | Range | Intersection | Union | IoU | |
|:-:|---|:-:|:-:|:-:|:-:|
| B | 800–1800 | 100 | 1000 | 0.100 | ✅ |

### 💸 What it costs

| Cost | Why |
|---|---|
| 📈 More chunks | 3000 chars → 3 chunks without overlap, 4 with overlap 200. Bigger index, more indexing time. |
| 👯 Near-duplicate results | Neighbouring chunks share text, so they often score alike. Two of your precious top-5 slots may point at almost the same place. |
| 📏 Size bookkeeping | Overlap must not push any chunk past the maximum. |

> [!TIP]
> ⚖️ Overlap is a **safety net for blind cuts**. The better your boundaries follow the document's structure (Section 5), the less you need it, because a section or function boundary rarely cuts an idea in half.

---

## 🧱 5. Where to cut: fixed vs structure-aware

### ✂️ Fixed-size (blind) chunking

Cut every *N* characters, regardless of content.

```text
"...set the environment variable VLLM_PO" | "RT to change the port. The default..."
                                      ✂️ cut in the middle of a word
```

| ✅ | ❌ |
|---|---|
| Trivial, fast, sizes are exact | Cuts words, sentences, functions and code blocks in half |
| Works on any file | Ignores the structure that authors already put there |

### 🏗️ Structure-aware chunking

Cut where the **document itself** has natural boundaries: headings, paragraphs, functions, classes.

| ✅ | ❌ |
|---|---|
| Each chunk is a meaningful unit (a section, a function) | Sizes vary a lot |
| Fewer ideas split across chunks | Needs a plan for units **bigger** than the maximum, and for tiny ones |
| Boundaries can match how references were drawn | Format-specific: Markdown and Python need different rules |

### 🪜 The fallback ladder

Real files are messy: a "section" may be 12,000 characters long, or 40. A common pattern is a **ladder** of increasingly fine boundaries. Use the coarsest boundary that produces small-enough pieces, and step down only when you must:

```text
🏛️  Biggest meaningful unit   (a heading's section / a top-level function or class)
      │  too big?
      ▼
🧱  Smaller unit               (sub-section / a method inside a class)
      │  too big?
      ▼
¶   Paragraphs / blank lines
      │  too big?
      ▼
📄  Lines
      │  too big? (a single huge line…)
      ▼
✂️  Hard cut at the maximum    (last resort)
```

And the reverse problem: many **tiny** neighbouring pieces (a heading with one line under it, a 3-line helper function) carry very little search signal on their own. Merging small neighbours, while staying under the maximum, is another decision to consider. 🤝

> [!NOTE]
> 🧭 Which rungs you use, and where merging happens, is **your design**. Write it down: the README must explain your chunking strategy, and you'll defend it.

---

## 📝 6. Strategy 1: Markdown and text

### 🔎 What structure does Markdown give you?

```markdown
# Engine arguments                      ← level-1 heading: the page topic

Intro paragraph about the engine…

## Memory                               ← level-2 heading: a section

### --gpu-memory-utilization            ← level-3 heading: a sub-section

Fraction of GPU memory to use…

```bash                                 ← fenced code block (3 backticks)
vllm serve model --gpu-memory-utilization 0.8
```                                     

| Flag | Default |                       ← table
|------|---------|
| ...  | ...     |
```

| Element | What it tells you |
|---|---|
| 🏷️ `#`, `##`, `###` headings | Topic boundaries, nested in a hierarchy |
| ¶ Blank lines | Paragraph boundaries |
| 💻 Fenced code blocks (```` ``` ````) | A unit that should **not** be cut inside, and whose lines may *look* like headings (`# comment` in a bash block!) |
| 📋 Lists and tables | Units where every line belongs with its neighbours |

### ✏️ Worked example

Take this file (simplified):

```markdown
# Serving                                   ← A starts
Intro: how to run vLLM as a server.

## Port                                     ← B starts
Default is 8000. Use --port to change it.

## Host                                     ← C starts
Default is localhost.
```

Heading-based boundaries give three sections, **A** (title + intro), **B** (Port) and **C** (Host), each one a self-contained topic. A question like *"How do I change the port?"* matches **B** strongly, and B's range is tight around the answer. 🎯

Now imagine section B were 6000 characters long. It has to be cut further (paragraphs, then lines…), and the pieces after the first one **no longer contain the word "Port"** from the heading. Section 8 discusses why that matters.

### ⚠️ Markdown traps

| Trap | Why it's a trap |
|---|---|
| `#` inside a code block | A bash comment `# install deps` is **not** a heading. Cutting there splits the code block. |
| Headings with no body | A heading followed directly by a sub-heading gives a near-empty section. |
| Front matter / HTML / admonitions | Docs sites add non-Markdown syntax (`---` blocks, `<div>`, `!!! note`…). Decide how to treat them. |
| Very long tables or lists | One "paragraph" may exceed the maximum on its own. |

> [!TIP]
> 📄 Other text-like files (`.rst`, `.txt`…) don't share Markdown's syntax, but they still have **blank-line paragraphs**. Whether you index them, and with which strategy, is part of your design (doc 01, Section 1).

---

## 🐍 7. Strategy 2: Python code

### 🔎 What structure does Python give you?

```python
"""Module docstring: what this file is about."""      ← module header
import os
from vllm.config import ModelConfig

DEFAULT_PORT = 8000                                    ← module-level code

@dataclass                                             ← decorator (belongs to the class!)
class ServerArgs:                                      ← top-level class
    """Arguments for the API server."""
    host: str = "localhost"
    port: int = DEFAULT_PORT

    def validate(self) -> None:                        ← method
        ...

def build_server(args: ServerArgs) -> Server:          ← top-level function
    """Create and configure the server."""
    ...
```

| Unit | Notes |
|---|---|
| 📦 Top-level **function** / **class** | The natural unit: one definition = one idea |
| 🧷 **Decorators** and **comments** just above a definition | Belong **with** it. Cutting them off leaves `@dataclass` alone in the previous chunk. |
| 📜 **Docstrings** | Often the most "English" part of code: the words a question is most likely to share. Precious for lexical search 💎 |
| 🔧 **Methods** inside a class | The rung below when a class is too big |
| 🏝️ **Module-level code** between definitions | Imports, constants, `if __name__ == "__main__":` … don't forget it, or it falls in a gap (Section 2) |

### 🧰 How can a program find these boundaries?

Two broad families of approach:

| Approach | Idea | Trade-offs |
|---|---|---|
| 🌳 **Parse the code** | Python's standard library includes the `ast` module, which turns source code into a tree of nodes. Definition nodes record where they **start and end**. | ✅ Exact boundaries, nesting known · ❌ Positions come as **line numbers**, not character offsets: you must convert (and remember decorators). Files with syntax errors can't be parsed → you need a fallback. |
| 🔤 **Pattern matching** | Look for lines starting with `def`, `class`, `async def`, `@`… | ✅ Simple, never fails to run · ❌ Fooled by strings or comments containing those words, and by nested definitions |

> [!NOTE]
> 🔢 **Lines → characters.** Line 1 starts at character 0. Line *n* starts right after the `\n` that ends line *n − 1*. Turning "lines 40 to 85" into `[first:last]` correctly (inclusive or exclusive end? the last `\n` included or not?) is exactly the kind of off-by-one that the **invariants** in Section 9 will catch. 🧪

### ⚠️ Code traps

| Trap | Why it's a trap |
|---|---|
| A 3000-line class | Must step down the ladder (methods), but then each method loses the class name |
| Decorators | `@app.post("/v1/completions")` is part of the route handler, and contains words a question may use! |
| Tiny functions | One-liners give chunks with almost no signal: merge neighbours? |
| Files that don't parse | Some files may use syntax your Python version doesn't accept, or be templates. The program must **not crash** (subject rule) and should still chunk them somehow. |

---

## 🧭 8. The lost-context problem

When a big unit is cut into pieces, the later pieces lose the information that **named** them:

```python
class LLMEngine:                      ← chunk 1 contains "LLMEngine"
    ...
    def step(self) -> list[...]:      ← chunk 7: "def step(self)…"
        ...                              no "LLMEngine" anywhere in it 😢
```

```markdown
## Speculative decoding               ← chunk 1 contains the heading
...
(2000 characters later)               ← chunk 3: talks about "draft model"
                                         but never says "speculative decoding" 😢
```

A question like *"How does the LLMEngine step function work?"* or *"Which draft model does speculative decoding use?"* now matches chunk 7 / chunk 3 **worse** than it should.

> [!TIP]
> 💡 Remember the subject's hint (lightbulb, p. 11): *what you keep at indexing time decides what you can still match*. 🔑 The **text you index** for a chunk and the **address you return** for it don't have to be the same thing. The address must stay exact (doc 01), but what makes a chunk *findable* is up to you. How you could use that freedom (file name? heading path? class name?) is a design question worth thinking about. 🤔

> [!WARNING]
> ⚠️ Whatever you add for searching must **never** change the offsets. `first` / `last` always refer to the original file text.

---

## 🧪 9. Invariants: what must always be true

Chunking bugs are silent: nothing crashes, recall is just mysteriously low. 🐛 The cure is to write down what must **always** hold, and test it on the **whole corpus**:

| # | Invariant | Catches |
|:-:|---|---|
| 1 | `0 ≤ first < last ≤ len(file_text)` | Negative or out-of-range offsets |
| 2 | `last − first ≤ max_chunk_size` | 💣 The output-invalidating bug |
| 3 | The chunk's text is **exactly** `file_text[first:last]` | Relative/absolute offset mix-ups, line→char conversion errors |
| 4 | Chunks of a file, sorted, leave **no gaps** you didn't intend | Content that can never be found |
| 5 | Chunks don't overlap **unless** you chose overlap | Accidental duplicates |
| 6 | Running twice gives the **same** chunks | Non-determinism |
| 7 | No chunk is empty or whitespace-only | Useless index entries |

> [!TIP]
> 🧪 These make perfect **unit tests** (the subject asks for pytest/unittest, not graded). Try them on small hand-made files where you know the right answer, then run them over all of `data/raw/`. A single failure among 10,000 chunks is worth finding **now**. 🔍

---

## 📊 10. Measuring the effect of your choices

The subject asks you to **report** how chunk size affects recall@k. That calls for experiments, not opinions. 🔬

**Method:**

1. 🎛️ Change **one** thing at a time (size, *or* overlap, *or* a strategy rule).
2. 🔁 Re-index, re-run `search_dataset`, evaluate (your `evaluate` command or the moulinette).
3. 📝 Record the result in a table.

A table you could fill in for your README:

| Max size | Overlap | Strategy notes | # chunks | Index time | Docs R@5 | Code R@5 |
|:-:|:-:|---|:-:|:-:|:-:|:-:|
| 2000 | 0 | … | … | … | … | … |
| 1000 | 0 | … | … | … | … | … |
| 1000 | 200 | … | … | … | … | … |
| 500 | 0 | … | … | … | … | … |

> [!NOTE]
> 📉 Look at **docs and code separately**. A change can help one and hurt the other. That's one reason the subject wants two strategies.

> [!WARNING]
> ⏱️ Keep an eye on the **index time** column: the whole corpus must index in **≤ 5 minutes**. Smaller chunks and more overlap both mean more chunks to process.

---

## 🚫 11. Common misconceptions

| ❌ Myth | ✅ Reality |
|---|---|
| "Chunking is just preprocessing; the search algorithm is what matters." | Chunking decides **what can be found** and whether a hit **counts** (IoU). A great ranker can't fix bad chunks. |
| "Bigger chunks are safer: more chance to contain the answer." | They can contain the answer and **still fail** the IoU test against a narrow reference. |
| "Smaller is always more precise, so always better." | Tiny chunks lose context and search signal, and multiply index size and time. |
| "More overlap is free insurance." | It costs chunks, time, and wastes top-k slots on near-duplicates. |
| "One clever strategy works for all files." | Markdown and Python have different structure. The subject requires two strategies for a reason. |
| "Parsing Python is safe." | Some files may not parse. The program must fall back, not crash. |
| "I can clean the text before chunking (strip, remove comments…)." | Offsets must refer to the **original** text. You may *index* a cleaned version, but never shift the address. |

---

## ✅ 12. Check your understanding

Try first, then open the hints. 🧩

**1.** Give two reasons, from two different parts of the project, why whole files can't be used as search results.
<details><summary>💡 Hint</summary>One comes from the grader's rules, one from how ranking or the LLM works. (Section 1)</details>

**2.** A reference is 80 characters wide. Your chunk contains it entirely and is 2000 characters wide. Does it count? What's the largest chunk that could still count?
<details><summary>💡 Hint</summary>When the chunk contains the reference, IoU = reference ÷ chunk. Solve for the 0.05 limit. (Section 3)</details>

**3.** With size 1000 and overlap 250, where do the first four chunks start? How many chunks does a 3000-character text produce?
<details><summary>💡 Hint</summary>The step between starts is size − overlap. Don't forget the last, shorter chunk. (Section 4)</details>

**4.** Your Markdown splitter cuts on every line starting with `#`. Which kind of content does it break, and how?
<details><summary>💡 Hint</summary>Where else can a line start with <code>#</code> in a docs page? (Section 6, traps)</details>

**5.** A Python class is 9000 characters long. Describe what happens to it, step by step, using the fallback ladder. What information do the later pieces lose?
<details><summary>💡 Hint</summary>Which rung comes below "top-level class"? What did the first line of the class contain that the method pieces don't? (Sections 5 and 8)</details>

**6.** Your recall is suspiciously low on code questions only, and spot checks show results "near" the right function but slightly off. Which invariant would you test first?
<details><summary>💡 Hint</summary>Code chunk positions often start life as <b>line numbers</b>. What can go wrong turning them into characters? (Sections 7 and 9)</details>

**7.** You want chunks to be easier to find without changing their addresses. What's the key idea that makes this possible?
<details><summary>💡 Hint</summary>Are "what you index" and "what you return" necessarily the same text? (Section 8)</details>

---

## 📚 Further reading

- 🌳 Python `ast` module (parsing source code, node positions): <https://docs.python.org/3/library/ast.html>
- 📝 CommonMark spec (what officially counts as a heading, a code block…): <https://spec.commonmark.org/>
- 📘 Manning, Raghavan & Schütze, *Introduction to Information Retrieval*, ch. 2 on documents and indexing units: <https://nlp.stanford.edu/IR-book/>

---

<div align="center">

**← Previous** [01 — The corpus and character offsets 📍](01-corpus-and-offsets.md) · [🏠 Docs index](README.md) · **Next →** [03 — Tokenization 🔤](03-tokenization.md)

</div>
