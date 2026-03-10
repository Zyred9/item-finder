/**
 * 物品详情页
 */
const api = require('../../utils/api')
const util = require('../../utils/util')

/** 扩展字段 key -> 中文标签 */
const EXTENSION_LABELS = {
  expire_date: '有效期',
  production_date: '生产日期',
  shelf_life_days: '保质期(天)',
  open_date: '开封日期',
  open_shelf_life: '开封后保质期',
  dosage: '用法用量',
  document_number: '证件号',
  issuer: '发证机关',
  brand: '品牌',
  model: '型号',
  purchase_date: '购买日期',
  warranty_date: '保修到期',
  size: '尺码',
  color: '颜色',
  season: '季节',
  material: '材质',
  storage_condition: '储存条件'
}

Page({
  data: {
    item: null,
    loading: true,
    hasExtensionFields: false,
    extensionRows: [],
    createdAtText: ''
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
      item.photo_path = api.resolveStaticUrl(item.photo_path)
      const createdAtText = item.created_at ? util.formatTime(item.created_at) : ''
      const ext = item.extension && typeof item.extension === 'object' ? item.extension : {}
      const extensionRows = []
      Object.keys(ext).forEach((k) => {
        const v = ext[k]
        if (v != null && String(v).trim() !== '') {
          extensionRows.push({
            label: EXTENSION_LABELS[k] || k,
            value: typeof v === 'string' ? v : (v && typeof v === 'object' && v.toString ? v.toString() : String(v))
          })
        }
      })
      const hasExtensionFields = extensionRows.length > 0
      this.setData({
        item,
        loading: false,
        hasExtensionFields,
        extensionRows,
        createdAtText
      })
    } catch (err) {
      console.error('加载失败', err)
      this.setData({ loading: false })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  onEdit() {
    const item = this.data.item
    if (!item || !item.id) return
    wx.navigateTo({ url: `/pages/store/store?id=${item.id}` })
  },

  async onDelete() {
    wx.showModal({
      title: '确认删除',
      content: '删除后无法恢复，确定要删除吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.deleteItem(this.data.item.id)
            wx.showToast({ title: '已删除', icon: 'success' })
            setTimeout(() => wx.navigateBack(), 1500)
          } catch (err) {
            wx.showToast({ title: '删除失败', icon: 'none' })
          }
        }
      }
    })
  },

  onPreviewImage() {
    if (this.data.item && this.data.item.photo_path) {
      wx.previewImage({
        urls: [this.data.item.photo_path]
      })
    }
  }
})