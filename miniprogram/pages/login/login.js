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
      const result = await api.login(code)
      
      // 保存用户信息
      api.setUserInfo(result.user_id, result.family_id)
      
      if (!result.family_id) {
        // 新用户，需要创建/加入家庭
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