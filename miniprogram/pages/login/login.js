/**
 * 登录页
 */
const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    loading: false
  },

  async onLogin() {
    this.setData({ loading: true })

    try {
      const code = await app.login()
      let userInfo = null
      try {
        const res = await wx.getUserProfile({ desc: '用于展示头像与昵称' })
        if (res && res.userInfo) userInfo = res.userInfo
      } catch (e) {
        console.warn('获取微信头像/昵称失败，将仅登录', e)
      }

      const result = await api.login(code, userInfo)

      api.setUserInfo(result.user_id, result.family_id, {
        avatarUrl: result.avatar_url || (userInfo && userInfo.avatarUrl),
        nickname: result.nickname || (userInfo && userInfo.nickName)
      })

      if (!result.family_id) {
        wx.navigateTo({ url: '/pages/family/family' })
        return
      }

      wx.switchTab({ url: '/pages/index/index' })
    } catch (err) {
      console.error('登录失败', err)
      wx.showToast({ title: '登录失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  }
})