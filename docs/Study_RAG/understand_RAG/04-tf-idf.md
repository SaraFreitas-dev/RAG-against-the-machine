<div align="center">

# 📊 04 — TF-IDF

**Scoring a chunk: how often a term appears × how rare it is**

`📚 Concepts` · `⏱️ ~20 min read` · `🎯 Prerequisite: 03 — Tokenization`

</div>

---

> [!IMPORTANT]
> **TL;DR** — After tokenization, every chunk is a bag of terms. To rank chunks for a question, we need a **score**. TF-IDF builds it from two intuitions:
> - 🔁 **TF (Term Frequency)**: a chunk that mentions a question term **more often** is probably more about it;
> - 💎 **IDF (Inverse Document Frequency)**: a term that appears in **few** chunks is a much stronger clue than one that appears everywhere.
>
> Multiply the two, add them up over the question's terms, and you get a ranking. It's simple, fast, explainable, and one of the two methods the subject accepts.

---

## 📑 Contents

1. [🎯 The problem: turning matches into a ranking](#-1-the-problem-turning-matches-into-a-ranking)
2. [🧮 Vocabulary: N, tf, df](#-2-vocabulary-n-tf-df)
3. [🔁 TF: how often?](#-3-tf-how-often)
4. [💎 IDF: how rare?](#-4-idf-how-rare)
5. [✖️ Putting them together](#️-5-putting-them-together)
6. [✏️ Worked example, by hand](#️-6-worked-example-by-hand)
7. [😈 The repetition problem, and log-scaled TF](#-7-the-repetition-problem-and-log-scaled-tf)
8. [📐 Vectors and cosine similarity](#-8-vectors-and-cosine-similarity)
9. [🧩 The variants zoo](#-9-the-variants-zoo)
10. [🚧 Limitations: the road to BM25](#-10-limitations-the-road-to-bm25)
11. [🚫 Common misconceptions](#-11-common-misconceptions)
12. [✅ Check your understanding](#-12-check-your-understanding)

---

## 🎯 1. The problem: turning matches into a ranking

In doc 00 we scored chunks by **counting** matching words. That breaks quickly:

```text
question: "what is the default port"

chunk X: "the model is loaded and the weights are cast"        → matches: what? no · the ✔ · is ✔   → 2
chunk Y: "the default port is 8000"                            → matches: the ✔ · default ✔ · port ✔ · is ✔ → 4
chunk Z: "the the the the is is is is the is"                  → matches: the ✔ · is ✔ (many times!)
```

Two things are wrong with plain counting:

| | Problem | Example |
|:-:|---|---|
| 🗑️ | **All words count the same.** Matching `the` is worth as much as matching `port`. | X gets 2 points for `the` and `is`, which says nothing about ports |
| 🔁 | **What about repetition?** Should matching a word 10 times count 10×? | Z would win if we counted every occurrence |

TF-IDF fixes the first problem with **IDF** and handles the second with **TF** (and Section 7 refines it).

---

## 🧮 2. Vocabulary: N, tf, df

In IR (Information Retrieval) books, every unit you search is called a **document**. In this project, a "document" is a **chunk**. 📦 = 📄

| Symbol | Name | Meaning | Depends on |
|:-:|---|---|---|
| **N** | Collection size | Total number of chunks in the index | the index |
| **tf(t, d)** | Term frequency | How many times term *t* appears in chunk *d* | one term + one chunk |
| **df(t)** | Document frequency | How many **chunks** contain *t* at least once | one term, whole index |

> [!WARNING]
> 🧠 Don't confuse **tf** and **df**:
> - `tf` looks **inside one chunk** and counts **occurrences**;
> - `df` looks **across all chunks** and counts **chunks**: a term appearing 50 times in one chunk still adds just **1** to `df`.

---

## 🔁 3. TF: how often?

**Intuition:** a chunk that says `port` five times is probably more *about* ports than one that mentions it once in passing.

The simplest version is the raw count:

```text
tf(t, d) = number of times t appears in d
```

```text
chunk: "port server port default"

tf(port)    = 2
tf(server)  = 1
tf(default) = 1
tf(model)   = 0
```

> [!NOTE]
> 🔁 Raw counts grow **linearly**: 10 mentions = 10× the weight of 1. Is the 10th `port` really as informative as the first? Probably not. Hold that thought until Section 7. 🤔

---

## 💎 4. IDF: how rare?

**Intuition:** if a term appears in **almost every** chunk (`the`, `self`, `vllm` 😅), finding it in a chunk tells you nothing. If it appears in **very few** chunks (`gpu_memory_utilization`), finding it is strong evidence. 🕵️

The classic formula:

```text
              N
idf(t) = log ────
             df(t)
```

### 🔍 Reading the formula

| Situation | N / df | log(N / df) | Meaning |
|---|:-:|:-:|---|
| Term in **every** chunk (df = N) | 1 | **0** | 🗑️ Worthless: it can't tell chunks apart |
| Term in **half** the chunks | 2 | small | 🤏 Weak clue |
| Term in **1** chunk out of 10,000 | 10,000 | large | 💎 Very strong clue |

### 🤔 Why the logarithm?

Without the log, a term in 1 chunk would be worth **10,000×** a term in half the chunks. A single rare word (a typo, a variable name) would dominate every score. The log **compresses** that range: rare terms still win, but not by absurd margins.

```text
N = 10,000

df       N/df        log(N/df)   (natural log)
10,000   1           0.00
1,000    10          2.30
100      100         4.61
10       1,000       6.91
1        10,000      9.21
```

> [!TIP]
> 📐 Which base (natural log, log₁₀, log₂) doesn't matter for **ranking**: changing the base multiplies every IDF by the same constant, so the order of chunks stays the same.

> [!NOTE]
> 🌍 IDF works because word frequencies are extremely uneven (**Zipf's law**): a handful of words are everywhere, and most words are rare. IDF exploits exactly that.

---

## ✖️ 5. Putting them together

The **weight** of term *t* in chunk *d*:

```text
w(t, d) = tf(t, d) × idf(t)
```

To score a chunk for a question *q*, one simple approach sums the weights of the question's terms:

```text
score(q, d) = Σ  tf(t, d) × idf(t)
             t ∈ q
```

In words: *for every term in the question, if the chunk contains it, add "how often it appears there" × "how rare it is overall".*

| | High tf | Low tf |
|---|---|---|
| **High idf** (rare term) | 🥇 Strong: the chunk focuses on a rare topic | 👍 Good: mentions a rare topic |
| **Low idf** (common term) | 🤏 Weak: repeats a common word | 🗑️ Almost nothing |

> [!NOTE]
> ⚡ Only terms that appear in **both** the question and the chunk contribute. Every other term has `tf = 0` and adds nothing. That's what makes search fast with an **inverted index** (doc 06): you only need to look at chunks that contain at least one question term.

---

## ✏️ 6. Worked example, by hand

A tiny index with **N = 4** chunks (already tokenized):

| Chunk | Terms |
|:-:|---|
| C1 | port · server · port · default |
| C2 | server · start · model |
| C3 | model · config · port |
| C4 | model · load · model · weights |

### 1️⃣ Document frequency and IDF (natural log)

| Term | In chunks | df | N / df | **idf** |
|---|---|:-:|:-:|:-:|
| port | C1, C3 | 2 | 2 | **0.693** |
| default | C1 | 1 | 4 | **1.386** |
| server | C1, C2 | 2 | 2 | **0.693** |
| model | C2, C3, C4 | 3 | 1.33 | **0.288** |
| start, config, load, weights | one each | 1 | 4 | **1.386** |

👀 `model` is in 3 of 4 chunks, so its idf is low. `default` is in 1 chunk, so its idf is high.

### 2️⃣ Score the question *"default port"*

| Chunk | tf(default) | tf(port) | Computation | **Score** |
|:-:|:-:|:-:|---|:-:|
| C1 | 1 | 2 | 1 × 1.386 + 2 × 0.693 | **2.773** 🥇 |
| C2 | 0 | 0 | — | **0** |
| C3 | 0 | 1 | 1 × 0.693 | **0.693** 🥈 |
| C4 | 0 | 0 | — | **0** |

**Ranking:** C1 → C3 → (C2, C4). ✅ C1, the chunk about the default port, wins clearly.

> [!TIP]
> 🧠 Notice that matching `default` (rare) is worth **twice** as much as one `port` (more common). That's IDF doing its job: the rarer clue counts more.

---

## 😈 7. The repetition problem, and log-scaled TF

Let's add a fifth, silly chunk to the index:

```text
C5: port port port port port port port port port port     (10 × "port")
```

Adding a chunk changes **N** and possibly **df**, so the IDFs change too:

| Term | df | idf (N = 5) |
|---|:-:|:-:|
| port | 3 | 0.511 |
| default | 1 | 1.609 |

### 🔁 With raw TF

| Chunk | Computation | **Score** |
|:-:|---|:-:|
| C5 | 10 × 0.511 | **5.108** 🥇 😱 |
| C1 | 1 × 1.609 + 2 × 0.511 | **2.631** |

The chunk that **only repeats one word** beats the one that actually answers the question. With real text this happens with long code files that repeat an identifier everywhere, or tables listing a word on every row.

### 📉 With log-scaled TF

A common fix is to **dampen** repetition:

```text
tf'(t, d) = 1 + log(tf(t, d))      if tf > 0
          = 0                       otherwise
```

| Raw tf | 1 + ln(tf) |
|:-:|:-:|
| 1 | 1.00 |
| 2 | 1.69 |
| 10 | 3.30 |
| 100 | 5.61 |

Now 10 mentions are worth about 3×, not 10×:

| Chunk | Computation | **Score** |
|:-:|---|:-:|
| C1 | 1.00 × 1.609 + 1.69 × 0.511 | **2.474** 🥇 ✅ |
| C5 | 3.30 × 0.511 | **1.687** |

> [!IMPORTANT]
> 🎯 The idea that **more repetitions help, but with diminishing returns** is called **saturation**. Log-TF is one way to get it. BM25 (doc 05) builds saturation in more carefully, with a parameter to control it.

---

## 📐 8. Vectors and cosine similarity

There's a second, more geometric way to use TF-IDF.

### 🧭 Each text is a vector

Imagine one axis per term in the vocabulary. A chunk becomes a point (a **vector**) whose coordinate on each axis is that term's TF-IDF weight. A question is turned into a vector the same way.

```text
            port
             ▲
             │     • C1  (lots of "port", some "default")
             │    /
             │   /   • question
             │  /  /
             │ / /
             │//___________________► default
```

With tens of thousands of terms, these vectors have tens of thousands of dimensions, but each chunk uses only a few, so almost all coordinates are 0. That's called a **sparse** vector. 🕳️

### 📏 Cosine similarity

Instead of summing, measure the **angle** between the question vector and each chunk vector:

```text
                 q · d
cos(q, d) = ───────────────
             ‖q‖ × ‖d‖
```

| Part | Meaning |
|---|---|
| `q · d` (dot product) | Sum, over shared terms, of (question weight × chunk weight) |
| `‖q‖`, `‖d‖` | The vectors' lengths |
| Result | 1 = same direction (same mix of terms), 0 = nothing in common |

> [!NOTE]
> 🧮 Dividing by `‖d‖` is a form of **length normalization**: a huge chunk with many terms gets a long vector, so its matches count for less. Without it, longer chunks win just because they contain more words. BM25 (doc 05) handles length in its own, more tunable way.

---

## 🧩 9. The variants zoo

"TF-IDF" isn't one formula, it's a **family**. Every library and textbook picks slightly different pieces:

| Piece | Common options |
|---|---|
| 🔁 **TF** | raw count · `1 + log(tf)` · `tf / chunk length` · binary (1 if present) |
| 💎 **IDF** | `log(N / df)` · smoothed `log((N + 1) / (df + 1)) + 1` (avoids division by 0 and zero weights) · `log((N − df) / df)` (probabilistic) |
| 📏 **Normalization** | none · cosine (vector length) · divide by chunk length |
| 🎯 **Scoring** | sum of weights · cosine similarity |

> [!TIP]
> 📝 Whatever you choose, **write down exactly which variant** you use in your README ("Retrieval method" section): the formula, and why. Evaluators expect you to explain your ranking mechanism, and "I used TF-IDF" isn't precise enough. 🎤

> [!WARNING]
> 📚 If you use a library implementation, read its documentation to know **which** variant it computes. You must be able to explain it at the defense, and the subject requires you to *implement* TF-IDF or BM25: check with your peers what's considered acceptable. 🤝

---

## 🚧 10. Limitations: the road to BM25

TF-IDF is a great baseline, but it has known weaknesses:

| Limitation | Why it hurts here |
|---|---|
| 🔁 **Saturation is ad hoc** | Raw TF doesn't saturate at all. Log-TF does, but you can't **tune** how fast. |
| 📏 **Length handling is crude** | Cosine normalization can over-punish long chunks, or under-punish them, with no knob to adjust. Your chunks vary a lot in size (doc 02). |
| 🎛️ **No parameters to tune** | When results are off, there's nothing to adjust except the formula itself. |
| 🧩 **Bag of words** | Word order and proximity are ignored: "port default" = "default port". |
| 🗣️ **Exact matching only** | No synonyms, no abbreviations (doc 03, Section 9). |

The first three are exactly what **BM25** addresses: tunable **saturation** (`k1`) and tunable **length normalization** (`b`). The last two are shared by all lexical methods.

---

## 🚫 11. Common misconceptions

| ❌ Myth | ✅ Reality |
|---|---|
| "TF-IDF is one fixed formula." | It's a family. TF, IDF and normalization each have several variants. |
| "df counts how many times a term appears in the corpus." | It counts **chunks** containing the term. Repetitions inside a chunk don't change df. |
| "A term in every chunk gets a negative weight." | With `log(N/df)` it gets **zero**. Some variants avoid zero with smoothing. |
| "The log base changes the ranking." | It only scales all scores by a constant. The ranking is unchanged. |
| "IDF depends on the question." | IDF depends only on the **index**. It's computed once, at indexing time. |
| "More matching words always means a better chunk." | Rare matches matter more than common ones, and repetitions should saturate. |
| "Adding a chunk doesn't affect other chunks' scores." | It changes **N** and maybe **df**, so every IDF shifts a little. |

---

## ✅ 12. Check your understanding

Try first, then open the hints. 🧩

**1.** In an index of 1000 chunks, `self` appears in 900 chunks and `max_num_seqs` in 4. Compute both IDFs (natural log). Which term is the better clue, and by how much?
<details><summary>💡 Hint</summary>idf = ln(N / df). Compare ln(1000/900) and ln(1000/4). (Section 4)</details>

**2.** A term appears 30 times in one chunk and nowhere else. What are its `tf` in that chunk and its `df`?
<details><summary>💡 Hint</summary>tf looks inside one chunk; df counts chunks. (Section 2)</details>

**3.** In the worked example (N = 4), score the question *"model port"* for all four chunks. Which one wins? Is that what you'd expect?
<details><summary>💡 Hint</summary>idf(model) = 0.288, idf(port) = 0.693. C3 contains both, once each. (Section 6)</details>

**4.** Why does adding the silly chunk C5 change the scores of C1, even though C1's text didn't change?
<details><summary>💡 Hint</summary>Which two quantities in the IDF formula depend on the whole index? (Sections 4 and 7)</details>

**5.** With log-scaled TF, how much more is a term worth if it appears 100 times rather than once? And with raw TF?
<details><summary>💡 Hint</summary>Compare 1 + ln(100) with 1 + ln(1). (Section 7)</details>

**6.** Your chunks range from 50 to 2000 characters. With plain "sum of TF × IDF" scoring, which chunks have an unfair advantage, and why?
<details><summary>💡 Hint</summary>Which chunks contain more terms, and more repetitions, just by being bigger? What does cosine normalization do about it? (Sections 8 and 10)</details>

**7.** Is IDF computed at indexing time or at search time? What does that mean for performance?
<details><summary>💡 Hint</summary>Does df depend on the question? (Section 11)</details>

---

## 📚 Further reading

- 📘 Manning, Raghavan & Schütze, *Introduction to Information Retrieval*, ch. 6 (term weighting, TF-IDF, vector space model): <https://nlp.stanford.edu/IR-book/>
- 📄 Karen Spärck Jones, *A statistical interpretation of term specificity and its application in retrieval* (1972), the paper that introduced IDF: <https://doi.org/10.1108/eb026526>

---

<div align="center">

**← Previous** [03 — Tokenization 🔤](03-tokenization.md) · [🏠 Docs index](README.md) · **Next →** [05 — BM25 🏆](05-bm25.md)

</div>
