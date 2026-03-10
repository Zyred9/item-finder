/**
 * 家庭管理页
 */
const api = require('../../utils/api')

Page({
  data: {
    familyInfo: null,
    members: [],
    inviteCode: '',
    inputCode: ''
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    const familyId = api.getFamilyId()
    if (!familyId) return
    
    try {
      const [family, members] = await Promise.all([
        api.getFamily(familyId),
        api.getFamilyMembers(familyId)
      ])
      
      this.setData({ 
        familyInfo: family, 
        members,
        inviteCode: family.invite_code
      })
    } catch (err) {
      console.error('加载失败', err)
    }
  },

  async onCreateFamily() {
    try {
      const result = await wx.showModal({
        title: '创建家庭',
        editable: true,
        placeholderText: '输入家庭名称'
      })

      if (result.confirm && result.content) {
        const family = await api.createFamily(result.content)
        api.setUserInfo(api.getUserId(), family.id)
        wx.showToast({ title: '创建成功', icon: 'success' })
        wx.switchTab({ url: '/pages/index/index' })
      }
    } catch (err) {
      wx.showToast({ title: '创建失败', icon: 'none' })
    }
  },

  onInputCode(e) {
    this.setData({ inputCode: e.detail.value.toUpperCase() })
  },

  async onJoinFamily() {
    const code = this.data.inputCode.trim()
    if (!code || code.length !== 6) {
      wx.showToast({ title: '请输入6位邀请码', icon: 'none' })
      return
    }

    try {
      const res = await api.joinFamily(code)
      const familyId = res.family_id || (res.family && res.family.id) || res.id
      if (familyId) {
        api.setUserInfo(api.getUserId(), familyId)
      }
      wx.showToast({ title: '加入成功', icon: 'success' })
      wx.switchTab({ url: '/pages/index/index' })
    } catch (err) {
      wx.showToast({ title: '邀请码无效', icon: 'none' })
    }
  },

  onCopyCode() {
    wx.setClipboardData({
      data: this.data.inviteCode,
      success: () => wx.showToast({ title: '已复制', icon: 'success' })
    })
  }
})