/**
 * 家庭管理页
 */
const api = require('../../utils/api')

Page({
  data: {
    familyInfo: null,
    members: [],
    inviteCode: '',
    inputCode: '',
    currentUserId: '',
    editingRemarkUserId: '',
    isAdmin: false
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
      const currentUserId = api.getUserId()
      const currentUser = members.find(m => String(m.id) === String(currentUserId))
      this.setData({
        familyInfo: family,
        members: members || [],
        inviteCode: family.invite_code,
        currentUserId: currentUserId || '',
        editingRemarkUserId: '',
        isAdmin: currentUser && currentUser.is_admin ? true : false
      })
    } catch (err) {
      console.error('加载失败', err)
    }
  },

  async onRemarkEditTap(e) {
    const userId = e.currentTarget.dataset.userId
    if (userId === undefined || userId === null || userId === '') return
    this.setData({ editingRemarkUserId: Number(userId) })
  },

  onRemarkInput(e) {
    const userId = e.currentTarget.dataset.userId
    const value = e.detail.value
    if (!userId) {
      return
    }
    const members = (this.data.members || []).map((m) => {
      if (Number(m.id) === Number(userId)) {
        return { ...m, _tempRemark: value }
      }
      return m
    })
    this.setData({ members })
  },

  async onRemarkBlur(e) {
    const userId = e.currentTarget.dataset.userId
    let value = (e.detail.value || '').trim()
    if (!userId) {
      this.setData({ editingRemarkUserId: '' })
      return
    }
    const members = this.data.members || []
    const target = members.find((m) => Number(m.id) === Number(userId))
    if (!target) {
      this.setData({ editingRemarkUserId: '' })
      return
    }
    if (value.length > 6) {
      value = value.slice(0, 6)
      wx.showToast({ title: '备注最多6个字', icon: 'none' })
    }
    const original = (target.remark || target.nickname || '').trim()
    if (value === original) {
      this.setData({ editingRemarkUserId: '' })
      return
    }
    try {
      await api.updateUserRemark(userId, value)
      const updated = members.map((m) => {
        if (Number(m.id) === Number(userId)) {
          return { ...m, remark: value, _tempRemark: undefined }
        }
        return m
      })
      this.setData({
        members: updated,
        editingRemarkUserId: ''
      })
      wx.showToast({ title: '备注已更新', icon: 'success' })
    } catch (err) {
      wx.showToast({ title: '更新失败', icon: 'none' })
      this.loadData()
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
  },

  async onDeleteMemberTap(e) {
    const memberId = e.currentTarget.dataset.userId
    const memberName = e.currentTarget.dataset.userName
    const familyId = api.getFamilyId()

    if (!memberId || !familyId) return

    wx.showModal({
      title: '删除成员',
      content: `确定要删除"${memberName}"吗？删除后该成员将无法访问家庭物品。`,
      confirmText: '删除',
      confirmColor: '#FF6B5B',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.removeFamilyMember(familyId, memberId)
            wx.showToast({ title: '删除成功', icon: 'success' })
            this.loadData()
          } catch (err) {
            console.error('删除失败', err)
            wx.showToast({ title: err && err.message ? err.message : '删除失败', icon: 'none' })
          }
        }
      }
    })
  }
})