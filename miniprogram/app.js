/**
 * 寻物记小程序入口
 */

App({
  globalData: {
    userInfo: null,
    familyInfo: null,
    pendingChatQuery: ''
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
   * 开发环境：返回存储的固定 openid（如果没有则生成一个）
   * 生产环境：调用 wx.login() 获取 code
   */
  async login() {
    return new Promise((resolve, reject) => {
      // 开发环境：使用固定的 mock openid
      let mockOpenid = wx.getStorageSync('mockOpenid')
      if (!mockOpenid) {
        // 生成一个固定的 mock openid
        mockOpenid = 'mock_' + this.generateUUID()
        wx.setStorageSync('mockOpenid', mockOpenid)
      }
      
      // 返回 mock openid 作为 code（后端会识别 mock_ 前缀）
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