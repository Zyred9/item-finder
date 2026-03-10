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
    offset: 0
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
    return (list || []).map((item) => ({
      ...item,
      photo_path: api.resolveStaticUrl(item.photo_path),
      created_at: item.created_at ? util.formatTime(item.created_at) : ''
    }))
  },

  onItemTap(e) {
    const id = e.currentTarget.dataset.id
    if (id) {
      wx.navigateTo({ url: `/pages/detail/detail?id=${id}` })
    }
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
