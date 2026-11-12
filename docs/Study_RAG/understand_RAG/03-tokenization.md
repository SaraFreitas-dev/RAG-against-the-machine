<div align="center">

# 🔤 03 — Tokenization

**Turning text into the terms a search engine can compare**

`📚 Concepts` · `⏱️ ~20 min read` · `🎯 Prerequisite: 02 — Chunking`

</div>

---

> [!IMPORTANT]
> **TL;DR** — Lexical search (TF-IDF, BM25) doesn't compare sentences, it compares **terms**. **Tokenization** is the function that turns a text into a list of terms, and it runs on **both sides**:
> - 📦 on every **chunk**, at indexing time;
> - ❓ on every **question**, at search time.
>
> A question and a chunk can only "agree" on terms that **both** produce **identically**. So tokenization decides which matches are even possible, long before any scoring formula runs. 🎯

---

## 📑 Contents

1. [🧱 What is a term?](#-1-what-is-a-term)
2. [🪞 The golden rule: same tokenizer on both sides](#-2-the-golden-rule-same-tokenizer-on-both-sides)
3. [✂️ Splitting: where does a term end?](#️-3-splitting-where-does-a-term-end)
4. [🔡 Lowercasing](#-4-lowercasing)
5. [🐍 Code identifiers: the heart of this project](#-5-code-identifiers-the-heart-of-this-project)
6. [🚮 Stopwords](#-6-stopwords)
7. [🌱 Stemming and lemmatization](#-7-stemming-and-lemmatization)
8. [✏️ Worked example: four tokenizers, one question](#️-8-worked-example-four-tokenizers-one-question)
9. [🧩 The vocabulary-mismatch problem](#-9-the-vocabulary-mismatch-problem)
10. [🤖 Search tokens ≠ LLM tokens](#-10-search-tokens--llm-tokens)
11. [⏱️ Speed matters too](#️-11-speed-matters-too)
12. [🚫 Common misconceptions](#-12-common-misconceptions)
13. [✅ Check your understanding](#-13-check-your-understanding)

---

## 🧱 1. What is a term?

A **term** (or **token**) is the smallest unit the search engine compares. For lexical search, two texts "share something" only if they contain the **exact same term**: same characters, same case, nothing more, nothing less.

```text
text:   "Use --port to change the default port."
terms:  ["use", "port", "to", "change", "the", "default", "port"]
```

To the search engine, `"port"` and `"Port"` are as different as `"port"` and `"banana"` 🍌, unless the tokenizer makes them identical.

> [!NOTE]
> 🧠 Lexical search has **no idea what words mean**. It only knows whether two strings are equal. All the "intelligence" about what counts as the same word lives in the tokenizer.

---

## 🪞 2. The golden rule: same tokenizer on both sides

```text
 📦 chunk text  ──► 🔤 tokenizer ──► chunk terms ─┐
                                                 ├──► 🔍 compare ──► score
 ❓ question    ──► 🔤 tokenizer ──► query terms ─┘
                      ▲
                      └── must be the SAME function
```

If the index lowercases but the query doesn't, `"Port"` in the question never matches `"port"` in the index. If the index splits `max_num_seqs` into parts but the query keeps it whole, they never meet. 🙅

> [!CAUTION]
> ⚠️ This is the easiest bug to introduce and the hardest to notice: nothing crashes, recall just drops. Changing the tokenizer also means **re-indexing** — an old index built with the previous tokenizer is silently incompatible. 🔄

---

## ✂️ 3. Splitting: where does a term end?

The simplest idea, splitting on spaces, breaks quickly on real text:

| Text | Split on spaces | Problem |
|---|---|---|
| `server.` | `server.` | Punctuation glued on, so it won't match `server` |
| `(model,` | `(model,` | Same |
| `"--port"` | `"--port"` | Quotes and dashes glued on |
| `config.yaml` | `config.yaml` | Is that one term or two? |
| `vllm.engine.arg_utils` | one term | Is that one term, three, or more? |

A more useful idea: decide which characters can be **part of** a term (letters, digits, maybe `_`…) and split on **everything else**.

> [!TIP]
> 🧭 "Which characters belong to a term?" sounds trivial, but for **code** it's a real decision. Is `_` a separator or part of a name? What about `.` and `-`? Section 5 shows why there's no single right answer, and why keeping **more than one version** of a term can help. 🤔

---

## 🔡 4. Lowercasing

| ✅ Pros | ❌ Cons |
|---|---|
| `Port`, `PORT`, `port` all match | Loses distinctions that sometimes matter |
| Questions are written casually; code and docs use all kinds of casing | `LLM` (the class) and `llm` (a variable) become the same term |

> [!NOTE]
> 🤏 For this project the pros usually win by far: people asking questions don't reproduce exact casing. But **when** you lowercase matters for code identifiers: `SamplingParams` carries information in its capital letters (where the word boundaries are). Lowercase it **too early** and that information is gone. 👇

---

## 🐍 5. Code identifiers: the heart of this project

Code names glue several words into one string, using different conventions:

| Convention | Example | Words inside |
|---|---|---|
| 🐍 `snake_case` | `gpu_memory_utilization` | gpu · memory · utilization |
| 🐫 `camelCase` / `PascalCase` | `SamplingParams` | sampling · params |
| 🔠 Acronym + word | `LLMEngine`, `HTTPServer` | llm · engine / http · server |
| 🚩 CLI flags (kebab) | `--gpu-memory-utilization` | gpu · memory · utilization |
| 🌐 Env variables | `VLLM_USE_V1` | vllm · use · v1 |
| 🧭 Dotted paths | `vllm.engine.arg_utils` | vllm · engine · arg · utils |

### 🎭 Two kinds of questions

The subject's lightbulb hint (p. 11) says questions either **quote an identifier verbatim** or **paraphrase an idea**:

| Question style | Example | What helps matching |
|---|---|---|
| 🎯 **Verbatim** | *"What does `gpu_memory_utilization` control?"* | Keeping `gpu_memory_utilization` as **one whole term**: it's rare, so a match on it is very strong evidence |
| 💬 **Paraphrase** | *"How much GPU memory does vLLM use?"* | Splitting into **parts** (`gpu`, `memory`, `utilization`) so ordinary words can match pieces of the name |

Keep only the whole name and paraphrased questions can't reach it. Keep only the parts and you lose the strong, rare signal of the exact identifier. ⚖️

### 🔗 Same concept, different spellings

vLLM, like many projects, spells one setting several ways:

```text
docs:      --gpu-memory-utilization        ← CLI flag (dashes)
code:      gpu_memory_utilization          ← Python attribute (underscores)
question:  "gpu memory utilization"        ← plain words
```

Whole-name matching alone makes these **three different terms**. Splitting into parts makes them share `gpu`, `memory` and `utilization`. 🤝

### ✂️ CamelCase boundaries

Where are the words in `LLMEngine`? A human sees `LLM` + `Engine`. The boundary sits where an uppercase run meets an uppercase-then-lowercase pair. Some tricky cases to think about:

| Identifier | Natural parts |
|---|---|
| `SamplingParams` | sampling · params |
| `LLMEngine` | llm · engine |
| `getHTTPResponse` | get · http · response |
| `Qwen2VLForConditionalGeneration` | qwen · 2 · vl · for · conditional · generation (digits are a judgement call) |

> [!TIP]
> 💡 There's no requirement to choose **one** representation. A tokenizer can emit **several terms** for the same identifier: the whole name *and* its parts. Whether that's a good idea, and how it interacts with scoring (one identifier now counts several times…), is worth testing on your datasets. 🧪

---

## 🚮 6. Stopwords

**Stopwords** are extremely common words that carry little meaning on their own: *the, a, of, in, is, how, do, what…*

```text
question:   "how do I change the port in vllm"
no stops:   ["change", "port", "vllm"]
```

| ✅ Removing them | ❌ Removing them |
|---|---|
| Fewer terms → smaller index, faster search | Some "stopwords" matter: `"not"`, `"no"`, `"all"`, `"none"` |
| Scores focus on meaningful words | In code, `in`, `is`, `if`, `for`, `None` are syntax… and sometimes exactly what's asked |

> [!NOTE]
> 🧮 Good ranking functions (TF-IDF, BM25, docs 04–05) already give **very low weight** to terms that appear everywhere. So stopwords hurt much less than you'd expect, and removing them is more about **speed and size** than accuracy. Measure before deciding. 📊

> [!TIP]
> 🐍 Code has its own "stopwords": `self`, `def`, `return`, `import`, `None`, `args`… They appear in almost every Python chunk. A ranking function's rarity weighting handles them too, but it's useful to **know** they're there when you inspect why a chunk scored well.

---

## 🌱 7. Stemming and lemmatization

Different forms of the same word don't match by default:

```text
question:  "How do I configure the server?"
chunk:     "Server configuration options..."
           configure ≠ configuration  ❌
```

| Technique | Idea | Example |
|---|---|---|
| ✂️ **Stemming** | Chop endings with rules | configure, configured, configuration → `configur` |
| 📖 **Lemmatization** | Map to the dictionary form | ran, running, runs → `run` |

| ✅ Pros | ❌ Cons |
|---|---|
| More matches between different word forms | **Over-stemming**: unrelated words collapse (classic example: *universe* and *university* both → `univers`) |
| Helps paraphrased questions | Mangles code identifiers if applied to them |
|  | An extra library and extra time on every token |

> [!WARNING]
> 🤔 Stemming was designed for **English prose**. Applying it to code names (`params`, `utils`, `seqs`) can do odd things. If you try it, think about **which terms** it should touch.

---

## ✏️ 8. Worked example: four tokenizers, one question

**Chunk** (from a made-up `arg_utils.py`):

```python
parser.add_argument("--max-num-seqs", type=int,
                    help="Maximum number of sequences per iteration.")
self.max_num_seqs = max_num_seqs
```

Let's compare four tokenizers, each adding one idea:

| | Tokenizer |
|:-:|---|
| **A** | Split on spaces only, keep case |
| **B** | Lowercase, split on anything that isn't a letter, digit or `_` |
| **C** | Like B, but also emit the **parts** of identifiers (split on `_`) |
| **D** | Like C, minus stopwords |

### ❓ Question 1 (paraphrase): *"How do I set the max number of sequences in vLLM?"*

| | Some chunk terms | Matching terms | Notes |
|:-:|---|---|---|
| **A** | `parser.add_argument("--max-num-seqs",` · `help="Maximum` · `number` · `of` · `sequences` · `iteration.")` | number, of, sequences | `max` never matches: it's buried inside glued strings |
| **B** | `parser` · `add_argument` · `max` · `num` · `seqs` · `maximum` · `number` · `of` · `sequences` · `max_num_seqs` | max, number, of, sequences | `--max-num-seqs` split on `-`, so `max` now matches |
| **C** | B + `add` · `argument` + the parts of `max_num_seqs` | max, number, of, sequences | Same matches here, but `max` now appears more often in the chunk |
| **D** | C without `of`, `per`… | max, number, sequences | Only meaningful matches left |

### ❓ Question 2 (verbatim): *"What does max_num_seqs control?"*

| | Query terms | Matching terms | Notes |
|:-:|---|---|---|
| **A** | `What` · `does` · `max_num_seqs` · `control?` | max_num_seqs | Works by luck: it's followed by a space in both texts |
| **B** | `what` · `does` · `max_num_seqs` · `control` | max_num_seqs | Matches the attribute, but **not** the flag `--max-num-seqs` (split into `max`, `num`, `seqs`) |
| **C** | B + `max` · `num` · `seqs` | max_num_seqs, max, num, seqs | Now the flag's words match too: both spellings are reachable 🤝 |
| **D** | C without `what`, `does` | max_num_seqs, max, num, seqs | Same, cleaner |

> [!IMPORTANT]
> 🔍 Notice what **never** matches in any version: the question says `sequences`, the code says `seqs`; the question says `max`, the help text says `Maximum`. Abbreviations and synonyms are invisible to lexical search, whatever the tokenizer. That's Section 9. 👇

---

## 🧩 9. The vocabulary-mismatch problem

Questions and sources are written by **different people** with **different words**:

| Question says | Source says | Lexical match? |
|---|---|:-:|
| sequences | seqs | ❌ |
| maximum | max | ❌ |
| launch | start / serve | ❌ |
| VRAM | gpu memory | ❌ |
| configure | configuration | ❌ (✅ with stemming) |
| GPU | gpu | ❌ (✅ with lowercasing) |

Tokenization can close **some** gaps (case, punctuation, word forms, identifier parts), but never **synonyms** or **abbreviations**. Those need either:

- 🧭 **semantic search**, which matches meaning instead of strings (bonus, doc 11), or
- 🗂️ extra knowledge you add yourself, like synonym or abbreviation lists, with all the risk of hand-made rules.

> [!TIP]
> 🔬 When a question fails, put its terms next to the reference chunk's terms and look at **which words don't meet**. That tells you whether the fix belongs in tokenization, chunking (doc 02, the lost-context problem), or is simply beyond lexical search.

---

## 🤖 10. Search tokens ≠ LLM tokens

The word "token" means two different things in this project:

| | 🔍 Search tokenizer | 🤖 LLM tokenizer (Qwen) |
|---|---|---|
| **Who designs it** | **You** | Fixed, shipped with the model |
| **Units** | Words / identifier parts | Sub-word pieces learned from data (`"utilization"` might be 2–3 pieces) |
| **Used for** | Matching questions to chunks | Feeding text to the model, counting the context budget |
| **Where** | Index + search (docs 03–06) | Augment + generate (doc 08) |

> [!WARNING]
> 🙅 Don't mix them up. The LLM's tokenizer is designed for the model, not for retrieval. And the context budget for Qwen must be counted in **its** tokens, not your search terms.

---

## ⏱️ 11. Speed matters too

The tokenizer runs **a lot**:

| When | How often | Budget |
|---|---|---|
| 📦 Indexing | Once per chunk, over the **whole corpus** (tens of thousands of chunks) | Everything must finish in **≤ 5 min** |
| ❓ Searching | Once per question | **200 questions in ≤ 90 s**, including scoring |

Every extra step (several term versions, stemming, complex regular expressions) multiplies over the whole corpus. Usually it's fine, but measure it: `tqdm` already shows you chunks per second. ⏲️

---

## 🚫 12. Common misconceptions

| ❌ Myth | ✅ Reality |
|---|---|
| "Tokenizing is just `split()`." | Splitting on spaces leaves punctuation glued to words and breaks most matches in code. |
| "The ranking formula is where the quality comes from." | The formula only scores terms that **already match**. Tokenization decides what can match. |
| "Index and query can be processed differently." | They must go through the **same** function, or matches silently disappear. |
| "Removing stopwords is essential." | TF-IDF / BM25 already down-weight frequent terms. It's mostly a size/speed choice. |
| "Splitting identifiers into parts loses information." | Only if you **replace** the whole name. Emitting both is an option. |
| "Stemming always helps." | It can merge unrelated words and mangle code names. |
| "A good tokenizer solves synonyms." | Lexical search can't know that *launch* ≈ *start*. That's the job of semantic search. |
| "Tokens are tokens." | Search terms (yours) and LLM tokens (Qwen's) are different things with different purposes. |

---

## ✅ 13. Check your understanding

Try first, then open the hints. 🧩

**1.** Your index lowercases text, but you forgot to lowercase questions. Which questions are affected, and how would you notice?
<details><summary>💡 Hint</summary>Which question words contain capitals? Think about identifiers like <code>LLMEngine</code> and words at the start of a sentence. (Section 2)</details>

**2.** Split `--gpu-memory-utilization`, `gpu_memory_utilization` and `GPUMemoryUtilization` into the parts a human would see. Which tokenizer rules are needed so that all three share terms?
<details><summary>💡 Hint</summary>Three separators are involved: <code>-</code>, <code>_</code>, and a change of case. (Section 5)</details>

**3.** Why might a question that quotes an identifier verbatim be **easier** to answer than a paraphrased one, if the tokenizer keeps whole identifiers?
<details><summary>💡 Hint</summary>How many chunks in the corpus contain that exact identifier? How rare is it, compared with words like "memory"? (Section 5, and doc 04)</details>

**4.** Removing stopwords barely changed your recall. Is that surprising? Why or why not?
<details><summary>💡 Hint</summary>How do ranking functions weight terms that appear in almost every chunk? (Section 6)</details>

**5.** In the worked example, why does tokenizer A match `max_num_seqs` in question 2 only "by luck"?
<details><summary>💡 Hint</summary>What would happen if the question had been <i>"What does max_num_seqs do?"</i> with a question mark right after the name? (Section 8)</details>

**6.** A question says *"How do I limit concurrent requests?"* and the reference chunk only talks about `max_num_seqs`. Can any tokenizer fix this? What could?
<details><summary>💡 Hint</summary>Is there a single word in common, even after splitting and stemming? (Section 9)</details>

**7.** Your colleague suggests using Qwen's tokenizer for the BM25 index "since we already load it". What would you answer?
<details><summary>💡 Hint</summary>What is each tokenizer designed for? What units does Qwen's tokenizer produce? (Section 10)</details>

---

## 📚 Further reading

- 📘 Manning, Raghavan & Schütze, *Introduction to Information Retrieval*, ch. 2 (tokenization, stopwords, stemming, lemmatization): <https://nlp.stanford.edu/IR-book/>
- 🔣 Python `re` module (regular expressions, character classes): <https://docs.python.org/3/library/re.html>
- 🌱 The Porter stemming algorithm, by its author: <https://tartarus.org/martin/PorterStemmer/>

---

<div align="center">

**← Previous** [02 — Chunking ✂️](02-chunking.md) · [🏠 Docs index](README.md) · **Next →** [04 — TF-IDF 📊](04-tf-idf.md)

</div>
