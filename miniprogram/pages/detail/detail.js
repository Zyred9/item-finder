/**
 * 物品详情页
 */
const api = require('../../utils/api')
const util = require('../../utils/util')

/** 扩展字段 key -> 中文标签（只保留核心字段） */
const EXTENSION_LABELS = {
  expire_date: '有效期',
  production_date: '生产日期',
  shelf_life_days: '保质期 (天)',
  warranty_date: '保修到期'
}

Page({
  data: {
    item: null,
    loading: true,
    hasExtensionFields: false,
    extensionRows: [],
    createdAtText: '',
    expiryStatus: null, // 'expired' | 'expiring' | null
    expiryLabel: '', // 已过期 X 天 / 临期 X 天
    categoryIcon: '' // 分类图标
  },

  onLoad(options) {
    const id = options.id
    if (id) {
      this.loadItem(id)
    }
  },

  async loadItem(itemId) {
    try {
      const item = await api.getItem(itemId)
      if (!item) {
        this.setData({ loading: false })
        return
      }
      
      // 处理扩展信息
      const extension = item.extension || {}
      const extensionRows = []
      for (const key of Object.keys(EXTENSION_LABELS)) {
        const value = extension[key]
        if (value !== null && value !== undefined && value !== '') {
          extensionRows.push({
            label: EXTENSION_LABELS[key],
            value: value
          })
        }
      }
      
      // 计算过期状态
      const { expiryStatus, expiryLabel } = this.calculateExpiryStatus(extension)
      
      // 获取分类图标
      const categoryIcon = this.getCategoryIcon(item.category_name)
      
      // 格式化存放时间（只展示年月日）
      const createdAtText = item.created_at ? this.formatDateOnly(item.created_at) : ''
      
      this.setData({
        item,
        hasExtensionFields: extensionRows.length > 0,
        extensionRows,
        createdAtText,
        expiryStatus,
        expiryLabel,
        categoryIcon,
        loading: false
      })
    } catch (err) {
      console.error('加载失败', err)
      this.setData({ loading: false })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  /**
   * 计算过期状态
   * @param {Object} extension - 扩展信息（包含 expire_date）
   * @returns {Object} - { expiryStatus: 'expired' | 'expiring' | null, expiryLabel: string }
   */
  calculateExpiryStatus(extension) {
    if (!extension || !extension.expire_date) {
      return { expiryStatus: null, expiryLabel: '' }
    }

    const expireDateStr = extension.expire_date
    if (!expireDateStr) {
      return { expiryStatus: null, expiryLabel: '' }
    }

    const today = new Date()
    today.setHours(0, 0, 0, 0)

    const expireDate = new Date(expireDateStr)
    if (isNaN(expireDate.getTime())) {
      return { expiryStatus: null, expiryLabel: '' }
    }

    const diffTime = expireDate - today
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays < 0) {
      // 已过期
      return {
        expiryStatus: 'expired',
        expiryLabel: `已过期${Math.abs(diffDays)}天`
      }
    } else if (diffDays <= 60) {
      // 临期（60 天内）
      return {
        expiryStatus: 'expiring',
        expiryLabel: diffDays === 0 ? '今日过期' : `临期${diffDays}天`
      }
    }

    return { expiryStatus: null, expiryLabel: '' }
  },

  /**
   * 格式化日期（只展示年月日）
   * @param {string} dateTime - ISO 日期时间字符串
   * @returns {string} 格式化后的日期（YYYY-MM-DD）
   */
  formatDateOnly(dateTime) {
    if (!dateTime) return ''
    try {
      const date = new Date(dateTime)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    } catch (e) {
      return dateTime
    }
  },

  /**
   * 根据分类获取图标
   * @param {string} categoryName - 分类名称
   * @returns {string} 图标路径
   */
  getCategoryIcon(categoryName) {
    if (!categoryName) {
      return '/assets/icons/home.svg'
    }
    
    const text = String(categoryName).toLowerCase()
    
    // 食品饮料类
    if (text.includes('food') || text.includes('食品') || text.includes('饮料') || text.includes('零食') || text.includes('调味') || text.includes('粮油')) {
      return '/assets/icons/food.svg'
    }
    
    // 药品健康类
    if (text.includes('medicine') || text.includes('药') || text.includes('保健') || text.includes('医疗')) {
      return '/assets/icons/medicine.svg'
    }
    
    // 服饰鞋包类
    if (text.includes('clothing') || text.includes('衣服') || text.includes('鞋') || text.includes('包') || text.includes('服饰')) {
      return '/assets/icons/clothing.svg'
    }
    
    // 数码家电类
    if (text.includes('electronics') || text.includes('电子') || text.includes('数码') || text.includes('家电') || text.includes('手机') || text.includes('电脑')) {
      return '/assets/icons/electronics.svg'
    }
    
    // 证件文件类
    if (text.includes('document') || text.includes('证件') || text.includes('文件') || text.includes('卡') || text.includes('票据')) {
      return '/assets/icons/document.svg'
    }
    
    // 生活用品类（默认）
    return '/assets/icons/home.svg'
  },

  onShareAppMessage() {
    const item = this.data.item
    return {
      title: item ? item.name : '寻物记',
      path: `/pages/detail/detail?id=${this.data.item ? this.data.item.id : ''}`
    }
  }
})
