<template>
  <div :class="['markdown-content', className]" v-html="html"></div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  content: { type: String, required: true },
  className: { type: String, default: '' }
})

const html = ref('')

// 尝试使用 markdown-it + rehype-like highlighting，如果不可用则降级为简单的换行与转义
async function renderMarkdown(text) {
  if (!text) {
    html.value = ''
    return
  }

  // 简单转义
  const escapeHtml = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

  try {
    const mdModule = await import(/* @vite-ignore */ 'markdown-it')
    const hljsModule = await import(/* @vite-ignore */ 'highlight.js')
    const MarkdownIt = mdModule.default || mdModule
    const hljs = hljsModule.default || hljsModule
    const md = new MarkdownIt({ html: true, linkify: true, highlight: function (str, lang) {
      if (lang && hljs.getLanguage(lang)) {
        try { return '<pre class="hljs"><code>' + hljs.highlight(str, { language: lang }).value + '</code></pre>' } catch (err) {}
      }
      return '<pre class="hljs"><code>' + escapeHtml(str) + '</code></pre>'
    }})
    html.value = md.render(text)
    return
  } catch (e) {
    // fallback
  }

  // fallback simple renderer: paragraphs and inline code
  const simple = escapeHtml(text)
    .replace(/```([\s\S]*?)```/g, (m, p1) => `<pre class="hljs"><code>${escapeHtml(p1)}</code></pre>`)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n\n+/g, '</p><p>')
  html.value = `<p>${simple}</p>`
}

watch(() => props.content, (v) => { renderMarkdown(v) }, { immediate: true })

onMounted(() => { renderMarkdown(props.content) })
</script>

<style scoped>
.markdown-content p { margin: 0 0 8px 0 }
.markdown-content pre { background: #0f1724; color: #e6eef8; padding: 12px; border-radius: 6px; overflow:auto }
.markdown-content code { background:#f3f4f6; padding: 2px 6px; border-radius:4px }
</style>
