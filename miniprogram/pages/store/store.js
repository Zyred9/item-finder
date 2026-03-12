/**
 * 存物页面
 */
const api = require('../../utils/api')
const util = require('../../utils/util')

// 图片/语音识别出的扩展字段若当前分类未配置，用此配置展示（保证「扩展信息」区块可见）
const DEFAULT_EXTENSION_FIELD_CONFIGS = [
  { name: 'expire_date', label: '过期日期', type: 'date', required: false },
  { name: 'production_date', label: '生产日期', type: 'date', required: false },
  { name: 'warranty_date', label: '保修到期日', type: 'date', required: false },
  { name: 'shelf_life_days', label: '保质期(天)', type: 'number', required: false },
  { name: 'open_date', label: '开封日期', type: 'date', required: false },
  { name: 'open_shelf_life', label: '开封后保质(天)', type: 'number', required: false }
]

Page({
  data: {
    // 编辑模式
    editItemId: '',
    
    // 表单数据
    formData: {
      name: '',
      location: '',
      description: '',
      category_id: '',
      photo_path: ''
    },
    
    // 分类
    categories: [],
    selectedCategory: null,
    extensionFields: [],
    
    // 扩展字段值
    extensionValues: {},
    /** 扩展信息：凭证照（拍照） */
    extensionPhotoPath: '',
    /** 扩展信息：语音补充（语音识别结果，可编辑） */
    extensionVoiceText: '',
    /** 扩展信息：是否正在录扩展语音 */
    isRecordingExtension: false,
    /** 扩展语音识别结果是否已展示 */
    showExtensionVoiceResult: false,
    /** 主图理解给出的分类建议（文本，未匹配到分类时展示） */
    suggestedCategoryName: '',
    
    // 状态
    isRecording: false,
    submitting: false,
    /** 语音识别原文（仅识别到内容后才展示块） */
    voiceResultText: '',
    showVoiceResult: false
  },

  async onLoad(options) {
    await this.loadCategories()
    const id = options.id
    if (id) {
      this.setData({ editItemId: id })
      await this.loadItemForEdit(id)
    }
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
   * 编辑模式：拉取物品并回填表单
   */
  async loadItemForEdit(itemId) {
    try {
      wx.showLoading({ title: '加载中...' })
      const item = await api.getItem(itemId)
      wx.hideLoading()
      if (!item) {
        wx.showToast({ title: '物品不存在', icon: 'none' })
        return
      }
      const categories = this.data.categories || []
      const categoryId = item.category_id != null ? item.category_id : ''
      const selectedCategory = (categoryId !== '' && categoryId != null)
        ? categories.find((c) => Number(c.id) === Number(categoryId)) || null
        : null
      const extensionFields = (selectedCategory && selectedCategory.extension_fields) || []
      const ext = item.extension && typeof item.extension === 'object' ? item.extension : {}
      const extensionValues = {}
      Object.keys(ext).forEach((k) => {
        const v = ext[k]
        if (v != null && String(v).trim() !== '') {
          extensionValues[k] = v
        }
      })
      this.setData({
        formData: {
          name: item.name || '',
          location: item.location || '',
          description: (item.description || '').trim(),
          category_id: categoryId,
          photo_path: api.resolveStaticUrl(item.photo_path) || ''
        },
        selectedCategory,
        extensionFields,
        extensionValues
      })
    } catch (err) {
      wx.hideLoading()
      console.error('加载物品失败', err)
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  /**
   * 输入物品名
   */
  onNameInput(e) {
    this.setData({ 'formData.name': e.detail.value })
  },

  /**
   * 输入位置
   */
  onLocationInput(e) {
    this.setData({ 'formData.location': e.detail.value })
  },

  /**
   * 输入描述
   */
  onDescInput(e) {
    this.setData({ 'formData.description': e.detail.value })
  },

  /**
   * 拍照（主图），可选调用主图理解填充名称/分类建议
   */
  onTakePhoto() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['camera', 'album'],
      success: async (res) => {
        const tempFilePath = res.tempFiles[0].tempFilePath
        this.setData({ 'formData.photo_path': tempFilePath })
        wx.showLoading({ title: '识别中...', mask: true })
        try {
          const out = await api.photoUnderstand(tempFilePath)
          const name = (out && out.suggested_name) || ''
          const categorySuggestion = (out && out.suggested_category) || ''
          const suggestedExt = (out && out.suggested_extension) && typeof out.suggested_extension === 'object' ? out.suggested_extension : {}
          const hasAny = name || categorySuggestion || Object.keys(suggestedExt).length > 0
          if (hasAny) {
            const updates = {}
            if (name) updates['formData.name'] = name
            const categories = this.data.categories || []
            const match = categories.find(
              (c) => c.name && categorySuggestion && c.name.includes(categorySuggestion)
            )
            if (match) {
              updates['formData.category_id'] = match.id
              updates.selectedCategory = match
              updates.extensionFields = match.extension_fields || []
            }
            if (categorySuggestion && !match) {
              updates.suggestedCategoryName = categorySuggestion
            }
            if (Object.keys(suggestedExt).length > 0) {
              updates.extensionValues = { ...(this.data.extensionValues || {}), ...suggestedExt }
              // 识别出扩展字段时，确保「扩展信息」区块展示：当前分类若无对应配置则补默认配置
              const baseFields = updates.extensionFields !== undefined ? updates.extensionFields : (this.data.extensionFields || [])
              const existingNames = baseFields.map((f) => f.name)
              const toAdd = DEFAULT_EXTENSION_FIELD_CONFIGS.filter(
                (d) => suggestedExt[d.name] !== undefined && existingNames.indexOf(d.name) === -1
              )
              updates.extensionFields = baseFields.concat(toAdd)
            }
            this.setData(updates)
            if (name) wx.showToast({ title: '已识别建议名称', icon: 'success' })
            else if (Object.keys(suggestedExt).length > 0) wx.showToast({ title: '已识别日期等信息', icon: 'success' })
          }
        } catch (e) {
          console.warn('主图理解未启用或失败', e)
        } finally {
          wx.hideLoading()
        }
      }
    })
  },

  /**
   * 语音输入
   */
  onStartRecord() {
    this.setData({ isRecording: true })
    
    wx.startRecord({
      success: (res) => {
        const tempFilePath = res.tempFilePath
        this.recognizeVoice(tempFilePath)
      },
      fail: (err) => {
        console.error('录音失败', err)
        this.setData({ isRecording: false })
      }
    })
  },

  onStopRecord() {
    wx.stopRecord()
    this.setData({ isRecording: false })
  },

  /**
   * 扩展信息 - 拍照（凭证/说明书等）
   */
  onExtensionPhoto() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['camera', 'album'],
      success: (res) => {
        const tempFilePath = res.tempFiles[0].tempFilePath
        this.setData({ extensionPhotoPath: tempFilePath })
      }
    })
  },

  /**
   * 扩展凭证照 - 提取文字（OCR）
   */
  async onExtensionOcr() {
    const path = this.data.extensionPhotoPath
    if (!path) {
      wx.showToast({ title: '请先拍摄或选择凭证照', icon: 'none' })
      return
    }
    try {
      wx.showLoading({ title: '提取中...', mask: true })
      const out = await api.photoOcr(path)
      wx.hideLoading()
      const text = (out && out.text && String(out.text).trim()) || ''
      if (text) {
        const prev = this.data.extensionVoiceText || ''
        const setData = {
          extensionVoiceText: prev ? `${prev}\n${text}` : text,
          showExtensionVoiceResult: true
        }
        const suggestedExt = (out && out.suggested_extension) && typeof out.suggested_extension === 'object' ? out.suggested_extension : {}
        if (Object.keys(suggestedExt).length > 0) {
          setData.extensionValues = { ...(this.data.extensionValues || {}), ...suggestedExt }
          const baseFields = this.data.extensionFields || []
          const existingNames = baseFields.map((f) => f.name)
          const toAdd = DEFAULT_EXTENSION_FIELD_CONFIGS.filter(
            (d) => suggestedExt[d.name] !== undefined && existingNames.indexOf(d.name) === -1
          )
          if (toAdd.length > 0) setData.extensionFields = baseFields.concat(toAdd)
        }
        this.setData(setData)
        wx.showToast({ title: Object.keys(suggestedExt).length > 0 ? '已提取文字并识别日期' : '已提取文字', icon: 'success' })
      } else {
        wx.showToast({ title: '未识别到文字', icon: 'none' })
      }
    } catch (e) {
      wx.hideLoading()
      wx.showToast({ title: e.message || 'OCR 失败', icon: 'none' })
    }
  },

  /**
   * 扩展信息 - 语音开始（保存路径，松开发送后识别）
   */
  onExtensionVoiceStart() {
    this.setData({ isRecordingExtension: true })
    this._extensionRecordPath = null
    wx.startRecord({
      success: (res) => {
        if (res && res.tempFilePath) this._extensionRecordPath = res.tempFilePath
      },
      fail: () => {
        this.setData({ isRecordingExtension: false })
      }
    })
  },

  onExtensionVoiceEnd() {
    wx.stopRecord()
    this.setData({ isRecordingExtension: false })
    const path = this._extensionRecordPath
    if (path) {
      setTimeout(() => this.recognizeExtensionVoice(path), 300)
    }
    this._extensionRecordPath = null
  },

  async recognizeExtensionVoice(filePath) {
    wx.showLoading({ title: '识别中...', mask: true })
    try {
      const result = await api.uploadVoice(filePath, 'store')
      const text = (result && result.text && String(result.text).trim()) || ''
      if (text) {
        const updates = { extensionVoiceText: text, showExtensionVoiceResult: true }
        if (result.entities) {
          const extKeys = ['expire_date', 'production_date', 'shelf_life_days', 'open_date', 'open_shelf_life', 'warranty_date']
          const entityExt = {}
          extKeys.forEach((k) => {
            if (result.entities[k] !== undefined && result.entities[k] !== null && result.entities[k] !== '') {
              entityExt[k] = result.entities[k]
            }
          })
          if (Object.keys(entityExt).length > 0) {
            updates.extensionValues = { ...(this.data.extensionValues || {}), ...entityExt }
            const baseFields = this.data.extensionFields || []
            const existingNames = baseFields.map((f) => f.name)
            const toAdd = DEFAULT_EXTENSION_FIELD_CONFIGS.filter(
              (d) => entityExt[d.name] !== undefined && existingNames.indexOf(d.name) === -1
            )
            if (toAdd.length > 0) updates.extensionFields = baseFields.concat(toAdd)
          }
        }
        this.setData(updates)
        wx.showToast({ title: updates.extensionValues ? '已识别（含日期）' : '已识别', icon: 'success' })
      }
    } catch (err) {
      console.error('扩展语音识别失败', err)
    } finally {
      wx.hideLoading()
    }
  },

  onExtensionVoiceInput(e) {
    this.setData({ extensionVoiceText: e.detail.value })
  },

  /**
   * 语音识别（主表单）
   */
  async recognizeVoice(filePath) {
    wx.showLoading({ title: '识别中...', mask: true })
    try {
      const result = await api.uploadVoice(filePath, 'store')
      const text = (result && result.text && String(result.text).trim()) || ''
      if (text) {
        const updates = { voiceResultText: text, showVoiceResult: true }
        let toastTitle = '已识别'
        if (result.entities) {
          const e = result.entities
          const itemName = e.item_name || ''
          const location = e.location || ''
          const description = e.description || result.text
          const categoryName = e.category_name || ''
          if (itemName) updates['formData.name'] = itemName
          if (location) updates['formData.location'] = location
          if (description) updates['formData.description'] = description

          const categories = this.data.categories || []
          const match = categories.find(
            (c) => c.name && categoryName && (c.name === categoryName || c.name.includes(categoryName) || categoryName.includes(c.name))
          )
          if (match) {
            updates['formData.category_id'] = match.id
            updates.selectedCategory = match
            updates.extensionFields = match.extension_fields || []
            updates.suggestedCategoryName = ''
          } else if (categoryName) {
            updates.suggestedCategoryName = categoryName
            toastTitle = '已识别，含分类建议'
          }
          const extKeys = ['expire_date', 'production_date', 'shelf_life_days', 'open_date', 'open_shelf_life', 'warranty_date']
          const entityExt = {}
          extKeys.forEach((k) => {
            if (e[k] !== undefined && e[k] !== null && e[k] !== '') entityExt[k] = e[k]
          })
          if (Object.keys(entityExt).length > 0) {
            updates.extensionValues = { ...(this.data.extensionValues || {}), ...entityExt }
            toastTitle = '已识别（含过期/保修日期）'
            const baseFields = updates.extensionFields !== undefined ? updates.extensionFields : (this.data.extensionFields || [])
            const existingNames = baseFields.map((f) => f.name)
            const toAdd = DEFAULT_EXTENSION_FIELD_CONFIGS.filter(
              (d) => entityExt[d.name] !== undefined && existingNames.indexOf(d.name) === -1
            )
            updates.extensionFields = baseFields.concat(toAdd)
          }
        }
        this.setData(updates)
        wx.showToast({ title: toastTitle, icon: 'success' })
      } else {
        wx.showToast({ title: '无法识别出文字', icon: 'none' })
      }
    } catch (err) {
      console.error('语音识别失败', err)
      const msg = (err && err.message) || '识别失败'
      wx.showToast({ title: msg, icon: 'none' })
    } finally {
      wx.hideLoading()
    }
  },

  /**
   * 选择分类（picker 返回的是 range 的索引）
   */
  onCategoryChange(e) {
    const index = parseInt(e.detail.value, 10)
    const categories = this.data.categories
    const category = categories[index] || null
    this.setData({
      'formData.category_id': category ? category.id : '',
      selectedCategory: category,
      extensionFields: (category && category.extension_fields) || [],
      suggestedCategoryName: ''
    })
  },

  /**
   * 扩展字段输入（picker 为索引，需转为选项值）
   */
  onExtensionInput(e) {
    const { field } = e.currentTarget.dataset
    const value = e.detail.value
    const ext = (this.data.extensionFields || []).find(f => f.name === field)
    const options = ext && ext.options
    const finalValue = (Array.isArray(options) && options[value] != null)
      ? (typeof options[value] === 'object' ? options[value].label : options[value])
      : value
    this.setData({
      [`extensionValues.${field}`]: finalValue
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
   * 提交表单（新建或编辑）
   */
  async onSubmit() {
    const { formData, extensionValues, extensionVoiceText, editItemId } = this.data

    if (!api.getFamilyId()) {
      wx.showToast({ title: '请先加入或创建家庭', icon: 'none' })
      setTimeout(() => {
        wx.switchTab({ url: '/pages/family/family' })
      }, 1500)
      return
    }
    if (!formData.name.trim()) {
      wx.showToast({ title: '请输入物品名', icon: 'none' })
      return
    }
    if (!formData.location.trim()) {
      wx.showToast({ title: '请输入存放位置', icon: 'none' })
      return
    }

    this.setData({ submitting: true })

    try {
      let photoPath = formData.photo_path
      if (photoPath && photoPath.startsWith('wxfile://')) {
        // TODO: 上传照片
      }

      let description = (formData.description || '').trim()
      if (extensionVoiceText && extensionVoiceText.trim()) {
        description = description ? description + '\n[扩展补充] ' + extensionVoiceText.trim() : '[扩展补充] ' + extensionVoiceText.trim()
      }

      const payload = {
        name: formData.name,
        location: formData.location,
        description: description || undefined,
        category_id: formData.category_id || null,
        photo_path: photoPath,
        extension: Object.keys(extensionValues).length > 0 ? extensionValues : null
      }

      if (editItemId) {
        await api.updateItem(editItemId, payload)
        wx.showToast({ title: '修改成功', icon: 'success' })
        setTimeout(() => wx.navigateBack(), 1500)
        return
      }

      await api.createItem(payload)
      wx.showToast({ title: '保存成功', icon: 'success' })

      this.setData({
        formData: {
          name: '',
          location: '',
          description: '',
          category_id: '',
          photo_path: ''
        },
        selectedCategory: null,
        extensionFields: [],
        extensionValues: {},
        voiceResultText: '',
        showVoiceResult: false,
        extensionPhotoPath: '',
        extensionVoiceText: '',
        showExtensionVoiceResult: false
      })
    } catch (err) {
      console.error('保存失败', err)
      wx.showToast({ title: '保存失败', icon: 'none' })
    } finally {
      this.setData({ submitting: false })
    }
  }
})