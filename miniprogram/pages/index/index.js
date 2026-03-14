/**
 * 首页
 */
const api = require('../../utils/api')
const util = require('../../utils/util')

Page({
  data: {
    familyName: '我的家',
    greeting: '你好',
    recentItems: [],
    reminders: [],
    displayReminders: [],
    urgentCount: 0,
    warningCount: 0,
    itemStats: {
      total: 0,
      expiringSoon: 0,
      expired: 0
    },
    loading: true,
    refreshing: false
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
      const [itemsData, remindersData, familyData, statsData] = await Promise.all([
        api.getFamilyItems(familyId, 10),
        api.getReminders(familyId, 'pending'),
        api.getFamily(familyId),
        api.getItemStats(familyId)
      ])

      const rawReminders = remindersData.reminders || []
      const reminders = rawReminders.map((r) => this.normalizeReminder(r))
      const sortedByExpiry = reminders.slice().sort((a, b) => {
        const da = a.days_left != null ? a.days_left : 999999
        const db = b.days_left != null ? b.days_left : 999999
        return da - db
      })
      const displayReminders = sortedByExpiry.slice(0, 3)
      const recentItems = (itemsData.items || []).map((it) => {
        const raw = it.created_at || ''
        const d = new Date(raw)
        const created_at_label = isNaN(d.getTime())
          ? raw.replace('T', ' ').slice(0, 16)
          : `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
        const categoryIcon = this.getCategoryIcon(it.category_name)
        return { 
          ...it, 
          photo_path: api.resolveStaticUrl(it.photo_path), 
          created_at_label,
          category_icon: categoryIcon
        }
      })

      const itemStats = {
        total: statsData.total || 0,
        expiringSoon: statsData.expiring_soon || 0,
        expired: statsData.expired || 0
      }

      this.setData({
        recentItems,
        reminders,
        displayReminders,
        urgentCount: remindersData.urgent_count || 0,
        warningCount: remindersData.warning_count || 0,
        itemStats,
        familyName: familyData.name || '我的家',
        loading: false
      })
    } catch (err) {
      console.error('加载数据失败', err)
      this.setData({ loading: false })
    }
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
   * 根据分类返回对应的图标路径（支持分类名和分类 code）
   */
  getCategoryIcon(categoryNameOrCode) {
    if (!categoryNameOrCode) {
      return '/assets/icons/map-pin.svg'
    }
    
    const text = String(categoryNameOrCode).toLowerCase()
    
    // 食品饮料类
    if (text.includes('food') || text.includes('食品') || text.includes('饮料') || text.includes('零食') || text.includes('调味') || text.includes('粮油')) {
      return '/assets/icons/food.svg'
    }
    
    // 药品健康类
    if (text.includes('medicine') || text.includes('药') || text.includes('保健') || text.includes('医疗')) {
      return '/assets/icons/medicine.svg'
    }
    
    // 服饰鞋包类
    if (text.includes('clothing') || text.includes('衣服') || text.includes('鞋') || text.includes('包') || text.includes('服饰')) {
      return '/assets/icons/clothing.svg'
    }
    
    // 数码家电类
    if (text.includes('electronics') || text.includes('电子') || text.includes('数码') || text.includes('家电') || text.includes('手机') || text.includes('电脑')) {
      return '/assets/icons/electronics.svg'
    }
    
    // 证件文件类
    if (text.includes('document') || text.includes('证件') || text.includes('文件') || text.includes('卡') || text.includes('票据')) {
      return '/assets/icons/document.svg'
    }
    
    // 生活用品类（默认）
    return '/assets/icons/home.svg'
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
    const rawDate = item.expire_at || item.remind_at
    let expire_at_display = ''
    if (rawDate) {
      const d = new Date(rawDate)
      if (!isNaN(d.getTime())) {
        expire_at_display = `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
      } else {
        expire_at_display = String(rawDate)
      }
    }
    const displayTitle = item.title || item.item_name || '提醒'
    const loc = item.item_location ? `📍 ${item.item_location}` : ''
    const tail = item.content || (expire_at_display ? `${expire_at_display} 过期` : '')
    const displayContent = [loc, tail].filter(Boolean).join(' · ')
    const item_photo_display = (item.item_photo && api.resolveStaticUrl(item.item_photo)) || ''
    return {
      ...item,
      icon: item.icon || iconMap[level],
      time_label: timeLabel || (item.time_label || ''),
      expire_at_display: expire_at_display,
      display_content: displayContent || item.content || '',
      display_title: displayTitle,
      item_photo_display: item_photo_display
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
   * 下拉刷新（scroll-view 内下拉）
   */
  onRefresherRefresh() {
    this.setData({ refreshing: true })
    this.loadData().then(() => {
      this.setData({ refreshing: false })
    }).catch(() => {
      this.setData({ refreshing: false })
    })
  },

  onPullDownRefresh() {
    this.loadData().then(() => {
      wx.stopPullDownRefresh()
    })
  }
})