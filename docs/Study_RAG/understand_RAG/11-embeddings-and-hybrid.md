<div align="center">

# 🧭 11 — Embeddings and hybrid retrieval *(bonus)*

**Searching by meaning, and combining it with lexical search**

`📚 Concepts` · `⏱️ ~25 min read` · `🎯 Prerequisite: 05 — BM25 · 07 — Evaluation` · `🎁 Bonus`

</div>

---

> [!IMPORTANT]
> **TL;DR** — Lexical search (TF-IDF, BM25) only matches **identical terms**, so it can't see that *"launch"* and *"start"* mean the same thing. **Semantic search** turns every text into a **vector of numbers** (an **embedding**) so that texts with similar **meaning** end up close together, even when they share no words. 🧭
>
> **Hybrid retrieval** combines both rankings into one list, keeping lexical search's strength on exact identifiers and semantic search's strength on paraphrases. 🤝
>
> Two of the five bonuses: **(1) semantic embeddings** with a lightweight CPU model such as `all-MiniLM-L6-v2`, and **(2) hybrid retrieval**.

---

> [!CAUTION]
> 🚧 *"The bonus is graded only once the entire mandatory part is validated."* A bonus must be **implemented and working**, and you may be asked to demonstrate it. Don't start here while the mandatory recall thresholds or robustness checks aren't solid. And the bonus must never **replace** the mandatory lexical method: it sits **next to** it.

---

## 📑 Contents

