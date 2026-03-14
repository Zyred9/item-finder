/**
 * 全部物品列表（分页）
 */
const api = require('../../utils/api')
const util = require('../../utils/util')

const PAGE_SIZE = 20

Page({
  data: {
    items: [],
    total: 0,
    loading: false,
    loadingMore: false,
    hasMore: true,
    offset: 0,
    swipingItemId: null,
    swipeOffset: 0,
    swipeTransition: false
  },

  onLoad() {
    this.loadFirst()
  },

  onShow() {
    if (!api.getFamilyId()) {
      wx.navigateBack()
      return
    }
  },

  async loadFirst() {
    this.setData({ loading: true, offset: 0, hasMore: true })
    try {
      const familyId = api.getFamilyId()
      if (!familyId) {
        this.setData({ loading: false })
        return
      }
      const res = await api.getFamilyItems(familyId, PAGE_SIZE, 0)
      const items = res.items || []
      const total = res.total != null ? res.total : items.length
      this.setData({
        items: this.formatItems(items),
        total,
        offset: items.length,
        hasMore: items.length < total,
        loading: false
      })
    } catch (err) {
      console.error('加载失败', err)
      this.setData({ loading: false, hasMore: false })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  async loadMore() {
    if (this.data.loadingMore || !this.data.hasMore) return
    const familyId = api.getFamilyId()
    if (!familyId) return
    this.setData({ loadingMore: true })
    try {
      const offset = this.data.offset
      const res = await api.getFamilyItems(familyId, PAGE_SIZE, offset)
      const next = res.items || []
      const total = res.total != null ? res.total : 0
      const newItems = this.data.items.concat(this.formatItems(next))
      this.setData({
        items: newItems,
        offset: newItems.length,
        hasMore: newItems.length < total,
        loadingMore: false
      })
    } catch (err) {
      console.error('加载更多失败', err)
      this.setData({ loadingMore: false })
    }
  },

  formatItems(list) {
    return (list || []).map((item) => {
      const formatted = {
        ...item,
        photo_path: api.resolveStaticUrl(item.photo_path),
        created_at: item.created_at ? util.formatTime(item.created_at) : ''
      }
      
      // 添加过期状态标签
      if (item.extension && item.extension.expire_date) {
        const expireDate = new Date(item.extension.expire_date)
        const today = new Date()
        const diffTime = expireDate - today
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
        
        if (diffDays < 0) {
          // 已过期
          formatted.expiry_status = 'expired'
          formatted.expiry_label = `已过期${-diffDays}天`
        } else if (diffDays <= 30) {
          // 临期（30 天内）
          formatted.expiry_status = 'expiring'
          formatted.expiry_label = `临期${diffDays}天`
        }
        // 正常的超过 30 天，不添加标签
      }
      
      return formatted
    })
  },

  onItemTap(e) {
    if (this._suppressTap) {
      this._suppressTap = false
      return
    }
    const id = e.currentTarget.dataset.id
    if (id) {
      wx.navigateTo({ url: `/pages/detail/detail?id=${id}` })
    }
  },

  onItemTouchStart(e) {
    const touch = e.touches && e.touches[0]
    if (!touch) return
    this._touchStartX = touch.clientX
    this._touchStartY = touch.clientY
    this._touchStartTime = Date.now()
    this._suppressTap = false
    const id = e.currentTarget.dataset.id
    this._touchItemId = id
    this.setData({
      swipingItemId: id,
      swipeOffset: 0,
      swipeTransition: false
    })
  },

  onItemTouchMove(e) {
    if (this._touchStartX == null || this.data.swipingItemId !== e.currentTarget.dataset.id) return
    const touch = e.touches && e.touches[0]
    if (!touch) return
    const dx = touch.clientX - this._touchStartX
    const dy = touch.clientY - this._touchStartY
    if (Math.abs(dx) < Math.abs(dy)) return
    const maxLeft = -100
    const offset = Math.max(maxLeft, Math.min(0, dx))
    this.setData({ swipeOffset: offset })
  },

  onItemTouchEnd(e) {
    const touch = e.changedTouches && e.changedTouches[0]
    if (!touch || this._touchStartX == null) return
    const dx = touch.clientX - this._touchStartX
    const dy = touch.clientY - this._touchStartY
    const dt = Date.now() - (this._touchStartTime || 0)
    const id = this._touchItemId || e.currentTarget.dataset.id
    this._touchStartX = null
    this._touchStartY = null
    this._touchStartTime = null

    const threshold = -60
    if (this.data.swipeOffset <= threshold) {
      this._touchItemId = null
      this.setData({
        swipingItemId: null,
        swipeOffset: 0,
        swipeTransition: true
      })
      if (id) {
        this._suppressTap = true
        this.confirmDelete(id)
      }
    } else {
      this.setData({ swipeTransition: true }, () => {
        this.setData({ swipeOffset: 0 }, () => {
          setTimeout(() => {
            this.setData({
              swipingItemId: null,
              swipeTransition: false
            })
          }, 260)
        })
      })
      this._touchItemId = null
    }
  },

  onDeleteTap(e) {
    const id = e.currentTarget.dataset.id
    if (!id) return
    this.confirmDelete(id)
  },

  confirmDelete(id) {
    wx.showModal({
      title: '删除物品',
      content: '删除后将无法恢复，确认删除该物品？',
      confirmColor: '#ff6b5b',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.deleteItem(id)
          wx.showToast({ title: '已删除', icon: 'success' })
          this.loadFirst()
        } catch (err) {
          console.error('删除失败', err)
          wx.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    })
  },

  onPullDownRefresh() {
    this.loadFirst().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  onReachBottom() {
    this.loadMore()
  }
})
