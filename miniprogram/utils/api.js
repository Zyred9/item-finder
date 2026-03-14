/**
 * API 请求封装
 * - 模拟器（小程序在电脑上跑）：用 127.0.0.1
 * - 真机调试/真机预览（小程序在手机上跑）：填电脑的局域网 IP，并确保电脑防火墙放行 8000 端口
 */
const API_HOST = '192.168.0.7' // 真机调试时填电脑局域网 IP，如 '192.168.0.7'，模拟器留空
const API_ORIGIN = API_HOST ? `http://${API_HOST}:8000` : 'http://127.0.0.1:8000'
const API_BASE_URL = `${API_ORIGIN}/api`
console.log('[api] API_BASE_URL =', API_BASE_URL)

/**
 * 将后端返回的相对静态路径补全为绝对 URL（用于 <image src>）
 * - 后端一般返回：/uploads/photos/...
 */
function resolveStaticUrl(path) {
  if (!path) return ''
  const s = String(path)
  if (s.startsWith('http://') || s.startsWith('https://')) return s
  if (s.startsWith('/')) return `${API_ORIGIN}${s}`
  return s
}

/**
 * 获取用户 ID
 */
function getUserId() {
  return wx.getStorageSync('userId')
}

/**
 * 获取家庭 ID
 */
function getFamilyId() {
  return wx.getStorageSync('familyId')
}

/**
 * 通用请求方法
 */