1. [🧩 The problem semantic search solves](#-1-the-problem-semantic-search-solves)
2. [🔢 What is an embedding?](#-2-what-is-an-embedding)
3. [📐 Measuring similarity](#-3-measuring-similarity)
4. [🧪 Where embeddings come from](#-4-where-embeddings-come-from)
5. [⚖️ Sparse vs dense](#️-5-sparse-vs-dense)
6. [🗄️ A vector index](#️-6-a-vector-index)
7. [⚠️ Limits you'll hit in this project](#️-7-limits-youll-hit-in-this-project)
8. [🤝 Hybrid retrieval: why combine?](#-8-hybrid-retrieval-why-combine)
9. [🔀 Combining rankings](#-9-combining-rankings)
10. [✏️ Worked example: Reciprocal Rank Fusion](#️-10-worked-example-reciprocal-rank-fusion)
11. [📊 Evaluating the bonus](#-11-evaluating-the-bonus)
12. [🚫 Common misconceptions](#-12-common-misconceptions)
13. [✅ Check your understanding](#-13-check-your-understanding)

---

## 🧩 1. The problem semantic search solves

Doc 03, Section 9 listed the **vocabulary mismatch** cases that no tokenizer can fix:

| Question says | Source says | Lexical | Semantic |
|---|---|:-:|:-:|
| launch the API | start the server | ❌ | ✅ likely |
| reduce VRAM usage | lower `gpu_memory_utilization` | ❌ | 🤔 maybe |
| limit concurrent requests | `max_num_seqs` | ❌ | 🤔 hard |
| `gpu_memory_utilization` | `gpu_memory_utilization` | ✅ | 🤔 weaker |

> [!NOTE]
> 🔄 Notice the last row: semantic search is **not** strictly better. Exact identifiers are lexical search's home turf. That's the whole case for hybrid retrieval (Section 8). ⚖️

---

## 🔢 2. What is an embedding?

An **embedding** is a fixed-length list of numbers (a **vector**) that represents a text's meaning.

```text
"Start the OpenAI-compatible server"   →  [ 0.021, -0.113, 0.087, …, 0.045 ]   (384 numbers)
"How do I launch the API?"             →  [ 0.019, -0.098, 0.091, …, 0.052 ]   (384 numbers)
"Install vLLM with pip"                →  [-0.071,  0.034, -0.012, …, 0.110 ]  (384 numbers)
```

The individual numbers don't have readable meanings. What matters is the **geometry**: texts about similar things get vectors pointing in similar directions. 🧭

### 🗺️ The map analogy

Imagine a map where every text is a city. A good embedding model places cities so that:

- 🏙️ texts about **starting servers** cluster in one region,
- 🏘️ texts about **GPU memory** in another,
- 🏡 texts about **installation** in a third…

…and a question lands **near** the texts that answer it, whatever words it uses.

### 🧸 A toy version with 3 dimensions

Pretend each dimension measures one theme (real models learn hundreds of unnamed dimensions):

| Text | 🖥️ serving | 🎮 GPU memory | 📦 install |
|---|:-:|:-:|:-:|
| ❓ *"How do I launch the API?"* | 0.9 | 0.1 | 0.2 |
| A: *"Start the OpenAI-compatible server with vllm serve"* | 0.8 | 0.2 | 0.1 |
| B: *"Set gpu_memory_utilization to limit memory"* | 0.1 | 0.9 | 0.1 |
| C: *"Install vLLM with pip"* | 0.2 | 0.1 | 0.9 |

The question shares **no words** with chunk A, yet their vectors point the same way. 🎯

---

## 📐 3. Measuring similarity

The standard measure is **cosine similarity** (the same idea as in doc 04, Section 8, but on dense vectors):

```text
                 a · b
cos(a, b) =  ───────────
             ‖a‖ × ‖b‖
```

| Value | Meaning |
|:-:|---|
| 1 | Same direction: very similar meaning |
| 0 | Unrelated |
| < 0 | Opposite directions (rarer in practice with text) |

### 🧮 The toy example

| Chunk | cos(question, chunk) | Rank |
|:-:|:-:|:-:|
| A (start the server) | **0.987** | 🥇 |
| C (install) | 0.430 | 🥈 |
| B (GPU memory) | 0.237 | 🥉 |

✅ Chunk A wins without sharing a single word with the question.

> [!TIP]
> ⚡ If every vector is **normalized** to length 1 beforehand, cosine similarity becomes a plain **dot product**: one multiplication and sum per dimension. That's what makes comparing one question to thousands of chunks fast. The `all-MiniLM-L6-v2` model card uses normalized embeddings with cosine similarity.

---

## 🧪 4. Where embeddings come from

You don't compute embeddings by hand: a **pretrained encoder** model does it.

| Step | What happens |
|---|---|
| 📚 Pre-training | A transformer learns language from a lot of text |
| 🤝 Similarity training | It's then trained on **pairs** that should be close (question ↔ answer, title ↔ paragraph…) and pushed away from unrelated texts |
| 🧭 Result | A function: text in → vector out, where "close vectors" ≈ "related meaning" |

### 🐣 `all-MiniLM-L6-v2` (suggested by the subject)

| | |
|---|---|
| Parameters | ~22.7 M (tiny next to Qwen's 600 M) |
| Output | **384**-dimensional vectors |
| Intended for | Sentences and **short paragraphs**: retrieval, clustering, similarity |
| Max input | **256 word pieces**: longer text is **truncated** |
| Training length | 128 tokens |
| Runs on | CPU, comfortably |

> [!WARNING]
> ✂️ That 256-word-piece limit matters a lot here (Section 7). 🔍

> [!NOTE]
> 🤖 This encoder is **not** an LLM like Qwen: it doesn't generate text. It only maps text to vectors. Different model, different tokenizer, different job.

---

## ⚖️ 5. Sparse vs dense

| | 🔤 Sparse (TF-IDF, BM25) | 🧭 Dense (embeddings) |
|---|---|---|
| Vector length | Vocabulary size (tens of thousands) | Fixed and small (e.g. 384) |
| Non-zero values | Few (only the chunk's terms) | All of them |
| Each dimension means… | One specific term | Nothing readable |
| Matches | **Identical terms** | **Similar meaning** |
| Exact identifiers | ✅ Excellent | 🤔 Weaker |
| Paraphrases, synonyms | ❌ Blind | ✅ Good |
| Explainability | ✅ "Matched `port` (rare) twice" | ❌ "The vectors are close" |
| Index cost | Counting, fast | Running a neural network on every chunk |
| Needs a model | No | Yes (download, load, CPU time) |

---

## 🗄️ 6. A vector index

### 🏗️ At indexing time

```text
for each chunk:
    vector = encoder(chunk text)       ← the expensive part
store all vectors as one N × 384 table, aligned with your chunk IDs
```

| Concern | Detail |
|---|---|
| ⏱️ **Time** | Encoding every chunk on a CPU takes real time, and the subject's **5-minute** indexing limit still applies. Encoding chunks in **batches** is much faster than one by one |
| 💾 **Size** | ~13,000 chunks × 384 floats × 4 bytes ≈ **21 MB**. Small |
| 🔗 **Alignment** | Row *i* of the table must belong to chunk *i* of the chunk store (doc 06). An off-by-one here silently returns the wrong addresses 😱 |
| 💾 **Persistence** | Saved next to the lexical index in `data/processed/`. Numeric array formats suit it well (doc 06, Section 7) |

### 🔍 At search time

```text
q = encoder(question)                   ← one encoding per question, fast
scores = similarity(q, every chunk vector)
keep the top-k
```

> [!TIP]
> 📏 At this scale (tens of thousands of vectors), comparing the question with **every** vector is perfectly fine: it's one matrix-vector product. Approximate nearest-neighbour libraries (FAISS, HNSW…) exist for **millions** of vectors, and aren't needed here.

> [!NOTE]
> 🧩 The inverted-index trick (doc 06) doesn't apply to dense vectors: every value is non-zero, so every chunk is a candidate. The speed comes from vectorized arithmetic instead.

---

## ⚠️ 7. Limits you'll hit in this project

| Limit | Why it matters here |
|---|---|
| ✂️ **Truncation at 256 word pieces** | A 2000-character chunk is often **well over** 256 pieces, especially code. Only the **beginning** of the chunk is embedded, and the rest is invisible to semantic search 🙈 |
| 🐍 **Code** | The model was trained mostly on natural language. Code, identifiers and symbols are represented less well |
| 🔤 **Exact names** | Two different config names in similar contexts can get almost identical vectors |
| 🧠 **No explanations** | When a semantic result is wrong, it's hard to say why |
| 🐢 **CPU cost** | Encoding the whole corpus competes with the 5-minute indexing budget |
| ↔️ **Asymmetry** | Questions are short, chunks are long. Models trained on short-to-short similarity may handle this less well |

> [!IMPORTANT]
> 📐 Truncation interacts with **chunk size** (doc 02). Chunks sized well for BM25 and the IoU test may be too long to embed fully. Some designs embed a shorter version of each chunk, or use different granularities for the two indexes. Each choice has consequences for alignment and for what the returned address covers. 🤔

---

## 🤝 8. Hybrid retrieval: why combine?

The two methods fail on **different** questions:

| Question | BM25 | Semantic |
|---|:-:|:-:|
| *"What does `max_num_seqs` control?"* (exact identifier) | ✅ | 🤔 |
| *"How do I launch the API server?"* (paraphrase) | 🤔 | ✅ |
| *"Which env var sets the port?"* (mix) | 🤔 | 🤔 |

If their **mistakes don't overlap**, combining them can beat both. That's the whole idea of hybrid retrieval. 🤝

> [!NOTE]
> 📈 "Can beat both" isn't guaranteed: a bad combination can also be **worse** than the better of the two. Hybrid retrieval only earns its place if your evaluation shows it (Section 11).

---

## 🔀 9. Combining rankings

You have two ranked lists for the same question. How do you merge them?

### 🧮 Option A: combine scores

```text
final(d) = α · normalized_bm25(d) + (1 − α) · normalized_cosine(d)
```

| Issue | Why |
|---|---|
| 📏 **Different scales** | BM25 scores are unbounded (2.05, 14.7…), cosine is around 0–1. Adding them raw lets BM25 dominate |
| 🔧 **Normalization needed** | Min-max per query, z-score… each with quirks (one outlier squashes everything else) |
| 🎛️ **A weight α to tune** | More tuning, more risk of overfitting the public datasets (doc 05, Section 8) |

### 🏅 Option B: combine ranks (Reciprocal Rank Fusion)

Ignore the raw scores and use only the **positions**:

```text
               1
RRF(d) =  Σ  ─────────
         lists  k + rank(d)
```

| Part | Meaning |
|---|---|
| `rank(d)` | Position of chunk *d* in a list (1 = best). A list that doesn't contain *d* adds nothing |
| `k` | A constant, commonly **60**, that softens the gap between rank 1 and rank 2 |
| Sum over lists | A chunk ranked well in **both** lists gets the highest total |

| ✅ RRF | ❌ RRF |
|---|---|
| No score normalization needed | Throws away how **confident** each method was |
| Almost nothing to tune | A chunk ranked 1st by only one method can lose to one ranked moderately by both |
| Robust, widely used | Ties can happen (see below) |

> [!TIP]
> 🎣 Both options need **candidates**: typically the top N (say 20–100) from each method, merged. A chunk outside both candidate lists can't appear in the final result, so N must be comfortably larger than the final k.

---

## ✏️ 10. Worked example: Reciprocal Rank Fusion

Two rankings for the same question (`k = 60`):

| Rank | 🔤 BM25 | 🧭 Semantic |
|:-:|:-:|:-:|
| 1 | A | C |
| 2 | B | F |
| 3 | C | A |
| 4 | D | G |
| 5 | E | B |

### 🧮 RRF scores

| Chunk | BM25 rank | Semantic rank | Computation | **RRF** |
|:-:|:-:|:-:|---|:-:|
| A | 1 | 3 | 1/61 + 1/63 | **0.03227** |
| C | 3 | 1 | 1/63 + 1/61 | **0.03227** |
| B | 2 | 5 | 1/62 + 1/65 | **0.03151** |
| F | — | 2 | 1/62 | 0.01613 |
| D | 4 | — | 1/64 | 0.01562 |
| G | — | 4 | 1/64 | 0.01562 |
| E | 5 | — | 1/65 | 0.01538 |

### 🏁 Final top-5

| Rank | Chunk | Why |
|:-:|:-:|---|
| 1–2 | A, C (tie) | Strong in **both** lists |
| 3 | B | Good in both |
| 4 | F | Only semantic, but ranked 2nd there |
| 5 | D or G (tie) | One list each, rank 4 |

👀 Observations:

- 🤝 Chunks found by **both** methods dominate the top: agreement is rewarded.
- ⚖️ A and C tie exactly: rank 1 + rank 3 = rank 3 + rank 1. Your program needs a **tie-breaking rule** (prefer the lexical rank? the semantic one?) and it should be deterministic.
- 🎯 F, invisible to BM25, makes the top 5 thanks to semantic search alone. That's the kind of question hybrid retrieval rescues.

---

## 📊 11. Evaluating the bonus

To show the bonus **works** (the subject's requirement), compare the three systems on the **same** datasets with the **same** chunks:

| System | Docs R@5 | Code R@5 | Search time (200 q) |
|---|:-:|:-:|:-:|
| 🔤 BM25 only | … | … | … |
| 🧭 Semantic only | … | … | … |
| 🤝 Hybrid | … | … | … |

| Look at | Why |
|---|---|
| 📝 Docs vs 💻 code separately | Semantic search may help docs (prose) and barely help code, or even hurt it |
| ⏱️ Time | The **90-second** budget for 200 questions still applies |
| 🔍 Per-question changes | Which questions did hybrid **fix**, which did it **break**? (doc 07, Section 9) |

> [!TIP]
> 🎤 For the defense, keep one or two **concrete examples**: a paraphrased question BM25 misses and hybrid finds, with both rankings side by side. It shows you understand *why* the bonus helps, not only that a number went up. 📈

---

## 🚫 12. Common misconceptions

| ❌ Myth | ✅ Reality |
|---|---|
| "Semantic search is strictly better than BM25." | It's better on paraphrases and worse on exact identifiers. They're complementary. |
| "The embedding sees my whole 2000-character chunk." | Input beyond 256 word pieces is **truncated**. |
| "Each of the 384 numbers means something." | Only the overall direction is meaningful. |
| "Add BM25 and cosine scores together." | Their scales are unrelated. Normalize first, or combine ranks (RRF). |
| "Hybrid always improves results." | Only if the two methods' mistakes differ. Measure it. |
| "Large-scale vector databases are needed." | At ~13,000 chunks, comparing with every vector is fast enough. |
| "The bonus can replace BM25/TF-IDF." | The mandatory part requires a lexical method. Semantic search comes **on top**. |
| "The embedding model is like Qwen." | It's a small encoder: text → vector. It doesn't generate text. |

---

## ✅ 13. Check your understanding

Try first, then open the hints. 🧩

**1.** Name one question type where BM25 beats semantic search, and one where it's the other way round. Why?
<details><summary>💡 Hint</summary>One quotes an exact identifier; the other uses different words for the same idea. (Sections 1 and 8)</details>

**2.** In the toy example, chunk A shares no words with the question but scores 0.987. Explain in one sentence why that's possible.
<details><summary>💡 Hint</summary>What does an embedding encode, instead of words? (Sections 2 and 3)</details>

**3.** Your chunks are up to 2000 characters, and many code chunks exceed 256 word pieces. What part of those chunks does the semantic index actually "see"? What could you do about it?
<details><summary>💡 Hint</summary>Truncation keeps the beginning. Think about chunk granularity, and what each index stores. (Section 7)</details>

**4.** BM25 scores for a query range from 0 to 18, cosine scores from 0.1 to 0.6. What goes wrong if you simply add them?
<details><summary>💡 Hint</summary>Which method would decide almost every ranking? (Section 9)</details>

**5.** Recompute the RRF table if chunk G were ranked 4th by **both** methods (and D not at all). Where does G land?
<details><summary>💡 Hint</summary>G would get 1/64 + 1/64. Compare with B's 0.03151. (Section 10)</details>

**6.** After adding hybrid retrieval, docs R@5 rises from 0.84 to 0.88, code R@5 drops from 0.55 to 0.51, and search time doubles. What would you report, and would you keep it as default?
<details><summary>💡 Hint</summary>Thresholds are per dataset. Time budgets still apply. Could the combination be weighted differently? (Section 11)</details>

**7.** Your vector table has one row fewer than your chunk store because one chunk failed to encode. What happens to the search results, and how would you notice?
<details><summary>💡 Hint</summary>Row i should be chunk i. What happens to every row after the gap? (Section 6, alignment)</details>

---

## 📚 Further reading

- 🤗 `all-MiniLM-L6-v2` model card: <https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2>
- 📦 Sentence Transformers documentation: <https://www.sbert.net/>
- 📄 Reimers & Gurevych, *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks* (2019): <https://arxiv.org/abs/1908.10084>
- 📄 Cormack, Clarke & Büttcher, *Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods* (2009): <https://doi.org/10.1145/1571941.1572114>

---

<div align="center">

**← Previous** [10 — A robust CLI 🛡️](10-robust-cli.md) · [🏠 Docs index](README.md)

🎉 **You've reached the end of the docs.**

</div>
