<div align="center">

# 🧾 09 — Pydantic in practice

**Data models that check themselves, between every stage of the pipeline**

`📚 Concepts` · `⏱️ ~20 min read` · `🎯 Prerequisite: basic Python classes and type hints`

</div>

---

> [!IMPORTANT]
> **TL;DR** — **Pydantic** turns a class with type hints into a **validator**: when you create an object, it checks (and, if allowed, converts) every field, and raises a clear error if something is wrong. 🛡️
>
> In this project the subject **requires** pydantic for the data exchanged between stages (`MinimalSource`, `RagDataset`, `StudentSearchResults`…). Used well, it means bad data is caught **where it enters**, not three stages later as a mysteriously low recall or an invalid moulinette file. 💥

---

## 📑 Contents

1. [🤔 Why validate at all?](#-1-why-validate-at-all)
2. [🧱 Models: type hints that are enforced](#-2-models-type-hints-that-are-enforced)
3. [🔄 Coercion: lax vs strict](#-3-coercion-lax-vs-strict)
4. [🎚️ `Field`: defaults and constraints](#️-4-field-defaults-and-constraints)
5. [🔍 Validators: field-level and model-level](#-5-validators-field-level-and-model-level)
6. [⏮️⏭️ `before` vs `after`](#️️-before-vs-after)
7. [👪 Inheritance and unions](#-7-inheritance-and-unions)
8. [📥📤 JSON in, JSON out](#-8-json-in-json-out)
9. [🚧 Validating between stages](#-9-validating-between-stages)
10. [🐢 When not to use pydantic](#-10-when-not-to-use-pydantic)
11. [🚫 Common misconceptions](#-11-common-misconceptions)
12. [✅ Check your understanding](#-12-check-your-understanding)

---

## 🤔 1. Why validate at all?

Python's type hints are **promises, not checks**. At runtime, nothing stops this:

```python
class Source:
    def __init__(self, first: int, last: int) -> None:
        self.first = first
        self.last = last

s = Source("12", None)   # 😶 Python happily accepts it
```

The bug surfaces much later, somewhere unrelated (`TypeError` during a subtraction, or worse, no error and a wrong result).

With pydantic:

```python
from pydantic import BaseModel

class Source(BaseModel):
    first: int
    last: int

Source(first="12", last=None)
# 💥 ValidationError: 1 validation error for Source
#    last
#      Input should be a valid integer [type=int_type, input_value=None, ...]
```

> [!TIP]
> 🧭 The error says **which field**, **what was received** and **what was expected**. When malformed JSON is fed to your program (the subject tests this!), that's the difference between a clear message and a traceback from deep inside your search code. 🛡️

---

## 🧱 2. Models: type hints that are enforced

A model is a class inheriting from `BaseModel`, with annotated fields:

```python
from pydantic import BaseModel

class Book(BaseModel):
    title: str
    pages: int
    tags: list[str]

b = Book(title="Dune", pages=412, tags=["sci-fi"])
b.pages        # 412
```

| Feature | What you get |
|---|---|
| ✅ **Validation on creation** | Wrong or missing fields raise `ValidationError` immediately |
| 🔢 **Nested models** | A field can itself be a model, or a list of models. Validated recursively 🪆 |
| 🧾 **Serialization** | Turn the object back into a dict or JSON (Section 8) |
| 🔍 **Type-checker friendly** | `mypy` understands the fields (and pydantic has a mypy plugin for even better checks) |

### 🪆 Nesting

```python
class Library(BaseModel):
    name: str
    books: list[Book]

Library(name="Home", books=[{"title": "Dune", "pages": 412, "tags": []}])
#                            ▲ a plain dict is validated into a Book automatically
```

> [!NOTE]
> 🔗 That's exactly how the project's models fit together: `StudentSearchResults` contains a list of `MinimalSearchResults`, each containing a list of `MinimalSource`. Validating the top object validates **everything inside**.

---

## 🔄 3. Coercion: lax vs strict

By default pydantic runs in **lax mode**: it converts values when the conversion is unambiguous.

| Field type | Input | Lax mode result |
|---|---|---|
| `int` | `"12"` | ✅ `12` |
| `int` | `12.0` | ✅ `12` |
| `int` | `12.5` | ❌ error (would lose information) |
| `int` | `"twelve"` | ❌ error |
| `str` | `12` | ❌ error (numbers aren't silently turned into strings) |
| `bool` | `"true"`, `1` | ✅ `True` |

> [!TIP]
> 🎚️ **Strict mode** (per field or per model) disables these conversions: `"12"` for an `int` becomes an error. For data your own program produced, lax mode is usually fine. For data where a wrong type signals a real bug, strict can catch more. Know which one you're in. 🤔

---

## 🎚️ 4. `Field`: defaults and constraints

`Field(...)` adds information to a field: a default, constraints, metadata.

### 🧷 Defaults

```python
from pydantic import BaseModel, Field
import uuid

class Ticket(BaseModel):
    title: str
    priority: int = 3                                           # simple default
    labels: list[str] = Field(default_factory=list)             # new list each time
    ticket_id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # computed default
```

| Kind | When to use |
|---|---|
| `= value` | Immutable defaults (numbers, strings, `None`) |
| `default_factory=…` | Defaults that must be **created fresh** each time (lists, dicts, IDs, timestamps) |

> [!WARNING]
> 🆔 A `default_factory` only runs when the field is **missing** from the input. That's convenient for brand-new objects, and dangerous when you meant to **copy** a value: forget to pass `question_id` when building an output object, and you silently get a **new random ID** that matches nothing in the ground truth (doc 07, Section 7). 😱

### 📏 Constraints

| Constraint | Applies to | Meaning |
|---|---|---|
| `ge`, `gt`, `le`, `lt` | numbers | ≥, >, ≤, < |
| `min_length`, `max_length` | strings, lists | Length bounds |
| `pattern` | strings | Must match a regular expression |

```python
class Rating(BaseModel):
    stars: int = Field(ge=1, le=5)
    comment: str = Field(min_length=1, max_length=500)
```

> [!NOTE]
> 🤔 Constraints are perfect for rules that depend on **one field alone** and **never change**. A limit that's configurable at runtime (like `--max_chunk_size`) doesn't belong hard-coded in a model: check it where the configuration is known.

---

## 🔍 5. Validators: field-level and model-level

When a rule is more than a simple bound, write a **validator**: a method pydantic calls during validation.

### 🔹 Field validator: one field

```python
from pydantic import BaseModel, field_validator

class User(BaseModel):
    username: str

    @field_validator("username")
    @classmethod
    def no_spaces(cls, value: str) -> str:
        if " " in value:
            raise ValueError("username must not contain spaces")
        return value
```

### 🔷 Model validator: several fields together

```python
from typing_extensions import Self   # Python 3.10; `from typing import Self` on 3.11+
from pydantic import BaseModel, model_validator

class DateRange(BaseModel):
    start: int
    end: int

    @model_validator(mode="after")
    def check_order(self) -> Self:
        if self.end < self.start:
            raise ValueError("end must not be before start")
        return self
```

| | Field validator | Model validator |
|---|---|---|
| Sees | One field's value | The whole object (or raw input, in `before` mode) |
| Use for | Format, normalization of one field | Rules **between** fields |
| Returns | The (possibly transformed) value | The object (`after`) or the data (`before`) |

> [!TIP]
> 🧠 Raise `ValueError` (or `AssertionError`) inside a validator: pydantic wraps it into a `ValidationError` with the field location. Don't raise `ValidationError` yourself.

### 🏷️ Why `-> Self`?

The return annotation of an `after` model validator is the model's own type. Writing the class name directly fails (the class doesn't exist yet while its body is being read), `"DateRange"` in quotes works, and **`Self`** is the most precise: if a subclass inherits the validator, the type checker knows it returns the **subclass**. 👪

---

## ⏮️⏭️ 6. `before` vs `after`

Model validators (and field validators) can run at two moments:

```text
raw input (dict, JSON…) ──► ⏮️ before ──► field validation & coercion ──► ⏭️ after ──► ✅ object
```

| | ⏮️ `mode="before"` | ⏭️ `mode="after"` |
|---|---|---|
| Receives | The **raw** input, usually a `dict` (could be anything) | The **built object**, with every field already validated and typed |
| Types guaranteed? | ❌ No: values may be strings, `None`, missing… | ✅ Yes |
| Typical job | **Transform** the input: rename keys, fill legacy formats, normalize | **Check** rules across fields |
| Returns | The (modified) input data | `self` |

### 🎯 Which one?

```text
"end must be ≥ start"                  → ⏭️ after   (compare two validated ints)
"accept 'begin' as an old name for 'start'"  → ⏮️ before (reshape the dict before validation)
```

> [!IMPORTANT]
> 🧭 Rule of thumb: **checking** relationships between fields → `after`. **Reshaping** input before validation → `before`. In `before` mode, `data["start"]` might be the string `"12"`, `None`, or not there at all, so every check would have to be defensive by hand.

---

## 👪 7. Inheritance and unions

### 👪 Inheritance

Models can extend other models, adding fields:

```python
class Animal(BaseModel):
    name: str

class Dog(Animal):
    breed: str          # Dog has name + breed
```

A subclass inherits fields **and validators**. The project uses this a lot: `AnsweredQuestion` extends `UnansweredQuestion`, `MinimalAnswer` extends `MinimalSearchResults`. Any model you add for your own needs can extend an existing one the same way.

### 🔀 Unions

A field can accept one of several types:

```python
class Shelter(BaseModel):
    animals: list[Dog | Animal]
```

Given a dict, which class does pydantic pick? In pydantic v2's default **smart mode**, it tries to find the **best match** for each item, rather than blindly taking the first type that validates.

> [!WARNING]
> 🔬 Unions where one type is a **subset** of another (every `Dog` is a valid `Animal`) are exactly where surprises happen. Don't assume: load a sample and **check** with `isinstance` which class you actually got. The project's `RagDataset` has this shape (`AnsweredQuestion | UnansweredQuestion`), so it's worth five minutes of testing. 🧪

### 🧹 Extra fields

By default, keys in the input that **aren't** fields of the model are silently **ignored**. That's convenient (an answered-question dataset can be read with a model that doesn't care about `answer`), but it can also hide typos (`fist_character_index`). Model configuration can change this behaviour (`extra="forbid"` turns unknown keys into errors).

---

## 📥📤 8. JSON in, JSON out

| Direction | Method | Input → Output |
|---|---|---|
| 📥 From a dict | `Model.model_validate(data)` | dict → object (validated) |
| 📥 From a JSON string | `Model.model_validate_json(text)` | str → object (parses **and** validates) |
| 📤 To a dict | `obj.model_dump()` | object → dict |
| 📤 To a JSON string | `obj.model_dump_json(indent=2)` | object → str |

> [!TIP]
> 📥 `model_validate_json` reports **both** kinds of problems with one exception type: broken JSON syntax *and* wrong structure. One `except ValidationError` covers "malformed JSON" from the subject's list of degenerate inputs. (File-level problems, such as a missing file, are a separate exception: doc 10.) 🛡️

> [!NOTE]
> 🧾 Producing output through `model_dump_json` from a validated model guarantees the file **matches the schema** the moulinette expects. Building JSON by hand with dicts gives up that guarantee.

---

## 🚧 9. Validating between stages

Where should data be validated? At the **boundaries**, where it crosses from one part of the system to another:

```text
 📂 dataset JSON ──🚧──► search ──🚧──► 📄 search results JSON ──🚧──► answer ──🚧──► 📄 answers JSON
     (input)      load           write          (file on disk)     load          write
```

| Boundary | Risk | Value of validation |
|---|---|---|
| 📥 **Loading** a file (dataset, search results) | Could be malformed, edited by hand, from an older version | 🛡️ High: this is untrusted input |
| 📤 **Writing** an output file | A bug in your code produces bad values (over-long source, wrong index) | 🛡️ High: one bad value invalidates the whole moulinette file |
| 🔁 **Inside** a stage | Your own code talking to itself | Lower: often plain Python objects are fine |

> [!IMPORTANT]
> 🎯 The subject's phrase is *"the structures you exchange between stages"*. Pydantic is required there. It catches problems **at the border**, with a precise message, instead of letting them travel. 🚧

---

## 🐢 10. When not to use pydantic

Validation has a cost. Creating a validated object is much slower than creating a plain tuple or dict.

| Data | Count | Pydantic? |
|---|---|---|
| Questions, search results, answers | Hundreds | ✅ Yes, required |
| Chunks (addresses + text) | Tens of thousands | 🤔 Fine in general: measure if indexing is slow |
| Postings entries (term, chunk ID, tf) | Possibly millions | ⚠️ Usually plain structures (tuples, dicts, arrays) |

> [!NOTE]
> 📜 The subject says so explicitly: *"Service or orchestration classes (indexer, retriever, pipeline, etc.) do not have to be pydantic."* Pydantic is for **data at the boundaries**, not for every object in the program. ⚖️

> [!WARNING]
> ⏩ Pydantic has a `model_construct` method that builds an object **without validation**. It's fast, but it skips every check, including the ones that protect the moulinette output. If you use it, use it only for data you have already validated. 🧯

---

## 🚫 11. Common misconceptions

| ❌ Myth | ✅ Reality |
|---|---|
| "Type hints already check types at runtime." | Plain Python ignores them at runtime. Pydantic enforces them. |
| "Pydantic never changes my values." | In lax mode it **converts** (`"12"` → `12`). Use strict mode to forbid that. |
| "`before` validators are for checks." | They're mainly for **reshaping** raw input. Checks across fields belong in `after`, where types are guaranteed. |
| "Raise `ValidationError` in a validator." | Raise `ValueError`. Pydantic builds the `ValidationError`. |
| "A `default_factory` ID is harmless." | It silently creates a new ID whenever you forget to copy one. |
| "Unknown fields cause errors." | By default they're ignored, which can hide typos. |
| "Unions pick the first type that works." | Pydantic v2 uses a smart mode. Test what you actually get. |
| "Every class should be a pydantic model." | Only data exchanged between stages needs it. Heavy internal structures are better plain. |

---

## ✅ 12. Check your understanding

Try first, then open the hints. 🧩

**1.** A model has `pages: int`. What happens with `pages="300"`, `pages=300.0`, `pages=300.5` and `pages=None`, in default (lax) mode?
<details><summary>💡 Hint</summary>Pydantic converts only when no information is lost and the meaning is unambiguous. (Section 3)</details>

**2.** You need "`end` must not be before `start`". Field validator or model validator? `before` or `after`? Why?
<details><summary>💡 Hint</summary>How many fields does the rule involve? When are both guaranteed to be ints? (Sections 5 and 6)</details>

**3.** An old version of your search results JSON used the key `"sources"` instead of `"retrieved_sources"`. Which kind of validator could accept both, and in which mode?
<details><summary>💡 Hint</summary>Is this checking a rule, or reshaping the input before the fields are validated? (Section 6)</details>

**4.** Your answers file has correct answers, but your evaluator finds no matching question IDs at all. The model for answers has `question_id: str = Field(default_factory=…)`. What probably happened?
<details><summary>💡 Hint</summary>When does a default factory run? (Section 4)</details>

**5.** You load a JSON file whose objects contain a field `fist_character_index` (typo). The model loads without error, but `first_character_index` is missing... or is it? What happens, and how could you make the typo an error?
<details><summary>💡 Hint</summary>Extra keys are ignored by default; the real field is required. And there's a configuration for unknown keys. (Section 7)</details>

**6.** Why validate **before writing** the search results file, if your own code produced the data?
<details><summary>💡 Hint</summary>What does the moulinette do with a file containing one source of 2001 characters? (Section 9, and doc 07)</details>

**7.** Indexing is slow, and profiling shows most time is spent creating millions of pydantic objects for postings. What does the subject allow you to do?
<details><summary>💡 Hint</summary>Which classes does the subject say don't have to be pydantic? (Section 10)</details>

---

## 📚 Further reading

- 🧱 Pydantic docs, *Models*: <https://docs.pydantic.dev/latest/concepts/models/>
- 🎚️ Pydantic docs, *Fields*: <https://docs.pydantic.dev/latest/concepts/fields/>
- 🔍 Pydantic docs, *Validators* (`before`, `after`, `wrap`): <https://docs.pydantic.dev/latest/concepts/validators/>
- 🔀 Pydantic docs, *Unions* (smart vs left-to-right mode): <https://docs.pydantic.dev/latest/concepts/unions/>
- 🔎 Pydantic docs, *mypy plugin*: <https://docs.pydantic.dev/latest/integrations/mypy/>

---

<div align="center">

**← Previous** [08 — Augment and generate with Qwen 🤖](08-augment-and-generate.md) · [🏠 Docs index](README.md) · **Next →** [10 — A robust CLI 🛡️](10-robust-cli.md)

</div>
