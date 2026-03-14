/**
 * 对话找物页面 - 参考设计原型 v3
 */
const api = require('../../utils/api')
const util = require('../../utils/util')
const { normalizeMatchedItems } = require('./chat_item_view')

Page({
  data: {
    messages: [],
    inputText: '',
    sessionId: '',
    isRecording: false,
    isTyping: false,
    scrollToView: '',
    inputMode: 'text', // 'text' | 'voice'
    /** 语音识别原文（仅识别到内容后才展示块） */
    voiceResultText: '',
    showVoiceResult: false
  },

  onLoad(options) {
    this.initRecorderManager()
    this.loadOrInitSession(options)
  },

  onShow() {
    this.consumePendingQuery()
  },

  onHide() {
    this.shouldRecognizeAfterRecord = false
    this.stopRecordingSafely()
  },

  onUnload() {
    this.shouldRecognizeAfterRecord = false
    this.stopRecordingSafely()
  },

  /** 存储 key：当前家庭的聊天 session */
  getChatSessionKey() {
    const familyId = api.getFamilyId() || 'default'
    return `chatSessionId_${familyId}`
  },

  getChatSessionId() {
    return wx.getStorageSync(this.getChatSessionKey()) || ''
  },

  setChatSessionId(sessionId) {
    const key = this.getChatSessionKey()
    if (sessionId) {
      wx.setStorageSync(key, sessionId)
    } else {
      wx.removeStorageSync(key)
    }
  },

  /**
   * 加载历史或初始化：与当前用户/家庭绑定，从后端拉取历史
   */
  async loadOrInitSession(options) {
    const familyId = api.getFamilyId()
    let sessionId = familyId ? this.getChatSessionId() : ''
    if (!sessionId) {
      sessionId = util.generateUUID()
      this.setChatSessionId(sessionId)
    }

    this.setData({ sessionId })

    if (!familyId) {
      this.setData({ messages: [] })
      this.addMessage('assistant', '你好呀！我是寻物记助手 👋\n\n请先创建或加入家庭后再找我找东西～', {
        suggestions: ['创建家庭', '加入家庭']
      })
      this.setData({ scrollToView: 'msg-0' })
      if (options.q) {
        this.setData({ inputText: decodeURIComponent(options.q) })
        setTimeout(() => this.sendMessage(), 500)
      }
      return
    }

    try {
      const res = await api.getChatHistory(familyId, sessionId, 50)
      const list = (res && res.messages) || []
      if (list.length > 0) {
        const messages = list.map(m => {
          const matchedItems = normalizeMatchedItems(
            (m.matched_items && (Array.isArray(m.matched_items) ? m.matched_items : [])) || [],
            api.resolveStaticUrl
          )
          return {
            id: m.id,
            role: m.role,
            roleClass: m.role === 'user' ? 'user' : 'assistant',
            content: m.content || '',
            time: m.created_at ? this.formatChatTime(m.created_at) : '',
            matchedItems
          }
        })
        this.setData({ 
          messages,
          scrollToView: 'msg-' + (messages.length - 1)
        })
        this.setChatSessionId(res.session_id || sessionId)
        if (options.q) {
          this.setData({ inputText: decodeURIComponent(options.q) })
          setTimeout(() => this.sendMessage(), 300)
        }
        return
      }
    } catch (err) {
      console.error('加载聊天历史失败', err)
    }

    this.setData({ messages: [] })
    this.addMessage('assistant', '你好呀！我是寻物记助手 👋\n\n帮我找东西超简单，试试这样说：', {
      suggestions: [
        '我的护照在哪？',
        '感冒药放哪了？',
        '主卧抽屉有什么？',
        '有什么快过期了？'
      ]
    })
    this.setData({ scrollToView: 'msg-0' })

    if (options.q) {
      this.setData({ inputText: decodeURIComponent(options.q) })
      setTimeout(() => this.sendMessage(), 500)
    }
  },

  formatChatTime(createdAt) {
    if (!createdAt) return ''
    const d = new Date(createdAt)
    const now = new Date()
    const today = now.getDate() === d.getDate() && now.getMonth() === d.getMonth() && now.getFullYear() === d.getFullYear()
    if (today) {
      return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }
    const yesterday = new Date(now)
    yesterday.setDate(yesterday.getDate() - 1)
    if (d.getDate() === yesterday.getDate() && d.getMonth() === yesterday.getMonth()) {
      return '昨天 ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }
    return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }) + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  },

  /**
   * 消费首页透传的搜索词
   */
  consumePendingQuery() {
    const app = getApp()
    const pendingChatQuery = app.globalData.pendingChatQuery
    if (!pendingChatQuery) {
      return
    }

    app.globalData.pendingChatQuery = ''
    this.setData({
      inputText: pendingChatQuery
    })
    setTimeout(() => this.sendMessage(), 100)
  },

  /**
   * 初始化录音管理器
   */
  initRecorderManager() {
    if (this.recorderManager) {
      return
    }

    const recorderManager = wx.getRecorderManager()
    recorderManager.onStart(() => {
      // #region agent log
      const _t = Date.now()
      const _p = { sessionId: 'fbaaed', location: 'chat.js:recorderOnStart', message: 'recorder started', data: { step: 'recorderOnStart', ts: _t }, timestamp: _t, hypothesisId: 'H2_H4' }
      console.log('[dbg]', _p)
      api.debugLog(_p)
      fetch('http://127.0.0.1:7573/ingest/4f348d8d-d0da-4dde-8c9c-877e839fb5ef', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'fbaaed' }, body: JSON.stringify(_p) }).catch(() => {})
      // #endregion
      console.log('开始录音')
    })
    recorderManager.onStop((res) => {
      // #region agent log
      const _t = Date.now()
      const _p = { sessionId: 'fbaaed', location: 'chat.js:recorderOnStop', message: 'recorder stopped', data: { step: 'recorderOnStop', duration: res.duration, ts: _t }, timestamp: _t, hypothesisId: 'H2_H4' }
      console.log('[dbg]', _p)
      api.debugLog(_p)
      fetch('http://127.0.0.1:7573/ingest/4f348d8d-d0da-4dde-8c9c-877e839fb5ef', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'fbaaed' }, body: JSON.stringify(_p) }).catch(() => {})
      // #endregion
      this.setData({ isRecording: false })
      console.log('录音结束', res)
      const duration = (res.duration || 0) / 1000
      if (this.shouldRecognizeAfterRecord && res.tempFilePath && duration >= 0.3) {
        this.recognizeVoice(res.tempFilePath)
      } else if (this.shouldRecognizeAfterRecord && duration > 0 && duration < 0.3) {
        wx.showToast({ title: '录音太短', icon: 'none' })
      }
      this.shouldRecognizeAfterRecord = false
    })
    recorderManager.onError((err) => {
      // #region agent log
      const _t = Date.now()
      const _p = { sessionId: 'fbaaed', location: 'chat.js:recorderOnError', message: 'recorder error', data: { step: 'recorderOnError', errMsg: (err && err.errMsg) || String(err), ts: _t }, timestamp: _t, hypothesisId: 'H2' }
      console.log('[dbg]', _p)
      api.debugLog(_p)
      fetch('http://127.0.0.1:7573/ingest/4f348d8d-d0da-4dde-8c9c-877e839fb5ef', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'fbaaed' }, body: JSON.stringify(_p) }).catch(() => {})
      // #endregion
      console.error('录音失败', err)
      this.setData({ isRecording: false })
      wx.showToast({ title: '录音失败', icon: 'none' })
    })

    this.recorderManager = recorderManager
  },

  /**
   * 安全停止录音
   */
  stopRecordingSafely() {
    if (!this.data.isRecording) {
      return
    }

    this.setData({ isRecording: false })
    if (!this.recorderManager) {
      return
    }

    try {
      this.recorderManager.stop()
    } catch (err) {
      console.error('停止录音失败', err)
    }
  },

  /**
   * 点击语音按钮：切换到语音输入模式（整条变按住说话）
   */
  switchToVoiceMode() {
    this.setData({ inputMode: 'voice' })
  },

  /**
   * 点击键盘图标：切回文字输入模式
   */
  switchToTextMode() {
    this.setData({ inputMode: 'text', voiceResultText: '', showVoiceResult: false })
  },

  /**
   * 输入文字
   */
  onInput(e) {
    this.setData({ inputText: e.detail.value })
  },

  /**
   * 点击建议标签
   */
  onSuggestionTap(e) {
    const text = e.currentTarget.dataset.text
    if (text === '创建家庭' || text === '加入家庭') {
      wx.navigateTo({ url: '/pages/family/family' })
      return
    }
    this.setData({ inputText: text })
    this.sendMessage()
  },

  /**
   * 发送消息
   */
  async sendMessage() {
    const text = this.data.inputText.trim()
    if (!text) return
    
    // 添加用户消息
    this.addMessage('user', text)
    this.setData({ inputText: '', isTyping: true, scrollToView: 'typing-anchor' })
    
    try {
      const familyId = api.getFamilyId()
      if (!familyId) {
        this.setData({ isTyping: false })
        this.addMessage('assistant', '你还没有加入家庭哦，请先创建或加入一个家庭', {
          suggestions: ['创建家庭', '加入家庭']
        })
        return
      }
      
      const result = await api.chat(familyId, this.data.sessionId, text)

      if (result.session_id) {
        this.setData({ sessionId: result.session_id })
        this.setChatSessionId(result.session_id)
      }

      const replyData = {
        intent: result.intent,
        matchedItems: normalizeMatchedItems(result.matched_items || [], api.resolveStaticUrl)
      }

      this.addMessage('assistant', result.reply, replyData)
      
    } catch (err) {
      console.error('对话失败', err)
      this.addMessage('assistant', '抱歉，出了点问题，请稍后再试 😔')
    } finally {
      this.setData({ isTyping: false })
    }
  },

  /**
   * 添加消息
   */
  addMessage(role, content, extra = {}) {
    const messages = this.data.messages
    const newMsg = {
      id: util.generateUUID(),
      role,
      roleClass: role === 'user' ? 'user' : 'assistant',
      content,
      time: new Date().toLocaleTimeString(),
      ...extra
    }
    messages.push(newMsg)
    
    this.setData({ 
      messages,
      scrollToView: 'msg-' + (messages.length - 1)
    })
  },

  /**
   * 语音输入 - 开始录音
   */
  onStartRecord() {
    // #region agent log
    const _t = Date.now()
    const _payload = { sessionId: 'fbaaed', location: 'chat.js:onStartRecord', message: 'hold start', data: { step: 'onStartRecord', isRecordingBefore: this.data.isRecording, ts: _t }, timestamp: _t, hypothesisId: 'H1_H3_H5' }
    console.log('[dbg]', _payload)
    api.debugLog(_payload)
    fetch('http://127.0.0.1:7573/ingest/4f348d8d-d0da-4dde-8c9c-877e839fb5ef', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'fbaaed' }, body: JSON.stringify(_payload) }).catch(() => {})
    // #endregion
    this.initRecorderManager()
    this.shouldRecognizeAfterRecord = true
    this.setData({ isRecording: true })

    this.recorderManager.start({
      format: 'aac',
      sampleRate: 16000,
      numberOfChannels: 1,
      duration: 60000
    })
  },

  /**
   * 语音输入 - 停止录音
   */
  onStopRecord() {
    // #region agent log
    const _t = Date.now()
    const _payload = { sessionId: 'fbaaed', location: 'chat.js:onStopRecord', message: 'hold end', data: { step: 'onStopRecord', ts: _t }, timestamp: _t, hypothesisId: 'H1_H3' }
    console.log('[dbg]', _payload)
    api.debugLog(_payload)
    fetch('http://127.0.0.1:7573/ingest/4f348d8d-d0da-4dde-8c9c-877e839fb5ef', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'fbaaed' }, body: JSON.stringify(_payload) }).catch(() => {})
    // #endregion
    this.stopRecordingSafely()
  },

  /**
   * 语音输入 - 取消录音
   */
  onCancelRecord() {
    // #region agent log
    const _t = Date.now()
    const _payload = { sessionId: 'fbaaed', location: 'chat.js:onCancelRecord', message: 'hold cancel', data: { step: 'onCancelRecord', ts: _t }, timestamp: _t, hypothesisId: 'H1_H5' }
    console.log('[dbg]', _payload)
    api.debugLog(_payload)
    fetch('http://127.0.0.1:7573/ingest/4f348d8d-d0da-4dde-8c9c-877e839fb5ef', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'fbaaed' }, body: JSON.stringify(_payload) }).catch(() => {})
    // #endregion
    this.shouldRecognizeAfterRecord = false
    this.stopRecordingSafely()
  },

  /**
   * 语音识别
   */
  async recognizeVoice(filePath) {
    try {
      wx.showLoading({ title: '识别中...' })
      const result = await api.uploadVoice(filePath)
      wx.hideLoading()

      const text = (result && result.text && String(result.text).trim()) || ''
      if (text) {
        this.setData({ inputText: text, voiceResultText: text, showVoiceResult: true })
        this.sendMessage()
      } else {
        wx.showToast({ title: '无法识别出文字', icon: 'none' })
      }
    } catch (err) {
      wx.hideLoading()
      console.error('语音识别失败', err)
      const msg = (err && err.message) || '识别失败'
      wx.showToast({ title: msg, icon: 'none' })
    }
  },

  /**
   * 点击物品
   */
  onItemClick(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({ url: `/pages/detail/detail?id=${id}` })
  },

  /**
   * 点击操作按钮
   */
  onActionClick(e) {
    const { type } = e.currentTarget.dataset
    
    switch (type) {
      case 'primary':
      case 'navigate':
        wx.showToast({ title: '导航功能开发中', icon: 'none' })
        break
      case 'photo':
        wx.showToast({ title: '查看照片功能开发中', icon: 'none' })
        break
      case 'tts':
        this.playTTS()
        break
      case '创建家庭':
      case '加入家庭':
        wx.navigateTo({ url: '/pages/family/family' })
        break
    }
  },

  /**
   * 语音播报
   */
  async playTTS() {
    const lastMsg = this.data.messages[this.data.messages.length - 1]
    if (!lastMsg || lastMsg.role !== 'assistant') return
    
    try {
      wx.showLoading({ title: '合成中...' })
      const result = await api.textToSpeech(lastMsg.content)
      wx.hideLoading()
      
      // 播放语音
      const innerAudioContext = wx.createInnerAudioContext()
      innerAudioContext.src = result.audio_url
      innerAudioContext.play()
    } catch (err) {
      wx.hideLoading()
      console.error('TTS 失败', err)
      wx.showToast({ title: '播报失败', icon: 'none' })
    }
  },

  /**
   * 从当前会话消息中提取压缩总结行，格式：物品名：位置
   */
  buildSummaryLines() {
    const messages = this.data.messages || []
    const uniqueMap = new Map()

    messages.forEach((msg) => {
      const matchedItems = Array.isArray(msg.matchedItems) ? msg.matchedItems : []
      matchedItems.forEach((item) => {
        const name = item && item.name ? String(item.name).trim() : ''
        const location = item && item.location ? String(item.location).trim() : ''
        if (!name || !location) {
          return
        }
        const itemId = item && item.id ? String(item.id) : ''
        const key = itemId || `${name}__${location}`
        if (!uniqueMap.has(key)) {
          uniqueMap.set(key, `${name}：${location}`)
        }
      })
    })

    return Array.from(uniqueMap.values())
  },

  /**
   * 压缩总结：提取当前会话中的物品与位置，成功后清空历史并展示结果
   */
  async onSummarize() {
    const familyId = api.getFamilyId()
    const sessionId = this.data.sessionId
    if (!familyId) {
      wx.showToast({ title: '请先加入家庭', icon: 'none' })
      return
    }
    if (!sessionId) {
      wx.showToast({ title: '暂无会话', icon: 'none' })
      return
    }

    const summaryLines = this.buildSummaryLines()
    if (summaryLines.length === 0) {
      wx.showToast({ title: '暂无可压缩结果', icon: 'none' })
      return
    }

    wx.showLoading({ title: '总结中...' })
    try {
      await api.clearChatHistory(familyId, sessionId)
      wx.hideLoading()

      const newSessionId = util.generateUUID()
      this.setChatSessionId(newSessionId)
      this.setData({
        messages: [],
        sessionId: newSessionId,
        scrollToView: ''
      })
      this.addMessage('assistant', summaryLines.join('\n'))
      wx.showToast({ title: '总结成功', icon: 'success' })
    } catch (err) {
      wx.hideLoading()
      console.error('压缩总结失败', err)
      const msg = (err && err.message) || (err && err.detail) || '总结失败，请稍后重试'
      wx.showToast({ title: msg, icon: 'none' })
    }
  },

  /**
   * 清空对话
   */
  onClear() {
    wx.showModal({
      title: '确认清空',
      content: '确定要清空对话记录吗？本地与服务器记录都会清空。',
      success: async (res) => {
        if (!res.confirm) return
        const familyId = api.getFamilyId()
        const oldSessionId = this.data.sessionId
        if (familyId && oldSessionId) {
          try {
            await api.clearChatHistory(familyId, oldSessionId)
          } catch (e) {
            console.error('清空服务器记录失败', e)
          }
        }
        const newSessionId = util.generateUUID()
        this.setChatSessionId(newSessionId)
        this.setData({ messages: [], sessionId: newSessionId })
        this.addMessage('assistant', '对话已清空，有什么我可以帮你的？', {
          suggestions: [
            '我的护照在哪？',
            '感冒药放哪了？',
            '主卧抽屉有什么？',
            '有什么快过期了？'
          ]
        })
      }
    })
  },

  /**
   * 分享
   */
  onShareAppMessage() {
    return {
      title: '寻物记 - 帮你找东西',
      path: '/pages/index/index'
    }
  }
})