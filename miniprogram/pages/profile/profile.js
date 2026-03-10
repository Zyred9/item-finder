/**
 * 个人中心页 - 对齐设计原型 v3
 */
const api = require('../../utils/api')

Page({
  data: {
    userInfo: null,
    familyInfo: null,
    userName: '我',
    avatarText: '👤',
    familyName: '',
    roleText: '',
    memberCount: 0,
    stats: {
      itemCount: 0,
      reminderCount: 0
    }
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    const userId = api.getUserId()
    const familyId = api.getFamilyId()

    if (!userId) {
      wx.navigateTo({ url: '/pages/login/login' })
      return
    }

    const app = getApp()
    const globalFamily = (app.globalData && app.globalData.familyInfo) || null
    const userName = (globalFamily && globalFamily.nickname) || '我'
    const avatarText = userName !== '我' && userName.length > 0 ? userName[0] : '👤'

    this.setData({ userName: userName || '我', avatarText })

    if (!familyId) {
      this.setData({ familyName: '', roleText: '', memberCount: 0 })
      return
    }

    try {
      const familyData = await api.getFamily(familyId)
      const familyName = familyData.name || familyData.family_name || '我的家庭'
      this.setData({ familyInfo: familyData, familyName, roleText: '成员' })

      const [membersRes, itemsRes] = await Promise.all([
        api.getFamilyMembers(familyId).catch(() => []),
        api.getFamilyItems(familyId, 1, 0).catch(() => ({ items: [], total: 0 }))
      ])
      const memberCount = Array.isArray(membersRes) ? membersRes.length : (membersRes.total || 0)
      const itemCount = (itemsRes && itemsRes.total != null) ? itemsRes.total : (itemsRes.items && itemsRes.items.length) || 0
      this.setData({
        memberCount,
        'stats.itemCount': itemCount
      })
    } catch (err) {
      console.error('加载失败', err)
      this.setData({ familyName: (this.data.familyInfo && this.data.familyInfo.name) || '我的家庭', roleText: '成员' })
    }
  },

  onManageFamily() {
    wx.navigateTo({ url: '/pages/family/family' })
  },

  onViewReminders() {
    wx.navigateTo({ url: '/pages/reminders/reminders' })
  },

  onPrivacy() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  onStats() {
    wx.switchTab({ url: '/pages/index/index' })
  },

  onHelp() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  onAbout() {
    wx.showToast({ title: '寻物记 v1.0', icon: 'none' })
  },

  onLogout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          api.clearUserInfo()
          wx.reLaunch({ url: '/pages/login/login' })
        }
      }
    })
  }
})