function request(url, method = 'GET', data = {}) {
  return new Promise((resolve, reject) => {
    const userId = getUserId()
    const requestUrl = `${API_BASE_URL}${url}`
    console.log('[api][request] start', { url: requestUrl, method, data, userId })

    wx.request({
      url: requestUrl,
      method: method,
      data: data,
      header: {
        'Content-Type': 'application/json',
        'X-User-Id': userId
      },
      success: (res) => {
        console.log('[api][request] success', {
          url: requestUrl,
          method,
          statusCode: res.statusCode,
          data: res.data
        })
        const authFailDetails = ['无效的用户ID', '未登录', '登录过期', '登录已过期']
        const detailStr = String(res.data && res.data.detail || '')
        const messageStr = String(res.data && res.data.message || '')
        const needReLogin = res.statusCode === 401 ||
          (res.data && (
            res.data.code === 401 ||
            authFailDetails.indexOf(res.data.detail) !== -1 ||
            (detailStr.indexOf('登录') !== -1 && detailStr.indexOf('过期') !== -1) ||
            (messageStr.indexOf('登录') !== -1 && messageStr.indexOf('过期') !== -1)
          ))
        if (needReLogin) {
          wx.removeStorageSync('userId')
          wx.removeStorageSync('familyId')
          wx.showToast({ title: '请重新登录', icon: 'none' })
          setTimeout(() => {
            wx.reLaunch({ url: '/pages/login/login' })
          }, 800)
          reject(new Error('未登录或登录已失效'))
          return
        }
        if (res.statusCode === 200 && res.data.code === 0) {
          resolve(res.data.data)
        } else if (res.data.code === 1001) {
          // 新用户，需要加入家庭
          resolve(res.data)
        } else {
          wx.showToast({
            title: res.data.message || res.data.detail || '请求失败',
            icon: 'none'
          })
          reject(res.data)
        }
      },
      fail: (err) => {
        console.error('[api][request] fail', {
          url: requestUrl,
          method,
          err
        })
        wx.showToast({
          title: (err && err.errMsg) ? '请求失败' : '网络错误',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

/**
 * API 方法
 */
module.exports = {
  resolveStaticUrl,
  // ========== 认证 ==========
  login: (code, userInfo) =>
    request('/auth/login', 'POST', {
      code,
      nickname: userInfo && userInfo.nickName ? userInfo.nickName : undefined,
      avatar_url: userInfo && userInfo.avatarUrl ? userInfo.avatarUrl : undefined
    }),

  // ========== 家庭 ==========
  createFamily: (name) => request('/families', 'POST', { name }),
  joinFamily: (inviteCode) => request('/families/join', 'POST', { invite_code: inviteCode }),
  getFamily: (familyId) => request(`/families/${familyId}`),
  getFamilyMembers: (familyId) => request(`/families/${familyId}/members`),

  // ========== 用户 ==========
  updateUserRemark: (userId, remark) => request(`/users/${userId}`, 'PATCH', { remark }),

  // ========== 物品 ==========
  createItem: (data) => {
    const userId = getUserId()
    const name = (data.name || '').trim()
    const location = (data.location || '').trim()
    const description = data.description != null ? String(data.description) : ''
    const categoryId = data.category_id != null ? String(data.category_id) : ''
    const photoPath = data.photo_path
    const extension = data.extension ? JSON.stringify(data.extension) : null

    const formFields = {
      name,
      location,
      description,
      category_id: categoryId,
      extension: extension
    }

    function getErrorMessage(res) {
      if (res.statusCode === 400 || res.statusCode === 422) {
        let body = res.data
        if (typeof body === 'string') {
          try {
            body = JSON.parse(body)
          } catch (e) {
            return res.statusCode === 400 ? '请求错误' : '参数错误'
          }
        }
        const msg = (body && (body.detail || body.message))
        if (typeof msg === 'string') return msg
        if (Array.isArray(msg) && msg[0] && msg[0].msg) return msg[0].msg
        return res.statusCode === 400 ? '请求错误' : '参数错误'
      }
      return '请求失败'
    }

    if (photoPath && typeof photoPath === 'string' && photoPath.trim()) {
      return new Promise((resolve, reject) => {
        wx.uploadFile({
          url: `${API_BASE_URL}/items`,
          filePath: photoPath.trim(),
          name: 'photo',
          formData: formFields,
          header: { 'X-User-Id': userId },
          success: (res) => {
            if (res.statusCode !== 200) {
              wx.showToast({ title: getErrorMessage(res), icon: 'none' })
              reject(new Error(getErrorMessage(res)))
              return
            }
            let body
            try {
              body = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
            } catch (e) {
              reject(new Error('解析失败'))
              return
            }
            if (body.code === 0 && body.data) {
              resolve(body.data)
            } else {
              wx.showToast({ title: body.message || '请求失败', icon: 'none' })
              reject(body)
            }
          },
          fail: (err) => {
            wx.showToast({ title: '网络错误', icon: 'none' })
            reject(err)
          }
        })
      })
    }

    const encoded = Object.keys(formFields)
      .map(k => `${encodeURIComponent(k)}=${encodeURIComponent(formFields[k])}`)
      .join('&')
    return new Promise((resolve, reject) => {
      wx.request({
        url: `${API_BASE_URL}/items`,
        method: 'POST',
        data: encoded,
        header: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-User-Id': userId
        },
        success: (res) => {
          if (res.statusCode === 200 && res.data.code === 0) {
            resolve(res.data.data)
          } else {
            wx.showToast({ title: getErrorMessage(res), icon: 'none' })
            reject(res.data || new Error(getErrorMessage(res)))
          }
        },
        fail: (err) => {
          wx.showToast({ title: '网络错误', icon: 'none' })
          reject(err)
        }
      })
    })
  },
  getItem: (itemId) => request(`/items/${itemId}`),
  updateItem: (itemId, data) => request(`/items/${itemId}`, 'PUT', data),
  deleteItem: (itemId) => request(`/items/${itemId}`, 'DELETE'),
  getFamilyItems: (familyId, limit = 20, offset = 0) =>
    request(`/items?family_id=${familyId}&limit=${limit}&offset=${offset}`),
  searchItems: (query, familyId, limit = 20) =>
    request(`/items/search?q=${encodeURIComponent(query)}&family_id=${familyId}&limit=${limit}`),

  // ========== 分类 ==========
  getCategories: () => request('/categories'),
  getCategoryDetail: (categoryId) => request(`/categories/${categoryId}`),

  // ========== 提醒 ==========
  getReminders: (familyId, status, level) => {
    let url = `/reminders?family_id=${familyId}`
    if (status) url += `&status=${status}`
    if (level) url += `&level=${level}`
    return request(url)
  },
  handleReminder: (reminderId, action, deferDays) => {
    const data = { action }
    if (deferDays) data.defer_days = deferDays
    return request(`/reminders/${reminderId}`, 'PUT', data)
  },

  // ========== 对话 ==========
  chat: (familyId, sessionId, message) => request('/chat', 'POST', {
    family_id: familyId,
    session_id: sessionId,
    message: message
  }),
  getChatHistory: (familyId, sessionId, limit = 50) =>
    request(`/chat/history?family_id=${familyId}&session_id=${sessionId}&limit=${limit}`),
  clearChatHistory: (familyId, sessionId) =>
    request(`/chat/history?family_id=${familyId}&session_id=${sessionId}`, 'DELETE'),
  summarizeChat: (familyId, sessionId) =>
    request('/chat/summarize', 'POST', { family_id: familyId, session_id: sessionId }),

  // ========== 帮助与反馈 ==========
  submitFeedback: (content, contact) =>
    request('/feedback', 'POST', { content: content || '', contact: contact || '' }),

  // ========== 位置 ==========
  getLocations: (familyId) => request(`/locations?family_id=${familyId}`),

  // ========== 上传 ==========
  uploadPhoto: (filePath) => {
    return new Promise((resolve, reject) => {
      const userId = getUserId()
      wx.uploadFile({
        url: `${API_BASE_URL}/items`,
        filePath: filePath,
        name: 'photo',
        header: {
          'X-User-Id': userId
        },
        success: (res) => {
          const data = JSON.parse(res.data)
          if (data.code === 0) {
            resolve(data.data)
          } else {
            reject(data)
          }
        },
        fail: reject
      })
    })
  },

  // ========== 语音 ==========
  uploadVoice: (filePath, scene = 'common') => {
    return new Promise((resolve, reject) => {
      const userId = getUserId()
      const requestUrl = `${API_BASE_URL}/chat/voice/recognize`
      console.log('[api][uploadVoice] start', { url: requestUrl, filePath, scene, userId })
      wx.uploadFile({
        url: requestUrl,
        filePath: filePath,
        name: 'file',
        formData: { format: 'json', scene },
        header: {
          'X-User-Id': userId
        },
        timeout: 120000,
        success: (res) => {
          console.log('[api][uploadVoice] success', {
            url: requestUrl,
            statusCode: res.statusCode,
            data: res.data
          })
          if (res.statusCode !== 200) {
            reject(new Error(res.statusCode === 401 ? '请先登录' : res.statusCode === 404 ? '语音识别服务不可用' : '识别失败'))
            return
          }
          let data
          try {
            data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
          } catch (e) {
            reject(new Error('解析结果失败'))
            return
          }
          if (data && data.code === 0 && data.data) {
            resolve(data.data)
          } else {
            reject(new Error((data && data.message) || '识别失败'))
          }
        },
        fail: (err) => {
          console.error('[api][uploadVoice] fail', {
            url: requestUrl,
            err
          })
          reject(err || new Error('网络错误'))
        }
      })
    })
  },

  /**
   * 真机调试埋点（不影响主流程，失败也忽略）
   */
  debugLog: (payload = {}) => {
    try {
      const userId = getUserId()
      const requestUrl = `${API_BASE_URL}/debug/log`
      wx.request({
        url: requestUrl,
        method: 'POST',
        data: payload,
        header: {
          'Content-Type': 'application/json',
          'X-User-Id': userId
        },
        success: () => { },
        fail: () => { }
      })
    } catch (e) {
      // ignore
    }
  },

  textToSpeech: (text, speed = 5, volume = 5) =>
    request('/chat/voice/tts', 'POST', { text, speed, volume }),

  // 存物主图理解（Qwen-VL）：拍照识物，建议名称/分类
  photoUnderstand: (filePath) => {
    return new Promise((resolve, reject) => {
      const userId = getUserId()
      wx.uploadFile({
        url: `${API_BASE_URL}/items/photo/understand`,
        filePath: filePath,
        name: 'photo',
        header: { 'X-User-Id': userId },
        success: (res) => {
          if (res.statusCode !== 200) {
            reject(new Error(res.data && (res.data.detail || res.data.message) || '识图失败'))
            return
          }
          let data
          try {
            data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
          } catch (e) {
            reject(new Error('解析失败'))
            return
          }
          if (data && data.code === 0 && data.data) resolve(data.data)
          else reject(new Error((data && data.message) || '识图失败'))
        },
        fail: reject
      })
    })
  },

  // 扩展凭证 OCR（说明书、发票、药盒等）
  photoOcr: (filePath) => {
    return new Promise((resolve, reject) => {
      const userId = getUserId()
      wx.uploadFile({
        url: `${API_BASE_URL}/items/photo/ocr`,
        filePath: filePath,
        name: 'photo',
        header: { 'X-User-Id': userId },
        success: (res) => {
          if (res.statusCode !== 200) {
            reject(new Error(res.data && (res.data.detail || res.data.message) || 'OCR 失败'))
            return
          }
          let data
          try {
            data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
          } catch (e) {
            reject(new Error('解析失败'))
            return
          }
          if (data && data.code === 0 && data.data) resolve(data.data)
          else reject(new Error((data && data.message) || 'OCR 失败'))
        },
        fail: reject
      })
    })
  },

  // ========== 工具 ==========
  getUserId,
  getFamilyId,

  setUserInfo: (userId, familyId, extra) => {
    wx.setStorageSync('userId', userId)
    if (familyId) wx.setStorageSync('familyId', familyId)
    if (extra) {
      if (extra.avatarUrl != null) wx.setStorageSync('avatarUrl', extra.avatarUrl)
      if (extra.nickname != null) wx.setStorageSync('nickname', extra.nickname)
    }
  },

  getAvatarUrl: () => wx.getStorageSync('avatarUrl') || '',
  getNickname: () => wx.getStorageSync('nickname') || '',

  clearUserInfo: () => {
    wx.removeStorageSync('userId')
    wx.removeStorageSync('familyId')
    wx.removeStorageSync('avatarUrl')
    wx.removeStorageSync('nickname')
  }
}
