/**
 * 物品编辑页面 - UI-UX-PRO-MAX
 */
const api = require('../../utils/api')
const util = require('../../utils/util')

Page({
  data: {
    // 物品 ID
    itemId: '',
    
    // 加载状态
    loading: false,
    submitting: false,
    
    // 名称长度警告
    nameLengthWarn: false,
    
    // 分类数据
    categories: [],
    selectedCategory: null,
    
    // 表单数据
    formData: {
      name: '',
      location: '',
      description: '',
      category_id: '',
      photo_path: ''
    },
    
    // 扩展字段
    extensionFields: [],
    extensionValues: {}
  },

  onLoad(options) {
    const itemId = options.id
    if (!itemId) {
      wx.showToast({
        title: '物品 ID 无效',
        icon: 'none'
      })
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
      return
    }
    
    this.setData({ itemId })
    this.loadCategories()
    this.loadItemData(itemId)
  },

  /**
   * 加载分类
   */
  async loadCategories() {
    try {
      const data = await api.getCategories()
      this.setData({ categories: data || [] })
    } catch (err) {
      console.error('加载分类失败', err)
    }
  },

  /**
   * 加载物品数据
   */
  async loadItemData(itemId) {
    this.setData({ loading: true })
    
    try {
      const item = await api.getItem(itemId)
      if (!item) {
        wx.showToast({
          title: '物品不存在',
          icon: 'none'
        })
        setTimeout(() => {
          wx.navigateBack()
        }, 1500)
        return
      }
      
      // 处理图片路径：如果是本地路径，转换为服务器 URL
      let photoPath = item.photo_path || ''
      if (photoPath) {
        // 检查是否是本地磁盘路径（Windows 或 Unix）
        if (photoPath.startsWith('C:\\') || 
            (photoPath.startsWith('/') && !photoPath.startsWith('/uploads'))) {
          // 提取文件名，构建正确的 URL
          const filename = photoPath.split(/[\\/]/).pop()
          // 尝试从路径中提取年份和月份，如果提取失败则使用当前日期
          let year = new Date().getFullYear()
          let month = String(new Date().getMonth() + 1).padStart(2, '0')
          
          // 尝试从路径中提取年份和月份（如：...\photos\2026\03\xxx.jpg）
          const pathParts = photoPath.split(/[\\/]/)
          const yearIndex = pathParts.findIndex(p => p === 'photos')
          if (yearIndex !== -1 && yearIndex + 2 < pathParts.length) {
            year = pathParts[yearIndex + 1]
            month = pathParts[yearIndex + 2]
          }
          
          photoPath = `/uploads/photos/${year}/${month}/${filename}`
        }
        // 转换为完整 URL
        photoPath = api.resolveStaticUrl(photoPath)
      }
      
      // 查找分类
      const categories = this.data.categories
      const categoryId = item.category_id != null ? item.category_id : ''
      const selectedCategory = categoryId 
        ? categories.find(c => Number(c.id) === Number(categoryId)) || null
        : null
      
      // 扩展字段
      const extensionFields = (selectedCategory && selectedCategory.extension_fields) || []
      const ext = item.extension || {}
      const extensionValues = {}
      Object.keys(ext).forEach(key => {
        if (ext[key] != null && String(ext[key]).trim() !== '') {
          extensionValues[key] = ext[key]
        }
      })
      
      this.setData({
        'formData.name': item.name || '',
        'formData.location': item.location || '',
        'formData.description': item.description || '',
        'formData.category_id': categoryId,
        'formData.photo_path': photoPath,
        selectedCategory,
        extensionFields,
        extensionValues,
        loading: false
      })
    } catch (err) {
      console.error('加载物品数据失败', err)
      this.setData({ loading: false })
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
    }
  },

  /**
   * 输入物品名称
   */
  onNameInput(e) {
    let value = e.detail.value
    if (value.length > 13) {
      value = value.substring(0, 13)
      wx.showToast({
        title: '最多 13 个字',
        icon: 'none'
      })
    }
    this.setData({
      'formData.name': value,
      nameLengthWarn: value.length > 10
    })
  },

  /**
   * 输入存放位置
   */
  onLocationInput(e) {
    this.setData({
      'formData.location': e.detail.value
    })
  },

  /**
   * 输入描述
   */
  onDescriptionInput(e) {
    this.setData({
      'formData.description': e.detail.value
    })
  },

  /**
   * 选择分类
   */
  onChooseCategory() {
    const categories = this.data.categories
    const categoryNames = categories.map(c => c.name)
    
    wx.showActionSheet({
      itemList: categoryNames,
      success: (res) => {
        const selected = categories[res.tapIndex]
        this.setData({
          selectedCategory: selected,
          'formData.category_id': selected.id,
          extensionFields: selected.extension_fields || []
        })
      }
    })
  },

  /**
   * 选择/更换图片
   */
  onChoosePhoto() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['camera', 'album'],
      success: (res) => {
        this.setData({
          'formData.photo_path': res.tempFiles[0].tempFilePath
        })
      }
    })
  },

  /**
   * 日期选择
   */
  onDateChange(e) {
    const { field } = e.currentTarget.dataset
    this.setData({
      [`extensionValues.${field}`]: e.detail.value
    })
  },

  /**
   * 扩展字段输入
   */
  onExtInput(e) {
    const { field } = e.currentTarget.dataset
    this.setData({
      [`extensionValues.${field}`]: e.detail.value
    })
  },

  /**
   * 取消编辑
   */
  onCancel() {
    wx.navigateBack()
  },

  /**
   * 保存修改
   */
  async onSave() {
    const { formData, extensionValues, itemId } = this.data
    
    // 验证必填项
    if (!formData.name.trim()) {
      wx.showToast({
        title: '请输入物品名称',
        icon: 'none'
      })
      return
    }
    
    if (formData.name.length > 13) {
      wx.showToast({
        title: '物品名不能超过 13 个字',
        icon: 'none'
      })
      return
    }
    
    if (!formData.location.trim()) {
      wx.showToast({
        title: '请输入存放位置',
        icon: 'none'
      })
      return
    }
    
    this.setData({ submitting: true })
    
    try {
      // 构建更新数据
      const payload = {
        name: formData.name.trim(),
        location: formData.location.trim(),
        description: (formData.description || '').trim(),
        category_id: formData.category_id || null
      }
      
      // 添加扩展信息
      const cleanExt = {}
      Object.keys(extensionValues).forEach(key => {
        const val = extensionValues[key]
        if (val != null && String(val).trim() !== '') {
          cleanExt[key] = val
        }
      })
      
      if (Object.keys(cleanExt).length > 0) {
        payload.extension = cleanExt
      }
      
      // 调用更新 API
      await api.updateItem(itemId, payload)
      
      wx.showToast({
        title: '保存成功',
        icon: 'success'
      })
      
      // 延迟返回，让用户看到成功提示
      setTimeout(() => {
        // 通知详情页刷新（通过事件通道）
        const eventChannel = this.getOpenerEventChannel()
        if (eventChannel) {
          eventChannel.emit('refreshItem', { itemId, success: true })
        }
        
        wx.navigateBack()
      }, 1500)
    } catch (err) {
      console.error('保存失败', err)
      wx.showToast({
        title: err.message || '保存失败',
        icon: 'none'
      })
    } finally {
      this.setData({ submitting: false })
    }
  }
})
