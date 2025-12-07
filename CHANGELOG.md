# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
- PPT/PDF image OCR and parsing improvements
  - Added `Hybrid-PPT-Extractor` combining `unstructured`, `python-pptx`, and PaddleOCR for robust content extraction.
  - Ensures `PIL.Image` converted to `numpy.ndarray` (BGR) before passing to PaddleOCR; fallback to temporary files if `cv2` missing.
  - Added function-signature check before passing `cls` to PaddleOCR to avoid unexpected keyword errors.
  - Implemented OCR singleton initialization to avoid `PDX has already been initialized` errors.
  - Embeddings upload now uses batched requests with retries to avoid `413 Request Entity Too Large` errors.

- Updated documentation: `README.md`, `DEPLOYMENT.md`, optimization logs.
  
- 依赖冲突修复：已移除 `peft`，`reranker` 使用 transformers 原生实现，避免依赖冲突。
- 检索与精排升级：Milvus topk=200 → reranker topk=50 → 返回 5 条。
- BGE 语义切片：采用 BGEChunker 按句子+token 切片，提升召回质量。
- 向量化上传分批与重试，提升稳定性并避免 413 错误。

