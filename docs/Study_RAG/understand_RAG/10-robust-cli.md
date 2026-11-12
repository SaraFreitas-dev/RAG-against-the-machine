<div align="center">

# 🛡️ 10 — A robust CLI

**Python Fire, tqdm, and never crashing in front of the evaluator**

`📚 Concepts` · `⏱️ ~20 min read` · `🎯 Prerequisite: 09 — Pydantic in practice`

</div>

---

> [!IMPORTANT]
> **TL;DR** — The CLI is the only part of your project the evaluator and the reference scripts actually **touch**. The subject asks for three things:
> - 🔥 a CLI built with **Python Fire**, invoked as `uv run python -m src <command> [options]`;
> - 📊 **tqdm** progress bars for long-running operations;
> - 🛡️ graceful handling of degenerate inputs: *"The CLI is tested with such edge cases and must **never crash with an unhandled traceback**."*
>
> A crash during the defense means the program *"will be considered non-functional"* (common instructions). Robustness isn't polish here, it's a requirement. 💥

---

## 📑 Contents

1. [🗺️ What the subject requires](#️-1-what-the-subject-requires)
2. [📦 `python -m src`: how the entry point works](#-2-python--m-src-how-the-entry-point-works)
3. [🔥 Python Fire basics](#-3-python-fire-basics)
4. [😈 Fire's surprises: types come from the values](#-4-fires-surprises-types-come-from-the-values)
5. [📊 tqdm progress bars](#-5-tqdm-progress-bars)
6. [🧯 Errors: expected problems vs bugs](#-6-errors-expected-problems-vs-bugs)
7. [🧪 The degenerate-input checklist](#-7-the-degenerate-input-checklist)
8. [📂 Paths: configurable, never hard-coded](#-8-paths-configurable-never-hard-coded)
9. [📢 stdout, stderr and exit codes](#-9-stdout-stderr-and-exit-codes)
10. [🛠️ Makefile `run` and `debug`](#️-10-makefile-run-and-debug)
11. [🚫 Common misconceptions](#-11-common-misconceptions)
12. [✅ Check your understanding](#-12-check-your-understanding)

---

## 🗺️ 1. What the subject requires

### 🧭 The commands (options shown are the minimum)

| Command | Options | Does |
|---|---|---|
| `index` | `--max_chunk_size <int>` | Ingest `data/raw/`, build the index under `data/processed/` |
| `search` | `<query> --k <int>` | Top-k sources for one query |
| `search_dataset` | `--dataset_path <path> --k <int> --save_directory <dir>` | Search a whole dataset → `StudentSearchResults` JSON |
| `answer` | `<query> --k <int>` | Answer one query |
| `answer_dataset` | `--student_search_results_path <path> --save_directory <dir>` | Answer a dataset → `StudentSearchResultsAndAnswer` JSON |
| `evaluate` | `--student_search_results_path <path> --dataset_path <path>` | Your own recall@k (doc 07) |

### 🧪 Degenerate inputs explicitly named

> *"empty query, nonsensical query, k=0, missing files, malformed JSON"*

These will be tried. Section 7 extends the list. 📋

> [!NOTE]
> 🤖 During the defense, **reference scripts** run `index → search_dataset → moulinette` automatically. If a command name, an option name or the output location differs from the subject, *"the corresponding checks are considered failed by design"*. Copy names exactly. 🔤

---

## 📦 2. `python -m src`: how the entry point works

```text
uv run python -m src search "How to configure the OpenAI server?" --k 5
│      │       │  │   └────────────────── arguments for your CLI
│      │       │  └─ the package (the src/ folder)
│      │       └─ "run a module as a script"
│      └─ the project's Python, from the uv environment
└─ uv: run inside the project environment
```

| Piece | Role |
|---|---|
| `src/__init__.py` | Makes `src` a **package** |
| `src/__main__.py` | The file Python runs for `python -m src` |
| `uv run` | Uses the project's environment (dependencies from `pyproject.toml` / `uv.lock`) |

> [!TIP]
> 📍 `python -m src` must be run from the **repository root** (the folder containing `src/`), which is also where the reference scripts run it. That matters for relative paths (Section 8).

---

## 🔥 3. Python Fire basics

**Fire** builds a CLI from ordinary Python code: you give it a function, a class or an object, and it exposes them as commands.

A toy example (not the project's CLI 🙂):

```python
import fire

class Kitchen:
    """A tiny kitchen CLI."""

    def boil(self, item: str, minutes: int = 10) -> None:
        """Boil an item."""
        print(f"Boiling {item} for {minutes} minutes")

if __name__ == "__main__":
    fire.Fire(Kitchen)
```

```text
$ python kitchen.py boil egg --minutes 7
Boiling egg for 7 minutes
$ python kitchen.py boil egg
Boiling egg for 10 minutes
$ python kitchen.py --help        ← help generated from names and docstrings
```

| Python | Becomes |
|---|---|
| A **method** of the class | A **command** (`boil`) |
| A parameter **without** default | A **positional** argument (`egg`) |
| A parameter **with** a default | An optional **flag** (`--minutes 7`) |
| Docstrings | `--help` text |

> [!TIP]
> 🔤 Fire accepts both `--max_chunk_size` and `--max-chunk-size` for a parameter named `max_chunk_size`. Name your parameters **exactly** as the subject's options.

### 🔁 Return values

If a command **returns** something, Fire **prints** it (a list is printed one item per line, some objects open Fire's interactive explorer). If you print results yourself, return `None` to avoid double or odd output. 🖨️

---

## 😈 4. Fire's surprises: types come from the values

This is the most important section for robustness. ⚠️

Fire does **not** convert arguments using your type hints. It looks at the **text typed on the command line** and guesses its Python type, as if it were a Python literal:

| Command line | Your function receives | Type |
|---|---|---|
| `search hello` | `'hello'` | `str` ✅ |
| `search 42` | `42` | `int` 😱 |
| `search True` | `True` | `bool` 😱 |
| `search '[1,2]'` | `[1, 2]` | `list` 😱 |
| `search ''` | `''` | `str` (empty) |
| `--k abc` | `'abc'` | `str` 😱 |
| `--k 2.5` | `2.5` | `float` 😱 |
| `--k 1e3` | `1000.0` | `float` 😱 |
| `--k` (no value) | `True` | `bool` 😱 |
| `--k=-3` | `-3` | `int` (negative) |

<sub>All verified with Python Fire. A type hint `k: int` changes none of these.</sub>

> [!CAUTION]
> 💣 So a "query" can arrive as an **int**, a **bool** or a **list**, and `k` as a **string**, a **float** or `True`. Code that does `query.lower()` or `results[:k]` will crash on some of these. **Check types yourself** at the start of each command. 🛡️

> [!WARNING]
> 🪤 Python quirk: `True` **is** an `int` (`isinstance(True, int)` is `True`). A check like "is k an int?" lets `--k` (with no value) through as `k = True`, which then behaves like `1`. Decide whether you want that. 🤔

> [!NOTE]
> 🧩 Missing **required** arguments are handled by Fire itself: it prints an error and the usage, and exits with code 2, without a traceback. Everything **inside** your function is your responsibility.

---

## 📊 5. tqdm progress bars

**tqdm** wraps an iterable and shows a live progress bar:

```text
Chunking:   100%|██████████| 1965/1965 [00:00<00:00, 16710 file/s]
Tokenizing: 100%|██████████| 13466/13466 [00:01<00:00, 10668 chunk/s]
```

| Feature | Use |
|---|---|
| `desc` | A label ("Chunking", "Searching"…) |
| `unit` | What's being counted (`file`, `chunk`, `question`) |
| `total` | Needed when iterating something whose length tqdm can't know (generators) |
| Rate + ETA | Shows speed: perfect to spot the slow stage (doc 06, Section 8) |

### 📍 Where bars belong

| Operation | Long-running? |
|---|---|
| Reading + chunking files (`index`) | ✅ |
| Tokenizing / building postings (`index`) | ✅ |
| Searching a dataset (`search_dataset`) | ✅ |
| Generating answers (`answer_dataset`) | ✅✅ (slowest) |
| A single `search` | ❌ Too fast to need one |

> [!TIP]
> 🖨️ `print()` inside a loop wrapped by tqdm breaks the bar into a mess of lines. tqdm provides `tqdm.write()` for messages during a loop. And tqdm draws on **stderr**, which keeps your real output (stdout) clean (Section 9).

---

## 🧯 6. Errors: expected problems vs bugs

Not all errors are equal:

| | 🌧️ Expected problems | 🐛 Bugs |
|---|---|---|
| **Examples** | Missing file, malformed JSON, `k = 0`, empty query, no index yet | `KeyError` in your own dict, off-by-one, wrong variable |
| **Cause** | The **user** or the **environment** | **Your code** |
| **Right response** | A clear message explaining what's wrong and how to fix it | Fix the code |

### 🧱 Where to handle expected problems

```text
command starts
   │
   ├── 1. validate arguments      (types, ranges, empty strings)        → clear message
   ├── 2. check files exist       (dataset, index, search results)      → clear message
   ├── 3. load & validate data    (JSON + pydantic, doc 09)             → clear message
   │
   └── 4. do the actual work      (now with trusted inputs)
```

> [!TIP]
> 🚪 Checking at the **entrance** of each command (steps 1–3) keeps the core logic simple: by step 4, inputs are known to be valid. Catching errors deep inside the search code, far from where they came from, gives vague messages.

### 🗂️ Exceptions you'll meet

| Exception | Typical cause |
|---|---|
| `FileNotFoundError` | Path doesn't exist |
| `IsADirectoryError` / `NotADirectoryError` | A folder where a file was expected, or the reverse |
| `PermissionError` | Can't read or write the location |
| `UnicodeDecodeError` | A file that isn't valid UTF-8 (binary files in the corpus!) |
| `json.JSONDecodeError` | Broken JSON syntax (if you parse JSON yourself) |
| `pydantic.ValidationError` | JSON is valid but has the wrong structure (doc 09, Section 8) |
| `OSError` | Parent of many file-system errors |

> [!WARNING]
> 🕳️ A final "catch everything" around the whole command guarantees no traceback, but it also **hides bugs**: a typo in your code becomes "Something went wrong". If you use one as a last resort, make its message useful, and keep a way to see the real traceback while developing (Section 10). Specific handlers for **expected** problems should come first. ⚖️

---

## 🧪 7. The degenerate-input checklist

For each case, your program needs a **defined, documented behaviour** and **no traceback**. *What* the behaviour is (error message, empty result, a default…) is your design choice: be ready to justify it. 🎤

### ❓ Queries

| Input | Think about |
|---|---|
| `""` (empty) | Error, or empty results? |
| `"   "` (only spaces) | Same as empty after tokenization? |
| `"???"` / only punctuation | Tokenizes to **nothing** |
| `"the of and"` | Only stopwords (if you remove them) → nothing |
| `"xqzvbn"` (nonsense) | Valid query, **no** matching terms → empty results, not a crash |
| `42`, `True` (Fire types) | Section 4 |

### 🔢 `k`

| Input | Think about |
|---|---|
| `0` | Explicitly named in the subject |
| Negative | `results[:-3]` silently does something very different in Python! 😱 |
| Larger than the number of matches | Return fewer results |
| `2.5`, `"abc"`, `True` | Section 4 |

### 📏 `max_chunk_size`

| Input | Think about |
|---|---|
| `0` or negative | Impossible to chunk |
| Above 2000 | The moulinette rejects sources wider than 2000 (doc 01) |
| Very small (e.g. 5) | Allowed? Millions of chunks? |

### 📂 Files and folders

| Input | Think about |
|---|---|
| Dataset path doesn't exist | Clear message |
| Path is a directory | Clear message |
| Malformed JSON | Clear message |
| Valid JSON, wrong structure | Pydantic error → clear message |
| Empty dataset (`"rag_questions": []`) | Valid! Produce a valid, empty output |
| `save_directory` doesn't exist | Create it? (doc 06 and Section 8) |
| No index when searching | "Run `index` first" (doc 06, Section 10) |
| Corpus contains binary / non-UTF-8 files | Skip or handle, never crash mid-indexing |

### ⌨️ Interruptions

| Input | Think about |
|---|---|
| `Ctrl+C` during a long run | A traceback for `KeyboardInterrupt` is ugly. A short "interrupted" message is friendlier |

> [!TIP]
> 📝 Turn this checklist into a small **script of commands** you run before every push. Five minutes, and you see what the evaluator will see. 🧪

---

## 📂 8. Paths: configurable, never hard-coded

The subject is explicit: *"All input and output paths must be configurable CLI arguments and never hard-coded."*

| ✅ Do | ❌ Don't |
|---|---|
| Take `dataset_path`, `save_directory`, `student_search_results_path` as arguments | Write `"data/datasets/…"` inside a function |
| Use `pathlib.Path` to join and inspect paths | Build paths with string `+` and `/` |
| Create the output folder if it's missing | Assume it exists |
| Keep the corpus `file_path` in the exact output format (doc 01, Section 7) | Let the output path depend on where the command was launched from |

### 📄 Output file names

The subject's walkthrough saves results under `--save_directory`, using the **same file name as the input dataset**:

```text
--dataset_path   data/datasets/UnansweredQuestions/dataset_docs_public.json
--save_directory data/output/search_results/UnansweredQuestions
saved to →       data/output/search_results/UnansweredQuestions/dataset_docs_public.json
```

> [!NOTE]
> 🗂️ Scoping outputs by dataset folder (`UnansweredQuestions/`, `AnsweredQuestions/`) avoids overwriting results, because the public datasets share file names.

---

## 📢 9. stdout, stderr and exit codes

| Channel | Purpose | Example |
|---|---|---|
| 📤 **stdout** | The command's **result** | The list of sources from `search`, the answer from `answer` |
| ⚠️ **stderr** | Everything **about** the run | Progress bars, warnings, error messages |
| 🔢 **Exit code** | Success or failure, for scripts | `0` = success, non-zero = failure |

> [!TIP]
> 🔌 Keeping results on stdout and messages on stderr means a script can capture the result without the noise. And returning a **non-zero exit code** on failure (for example with `sys.exit(1)` after printing a message) lets the reference scripts know a step failed, without any traceback.

---

## 🛠️ 10. Makefile `run` and `debug`

The common instructions require these Makefile rules:

| Rule | Does |
|---|---|
| `install` | Install dependencies (here: `uv sync`) |
| `run` | Run the main script |
| `debug` | Run it under Python's debugger (**pdb**) |
| `clean` | Remove caches (`__pycache__`, `.mypy_cache`…) |
| `lint` | `flake8 .` + `mypy .` with the subject's exact flags |

### 🐞 pdb in two minutes

Python's built-in debugger can run a module step by step: `python -m pdb -m <module> …`. When an uncaught exception happens, it stops right there so you can inspect variables.

| pdb command | Does |
|---|---|
| `n` | Next line |
| `s` | Step into a function |
| `c` | Continue until a breakpoint or error |
| `p <expr>` | Print a value |
| `l` | Show code around the current line |
| `q` | Quit |

> [!NOTE]
> 🧯 This is where a "catch everything" handler (Section 6) gets in the way: if every exception is swallowed, pdb never stops at it. One common approach is to let a debug option re-raise exceptions. Whether and how you do it is your call. 🤔

---

## 🚫 11. Common misconceptions

| ❌ Myth | ✅ Reality |
|---|---|
| "Type hints make Fire convert arguments." | Fire guesses types from the **text typed**. `search 42` gives an `int`, `--k abc` a `str`. |
| "If it works on the normal case, it works." | The CLI is **tested** with edge cases. One traceback = non-functional. |
| "Catch `Exception` everywhere and I'm safe." | You won't crash, but you'll hide bugs and give vague messages. Handle expected cases specifically. |
| "An empty dataset is an error." | It's valid input. The output should be a valid, empty result file. |
| "Negative `k` just returns nothing." | Python slicing with a negative number returns **almost everything**. |
| "`print` inside a tqdm loop is fine." | It breaks the bar. Use `tqdm.write`. |
| "Progress and results can share stdout." | Mixing them makes output hard to use from scripts. |
| "Paths like `data/raw` can stay in the code as defaults." | The subject says every input/output path must be a configurable argument, never hard-coded. |

---

## ✅ 12. Check your understanding

Try first, then open the hints. 🧩

**1.** A user runs `search 2024 --k 5`. What type does your function receive for the query? What could go wrong?
<details><summary>💡 Hint</summary>Fire reads <code>2024</code> as a Python literal. What happens when string methods are called on it? (Section 4)</details>

**2.** `search hello --k` is typed with no value after `--k`. What is `k`, and would `isinstance(k, int)` catch it?
<details><summary>💡 Hint</summary>A flag with no value becomes <code>True</code>. Is <code>bool</code> a subclass of <code>int</code>? (Section 4)</details>

**3.** What does `results[:k]` return for `k = -2` and a list of 10 results? Why is that dangerous here?
<details><summary>💡 Hint</summary>Negative slice ends count from the end of the list. (Section 7)</details>

**4.** The dataset file contains valid JSON, but every question lacks the `question` field. Which layer should catch this, and what should the user see?
<details><summary>💡 Hint</summary>Syntax is fine; structure isn't. Which tool from doc 09 checks structure? (Sections 6 and 7)</details>

**5.** Your `index` crashes after 3 minutes on one PNG file that slipped into the corpus. Name two ways to prevent it.
<details><summary>💡 Hint</summary>Choose which files to read (doc 01), and handle decoding errors per file without stopping the whole run. (Section 7)</details>

**6.** Why should progress bars and error messages go to stderr rather than stdout?
<details><summary>💡 Hint</summary>Imagine a script capturing the output of <code>search</code> to process it. (Section 9)</details>

**7.** Give one argument for and one against wrapping each command in a catch-all `except Exception`.
<details><summary>💡 Hint</summary>Think about the evaluator, and about yourself debugging with pdb. (Sections 6 and 10)</details>

---

## 📚 Further reading

- 🔥 Python Fire guide: <https://github.com/google/python-fire/blob/master/docs/guide.md>
- 📊 tqdm documentation: <https://tqdm.github.io/>
- 🧯 Python tutorial, *Errors and Exceptions*: <https://docs.python.org/3/tutorial/errors.html>
- 📂 Python `pathlib`: <https://docs.python.org/3/library/pathlib.html>
- 🐞 Python `pdb`: <https://docs.python.org/3/library/pdb.html>

---

<div align="center">

**← Previous** [09 — Pydantic in practice 🧾](09-pydantic.md) · [🏠 Docs index](README.md) · **Next →** [11 — Embeddings and hybrid retrieval 🧭](11-embeddings-and-hybrid.md)

</div>
