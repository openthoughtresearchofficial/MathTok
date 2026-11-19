# MathTok-v-1.0

**A Hybrid Canonicalized AST-Based Tokenization Framework for Mathematical Language Modeling**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Pytest](https://img.shields.io/badge/tests-118%20passed-success.svg)](tests/)

Developed by **Open Thought Research**  
Organization Repository: [OpenThoughtResearch / MathTok](https://github.com/openthoughtresearchofficial/MathTok)

---

## Overview

MathTok is a structure-aware mathematical tokenization and representation framework. Standard natural language processing tokenizers (Byte-Pair Encoding, WordPiece, SentencePiece Unigram) treat mathematical expressions as flat character sequences. This induces two major failure modes:
1. **Structural Fragmentation**: Splitting mathematical variables, Greek symbols, and composite operations into arbitrary character subwords.
2. **Semantic Divergence**: Producing completely disjoint token sequences for algebraically identical expressions (e.g., $x + 2$ vs. $2 + x$).

MathTok constructs a typed Abstract Syntax Tree (AST) from mathematical expressions (LaTeX or ASCII), canonicalizes algebraic structures symbolically with SymPy, flattens the tree via Depth-First Search (DFS) preorder traversal, and emits per-token structural attention metadata.

```text
Raw Mixed Text / Mathematical Expression
                  │
                  ▼
        Canonicalizer Engine          (SymPy: simplify, expand, normalize)
                  │
                  ▼
       Hybrid Mathematical Lexer      (split TEXT spans / MATH spans)
                  │
                  ▼
            AST Generator             (SymPy tree → typed ASTNode tree)
                  │
                  ▼
   Operator-Aware Semantic Registry   (arity, precedence, domain, role)
                  │
                  ▼
        Structural Serializer         (DFS preorder → flat token stream)
                  │
                  ▼
     Structural Attention Metadata    (depth, parent, sibling, subtree masks)
                  │
                  ▼
       Two-Tier Vocabulary + BPE      (fixed math vocab + HF BPE for text)
                  │
                  ▼
      Unified Structured Token Stream
```

---

## Model Architecture & 7-Layer Pipeline

1. **Layer 1: Canonicalization Engine (`canonicalizer.py`)** — Normalizes algebraic equivalences with SymPy (`simplify()` and `expand()`), resolving subtractions $a - b \to \text{Add}(a, \text{Mul}(-1, b))$ and divisions $a / b \to \text{Mul}(a, \text{Pow}(b, -1))$. Features an LRU cache (512 entries) and a 5.0s timeout to prevent parser hangs.
2. **Layer 2: Hybrid Mathematical Lexer (`lexer.py`)** — Segments raw text into alternating TEXT and MATH spans using unambiguous LaTeX delimiters (`$...$`, `$$...$$`, `\(...\)`, `\[...\]`) and balanced-boundary ASCII heuristics.
3. **Layer 3: AST Generator (`ast_generator.py`)** — Recursively translates SymPy trees into typed `ASTNode` hierarchies (Latin variables `VAR_X`, Greek `VAR_THETA`, integers `CONST_3`, binary fractions `FRAC`), guarded by `max_depth=20` recursion truncation.
4. **Layer 4: Operator Semantic Registry (`operator_registry.py`)** — Rich metadata repository storing `arity`, `precedence`, `associativity`, `semantic_role`, `domain`, commutativity, and explicit inverse pairs (`INVERSE_PAIRS`).
5. **Layer 5: Structural Serializer (`serializer.py`)** — Emits DFS preorder serialized tokens with multi-operand scope markers (`[SCOPE_OPEN]`, `[SCOPE_CLOSE]`) and subtree deduplication hashing.
6. **Layer 6: Structural Attention Metadata (`metadata.py`)** — Generates per-token tree context (`depth`, `node_id`, `parent_id`, `tree_position_key`) and synthesizes binary attention mask matrices (`parent`, `children`, `sibling`, `subtree`).
7. **Layer 7: Two-Tier Vocabulary (`vocabulary.py`)** — Reserves deterministic integer IDs for mathematical operators, variables, and constants, integrated with Hugging Face BPE for natural language text spans.
8. **Lossless Verification (`validator.py`)** — Includes `RoundTripValidator` to reconstruct SymPy expressions directly from serialized token metadata and formally verify symbolic equivalence.

---

## Quick Start & CLI Demo

### Installation

```bash
# Clone the repository
git clone https://github.com/openthoughtresearchofficial/MathTok.git
cd MathTok

# Install in editable mode
pip install -e .
```

### CLI Tokenization

```bash
# Tokenize a LaTeX expression
python -m mathtok.pipeline "$\sin(x^2) + 3x$"

# Output:
# Tokens      : 12
# S-expression: (OP_ADD (OP_MUL CONST_3 VAR_X) (FUNC_SIN (OP_POW VAR_X CONST_2)))
# Tokens: ['[MATH_START]', 'OP_ADD', 'OP_MUL', 'CONST_3', 'VAR_X', 'FUNC_SIN', '[SCOPE_OPEN]', 'OP_POW', 'VAR_X', 'CONST_2', '[SCOPE_CLOSE]', '[MATH_END]']
```

---

## Python API & Hugging Face Compatibility

```python
from mathtok import MathTokPipeline
from mathtok.vocabulary import MathTokHFTokenizer

# Initialize pipeline
pipeline = MathTokPipeline()

# 1. Encode mixed text + math
out = pipeline.encode("The derivative of $\\sin(x^2)$ is $2x\\cos(x^2)$.")
print("Tokens:", out.tokens)
print("S-expression:", out.sexp)
print("Input IDs:", out.input_ids)

# 2. Access structural attention metadata
for meta in out.metadata:
    print(meta.token, meta.depth, meta.tree_position_key, meta.children_ids)

# 3. Export and reload via Hugging Face interface
hf_tok = pipeline.get_hf_tokenizer()
hf_tok.save_pretrained("./mathtok-tokenizer")

# Drop-in reload
loaded_tok = MathTokHFTokenizer.from_pretrained("./mathtok-tokenizer")
encoded = loaded_tok("sin(x^2) + 3*x", return_tensors="pt")
print("Batch tensor shape:", encoded["input_ids"].shape)
```

---

## Empirical Benchmark Results

<p align="center">
  <img src="benchmark_table.png" alt="MathTok Empirical Benchmark Card" width="100%" />
</p>

### 1. 45-Expression Baseline Comparison (`evaluation/results/tokenizer_comparison_results.json`)

Evaluated independently at the tokenization level across 45 canonical benchmark expressions spanning 9 mathematical disciplines (Algebra, Arithmetic, Calculus, Equations, LaTeX/ASCII Equivalence, Logarithms/Exponentials, Matrices, Probability, Trigonometry):

| Tokenizer Architecture | Mean Tokens | SCR (Level 1) | Semantic Density (L2) | Structural Efficiency (L3) | Canonical Consistency (CCS) | Token Stability (TS) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **MathTok (Ours)** | **4.69** | **2.0792** | **0.5640** | 0.1909 | **0.9714** | **0.9800** |
| **GPT-2 BPE** | 14.61 | 0.7903 | 0.4989 | 0.2914 | 0.3964 | 0.8241 |
| **BERT WordPiece** | 15.63 | 0.7285 | 0.4606 | 0.2679 | 0.5857 | 0.8186 |
| **SentencePiece Unigram** | 23.01 | 0.5976 | 0.3659 | 0.2317 | 0.5390 | 0.7703 |
| **Character-Level Baseline** | 24.42 | 0.6081 | 0.3728 | 0.2354 | 0.5921 | 0.8083 |

- **Token Compression:** MathTok achieves **67.9% fewer tokens** than GPT-2 BPE and **79.6% fewer tokens** than SentencePiece Unigram.
- **Canonical Consistency:** **0.9714** Jaccard overlap on algebraically equivalent rewrites ($x + 2 \equiv 2 + x$) vs. 0.3964 for GPT-2 BPE.
- **Syntactic Stability:** **0.9800** length invariance across rewrites vs. 0.8241 for GPT-2.

### 2. 611-Expression Scale Benchmark (`evaluation/results/all_results_4way_optimized.json`)

Evaluating across 611 diverse mathematical expressions from the unified dataset:

| Model Setup | Mean Tokens | Token Reduction vs Baseline | Mean SCR (L1) | Relative SCR Advantage |
| :--- | :---: | :---: | :---: | :---: |
| **MathTok** | **44.94** | **Reference (0.0%)** | **1.9552** | **State of the Art** |
| **GPT-2 BPE** | 53.03 | -15.3% | 0.9625 | +2.03x MathTok Lead |
| **T5 (SentencePiece)** | 58.00 | -22.5% | 0.8647 | +2.26x MathTok Lead |
| **BERT WordPiece** | 61.91 | -27.4% | 0.9715 | +2.01x MathTok Lead |

### 3. Representation Learning: Equivalence Classification (`evaluation/results/classifier_equivalence_results.json`)

Evaluated with TF-IDF + Logistic Regression on strict leakage-isolated rewrite families (Train: `distributive`, `double_angle_trig`, `log_rules`, `pythagorean_trig`, `rational_cancellation`; Test: `binomial_sq`, `commutativity`, `diff_squares`, `exponent_rules`):

| Representation Scheme | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Feature Space |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Raw Text TF-IDF** | 0.5909 | 0.5909 | 1.0000 | 0.7429 | 0.7350 | 206 features |
| **MathTok AST TF-IDF** | 0.5909 | 0.5909 | 1.0000 | 0.7429 | **0.8889** | **160 features (-22.3%)** |

---

## Important Research Limitations

> [!WARNING]
> **Tokenization Efficiency $\neq$ Pretrained LLM Computation Accuracy in Frozen Models**  
> While MathTok demonstrates state-of-the-art token compression and canonical representation, feeding prefix AST token streams into **frozen** pretrained autoregressive language models causes an out-of-distribution syntactic distribution shift:
>
> | Setup (Qwen2.5-0.5B-Instruct, 18 tasks) | Overall Accuracy | Exact Accuracy |
> | :--- | :---: | :---: |
> | **Native Baseline (Standard text/LaTeX)** | **16.67%** | 11.11% |
> | **Pure MathTok AST Prompt** | 5.56% | 5.56% |
> | **Hybrid Prompt (Text + AST hints)** | **16.67%** | **16.67%** |
>
> Language models pretrained on web text and LaTeX cannot autonomously exploit AST prefix representations without structural pretraining or fine-tuning. Structural pretraining remains the subject of future research (`MathTok-Encoder`).

---

## Reproducing Benchmarks

```bash
# Run unit tests (118 passed)
pytest tests/ -v

# Run 45-benchmark tokenizer comparison
python -m evaluation.tokenizer_comparison

# Run 611-expression 4-way evaluation & regenerate plot
python -m evaluation.evaluate_4way_optimized

# Run expression equivalence classification experiment
python -m evaluation.classifier_evaluation

# Run full comparison suite
python -m evaluation.comparison

# Generate Word Document (.docx) report
python -m evaluation.generate_project_report_doc
```

---

## Repository Structure

```text
math_token/
├── mathtok/
│   ├── canonicalizer.py         # Layer 1: Canonicalization Engine
│   ├── lexer.py                 # Layer 2: Hybrid Mathematical Lexer
│   ├── ast_generator.py         # Layer 3: AST Generator
│   ├── operator_registry.py     # Layer 4: Semantic Operator Registry
│   ├── serializer.py            # Layer 5: Structural Serializer
│   ├── metadata.py              # Layer 6: Structural Attention Metadata
│   ├── vocabulary.py            # Layer 7: Two-Tier Vocabulary & HF Wrapper
│   ├── validator.py             # RoundTripValidator for symbolic reconstruction
│   ├── optimizer.py             # TokenOptimizer for representation candidates
│   ├── math_ir.py               # Intermediate Representation (IR)
│   └── pipeline.py              # End-to-end pipeline orchestrator
├── mathtok-tokenizer/           # Exported Hugging Face tokenizer package
│   ├── mathtok_vocab.json       # Deterministic mathematical vocabulary
│   ├── tokenizer_config.json    # Tokenizer configuration
│   └── special_tokens_map.json  # Special token mappings
├── evaluation/
│   ├── tokenizer_comparison.py  # 45-benchmark tokenizer comparison
│   ├── evaluate_4way_optimized.py # 611-expression 4-way evaluation & plotting
│   ├── classifier_evaluation.py # Expression equivalence classification
│   ├── comparison.py            # Comparison framework & metric calculations
│   ├── math_verifier.py         # Symbolic equivalence verification engine
│   ├── model_computation_eval.py# Frozen LLM downstream evaluation
│   ├── generate_project_report_doc.py # Project report Word doc generator
│   ├── datasets/                # Unified benchmark datasets
│   └── results/                 # Verified benchmark JSON & plot artifacts
├── tests/                       # Pytest test suite (118 tests)
├── benchmark_table.png          # Official empirical benchmark card
├── MODEL_CARD.md                # Official model card and specification
├── CITATION.cff                 # Citation metadata
└── PROJECT_REPORT.md            # Comprehensive project report
```

---

## Citation

```bibtex
@software{openthoughtresearch_mathtok_2026,
  author  = {Open Thought Research},
  title   = {MathTok: A Hybrid Canonicalized AST-Based Tokenization Framework for Mathematical Language Modeling},
  year    = {2026},
  version = {0.1.0},
  url     = {https://github.com/openthoughtresearchofficial/MathTok}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
