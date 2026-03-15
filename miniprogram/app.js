/**
 * 寻物记小程序入口
 */

App({
  globalData: {
    userInfo: null,
    familyInfo: null
  },

  onLaunch() {
    // 检查登录状态
    this.checkLoginStatus()
  },

  /**
   * 检查登录状态
   */
  checkLoginStatus() {
    const userId = wx.getStorageSync('userId')
    const familyId = wx.getStorageSync('familyId')
    
    if (userId && familyId) {
      this.globalData.userInfo = { userId }
      this.globalData.familyInfo = { familyId }
    }
  },

  /**
   * 登录
   * 开发环境：使用固定身份，避免「清空缓存后」每次变成新用户、被要求重新填邀请码。
   * 生产环境：应调用 wx.login() 获取 code，后端用 jscode2session 换 openid。
   */
  async login() {
    return new Promise((resolve, reject) => {
      // 优先用本地缓存的 mockOpenid；清空缓存后没有则用固定常量，保证同一设备始终对应同一用户
      const STORED = wx.getStorageSync('mockOpenid')
      const mockOpenid = STORED || 'mock_dev_fixed_user'
      if (!STORED) {
        wx.setStorageSync('mockOpenid', mockOpenid)
      }
      resolve(mockOpenid)
    })
  },

  /**
   * 生成 UUID
   */
  generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0
      const v = c === 'x' ? r : (r & 0x3 | 0x8)
      return v.toString(16)
    })
  }
})