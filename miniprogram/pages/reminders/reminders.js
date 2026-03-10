/**
 * 提醒列表页
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

  async loadData() {
    const familyId = api.getFamilyId()
    if (!familyId) return
    
    try {
      const data = await api.getReminders(familyId)
      this.setData({ reminders: data.reminders || [], loading: false })
    } catch (err) {
      console.error('加载失败', err)
      this.setData({ loading: false })
    }
  },

  async onHandle(e) {
    const { id, action } = e.currentTarget.dataset
    
    try {
      await api.handleReminder(id, action)
      wx.showToast({ title: '已处理', icon: 'success' })
      this.loadData()
    } catch (err) {
      wx.showToast({ title: '处理失败', icon: 'none' })
    }
  }
})