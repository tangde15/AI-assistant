<template>
  <div class="chat-app">
    <!-- 左侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <button class="new-chat-btn" @click="startNewSession">
          <span class="icon">+</span>
          <span>开启新对话</span>
        </button>
      </div>

      <nav class="history-nav">
        <div class="history-section">
          <h3 class="history-title">今天</h3>
          <div
            v-for="item in todayHistory.filter(s => s.preview && s.preview !== '无标题')"
            :key="item.session_id"
            :class="['history-item', { active: item.session_id === sessionId }]"
            @click="loadSession(item.session_id)"
          >
            <span class="history-text">{{ truncateText(item.preview, 20) }}</span>
            <button
              class="delete-btn"
              @click.stop="deleteSession(item.session_id)"
            >
              ×
            </button>
          </div>
        </div>

          <div class="history-section" v-if="olderHistory.filter(s => s.preview && s.preview !== '无标题').length > 0">
          <h3 class="history-title">更早</h3>
          <div
            v-for="item in olderHistory.filter(s => s.preview && s.preview !== '无标题')"
            :key="item.session_id"
            :class="['history-item', { active: item.session_id === sessionId }]"
            @click="loadSession(item.session_id)"
          >
            <span class="history-text">{{ truncateText(item.preview, 20) }}</span>
          </div>
        </div>
      </nav>
    </aside>

    <!-- 右侧主聊天区 -->
    <main class="main-content">
      <div class="chat-container">
        <div class="messages-container" ref="messagesContainer">
          <div v-if="!sessionId" class="welcome-section">
            <h1>欢迎使用 EasyRAG</h1>
            <p>开启一段新对话或选择历史记录继续</p>
          </div>

          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['message', `msg-${msg.role}`]"
          >
            <div class="message-inner">
              <div class="message-avatar">
                {{ msg.role === 'user' ? '你' : msg.role === 'ai' ? 'AI' : msg.role === 'tool' ? '工具' : '系统' }}
              </div>
              <div class="message-body">
                <div class="message-content"><MarkdownMessage :content="msg.content" /></div>
                <!-- 按工具块显示检索结果（按顺序：知识库或网络） -->
                <div v-if="msg.role === 'ai' && msg.toolBlocks && msg.toolBlocks.filter(b => b.parsed && b.parsed.items && b.parsed.items.length > 0).length > 0" class="web-results">
                  <div v-for="(block, bidx) in msg.toolBlocks.filter(b => b.parsed && b.parsed.items && b.parsed.items.length > 0)" :key="block.id || bidx" class="tool-block">
                    <div class="tool-block-header">
                      <span class="tool-block-label">{{ block.parsed.source === 'knowledge' ? '知识库检索结果' : (block.parsed.source === 'web' ? '网络搜索结果' : '检索结果') }}</span>
                    </div>
                    <div class="tool-block-items">
                      <div 
                        v-for="(result, idx) in block.parsed.items.slice(0,5)" 
                        :key="idx"
                        :class="['web-result-card', (block.parsed.source === 'web' ? 'web' : ''), { expanded: expandedResults[index + '-' + bidx + '-' + idx] }]"
                      >
                        <div class="web-result-header" @click="toggleResultExpanded(index + '-' + bidx, idx)">
                          <div class="web-result-left">
                            <div v-if="block.parsed.source === 'web'" class="result-number">#{{ idx + 1 }}</div>
                            <h4 class="web-result-title">{{ result.title || result.name || result.heading || '无标题' }}</h4>
                            <div class="web-result-meta">
                              <span class="web-result-source-pill">{{ result.source || block.parsed.source || '网页' }}</span>
                              <a v-if="result.link || result.url || result.href" :href="result.link || result.url || result.href" class="web-result-link" target="_blank" rel="noopener">访问网页</a>
                            </div>
                          </div>
                          <div class="web-result-right">
                            <span class="chevron" :class="{ open: !!expandedResults[index + '-' + bidx + '-' + idx] }">▾</span>
                          </div>
                        </div>
                        <!-- 默认显示简短摘要（若存在），展开后显示完整 snippet (这里目前同一内容，可后续扩展)-->
                        <div class="web-result-content" v-if="result.snippet">
                          <p class="snippet" :class="{ clipped: !expandedResults[index + '-' + bidx + '-' + idx] }">
                            {{ result.snippet }}
                          </p>
                          <div class="result-link-line">
                            <a v-if="result.link || result.url || result.href" :href="result.link || result.url || result.href" target="_blank" rel="noopener" class="web-result-link-inline">
                              {{ (result.domain || (result.link || result.url || result.href)) }}
                            </a>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <!-- 参考资料（来自工具调用） -->
                <div v-if="msg.role === 'ai' && msg.references && msg.references.filter(r => r && (r.title || r.link)).length > 0" class="references">
                  <div class="references-title">参考资料</div>
                    <ol class="references-list">
                    <li v-for="(ref, ridx) in msg.references.filter(r => r && (r.title || r.link))" :key="ridx">
                      <span class="ref-badge">{{ ridx + 1 }}</span>
                      <a v-if="getRefHref(ref)" :href="getRefHref(ref)" target="_blank" rel="noopener">{{ ref.title || getRefHref(ref) }}</a>
                      <span v-else class="ref-text">{{ ref.title }}</span>
                    </li>
                  </ol>
                </div>
              </div>
            </div>
          </div>

          <!-- 工具执行中的提示 -->
          <div v-if="currentToolExecuting" class="tool-executing-tip">
            <span class="spinner"></span>
            <span>{{ currentToolExecuting }}</span>
          </div>
        </div>

        <div class="input-container">
          <div class="input-area">
            <input
              v-model="inputQuestion"
              type="text"
              placeholder="输入你的问题，按回车或点发送"
              @keydown.enter="sendQuestion"
              :disabled="isLoading"
              class="input-field"
            />
            <button
              @click="sendQuestion"
              :disabled="isLoading"
              class="send-btn"
            >
              {{ isLoading ? '...' : '发送' }}
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, nextTick, computed } from 'vue'
import MarkdownMessage from './MarkdownMessage.vue'
import ToolOutput from './ToolOutput.vue'

