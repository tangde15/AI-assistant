def context_aware_split(text, max_len=350, overlap=60):
    """
    聪明的句子切片：按句号/换行优先切，再保证长度 <= max_len
    与 BGE 完全兼容，不依赖任何复杂库
    """
    import re

    # 按句子切
    sentences = re.split(r'(?<=[。！？.!?])\s*', text)

    chunks = []
    current = ""

    for s in sentences:
        if len(current) + len(s) <= max_len:
            current += s
        else:
            if current:
                chunks.append(current)
            current = s

    if current:
        chunks.append(current)

    # 加入 overlap
    final = []
    for i, chk in enumerate(chunks):
        if i == 0:
            final.append(chk)
        else:
            overlap_text = chunks[i-1][-overlap:]
            final.append(overlap_text + chk)

    return final
