/**
 * 提醒列表页 - 展示与首页智能提醒一致：名字、过期时间、剩余天数、所在位置、图片/默认 icon
 */
const api = require('../../utils/api')

Page({
  data: {
    reminders: [],
    loading: true
  },

  onShow() {
    this.loadData()
  },

  onPullDownRefresh() {
    this.loadData().then(() => {
      wx.stopPullDownRefresh()
    }).catch(() => {
      wx.stopPullDownRefresh()
    })
  },

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
    let displayTitle = item.title || item.item_name || '提醒'
    if (item.days_left != null && item.days_left > 30 && displayTitle) {
      if (displayTitle.indexOf('即将过期') !== -1) displayTitle = displayTitle.replace('即将过期', '过期提醒')
      else if (displayTitle.indexOf('开封后即将过期') !== -1) displayTitle = displayTitle.replace('开封后即将过期', '开封后保质提醒')
      else if (displayTitle.indexOf('保修即将到期') !== -1) displayTitle = displayTitle.replace('保修即将到期', '保修到期提醒')
    }
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

  async loadData() {
    const familyId = api.getFamilyId()
    if (!familyId) {
      wx.stopPullDownRefresh && wx.stopPullDownRefresh()
      return
    }

    try {
      const data = await api.getReminders(familyId, 'pending')
      const raw = data.reminders || []
      const reminders = raw.map((r) => this.normalizeReminder(r))
      this.setData({ reminders, loading: false })
    } catch (err) {
      console.error('加载失败', err)
      this.setData({ loading: false })
    }
  },

  async onHandle(e) {
    const { id, action } = e.currentTarget.dataset
    const deferDays = action === 'defer' ? 7 : undefined
    try {
      await api.handleReminder(id, action, deferDays)
      wx.showToast({ title: action === 'done' ? '已处理' : action === 'defer' ? '已延期' : '已忽略', icon: 'success' })
      this.loadData()
    } catch (err) {
      wx.showToast({ title: '处理失败', icon: 'none' })
    }
  }
})