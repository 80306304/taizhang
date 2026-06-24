const { get, put, del } = require('../../utils/api')
const { formatDateFull } = require('../../utils/util')

Page({
  data: {
    record: null,
    loading: true,
  },

  async onLoad(options) {
    if (!options.id) {
      wx.showToast({ title: '缺少记录ID', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1500)
      return
    }
    await this.loadRecord(parseInt(options.id))
  },

  async loadRecord(id) {
    try {
      const res = await get('/api/records', { search: '', page: 1, page_size: 100 })
      const record = (res.data || []).find(r => r.id === id)
      if (!record) {
        wx.showToast({ title: '记录不存在', icon: 'none' })
        this.setData({ loading: false })
        return
      }
      record._created_fmt = formatDateFull(record.created_at)
      record._returned_fmt = formatDateFull(record.returned_at)
      record._updated_fmt = formatDateFull(record.updated_at)
      this.setData({ record, loading: false })
      wx.setNavigationBarTitle({ title: `${record.customer} - ${record.product}` })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  doEdit() {
    wx.navigateTo({ url: `/pages/record-form/index?id=${this.data.record.id}` })
  },

  doReturn() {
    const id = this.data.record.id
    wx.showModal({
      title: '标记回款',
      content: '确定将此记录标记为已回款？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await put(`/api/records/${id}`, { is_returned: 1 })
            wx.showToast({ title: '已标记回款', icon: 'success' })
            this.loadRecord(id)
          } catch (e) {}
        }
      },
    })
  },

  doDelete() {
    const id = this.data.record.id
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条记录吗？此操作不可恢复。',
      success: async (res) => {
        if (res.confirm) {
          try {
            await del(`/api/records/${id}`)
            wx.showToast({ title: '已删除', icon: 'success' })
            setTimeout(() => wx.navigateBack(), 800)
          } catch (e) {}
        }
      },
    })
  },

  doTracking() {
    wx.navigateTo({ url: `/pages/tracking-detail/index?recordId=${this.data.record.id}` })
  },
})
