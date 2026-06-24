const { get } = require('../../utils/api')
const { buildDateParams, formatMoney } = require('../../utils/util')
const { getCurrentUser, isAdmin } = require('../../utils/auth')

Page({
  data: {
    user: null,
    period: 'all',
    dateFrom: '',
    dateTo: '',
    stats: {
      total_orders: 0,
      total_profit: 0,
      total_actual_profit: 0,
      total_cost: 0,
      total_buy_price: 0,
      returned_count: 0,
      unreturned_count: 0,
      return_rate: 0,
      shipping_count: 0,
      delivered_count: 0,
    },
    recentRecords: [],
    loading: true,
    isAdmin: false,
  },

  onShow() {
    const user = getCurrentUser()
    if (!user) {
      wx.reLaunch({ url: '/pages/login/index' })
      return
    }
    this.setData({ user, isAdmin: isAdmin() })
    this.loadData()
  },

  onPullDownRefresh() {
    this.loadData().finally(() => wx.stopPullDownRefresh())
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const dateParams = buildDateParams(this.data.period, this.data.dateFrom, this.data.dateTo)
      const [statsRes, recordsRes] = await Promise.all([
        get('/api/stats', dateParams),
        get('/api/records', { ...dateParams, page: 1, page_size: 10 }),
      ])
      this.setData({
        stats: statsRes.data || {},
        recentRecords: recordsRes.data || [],
        loading: false,
      })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  setPeriod(e) {
    const period = e.currentTarget.dataset.period
    this.setData({ period })
    if (period !== 'custom') {
      this.loadData()
    }
  },

  onDateFromChange(e) {
    this.setData({ dateFrom: e.detail.value })
    if (this.data.dateFrom && this.data.dateTo) this.loadData()
  },

  onDateToChange(e) {
    this.setData({ dateTo: e.detail.value })
    if (this.data.dateFrom && this.data.dateTo) this.loadData()
  },

  onRecordTap(e) {
    wx.navigateTo({ url: `/pages/record-detail/index?id=${e.detail.id}` })
  },

  goAdmin() {
    wx.navigateTo({ url: '/pages/admin/index' })
  },

  formatMoney(val) { return formatMoney(val) },
})
