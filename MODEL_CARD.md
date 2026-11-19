# MathTok-0.1 Model Card

### Model Details
- **Model Name:** MathTok-0.1
- **Organization:** Open Thought Research
- **Repository:** https://github.com/openthoughtresearchofficial/MathTok
- **Release Target:** OpenThoughtResearch/MathTok-0.1
- **Model Type:** Hybrid symbolic/structural mathematical tokenizer and representation pipeline.
- **Date:** 19 November 2026
- **License:** MIT

### Intended Use
- Mathematical expression tokenization and normalization.
- Canonicalized structural representation via typed ASTs.
- Tokenizer comparison and research benchmarking against subword baselines (GPT-2, T5, BERT, SentencePiece).
- Preprocessing and structural attention mask metadata generation for downstream mathematical language models.
- Research into mathematical representation, syntax distribution shift, and token efficiency.

### Out-of-Scope Use
- Treating token embeddings or similarity as a formal theorem prover.
- Unverified symbolic equivalence decisions without execution of computer algebra verification.
- Assuming zero-shot compatibility with frozen language models trained solely on natural text/LaTeX.
- High-stakes scientific, engineering, or financial calculations without independent symbolic checking.

### Architecture
MathTok decomposes mathematical tokenization into a 7-layer modular pipeline:
1. **Canonicalizer Engine (`canonicalizer.py`)**: SymPy-backed algebraic normalization (`simplify`, `expand`), subtractions to addition of negations, divisions to reciprocal multiplications.
2. **Hybrid Mathematical Lexer (`lexer.py`)**: Multi-stage segmentation of text and math spans with balanced expression expansion.
3. **AST Generator (`ast_generator.py`)**: SymPy expression tree conversion into typed `ASTNode` hierarchies with recursion limits (`max_depth=20`).
4. **Operator Semantic Registry (`operator_registry.py`)**: Mathematical domain, arity, precedence, associativity, and inverse mappings.
5. **Structural Serializer (`serializer.py`)**: DFS preorder flattening with scope boundary delimiters (`[SCOPE_OPEN]`, `[SCOPE_CLOSE]`).
6. **Structural Metadata Generator (`metadata.py`)**: Per-token hierarchical depth, positional keys, and binary attention masks (`parent`, `children`, `sibling`, `subtree`).
7. **Two-Tier Vocabulary (`vocabulary.py`)**: Fixed deterministic integer IDs for mathematical operators, variables, and constants, integrated with Hugging Face BPE for natural language text spans.

### Empirical Evaluation & Benchmarks
The verified release artifacts report:
1. **45-Expression Baseline Benchmark (`tokenizer_comparison_results.json`)**:
   - MathTok: **4.69 tokens/expr** (vs 14.61 GPT-2, 23.01 SentencePiece) — **67.9% reduction vs GPT-2**, **79.6% vs SentencePiece**.
   - Structural Compression Ratio (SCR): **2.0792** (vs 0.7903 GPT-2, 0.5976 SentencePiece).
   - Canonical Consistency Score (CCS): **0.9714** Jaccard overlap on algebraic rewrites (vs 0.3964 GPT-2).
   - Token Length Stability (TS): **0.9800** (vs 0.8241 GPT-2).
2. **611-Expression Scale Benchmark (`all_results_4way_optimized.json`)**:
   - MathTok Mean Tokens: **44.94** | Mean SCR: **1.9552**
   - GPT-2 BPE Mean Tokens: 53.03 | Mean SCR: 0.9625
   - T5 SentencePiece Mean Tokens: 58.00 | Mean SCR: 0.8647
   - BERT WordPiece Mean Tokens: 61.91 | Mean SCR: 0.9715
3. **Representation Equivalence Learning (`classifier_equivalence_results.json`)**:
   - Evaluated using TF-IDF + Logistic Regression on strict leakage-isolated rewrite families.
   - Raw Text TF-IDF: Accuracy 0.5909, F1 0.7429, ROC-AUC 0.7350 (206 features).
   - MathTok AST TF-IDF: Accuracy 0.5909, F1 0.7429, **ROC-AUC 0.8889** (**160 features**, -22.3% smaller space, +15.39 pts ROC-AUC).
4. **Frozen LLM Computation Verification (`computation_validation_summary.json`)**:
   - Evaluated on Qwen2.5-0.5B-Instruct across 18 benchmark problems.
   - Native Qwen Baseline: 16.67% overall accuracy.
   - Pure MathTok AST Prompt: 5.56% overall accuracy.
   - Hybrid Prompt (Text + AST hints): 16.67% overall accuracy.
   - Finding: Prefix AST representations induce an out-of-distribution syntactic distribution shift in frozen LLMs, highlighting the necessity of structural pretraining.

### Limitations
- Parser coverage depends on supported LaTeX/ASCII syntax and SymPy grammar capabilities.
- Canonicalization normalizes expressions algebraically (e.g. expanding products or ordering terms), which changes surface syntax.
- Compact structural token sequences do not autonomously transfer to frozen models without fine-tuning or structural pretraining.
- Structural Compression Ratio (SCR) is a defined evaluation metric incorporating structural density, depth, and canonical bonuses.

