<div align="center">

# 📍 01 — The corpus and character offsets

**How a source is located: a file path and a character range**

`📚 Concepts` · `⏱️ ~15 min read` · `🎯 Prerequisite: 00 — What is RAG`

</div>

---

> [!IMPORTANT]
> **TL;DR** — In this project a search result is **not text**, it's an **address** 📍:
> - 📁 **`file_path`**: which file, written **exactly** as in the corpus;
> - 🔢 **`first_character_index` → `last_character_index`**: which slice of that file, counted in **characters** from the start of the file.
>
> Get the address wrong by one folder or a few characters and the grader can't find your result, even if your search was perfect.

---

## 📑 Contents

1. [📦 What is the corpus?](#-1-what-is-the-corpus)
2. [🧵 A file is one long string](#-2-a-file-is-one-long-string)
3. [🔢 Character offsets](#-3-character-offsets)
4. [✏️ Worked example: counting by hand](#️-4-worked-example-counting-by-hand)
5. [🧨 Characters are not bytes, lines or tokens](#-5-characters-are-not-bytes-lines-or-tokens)
6. [🤔 Why addresses instead of text?](#-6-why-addresses-instead-of-text)
7. [📁 Why `file_path` must match exactly](#-7-why-file_path-must-match-exactly)
8. [🎯 How the grader uses the address](#-8-how-the-grader-uses-the-address)
9. [🔬 Explore the ground truth yourself](#-9-explore-the-ground-truth-yourself)
10. [🚫 Common misconceptions](#-10-common-misconceptions)
11. [✅ Check your understanding](#-11-check-your-understanding)

---

## 📦 1. What is the corpus?

The **corpus** is the full collection of documents your system searches. Here it's a snapshot of the **vLLM** repository, version 0.10.1, placed under `data/raw/`:

```text
data/raw/vllm-0.10.1/
├── 📝 docs/          ← Markdown documentation pages
├── 💡 examples/      ← small runnable Python scripts
├── 🐍 vllm/          ← the library's source code
├── 🧪 tests/
├── 📄 README.md
└── ... (configs, build files, CUDA kernels, etc.)
```

It contains **thousands of files** of very different kinds:

| Kind | Typical extensions | Useful for questions? |
|---|---|---|
| 📝 Documentation | `.md`, `.rst`, `.txt` | 🤔 You decide |
| 🐍 Python code | `.py` | 🤔 You decide |
| ⚙️ Configuration | `.yaml`, `.toml`, `.json`, `.cfg` | 🤔 You decide |
| ⚡ Low-level code | `.cu`, `.cpp`, `.h` | 🤔 You decide |
| 🖼️ Binary / assets | `.png`, `.so`, `.whl` | 🤔 You decide |

> [!NOTE]
> The subject says: *"Read the files **you judge useful**."* That's a design decision, and you'll be asked to justify it. 🧭 Section 9 shows how to make that choice **with evidence** instead of guessing.

> [!TIP]
> Every file you index costs time (the 5-minute limit ⏱️) and adds possible noise to the search. Every file you skip is a file you can **never** return as a result. ⚖️

---

## 🧵 2. A file is one long string

Forget lines and paragraphs for a moment. When you read a text file in Python, you get **one single string**: every letter, space, tab and line break, one after another.

```text
What you see in the editor:        What the program sees:

  # Title                           "# Title\nHello world\n"
  Hello world
```

> [!IMPORTANT]
> 🔑 The **line break** is a character too: `\n`. It's invisible in the editor, but it **takes one position** in the string, exactly like a letter.

Every character has a **position** (an **index**), starting at **0**:

| Index | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **Char** | `#` | `␣` | `T` | `i` | `t` | `l` | `e` | `\n` | `H` | `e` | `l` | `l` | `o` | `␣` | `w` | `o` | `r` | `l` | `d` | `\n` |

<sub>`␣` = a space.</sub>

This string has **20 characters**, indexed **0 to 19**.

---

## 🔢 3. Character offsets

A **source** points at a **slice** of that string:

```python
class MinimalSource(BaseModel):
    file_path: str                 # 📁 which file
    first_character_index: int     # 🟢 where the slice starts
    last_character_index: int      # 🔴 where the slice ends
```

The slice works like Python slicing: `text[first:last]`.

```text
text = "# Title\nHello world\n"

text[8:13]  →  "Hello"     ✂️ from index 8 up to (not including) 13
text[14:19] →  "world"
text[0:7]   →  "# Title"
```

> [!NOTE]
> 📐 With Python-style slicing, the **width** of a slice is simply `last - first`. `text[8:13]` has 13 − 8 = **5** characters.
>
> The subject's own examples are consistent with this convention: a chunk shown as `[0:2000]` for a maximum chunk size of 2000. Still, **don't take it on faith**. Section 9 shows how to confirm it against the reference data. 🔬

### 📏 The 2000-character rule

The moulinette rejects any source wider than **2000 characters** (its `max_context_length`):

| Source | Width | Valid? |
|---|:-:|:-:|
| `[0:2000]` | 2000 | ✅ |
| `[1699:3396]` | 1697 | ✅ |
| `[500:2600]` | 2100 | ❌ |

> [!CAUTION]
> 💣 A **single** over-long source makes your **whole output file invalid**, not just that question. That's why chunk size is capped by `--max_chunk_size`.

---

## ✏️ 4. Worked example: counting by hand

Here's a tiny Markdown file, `docs/serve.md`:

```markdown
# Serve
Run `vllm serve`.

## Port
Default is 8000.
```

As one string (with `\n` made visible):

```text
"# Serve\nRun `vllm serve`.\n\n## Port\nDefault is 8000.\n"
```

Let's find the offsets of each part.

| Part | Text | first | last | Width |
|---|---|:-:|:-:|:-:|
| Title line | `# Serve` | 0 | 7 | 7 |
| First `\n` | `\n` | 7 | 8 | 1 |
| Sentence | ``Run `vllm serve`.`` | 8 | 25 | 17 |
| Blank line | `\n\n` | 25 | 27 | 2 |
| Subtitle | `## Port` | 27 | 34 | 7 |
| `\n` | `\n` | 34 | 35 | 1 |
| Last sentence | `Default is 8000.` | 35 | 51 | 16 |
| Final `\n` | `\n` | 51 | 52 | 1 |

📏 Total length: **52** characters.

Now imagine your chunking splits this file into two sections, one per heading:

| Chunk | Covers | `first` | `last` | `text[first:last]` |
|:-:|---|:-:|:-:|---|
| 1️⃣ | the "Serve" section | 0 | 27 | ``"# Serve\nRun `vllm serve`.\n\n"`` |
| 2️⃣ | the "Port" section | 27 | 52 | `"## Port\nDefault is 8000.\n"` |

> [!TIP]
> ✅ Notice that **chunk 2 starts exactly where chunk 1 ends** (27). Together they cover the whole file with no gap and no overlap. That's a useful property to check in your own chunking.

### 🪆 Offsets inside offsets

Suppose you first cut out the "Port" section (starting at **27**), then look for `8000` **inside that section**:

```text
section = "## Port\nDefault is 8000.\n"
           0123456789...
```

`8000` sits at positions **19 → 23** *of the section*. In the **file**, that's:

```text
27 + 19 = 46   →   27 + 23 = 50
```

> [!WARNING]
> 🧨 This is the most common offset bug. A position **inside a piece** is **relative**. The output always needs **absolute** positions, counted from the start of the **file**. If you split in several steps, every step must carry the starting offset forward. ➕

---

## 🧨 5. Characters are not bytes, lines or tokens

"Position" can mean four different things. Only **one** is right here.

| Unit | What it counts | Used here? |
|---|---|:-:|
| 🔤 **Characters** | Each letter, space, `\n`… as Python's `str` sees it | ✅ **Yes** |
| 💾 **Bytes** | Raw storage on disk | ❌ |
| 📄 **Lines** | Line numbers, like in your editor | ❌ |
| 🧩 **Tokens** | Words or word-pieces, for search or for the LLM | ❌ |

### 💾 Characters vs bytes

Files are stored as bytes, usually with **UTF-8** encoding. Plain English letters take 1 byte each, but many characters take more:

| Character | Characters | UTF-8 bytes |
|:-:|:-:|:-:|
| `a` | 1 | 1 |
| `é` | 1 | 2 |
| `→` | 1 | 3 |
| `🚀` | 1 | 4 |

So in a file containing `é` or an emoji, **byte positions and character positions drift apart** 📉. Documentation files often contain such characters (arrows, accents, emojis…).

> [!IMPORTANT]
> 🔑 Offsets must be computed on the **decoded text** (a Python `str`), not on raw bytes.

### ↩️ The line-ending trap

Line breaks don't look the same on every system:

| System | Line ending | Characters |
|---|---|:-:|
| 🐧 Linux / macOS | `\n` | 1 |
| 🪟 Windows | `\r\n` | 2 |

By default, Python's `open()` in text mode **translates** `\r\n` into `\n` when reading ("universal newlines"). If a file in the corpus used `\r\n`, each line break would count as **2 characters for one reader and 1 for another**, and every offset after the first line would shift. 😱

> [!NOTE]
> 🔬 Whether this matters depends on the actual files and on how the reference data was produced. Don't guess: **check** a few reference sources (Section 9). If `text[first:last]` lands on sensible text, your reading matches the grader's.

---

## 🤔 6. Why addresses instead of text?

Why not just return the chunk's text as the result? Because an **address** is better in every way that matters for grading:

| | 📝 Returning text | 📍 Returning an address |
|---|---|---|
| **Precise** | ❌ The same sentence can appear in several files | ✅ Points to exactly one place |
| **Verifiable** | ❌ Hard to compare "close enough" text | ✅ Compare file + overlapping range |
| **Compact** | ❌ Up to 2000 chars per source × k × hundreds of questions | ✅ Three small fields |
| **Recoverable** | — | ✅ The text can always be re-read: `open(file_path).read()[first:last]` |

> [!TIP]
> 🔄 This also means your **index** doesn't strictly have to store the text: given an address, you can re-read it. Whether to store it anyway is a design choice (speed vs memory), and doc 06 discusses it.

---

## 📁 7. Why `file_path` must match exactly

The grader compares paths **character by character** 🔍. There is no "close enough".

The path must be **relative to the project root** and start with the corpus prefix, exactly like this:

```text
data/raw/vllm-0.10.1/docs/features/lora.md
```

| Your `file_path` | Match? | Why |
|---|:-:|---|
| `data/raw/vllm-0.10.1/docs/features/lora.md` | ✅ | Exact |
| `docs/features/lora.md` | ❌ | Missing prefix |
| `vllm-0.10.1/docs/features/lora.md` | ❌ | Missing `data/raw/` |
| `./data/raw/vllm-0.10.1/docs/features/lora.md` | ❌ | Extra `./` |
| `/home/sara/rag/data/raw/vllm-0.10.1/docs/features/lora.md` | ❌ | Absolute path |
| `data\raw\vllm-0.10.1\docs\features\lora.md` | ❌ | Windows backslashes |
| `data/raw/vllm-0.10.1/vllm-0.10.1/docs/features/lora.md` | ❌ | Unzipped twice 📦📦 |
| `data/raw/vllm-0.10.1/Docs/features/lora.md` | ❌ | Wrong case |

> [!CAUTION]
> ⚠️ A wrong prefix doesn't fail **one** question, it fails **all** of them. Your recall drops to **0%** even if your search is perfect. 😵 It's one of the first things to check when a score looks impossibly bad.

> [!WARNING]
> 🧭 The subject also forbids **hard-coded paths**: the corpus location comes from the CLI. So the path you *read from* and the path you *write in the output* must stay consistent however the program is called. Think about how your program turns "the file I opened" into "the string I output".

---

## 🎯 8. How the grader uses the address

> 🔭 *Short preview. Doc 07 covers evaluation in depth.*

For each **reference source** (from the ground-truth dataset), the grader checks whether **one of your top-k sources**:

1. 📁 is in the **same file**, and
2. 🔢 **overlaps** the reference range enough: an **IoU** (Intersection over Union) above **0.05**.

**IoU** compares two ranges: the length they **share**, divided by the length they **cover together**.

```text
reference:  [1000 ─────── 1200]                       (200 chars)

chunk A:  [0 ─────────────────────────────── 2000]     contains the reference
          intersection = 200   union = 2000   IoU = 0.10   ✅

chunk B:              [1150 ───────────────────────────── 3150]
          intersection = 50    union = 2150   IoU ≈ 0.023  ❌
```

> [!IMPORTANT]
> 🤯 Both chunks **touch** the reference, but only A counts. Chunk B overlaps it too little **relative to its size**. Chunk size and chunk boundaries directly affect what counts as "found". Keep this in mind for doc 02. ✂️

---

## 🔬 9. Explore the ground truth yourself

The datasets in `data/datasets/AnsweredQuestions/` contain the **reference sources** for every question: the exact addresses the grader expects. They're the best evidence you have. 🕵️

**Questions worth investigating** (no code given, that part is yours 🛠️):

| 🔍 Investigate | 🧭 Why it matters |
|---|---|
| Which **file extensions** appear in the reference sources, and how often? | Tells you which files are worth indexing (Section 1) |
| Which **folders** do they come from (`docs/`, `vllm/`, `examples/`…)? | Docs vs code questions point to different places |
| How **wide** are the reference ranges, usually? | Helps you reason about chunk size (doc 02) |
| For a few sources, open the file and print `text[first:last]`. Does it start and end at sensible places? | ✅ Confirms the slicing convention and your file reading (Sections 3 and 5) |
| How many reference sources does a typical question have? | Affects how hard recall@k is |

> [!TIP]
> 🧪 The "print the slice" check takes five minutes and can save you days. If the text looks shifted (cut mid-word, starting a few characters late…), your reading doesn't match the grader's, and **every** offset you produce will be off.

---

## 🚫 10. Common misconceptions

| ❌ Myth | ✅ Reality |
|---|---|
| "The indices are word or line numbers." | They're **character** positions from the start of the **file**. |
| "Line breaks don't count." | `\n` is a character and takes **one** position. |
| "Byte position = character position." | Only for plain ASCII. Accents, arrows and emojis take several bytes. |
| "The path just needs to point to the right file." | It must be **textually identical** to the corpus path. |
| "If my chunk overlaps the answer, it counts." | Only if the **IoU** is above 0.05. A big chunk barely touching the reference may not count. |
| "Offsets inside a section are fine." | Output offsets must be **absolute** (relative to the file). |
| "I can clean the text (strip, remove blank lines) before chunking." | Every removed character **shifts** all later positions. Offsets must refer to the **original** text. |

---

## ✅ 11. Check your understanding

Try first, then open the hints. 🧩

**1.** In the string `"ab\ncd"`, what is `text[3:5]`? What's its width?
<details><summary>💡 Hint</summary>Write the indices under each character. Don't forget that <code>\n</code> takes one position. (Section 2)</details>

**2.** A chunk covers `[1200:3300]`. Is it valid for the moulinette?
<details><summary>💡 Hint</summary>Compute <code>last - first</code> and compare it with the limit. What happens to the whole output file if it's not valid? (Section 3)</details>

**3.** You cut a section starting at file position 5000, and find a function at positions 120 → 900 **inside the section**. What are the function's offsets in the output?
<details><summary>💡 Hint</summary>Relative vs absolute. (Section 4, "Offsets inside offsets")</details>

**4.** A docs file contains `→` near the top. You compute offsets on the raw bytes instead of the decoded text. What goes wrong, and where in the file?
<details><summary>💡 Hint</summary>How many bytes is <code>→</code> in UTF-8? What happens to every position after it? (Section 5)</details>

**5.** Your recall is exactly **0%** on every question, even ones that look easy. What's the first thing you'd check?
<details><summary>💡 Hint</summary>Which mistake fails <b>every</b> question at once, regardless of search quality? (Section 7)</details>

**6.** The reference is `[400:600]`. Your chunk `[0:2000]` contains it fully. Your other chunk `[550:2550]` overlaps it. Which one counts, and why?
<details><summary>💡 Hint</summary>Compute intersection and union for each, then compare with 0.05. (Section 8)</details>

**7.** How could you check, before writing any search code, that your way of reading files produces the **same** offsets as the reference data?
<details><summary>💡 Hint</summary>The ground truth already contains addresses. What happens if you slice them yourself? (Section 9)</details>

---

## 📚 Further reading

- 🐍 Python tutorial: strings, indexing and slicing: <https://docs.python.org/3/tutorial/introduction.html#text>
- 🌍 Python Unicode HOWTO: characters vs bytes, encodings: <https://docs.python.org/3/howto/unicode.html>
- 📂 Python `open()` (see the `encoding` and `newline` parameters): <https://docs.python.org/3/library/functions.html#open>

---

<div align="center">

**← Previous** [00 — What is RAG 🧠](00-what-is-rag.md) · [🏠 Docs index](README.md) · **Next →** [02 — Chunking ✂️](02-chunking.md)

</div>