const backend = 'http://127.0.0.1:8000'
const messages = ref([])
const inputQuestion = ref('')
const sessionId = ref(null)
const isLoading = ref(false)
const messagesContainer = ref(null)
const expandedResults = ref({})
const currentToolExecuting = ref('')
const tempToolBlocks = ref([])
let aiMessageIndex = -1
let allSessions = ref([])

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const addMessage = async (role, content, meta = '', webResults = null) => {
  messages.value.push({
    role,
    content,
    meta: meta || (role === 'user' ? '你' : role === 'ai' ? 'assistant' : 'system'),
    webResults: webResults || null,
    toolBlocks: [],
    references: []
  })
  await scrollToBottom()
}

// 计算今天和更早的历史记录
const todayHistory = computed(() => {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  return allSessions.value.filter(s => {
    const sessionDate = new Date(s.timestamp * 1000)
    const sessionDay = new Date(
      sessionDate.getFullYear(),
      sessionDate.getMonth(),
      sessionDate.getDate()
    )
    return sessionDay.getTime() === today.getTime()
  })
})

const olderHistory = computed(() => {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  return allSessions.value.filter(s => {
    const sessionDate = new Date(s.timestamp * 1000)
    const sessionDay = new Date(
      sessionDate.getFullYear(),
      sessionDate.getMonth(),
      sessionDate.getDate()
    )
    return sessionDay.getTime() < today.getTime()
  })
})

const truncateText = (text, len) => {
  if (!text) return '新对话'
  return text.length > len ? text.substring(0, len) + '...' : text
}

const startNewSession = async () => {
  messages.value = []
  sessionId.value = null
  aiMessageIndex = -1
  inputQuestion.value = ''
  currentToolExecuting.value = ''
  expandedResults.value = {}
}

const loadSession = async (sid) => {
  if (sid === sessionId.value) return
  sessionId.value = sid
  messages.value = []
  aiMessageIndex = -1
  expandedResults.value = {}
  currentToolExecuting.value = ''

  try {
    const resp = await fetch(`${backend}/api/conversations/get`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sid })
    })
    if (resp.ok) {
      const data = await resp.json()
      for (const conv of data.conversations || []) {
        await addMessage('user', conv.user_message, '你')
        await addMessage('ai', conv.ai_message, 'assistant')
      }
    }
  } catch (err) {
    console.error('加载会话失败:', err)
  }
}

const deleteSession = async (sid) => {
  allSessions.value = allSessions.value.filter(s => s.session_id !== sid)
  if (sessionId.value === sid) {
    await startNewSession()
  }
}

