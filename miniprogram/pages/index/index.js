/**
 * 首页
 */
const api = require('../../utils/api')
const util = require('../../utils/util')

Page({
  data: {
    familyName: '我的家',
    greeting: '你好',
    searchKeyword: '',
    recentItems: [],
    reminders: [],
    urgentCount: 0,
    warningCount: 0,
    loading: true
  },

  onLoad() {
    this.setData({ greeting: this.getGreeting() })
    this.checkLogin()
  },

  onShow() {
    this.setData({ greeting: this.getGreeting() })
    if (api.getFamilyId()) {
      this.loadData()
    }
  },

  /**
   * 按时段返回问候语
   */
  getGreeting() {
    const hour = new Date().getHours()
    if (hour < 12) return '早上好'
    if (hour < 18) return '下午好'
    return '晚上好'
  },

  /**
   * 点击搜索框：进入找物页，有关键词则透传
   */
  onSearchTap() {
    const keyword = (this.data.searchKeyword || '').trim()
    if (keyword) {
      getApp().globalData.pendingChatQuery = keyword
    }
    wx.switchTab({ url: '/pages/chat/chat' })
  },

  /**
   * 检查登录状态
   */
  async checkLogin() {
    const userId = api.getUserId()
    
    if (!userId) {
      // 未登录，跳转登录页
      wx.navigateTo({ url: '/pages/login/login' })
      return
    }
    
    const familyId = api.getFamilyId()
    if (!familyId) {
      // 未加入家庭，跳转家庭页
      wx.navigateTo({ url: '/pages/family/family' })
      return
    }
    
    this.loadData()
  },

  /**
   * 加载数据
   */
  async loadData() {
    this.setData({ loading: true })
    
    try {
      const familyId = api.getFamilyId()
      
      // 并行加载
      const [itemsData, remindersData, familyData] = await Promise.all([
        api.getFamilyItems(familyId, 10),
        api.getReminders(familyId, 'pending'),
        api.getFamily(familyId)
      ])

      const rawReminders = remindersData.reminders || []
      const reminders = rawReminders.map((r) => this.normalizeReminder(r))
      const recentItems = (itemsData.items || []).map((it) => ({
        ...it,
        photo_path: api.resolveStaticUrl(it.photo_path)
      }))

      this.setData({
        recentItems,
        reminders,
        urgentCount: remindersData.urgent_count || 0,
        warningCount: remindersData.warning_count || 0,
        familyName: familyData.name || '我的家',
        loading: false
      })
    } catch (err) {
      console.error('加载数据失败', err)
      this.setData({ loading: false })
    }
  },

  /**
   * 搜索输入
   */
  onSearchInput(e) {
    this.setData({ searchKeyword: e.detail.value })
  },

  /**
   * 搜索
   */
  onSearch() {
    const keyword = this.data.searchKeyword.trim()
    if (!keyword) return

    getApp().globalData.pendingChatQuery = keyword
    wx.switchTab({
      url: '/pages/chat/chat'
    })
  },

  /**
   * 快速存物
   */
  onStoreItem() {
    wx.switchTab({ url: '/pages/store/store' })
  },

  /**
   * 快速找物
   */
  onFindItem() {
    wx.switchTab({ url: '/pages/chat/chat' })
  },

  /**
   * 查看物品详情
   */
  onItemClick(e) {
    const itemId = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/detail/detail?id=${itemId}`
    })
  },

  /**
   * 查看全部提醒
   */
  onViewAllReminders() {
    wx.navigateTo({ url: '/pages/reminders/reminders' })
  },

  /**
   * 最近存放「全部」：跳转分页物品列表
   */
  onViewAllItems() {
    wx.navigateTo({ url: '/pages/items/items' })
  },

  /**
   * 为提醒项补充展示用字段：icon、time_label、display_content（与原型一致）
   */
  normalizeReminder(item) {
    const level = item.level || 'normal'
    const iconMap = { urgent: '💊', warning: '🥛', normal: '📄' }
    let timeLabel = ''
    if (item.days_left != null) {
      if (item.days_left <= 0) timeLabel = '已过期'
      else if (item.days_left <= 7) timeLabel = `${item.days_left} 天`
      else if (item.days_left <= 31) timeLabel = `${Math.floor(item.days_left / 7)} 周`
      else timeLabel = `${Math.floor(item.days_left / 30)} 个月`
    } else if (item.expire_at) {
      timeLabel = String(item.expire_at)
    }
    const loc = item.item_location ? `📍 ${item.item_location}` : ''
    const tail = item.content || (item.expire_at ? `${item.expire_at} 过期` : '')
    const displayContent = [loc, tail].filter(Boolean).join(' · ')
    return {
      ...item,
      icon: item.icon || iconMap[level],
      time_label: timeLabel || (item.time_label || ''),
      display_content: displayContent || item.content || ''
    }
  },

  /**
   * 处理提醒（已处理 / 忽略 / 延期）
   */
  async onHandleReminder(e) {
    const { id, action } = e.currentTarget.dataset
    if (!id || !action) return
    try {
      const deferDays = action === 'defer' ? 7 : undefined
      await api.handleReminder(id, action, deferDays)
      wx.showToast({ title: action === 'done' ? '已处理' : action === 'defer' ? '已延期' : '已忽略', icon: 'success' })
      this.loadData()
    } catch (err) {
      console.error('处理失败', err)
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.loadData().then(() => {
      wx.stopPullDownRefresh()
    })
  }
})