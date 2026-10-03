<div align="center">

# 🤖 08 — Augment and generate with Qwen

**From retrieved chunks to a grounded answer, with a small local model**

`📚 Concepts` · `⏱️ ~25 min read` · `🎯 Prerequisite: 00 — What is RAG · 07 — Evaluation`

</div>

---

> [!IMPORTANT]
> **TL;DR** — Retrieval found the right chunks. Now two stages turn them into an answer:
> - 📎 **Augment**: build a **prompt** that puts the retrieved text, the question and instructions in front of the model, within its **token budget**;
> - ✍️ **Generate**: let **Qwen/Qwen3-0.6B** write the answer, with sensible **decoding settings** and the right **thinking mode**.
>
> The goal is an answer that is **coherent**, **grounded** in the sources (no major hallucination) and **on point**. The model is small, so the **prompt strategy** carries a lot of the weight, and the subject grades exactly that. 🎯

---

## 📑 Contents

1. [🗺️ Where we are in the pipeline](#️-1-where-we-are-in-the-pipeline)
2. [🧠 How an LLM produces text](#-2-how-an-llm-produces-text)
3. [🪙 Tokens and the context window](#-3-tokens-and-the-context-window)
4. [💬 Chat templates and roles](#-4-chat-templates-and-roles)
5. [📎 Building the prompt (augment)](#-5-building-the-prompt-augment)
6. [⚓ Grounding vs hallucination](#-6-grounding-vs-hallucination)
7. [💭 Qwen3's thinking mode](#-7-qwen3s-thinking-mode)
8. [🎲 Decoding: how the next token is chosen](#-8-decoding-how-the-next-token-is-chosen)
9. [🐢 Running on a CPU](#-9-running-on-a-cpu)
10. [🧾 From model output to JSON](#-10-from-model-output-to-json)
11. [🚫 Common misconceptions](#-11-common-misconceptions)
12. [✅ Check your understanding](#-12-check-your-understanding)

---

## 🗺️ 1. Where we are in the pipeline

```text
search_dataset ──► StudentSearchResults JSON ──► answer_dataset ──► StudentSearchResultsAndAnswer JSON
                   (question + retrieved_sources)    │               (… + answer)
                                                     │
                                    for each question:
                                    1. read the text at each source address   📍
                                    2. build a prompt                          📎
                                    3. generate with Qwen                      ✍️
                                    4. clean the output, store the answer      🧾
```

| Command | Input | Output |
|---|---|---|
| `answer <query> --k <int>` | One question | Its answer, using the retrieved context |
| `answer_dataset` | A `StudentSearchResults` JSON | A `StudentSearchResultsAndAnswer` JSON |

> [!NOTE]
> 🧾 The search results contain **addresses**, not text (doc 01). Step 1 needs the chunk text: from your index if you stored it, or by re-reading files (doc 06, Section 7).

---

## 🧠 2. How an LLM produces text

A language model does one thing, over and over: **given all the text so far, predict the next token**. 🔁

```text
input:   "The default port is"
model:   " 8000"   (most likely next token)
input:   "The default port is 8000"
model:   "."
...
```

| Consequence | Why it matters for RAG |
|---|---|
| 🎭 It always produces **plausible** text | Plausible ≠ true: without the right context, it confidently invents (doc 00) |
| 👀 It only "knows" its weights **plus what's in the input** | The prompt is your only way to give it the facts |
| ✍️ Every word of the prompt influences the output | Wording, order and instructions really matter |

### 🐣 Qwen3-0.6B in numbers

| | |
|---|---|
| Parameters | **0.6 billion** (0.44 B excluding embeddings) |
| Layers | 28 |
| Context length | **32,768 tokens** |
| Special feature | **Thinking** and **non-thinking** modes (Section 7) |

> [!WARNING]
> 🐣 0.6 B is **tiny** for an LLM. Expect it to struggle with multi-step reasoning, long inputs and ambiguous instructions. The subject knows this: answers are judged on being coherent and **mostly** grounded, "even if partially incomplete due to base-model limitations". Your job is to set it up to succeed. 🎯

---

## 🪙 3. Tokens and the context window

### 🧩 LLM tokens

The model doesn't read characters or words, it reads **tokens**: pieces of text from a fixed vocabulary learned during training (doc 03, Section 10, these are **not** your search terms).

```text
"gpu_memory_utilization"  →  something like  "gpu" · "_memory" · "_util" · "ization"
```

| Text type | Rough size |
|---|---|
| English prose | ~4 characters per token |
| Code, identifiers, symbols | Often fewer characters per token (more tokens for the same length) |

> [!TIP]
> 📏 These are rules of thumb. To know a prompt's real size, count it with **Qwen's own tokenizer**, which comes with the model.

### 🪟 The context window

The **context window** is the maximum number of tokens the model can handle at once: **input + output together**.

```text
|◄──────────────────────── 32,768 tokens ────────────────────────►|
|  instructions  |  retrieved chunks  |  question  |  ✍️ answer…   |
```

### 💸 The budget in practice

| Item | Rough size |
|---|---|
| 5 chunks × up to 2000 chars | up to ~10,000 chars ≈ **2,500–3,500 tokens** |
| Instructions + question | a few hundred tokens |
| Answer | a few hundred tokens (thousands with thinking, Section 7) |

That fits in 32k easily. So why care about the budget at all?

| Reason | Explanation |
|---|---|
| 🐢 **Speed** | On a CPU, time grows with prompt length. More context = slower answers (Section 9) |
| 😵 **Attention** | Small models handle long inputs poorly. Information in the **middle** of a long prompt tends to be used less ("lost in the middle") |
| 🗑️ **Noise** | Irrelevant chunks can pull the answer off topic |
| 💭 **Thinking tokens** | Thinking mode can produce thousands of tokens before answering |

> [!IMPORTANT]
> ⚖️ "Fits in the window" is not the same as "good for the model". The subject asks you to pass the context **within its token budget**. Choose how much context to give on purpose, and be able to explain the choice. 🎤

---

## 💬 4. Chat templates and roles

Chat models like Qwen3 are trained on **conversations** with roles:

| Role | Who | Typical content |
|---|---|---|
| 🛠️ **system** | The developer (you) | Rules and behaviour: "Answer only from the context…" |
| 🙋 **user** | The person asking | The question (and here, often the context too) |
| 🤖 **assistant** | The model | The answer |

The model doesn't see these as separate fields: a **chat template** turns the messages into one string with special markers. For Qwen it looks roughly like this:

```text
<|im_start|>system
You are a helpful assistant that answers questions about the vLLM codebase…<|im_end|>
<|im_start|>user
Context: …
Question: …<|im_end|>
<|im_start|>assistant
```

The model then continues after the last line, writing the assistant's turn.

> [!WARNING]
> 🧩 Don't build these markers by hand. The tokenizer that comes with the model knows its own template (in the Transformers library, `apply_chat_template`). Using the model's template is what makes it behave like the chat model it was trained to be. A prompt without it may get rambling or odd output.

---

## 📎 5. Building the prompt (augment)

This is where **your design** lives. Here are the decisions to make, and the trade-offs, not the answer. 🧭

### 🧱 The building blocks

| Block | Purpose | Questions to ask yourself |
|---|---|---|
| 📜 **Instructions** | Tell the model its job and its rules | Answer only from the context? What if the context doesn't contain the answer? How long should the answer be? |
| 📚 **Context** | The retrieved chunk texts | How many chunks? In what order? With what labels? |
| ❓ **Question** | What to answer | Placed before or after the context? |
| 🧾 **Format hints** | Shape of the answer | Plain text? Mention sources? |

### 📚 Presenting the context

```text
[Source 1: data/raw/vllm-0.10.1/docs/serving/openai_compatible_server.md]
…chunk text…

[Source 2: data/raw/vllm-0.10.1/vllm/entrypoints/openai/api_server.py]
…chunk text…
```

| Choice | Trade-off |
|---|---|
| 🏷️ **Labels** (file path, number) | Help the model tell sources apart, and let the answer refer to them. Cost a few tokens |
| 🔢 **How many chunks** | More = more chance the answer is there, but more noise and slower. The `k` used for answering doesn't have to equal the `k` used for search output |
| 🔀 **Order** | Best-ranked first? Last (closest to the question)? Small models are sensitive to position |
| ✂️ **Truncation** | If over budget: drop low-ranked chunks? Shorten long ones? |
| 👯 **Duplicates** | Overlapping chunks (doc 02) repeat text and waste budget |

### 📍 Where to put the question

| Layout | Idea |
|---|---|
| Context → Question | The question is the last thing read, right before the answer starts |
| Question → Context → Question | Repeats the question so the model knows what to look for while reading |

> [!TIP]
> 🔬 Prompting is **empirical**. Pick 10 questions, try two prompt variants, read the answers side by side. Keep notes: the README's "Design decisions" and "Challenges faced" sections are the natural place for what you learned. 📝

---

## ⚓ 6. Grounding vs hallucination

| | ⚓ Grounded | 🎭 Hallucinated |
|---|---|---|
| **Definition** | Every claim is supported by the provided context | Claims come from the model's memory or imagination |
| **Example** (doc 00) | *"The default port is 8000; use `--port` to change it."* | *"The default port is 5000; set `VLLM_PORT_DEFAULT`."* (invented) |

### 🛡️ What helps

| Technique | Idea |
|---|---|
| 📜 Explicit rule | "Use **only** the information in the context." |
| 🙋 An escape hatch | "If the context doesn't contain the answer, say so." Without it, the model feels pushed to answer anyway |
| 🏷️ Source labels | The model can tie statements to specific sources |
| ✂️ Less noise | Fewer, more relevant chunks leave less room to wander |
| 🎯 Focused question placement | Keeps the model on the question actually asked |

> [!WARNING]
> 🐣 With 0.6 B parameters, instructions are followed **imperfectly**. The model may still mix in outside knowledge, repeat itself, or ignore "say if you don't know". You can't eliminate this, only reduce it, and **show that you tried** with a deliberate strategy.

> [!NOTE]
> 🔗 Grounding starts with **retrieval** (doc 07). If the right source isn't in the context, no prompt can make the answer both grounded and correct. The best fix for many bad answers is better recall. 📈

---

## 💭 7. Qwen3's thinking mode

Qwen3 models can **think before answering**: they first write a reasoning trace, then the answer.

```text
<think>
The user asks about the default port. Source 1 says "The default port is 8000".
Source 2 shows port: int = 8000. Both agree…
</think>
The default port is 8000. You can change it with --port.
```

### 🎚️ Switching it on and off

| Method | How |
|---|---|
| 🔘 **Hard switch** | A flag when applying the chat template (`enable_thinking`, `True` by default) |
| 💬 **Soft switch** | With thinking enabled, adding `/think` or `/no_think` to a user message changes behaviour turn by turn |

### ⚖️ Trade-offs

| | 💭 Thinking | ⚡ Non-thinking |
|---|---|---|
| Reasoning | Can help on multi-step questions | Direct answer |
| Tokens produced | Many more (the trace can be long) | Just the answer |
| Speed on CPU | 🐢 Much slower | ⚡ Faster |
| Risk | Rambling or very long traces | Shallower answers |
| Output handling | You **must** remove the `<think>…</think>` part before storing the answer | Nothing to remove |

> [!CAUTION]
> 🧹 The reasoning trace is **not** the answer. If it ends up in your `answer` field, the JSON is cluttered and the evaluator reads the model's scratchpad instead of an answer. Whatever mode you choose, make sure only the final answer is stored. And if generation stops before `</think>` (token limit reached), decide what your program does.

> [!TIP]
> 🧮 With hundreds of questions in `answer_dataset` on a CPU, thinking mode can multiply total run time. Measure both modes on a handful of questions, compare quality **and** time, then decide and document why. ⏱️

---

## 🎲 8. Decoding: how the next token is chosen

At each step the model outputs a **probability** for every possible next token. **Decoding** decides which one to pick.

| Strategy | Idea | Effect |
|---|---|---|
| 🎯 **Greedy** | Always pick the most probable token | Deterministic, but prone to **repetition loops** |
| 🎲 **Sampling** | Pick randomly according to the probabilities | More natural, less repetitive, not deterministic |

### 🎛️ Sampling knobs

| Parameter | Controls | Lower → | Higher → |
|---|---|---|---|
| 🌡️ **temperature** | How "flat" the probabilities are | More predictable | More varied / risky |
| 🔝 **top_k** | Only consider the *k* most likely tokens | Safer | More options |
| 🥧 **top_p** | Only consider the smallest set of tokens whose probabilities add up to *p* | Safer | More options |
| 📏 **max new tokens** | Hard limit on output length | Shorter, may cut answers | Longer, slower |

### 📋 What Qwen recommends (model card)

| Mode | temperature | top_p | top_k |
|---|:-:|:-:|:-:|
| 💭 Thinking | 0.6 | 0.95 | 20 |
| ⚡ Non-thinking | 0.7 | 0.8 | 20 |

> [!WARNING]
> 🔁 The model card explicitly warns **against greedy decoding in thinking mode**: it can degrade quality and cause **endless repetition**. A `max new tokens` limit is your safety net against runaway generations.

> [!NOTE]
> 🎲 Sampling means two runs can give different answers. Fixing a **random seed** makes runs reproducible, which is handy when comparing prompts or demonstrating at the defense. 🎤

---

## 🐢 9. Running on a CPU

The bonuses mention a **CPU-only campus machine**, and many laptops have no usable GPU. A 0.6 B model runs on CPU, but slowly compared with retrieval:

| Factor | Effect |
|---|---|
| 💾 Model weights | Downloaded on first use (they must **not** be committed to the repo). Roughly 1–2.5 GB of memory depending on precision |
| ⏳ Loading | Takes seconds: load **once** per command, not per question (same rule as the index, doc 06) |
| 📏 Prompt length | Longer prompts take longer to process |
| ✍️ Output length | Each generated token costs a full model step: long answers and thinking traces are expensive |

> [!TIP]
> 📊 `tqdm` over the questions in `answer_dataset` shows seconds per question. Multiply by the dataset size before launching a full run. If it says three hours, reconsider context size, max tokens and thinking mode first. ⏱️

---

## 🧾 10. From model output to JSON

Each answered question becomes a `MinimalAnswer`:

```text
question_id        ← copied from the search results (never regenerated!)
question           ← copied
retrieved_sources  ← copied (the addresses)
answer             ← the cleaned model output
```

| Concern | Why |
|---|---|
| 🆔 Keep `question_id` | Matching answers to questions depends on it (doc 07, Section 7) |
| 🧹 Clean the output | Remove the thinking trace, stray template markers, leading/trailing whitespace |
| 🫥 Empty or failed generation | Decide what to store: an empty string? A clear message? Never a crash |
| 🛡️ Robustness | Missing search-results file, malformed JSON, a source address pointing to a missing file, `k = 0`… all must be handled gracefully (doc 10) |

---

## 🚫 11. Common misconceptions

| ❌ Myth | ✅ Reality |
|---|---|
| "The model will use the context automatically." | It **may** use it. Instructions, layout and noise level make a big difference, especially for a small model. |
| "It fits in 32k tokens, so include everything." | Speed, attention and noise all get worse with long prompts. |
| "Telling the model 'don't hallucinate' solves it." | It reduces it. A 0.6 B model still slips, and missing context can't be fixed by instructions. |
| "Thinking mode is always better." | It's slower, much more verbose, and its trace must be stripped. Measure. |
| "Greedy decoding is the safe, deterministic choice." | For Qwen3 in thinking mode it's explicitly discouraged: repetition loops. Use a seed for reproducibility instead. |
| "LLM tokens = my BM25 terms." | Different tokenizers, different purposes (doc 03, Section 10). |
| "The answer quality is graded by the moulinette." | The moulinette grades retrieval. Answers are judged by your evaluator, along with your prompt strategy. |

---

## ✅ 12. Check your understanding

Try first, then open the hints. 🧩

**1.** Five retrieved chunks of 2000 characters each: roughly how many tokens is that? Does it fit Qwen3-0.6B's context window? Give one reason to still use fewer chunks.
<details><summary>💡 Hint</summary>~4 characters per token for prose, fewer for code. Then think about speed, attention and noise. (Section 3)</details>

**2.** What does the chat template do, and why shouldn't you write the `<|im_start|>` markers yourself?
<details><summary>💡 Hint</summary>The model was trained on text in a very specific format. Who knows that format exactly? (Section 4)</details>

**3.** Your prompt says "Answer the question using the context." The context doesn't contain the answer, and the model invents one. What would you change in the prompt?
<details><summary>💡 Hint</summary>Does the model have a permitted way out when it can't answer? (Section 6)</details>

**4.** Your stored answers start with a long paragraph of the model "talking to itself". What happened, and what are your two options?
<details><summary>💡 Hint</summary>Which mode was active, and how is the trace delimited? (Section 7)</details>

**5.** In thinking mode with greedy decoding, some answers repeat the same sentence until the token limit. Why, and what do the model authors recommend?
<details><summary>💡 Hint</summary>Look at the decoding table and the model card's warning. (Section 8)</details>

**6.** `answer_dataset` takes 40 seconds per question on your laptop. List three settings you could change to speed it up, and what each might cost in quality.
<details><summary>💡 Hint</summary>Context size, max new tokens, thinking mode… and is the model loaded only once? (Sections 3, 7, 8 and 9)</details>

**7.** An answer is fluent and correct, but the retrieved sources don't contain that information. Is it "grounded"? Why does that matter here?
<details><summary>💡 Hint</summary>Where did the facts come from? What do the grading criteria say? (Section 6)</details>

---

## 📚 Further reading

- 🤗 Qwen3-0.6B model card (specs, thinking mode, recommended settings): <https://huggingface.co/Qwen/Qwen3-0.6B>
- 💬 Hugging Face Transformers, *Chat templates*: <https://huggingface.co/docs/transformers/main/en/chat_templating>
- 🎲 Hugging Face Transformers, *Generation strategies* (greedy, sampling, top-k, top-p): <https://huggingface.co/docs/transformers/generation_strategies>
- 📄 Liu et al., *Lost in the Middle: How Language Models Use Long Contexts* (2023): <https://arxiv.org/abs/2307.03172>

---

<div align="center">

**← Previous** [07 — Evaluation: recall@k and IoU 🎯](07-evaluation.md) · [🏠 Docs index](README.md) · **Next →** [09 — Pydantic in practice 🧾](09-pydantic.md)

</div>
