<template>
  <div class="tool-output">
    <div v-if="!isJson" class="raw-content">
      <pre class="whitespace-pre-wrap break-words text-sm font-mono">{{ content }}</pre>
    </div>

    <div v-else>
      <div v-if="!isCollapsible">
        <div class="content-render"><component :is="renderedContent" /></div>
      </div>

      <div v-else class="my-2">
        <button @click="isExpanded = !isExpanded" class="toggle-btn">
          <span :style="{display: 'inline-block', transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)'}">▶</span>
          <span class="font-semibold">{{ displayName }}结果</span>
          <span class="hint text-xs">{{ isExpanded ? '点击收起' : '点击展开' }}</span>
        </button>
        <div v-if="isExpanded" class="ml-4 border-l pl-3"><component :is="renderedContent" /></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  content: { type: String, required: true },
  toolName: { type: String, default: 'unknown_tool' },
  isCollapsible: { type: Boolean, default: true }
})

const isExpanded = ref(false)

// 工具名映射
const TOOL_NAME_MAP = {
  search_internet: '网络搜索',
  search_knowledge_base: '知识库搜索',
  unknown_tool: '工具'
}

const displayName = TOOL_NAME_MAP[props.toolName] || props.toolName

let parsed = null
const isJson = ref(true)
try {
  parsed = JSON.parse(props.content)
} catch (e) {
  isJson.value = false
}

import { h } from 'vue'

const renderArray = (arr) => {
  return {
    render() {
      return h('div', { class: 'space-y-3' }, arr.map((item, index) => {
        const children = []
        if (item.title) children.push(h('h4', { class: 'font-semibold text-yellow-100 mb-2 flex items-start gap-2' }, [h('span', { class: 'text-yellow-400' }, `#${index+1}`), h('span', item.title)]))
        if (item.snippet || item.body) children.push(h('p', { class: 'text-sm text-gray-300 mb-2 leading-relaxed' }, item.snippet || item.body))
        if (item.link || item.href) children.push(h('a', { href: item.link || item.href, target: '_blank', rel: 'noopener noreferrer', class: 'text-xs text-blue-400 hover:text-blue-300 underline flex items-center gap-1 mt-2' }, [`🔗`, ' ', item.link || item.href]))
        Object.entries(item).forEach(([key, value]) => {
          if (['title','snippet','body','link','href'].includes(key)) return
          if (value === null || value === undefined || value === '') return
          children.push(h('div', { class: 'text-xs text-gray-400 mt-1' }, [h('span', { class: 'font-semibold' }, `${key}: `), String(value)]))
        })
        return h('div', { key: index, class: 'bg-gray-800/50 rounded-lg p-3 border border-gray-700/50' }, children)
      }))
    }
  }
}

const renderObject = (obj) => {
  return {
    render() {
      return h('div', { class: 'bg-gray-800/50 rounded-lg p-3 border border-gray-700/50' }, Object.entries(obj).map(([key, value]) => h('div', { key, class: 'mb-2 last:mb-0' }, [h('span', { class: 'font-semibold text-yellow-300 text-sm' }, `${key}: `), h('span', { class: 'text-gray-300 text-sm' }, typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value))])))
    }
  }
}

const renderPrimitive = (val) => {
  return {
    render() { return h('div', { class: 'whitespace-pre-wrap break-words text-sm' }, String(val)) }
  }
}

const renderedContent = computed(() => {
  if (!isJson.value) return renderPrimitive(props.content)
  if (Array.isArray(parsed)) return renderArray(parsed)
  if (typeof parsed === 'object' && parsed !== null) return renderObject(parsed)
  return renderPrimitive(parsed)
})

// expose displayName/isJson for template binding
// (displayName is a plain string, isJson is a ref)
</script>

<style scoped>
.toggle-btn { display:flex; gap:8px; align-items:center; color:#d69e2e; background:none; border:0; cursor:pointer; }
.ml-4 { margin-left: 1rem }
.border-l { border-left: 2px solid rgba(0,0,0,0.08) }
.pl-3 { padding-left: .75rem }
</style>