const toggleResultExpanded = (msgIdx, resultIdx) => {
  const key = `${msgIdx}-${resultIdx}`
  expandedResults.value[key] = !expandedResults.value[key]
}

const getRefHref = (ref) => {
  if (!ref) return ''
  if (ref.link) return ref.link
  if (ref.url) return ref.url
  // 尝试从 title 中提取 URL
  const urlRegex = /(https?:\/\/[^\s]+)/
  const m = (ref.title || '').match(urlRegex)
  if (m) return m[0]
  return ''
}

// helper: escape regexp special chars
function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

const parseWebResults = (toolContent) => {
  // Try to robustly parse toolContent into { source: 'web'|'knowledge', items: [{title,link,snippet}] }
  const decodeUnicodeEscapes = (text) => {
    if (!text || typeof text !== 'string') return text
    // 处理 \uXXXX 序列
    try {
      return text.replace(/\\u[0-9a-fA-F]{4}/g, (m) => {
        try {
          const code = parseInt(m.slice(2), 16)
          return String.fromCharCode(code)
        } catch (e) { return m }
      })
    } catch (e) { return text }
  }
  const tryParseJson = (text) => {
    if (!text) return null
    try {
      const parsed = JSON.parse(text)
      return parsed
    } catch (e) {
      // 有时返回的字符串是 JSON 编码的字符串（双重编码），尝试再解析一次
      try {
        const stripped = text.trim()
        if ((stripped.startsWith('"') && stripped.endsWith('"')) || (stripped.startsWith("'") && stripped.endsWith("'"))) {
          const unquoted = stripped.slice(1, -1)
          try {
            return JSON.parse(unquoted)
          } catch (e2) {
            // continue
          }
        }
      } catch (e2) {
        // continue
      }
    }
    return null
  }

  const extractLinksAsItems = (text) => {
    const items = []
    if (!text) return items
    // 找出 URL
    const urlRegex = /(https?:\/\/[^\s"'<>]+)/g
    const found = Array.from(new Set((text.match(urlRegex) || [])))
    for (const u of found.slice(0, 6)) {
      items.push({ title: u, link: u, snippet: '' })
    }
    // 如果未找到 URL，则把文本首段做为 snippet
    if (items.length === 0) {
      const snippet = (text || '').replace(/\s+/g, ' ').trim().slice(0, 400)
      if (snippet) items.push({ title: snippet.substring(0, 60) + (snippet.length > 60 ? '...' : ''), link: '', snippet })
    }
    return items
  }

  try {
    // 第一轮：直接 parse
    let data = tryParseJson(toolContent)
    // 第二轮：如果解析出的仍然是字符串，尝试再次解析
    if (typeof data === 'string') {
      const data2 = tryParseJson(data)
      if (data2 !== null) data = data2
    }

    if (data) {
      // 如果已经是我们期望的结构
      if ((data.source === 'knowledge' || data.source === 'web') && Array.isArray(data.items)) {
        // 规范化 items（保证 title/link/snippet 字段）
        const items = data.items.slice(0, 8).map(it => {
          if (typeof it === 'string') return { title: it, link: '', snippet: it }
          return {
            title: decodeUnicodeEscapes(it.title || it.name || it.heading || (it.link || it.url ? '' : null)),
            link: it.link || it.url || it.href || '',
            snippet: decodeUnicodeEscapes(it.snippet || it.body || it.description || it.content || '')
          }
        }).filter(i => i.title || i.link || i.snippet)
        return { source: data.source, items }
      }

      // 如果解析为数组或常见的 results 字段
      if (Array.isArray(data)) {
        const items = data.slice(0, 8).map(it => (typeof it === 'string') ? { title: it, link: '', snippet: it } : {
          title: decodeUnicodeEscapes(it.title || it.name || it.heading || ''),
          link: it.link || it.url || it.href || '',
          snippet: decodeUnicodeEscapes(it.snippet || it.body || it.description || '')
        }).filter(i => i.title || i.link || i.snippet)
        return { source: 'web', items }
      }

      if (data.results && Array.isArray(data.results)) {
        const items = data.results.slice(0, 8).map(it => ({
          title: decodeUnicodeEscapes(it.title || it.name || ''),
          link: it.link || it.url || it.href || '',
          snippet: decodeUnicodeEscapes(it.snippet || it.body || it.description || '')
        })).filter(i => i.title || i.link || i.snippet)
        return { source: 'web', items }
      }
    }
  } catch (e) {
    console.log('parseWebResults unexpected error', e)
  }

  // 最后兜底：从纯文本中提取 URL 或摘要
  try {
    const items = extractLinksAsItems(toolContent).map(it => ({
      title: decodeUnicodeEscapes(it.title),
      link: it.link,
      snippet: decodeUnicodeEscapes(it.snippet)
    }))
    if (items.length > 0) return { source: 'web', items }
  } catch (e) {
    // ignore
  }

  return null
}

const loadAllSessions = async () => {
  try {
    const resp = await fetch(`${backend}/api/conversations/all`)
    if (resp.ok) {
      const data = await resp.json()
      const sessionMap = new Map()
      for (const conv of data.conversations || []) {
        if (!sessionMap.has(conv.session_id)) {
          sessionMap.set(conv.session_id, {
            session_id: conv.session_id,
            preview: conv.user_message || '无标题',
            timestamp: conv.timestamp || 0
          })
        }
      }
      allSessions.value = Array.from(sessionMap.values()).sort(
        (a, b) => b.timestamp - a.timestamp
      )
    }
  } catch (err) {
    console.error('加载会话历史失败:', err)
  }
}

const sendQuestion = async () => {
  const question = inputQuestion.value.trim()
  if (!question || isLoading.value) return

  isLoading.value = true
  inputQuestion.value = ''
  aiMessageIndex = -1
  currentToolExecuting.value = ''
  expandedResults.value = {}

  await addMessage('user', question, '你')

  try {
    const payload = sessionId.value 
      ? { question, session_id: sessionId.value }
      : { question }

    const response = await fetch(`${backend}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let aiContent = ''
    let webResults = null

    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()

      for (const line of lines) {
        if (!line.trim()) continue

        try {
          const obj = JSON.parse(line)

          if (obj.type === 'session') {
            sessionId.value = obj.content
            await loadAllSessions()
          } else if (obj.type === 'ai') {
            aiContent += obj.content

            // 过滤掉模型可能插入的“网络搜索结果”“知识库搜索结果”等提示行
            aiContent = aiContent.replace(/网络搜索结果\s*/g, '')
            aiContent = aiContent.replace(/知识库搜索结果\s*/g, '')
            aiContent = aiContent.replace(/让我搜索\s*/g, '')

            if (aiMessageIndex === -1) {
              await addMessage('ai', aiContent, 'assistant', webResults)
              aiMessageIndex = messages.value.length - 1
              // 如果在生成 AI 消息之前有临时工具块，附加到该消息
              if (tempToolBlocks.value.length > 0) {
                messages.value[aiMessageIndex].toolBlocks = tempToolBlocks.value.slice()
                tempToolBlocks.value = []
              }
            } else {
              messages.value[aiMessageIndex].content = aiContent
              await scrollToBottom()
            }
          } else if (obj.type === 'tool_start') {
            // 工具开始执行，设置提示
            const tn = obj.tool_name || ''
            if (tn.includes('search_knowledge') || tn === 'search_knowledge_base') {
              currentToolExecuting.value = '知识库检索中...'
            } else if (tn.includes('search_internet') || tn === 'search_internet') {
              currentToolExecuting.value = '联网搜索中...'
            } else if (tn.includes('smart_search') || tn === 'smart_search') {
              currentToolExecuting.value = '智能搜索中...'
            } else {
              currentToolExecuting.value = '正在检索...'
            }
            // 新建临时工具块，等待 tool 内容填充
            try {
              const block = {
                id: Date.now() + Math.random().toString(16).slice(2),
                tool_name: tn,
                type: tn.includes('search_knowledge') || tn === 'search_knowledge_base' ? 'knowledge' : (tn.includes('search_internet') || tn === 'search_internet' ? 'web' : 'other'),
                status: 'running',
                parsed: null,
                raw: null
              }
              tempToolBlocks.value.push(block)
            } catch (e) {
              console.warn('create temp tool block failed', e)
            }
          } else if (obj.type === 'tool') {
            // 处理工具调用
            const toolName = obj.tool_name || 'unknown'
            
            // 显示工具执行提示
            if (toolName.includes('search_knowledge') || toolName === 'search_knowledge_base') {
              currentToolExecuting.value = '知识库检索中...'
            } else if (toolName.includes('search_internet') || toolName === 'search_internet') {
              currentToolExecuting.value = '联网搜索中...'
            } else if (toolName.includes('smart_search') || toolName === 'smart_search') {
              currentToolExecuting.value = '智能搜索中...'
            }

            // 尝试解析网页结果或知识库结果
            const parsed = parseWebResults(obj.content)
            if (parsed) {
              // parsed now is { source, items }
              webResults = parsed.items || null
              // 更新当前 AI 消息的网页结果并把解析结果放入最后一个工具块
              if (aiMessageIndex >= 0) {
                let current = messages.value[aiMessageIndex].content || ''
                const items = parsed.items || []
                for (const r of items) {
                  if (!r || !r.title) continue
                  const t = (r.title || '').trim()
                  if (!t) continue
                  const regex = new RegExp('(^|\\n)\\s*' + escapeRegExp(t) + '\\s*(\\n|$)', 'g')
                  current = current.replace(regex, '\\n')
                }
                messages.value[aiMessageIndex].content = current.trim()
                messages.value[aiMessageIndex].webResults = webResults
                if (!messages.value[aiMessageIndex].toolBlocks) messages.value[aiMessageIndex].toolBlocks = []
                // attach to existing toolBlocks if any, else temp
                if (messages.value[aiMessageIndex].toolBlocks.length > 0) {
                  messages.value[aiMessageIndex].toolBlocks[messages.value[aiMessageIndex].toolBlocks.length - 1].parsed = parsed
                } else if (tempToolBlocks.value.length > 0) {
                  tempToolBlocks.value[tempToolBlocks.value.length - 1].parsed = parsed
                }
              } else {
                if (tempToolBlocks.value.length > 0) {
                  tempToolBlocks.value[tempToolBlocks.value.length - 1].parsed = parsed
                }
              }
            } else {
              // 未能解析为网页结果，保存原始内容到当前临时工具块
              if (tempToolBlocks.value.length > 0) {
                tempToolBlocks.value[tempToolBlocks.value.length - 1].raw = obj.content
              } else if (aiMessageIndex >= 0) {
                if (!messages.value[aiMessageIndex].toolBlocks) messages.value[aiMessageIndex].toolBlocks = []
                messages.value[aiMessageIndex].toolBlocks.push({ id: Date.now(), tool_name: toolName, type: 'other', status: 'done', raw: obj.content, parsed: null })
              }
            }

            await scrollToBottom()
          } else if (obj.type === 'tool_done') {
            // 工具执行完成，清除提示
            currentToolExecuting.value = ''
            // 标记临时工具块完成并把它们分配给当前 ai 消息（如果存在）
            try {
              for (const b of tempToolBlocks.value) {
                b.status = 'done'
              }
              if (tempToolBlocks.value.length > 0) {
                if (aiMessageIndex >= 0) {
                  if (!messages.value[aiMessageIndex].toolBlocks) messages.value[aiMessageIndex].toolBlocks = []
                  messages.value[aiMessageIndex].toolBlocks = messages.value[aiMessageIndex].toolBlocks.concat(tempToolBlocks.value)
                }
                tempToolBlocks.value = []
              }
            } catch (e) {
              console.warn('attach tempToolBlocks failed', e)
            }
          }
        } catch (err) {
          console.error('Parse error:', err)
        }
      }
    }

    if (buffer.trim()) {
      try {
        const obj = JSON.parse(buffer)
        if (obj.type === 'ai') {
          aiContent += obj.content
          if (aiMessageIndex === -1) {
            await addMessage('ai', aiContent, 'assistant', webResults)
          } else {
            messages.value[aiMessageIndex].content = aiContent
            await scrollToBottom()
          }
        }
      } catch (err) {
        console.warn('Buffer parse error:', err)
      }
    }
    // 流完成后，为最后一条 AI 消息生成参考资料列表（如果存在工具块）
    try {
      if (aiMessageIndex >= 0) {
        const blocks = messages.value[aiMessageIndex].toolBlocks || []
        const refs = []
        for (const b of blocks) {
          if (b.parsed && b.parsed.items && Array.isArray(b.parsed.items)) {
            for (const item of b.parsed.items) {
              // 每个 item 期望包含 title/link/snippet/source
              refs.push({ title: item.title || item.source || '来源', link: item.link || item.url || item.href || '' })
            }
          } else if (b.raw) {
            // 从 raw 文本中尝试提取第一行作为标题
            const firstLine = (b.raw || '').split('\n').find(l => l.trim()) || ''
            refs.push({ title: firstLine || b.tool_name || '来源', link: '' })
          }
        }
        messages.value[aiMessageIndex].references = refs
      }
    } catch (e) {
      console.warn('build references failed', e)
    }

    // 不要在聊天正文中显示 raw 工具文本；同时：对 references 做去重与过滤，并尝试在 AI 文本末尾追加 [1][2] 标注（仅作后处理）
    try {
      if (aiMessageIndex >= 0) {
        // 过滤 references（仅保留有 title 或 link 的）
        const refs = (messages.value[aiMessageIndex].references || []).filter(r => r && (r.title || r.link))
        // 去重（根据 link 或 title）
        const seen = new Set()
        const uniq = []
        for (const r of refs) {
          const key = (r.link || '') + '||' + (r.title || '')
          if (!seen.has(key)) {
            seen.add(key)
            uniq.push(r)
          }
        }
        messages.value[aiMessageIndex].references = uniq

        // 尝试在 AI 文本末尾追加引用标注（仅当文本中没有类似 [1] 的标注时）
        if (uniq.length > 0) {
          const content = messages.value[aiMessageIndex].content || ''
          if (!/\[1\]/.test(content)) {
            const markers = uniq.map((_, i) => `[${i+1}]`).join('')
            messages.value[aiMessageIndex].content = content.trim() + '\n\n' + markers
          }
        }
      }
    } catch (e) {
      console.warn('post-process references failed', e)
    }

    currentToolExecuting.value = ''
  } catch (err) {
    await addMessage('system', `错误: ${err.message}`, 'error')
    currentToolExecuting.value = ''
  } finally {
    isLoading.value = false
    await loadAllSessions()
  }
}

// 初始化时加载所有会话
loadAllSessions()
</script>

<style scoped>
.chat-app {
  display: flex;
  height: 100vh;
  background: #fff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* 左侧边栏 */
.sidebar {
  width: 280px;
  background: #f7f7f8;
  border-right: 1px solid #e6e6e6;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 12px;
  border-bottom: 1px solid #e6e6e6;
}

.new-chat-btn {
  width: 100%;
  padding: 10px 12px;
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.new-chat-btn:hover {
  background: #f5f5f5;
  border-color: #999;
}

.new-chat-btn .icon {
  font-size: 16px;
  font-weight: bold;
}

.history-nav {
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;
}

.history-section {
  padding: 8px 12px;
}

.history-title {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
  padding: 0 8px;
  text-transform: uppercase;
  font-weight: 500;
}

.history-item {
  padding: 8px 12px;
  margin-bottom: 6px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: transparent;
  transition: all 0.2s;
  font-size: 13px;
  color: #333;
}

.history-item:hover {
  background: #e6e6e6;
}

.history-item.active {
  background: #e6f7ff;
  border: 1px solid #bae7ff;
}

.history-text {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.delete-btn {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 16px;
  padding: 0 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.history-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: #f5222d;
}

/* 右侧主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #999;
}

.welcome-section h1 {
  font-size: 28px;
  color: #333;
  margin-bottom: 12px;
}

.welcome-section p {
  font-size: 14px;
  color: #999;
}

.message {
  display: flex;
  margin: 0;
}

.msg-user {
  justify-content: flex-end;
}

.msg-ai,
.msg-tool,
.msg-system {
  justify-content: flex-start;
}

.message-inner {
  display: flex;
  gap: 12px;
  max-width: 70%;
}

.msg-user .message-inner {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
  flex-shrink: 0;
}

.msg-user .message-avatar {
  background: #1890ff;
  color: white;
}

.msg-ai .message-avatar {
  background: #52c41a;
  color: white;
}

.msg-tool .message-avatar {
  background: #faad14;
  color: white;
}

.msg-system .message-avatar {
  background: #d9d9d9;
  color: #666;
}

.message-body {
  display: flex;
  flex-direction: column;
}

.message-content {
  padding: 10px 14px;
  border-radius: 8px;
  word-break: break-word;
  white-space: pre-wrap;
  line-height: 1.5;
  font-size: 14px;
}

.msg-user .message-content {
  background: #1890ff;
  color: white;
}

.msg-ai .message-content {
  background: #f6f6f6;
  color: #333;
}

.msg-tool .message-content {
  background: #fffbe6;
  color: #333;
  border: 1px solid #ffe58f;
}

.msg-system .message-content {
  background: #f5f5f5;
  color: #666;
  font-size: 12px;
}

/* 网页结果卡片 */
.web-results {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.web-result-card {
  border: 1px solid #e6e6e6;
  padding: 10px;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
}
.web-result-card.expanded {
  background: #f6faff;
}
.web-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.web-result-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}
.web-result-source {
  font-size: 12px;
  color: #888;
}
.web-result-link {
  font-size: 12px;
  color: #1890ff;
  text-decoration: none;
}
.web-result-link:hover {
  text-decoration: underline;
}
.web-result-content {
  margin-top: 8px;
  font-size: 13px;
  color: #333;
}

/* compact card + chevron */
.web-result-card {
  border: 1px solid #eef0f2;
  padding: 8px 10px;
  border-radius: 8px;
  background: #fff;
  cursor: default;
  display: flex;
  flex-direction: column;
}
.web-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.web-result-left {
  display: flex;
  flex-direction: column;
}
.web-result-title {
  font-size: 14px;
  margin: 0;
  font-weight: 600;
  color: #222;
}
.web-result-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 6px;
}
.web-result-source-pill {
  font-size: 12px;
  color: #666;
  background: #f5f7fa;
  padding: 4px 8px;
  border-radius: 999px;
}
.web-result-right {
  display: flex;
  align-items: center;
}
.chevron {
  display: inline-block;
  transition: transform 0.18s ease;
  color: #999;
}
.chevron.open { transform: rotate(180deg); color: #666 }
.expand-enter-active, .expand-leave-active { transition: all 0.18s ease }
.expand-enter-from, .expand-leave-to { max-height: 0; opacity: 0 }
.expand-enter-to, .expand-leave-from { max-height: 400px; opacity: 1 }

/* web-sourced card dark style (mimic screenshot) */
.web-result-card.web {
  background: #0f1724;
  border: 1px solid rgba(255,255,255,0.06);
  color: #e6eef8;
}
.web-result-card.web .web-result-title {
  color: #fff;
}
.web-result-card.web .web-result-meta {
  margin-top: 6px;
}
.web-result-card.web .web-result-link {
  color: #9ad1ff;
}
.web-result-card.web .web-result-content {
  color: #d7e7ff;
}
.result-number {
  display: inline-block;
  font-weight: 700;
  color: #ffd57a;
  margin-right: 8px;
  font-size: 14px;
}

/* 参考资料（紧凑） */
.references {
  margin-top: 8px;
  padding: 8px;
  background: transparent;
}
.references-title { display: none }
.references-list {
  margin: 0;
  padding-left: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.references-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #444;
}
.ref-badge {
  width: 20px;
  height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
  border-radius: 50%;
  font-size: 12px;
  color: #333;
}
.references-list a { color: #1890ff; text-decoration: none }
.references-list a:hover { text-decoration: underline }
.ref-text { color: #666 }

/* 参考资料样式 */
.references {
  margin-top: 8px;
  padding: 10px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
}
.references-title {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin-bottom: 6px;
}
.references-list {
  margin: 0;
  padding-left: 20px;
  color: #555;
}
.references-list li {
  margin-bottom: 6px;
  font-size: 13px;
}
.references-list a {
  color: #1890ff;
  text-decoration: none;
}
.references-list a:hover {
  text-decoration: underline;
}

.input-container {
  padding: 16px;
  border-top: 1px solid #e6e6e6;
  background: #fff;
}

.input-area {
  display: flex;
  gap: 8px;
  max-width: 100%;
}

.input-field {
  flex: 1;
  padding: 12px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 24px;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  outline: none;
  transition: all 0.2s;
}

.input-field:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.input-field:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.send-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #1890ff;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:hover:not(:disabled) {
  background: #40a9ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}

.send-btn:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}

/* 滚动条美化 */
.history-nav::-webkit-scrollbar,
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.history-nav::-webkit-scrollbar-track,
.messages-container::-webkit-scrollbar-track {
  background: transparent;
}

.history-nav::-webkit-scrollbar-thumb,
.messages-container::-webkit-scrollbar-thumb {
  background: #d9d9d9;
  border-radius: 3px;
}

.history-nav::-webkit-scrollbar-thumb:hover,
.messages-container::-webkit-scrollbar-thumb:hover {
  background: #bfbfbf;
}

@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
  
  .message-inner {
    max-width: 100% !important;
  }
}
</style>
