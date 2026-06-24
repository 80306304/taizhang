const { get, post } = require('../../utils/api')
const { debounce } = require('../../utils/util')
const { PAGE_SIZE } = require('../../utils/constants')

Page({
  data: {
    records: [],
    total: 0,
    page: 1,
    hasMore: false,
    loading: true,
    searchKey: '',
    filter: 'all',
    smartInput: '',
    syncing: false,
    // Filter options for chips
    filterOptions: [
      { value: 'all', label: '全部' },
      { value: '0', label: '未回款' },
      { value: '1', label: '已回款' },
    ],
  },

  _debounceTimer: null,

  onShow() {
    const app = getApp()
    if (!app.globalData.isLoggedIn) {
      wx.reLaunch({ url: '/pages/login/index' })
      return
    }
    // 从子页面返回时刷新
    if (this._needRefresh) {
      this._needRefresh = false
      this.loadRecords(true)
    }
  },

  onLoad() {
    this.loadRecords(true)
  },

  onPullDownRefresh() {
    this.loadRecords(true).finally(() => wx.stopPullDownRefresh())
  },

  onReachBottom() {
    if (this.data.records.length < this.data.total) {
      this.loadRecords(false)
    }
  },

  async loadRecords(reset) {
    if (reset) {
      this.setData({ page: 1, loading: true })
    }
    const { page, searchKey, filter } = this.data
    const params = { page, page_size: PAGE_SIZE }
    if (searchKey) params.search = searchKey
    if (filter !== 'all') params.is_returned = parseInt(filter)

    try {
      const res = await get('/api/records', params)
      const newRecords = reset ? (res.data || []) : [...this.data.records, ...(res.data || [])]
      const total = res.total || 0
      this.setData({
        records: newRecords,
        total,
        hasMore: newRecords.length < total,
        page: page + 1,
        loading: false,
      })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  // Search with debounce
  onSearchInput(e) {
    this.setData({ searchKey: e.detail.value })
    if (this._debounceTimer) clearTimeout(this._debounceTimer)
    this._debounceTimer = setTimeout(() => {
      this.loadRecords(true)
    }, 300)
  },

  // Filter chips
  onFilterChange(e) {
    this.setData({ filter: e.detail.value })
    this.loadRecords(true)
  },

  // Smart input
  onSmartInput(e) {
    this.setData({ smartInput: e.detail.value })
  },

  async parseSmartInput() {
    const text = this.data.smartInput.trim()
    if (!text) {
      wx.showToast({ title: '请输入内容', icon: 'none' })
      return
    }
    try {
      const res = await post('/api/records/parse', { text })
      // Navigate to form with parsed data
      const data = encodeURIComponent(JSON.stringify(res.data))
      this._needRefresh = true
      wx.navigateTo({ url: `/pages/record-form/index?parsed=${data}` })
    } catch (e) {
      // Error already handled by api.js
    }
  },

  async parseAndSave() {
    const text = this.data.smartInput.trim()
    if (!text) {
      wx.showToast({ title: '请输入内容', icon: 'none' })
      return
    }
    wx.showLoading({ title: '解析中...' })
    try {
      const parseRes = await post('/api/records/parse', { text })
      const record = parseRes.data
      record.raw_input = text
      await post('/api/records', record)
      wx.showToast({ title: '保存成功', icon: 'success' })
      this.setData({ smartInput: '' })
      this.loadRecords(true)
    } catch (e) {
      // Error handled
    } finally {
      wx.hideLoading()
    }
  },

  // Actions
  goAdd() {
    this._needRefresh = true
    wx.navigateTo({ url: '/pages/record-form/index' })
  },

  goImport() {
    this._needRefresh = true
    wx.navigateTo({ url: '/pages/import/index' })
  },

  onRecordTap(e) {
    wx.navigateTo({ url: `/pages/record-detail/index?id=${e.detail.id}` })
  },

  onRecordEdit(e) {
    this._needRefresh = true
    wx.navigateTo({ url: `/pages/record-form/index?id=${e.detail.id}` })
  },

  onRecordDelete(e) {
    const id = e.detail.id
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条记录吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await require('../../utils/api').del(`/api/records/${id}`)
            wx.showToast({ title: '删除成功', icon: 'success' })
            this.loadRecords(true)
          } catch (e) {}
        }
      },
    })
  },

  onRecordReturn(e) {
    const id = e.detail.id
    wx.showModal({
      title: '标记回款',
      content: '确定将此记录标记为已回款？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await require('../../utils/api').put(`/api/records/${id}`, { is_returned: 1 })
            wx.showToast({ title: '已标记回款', icon: 'success' })
            this.loadRecords(true)
          } catch (e) {}
        }
      },
    })
  },

  onRecordTracking(e) {
    const id = e.detail.id
    wx.navigateTo({ url: `/pages/tracking-detail/index?recordId=${id}` })
  },

  async syncTracking() {
    this.setData({ syncing: true })
    try {
      const res = await post('/api/tracking/sync')
      wx.showToast({ title: res.data?.message || '同步完成', icon: 'success' })
      this.loadRecords(true)
    } catch (e) {
      // handled
    } finally {
      this.setData({ syncing: false })
    }
  },

  refresh() {
    this.loadRecords(true)
  },
})
