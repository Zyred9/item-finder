/**
 * 帮助与反馈 - 提交表单到后端
 */
const api = require('../../utils/api')

Page({
  data: {
    content: '',
    contact: '',
    canSubmit: false,
    submitting: false
  },

  onContentInput(e) {
    const content = (e.detail && e.detail.value) || ''
    this.setData({
      content,
      canSubmit: content.trim().length > 0
    })
  },

  onContactInput(e) {
    this.setData({ contact: (e.detail && e.detail.value) || '' })
  },

  async onSubmit() {
    const content = (this.data.content || '').trim()
    if (!content) {
      wx.showToast({ title: '请填写反馈内容', icon: 'none' })
      return
    }

    this.setData({ submitting: true })
    try {
      await api.submitFeedback(content, (this.data.contact || '').trim())
      wx.showToast({ title: '提交成功，感谢反馈', icon: 'success' })
      this.setData({ content: '', contact: '', canSubmit: false })
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
    } catch (err) {
      console.error('提交反馈失败', err)
      wx.showToast({ title: '提交失败，请重试', icon: 'none' })
    } finally {
      this.setData({ submitting: false })
    }
  }
})
