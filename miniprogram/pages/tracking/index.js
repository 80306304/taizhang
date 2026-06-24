const { get, post, put } = require('../../utils/api')
const { isAdmin } = require('../../utils/auth')

Page({
  data: {
    companies: {},
    companyNames: [],
    companyCodes: [],
    companyIndex: 0,
    trackingNo: '',
    recordId: '',
    cron: '',
    isAdmin: false,
    loading: false,
  },

  onShow() {
    const app = getApp()
    if (!app.globalData.isLoggedIn) {
      wx.reLaunch({ url: '/pages/login/index' })
      return
    }
    this.setData({ isAdmin: isAdmin() })
    this.loadCompanies()
    if (this.data.isAdmin) this.loadCron()
  },

  async loadCompanies() {
    try {
      const res = await get('/api/tracking/companies')
      const data = res.data || {}
      const codes = Object.keys(data)
      const names = codes.map(c => data[c])
      this.setData({ companies: data, companyCodes: codes, companyNames: names })
    } catch (e) {}
  },

  async loadCron() {
    try {
      const res = await get('/api/tracking/cron')
      this.setData({ cron: res.data?.cron || '' })
    } catch (e) {}
  },

  onRecordIdInput(e) { this.setData({ recordId: e.detail.value }) },
  onTrackingNoInput(e) { this.setData({ trackingNo: e.detail.value }) },
  onCompanyChange(e) { this.setData({ companyIndex: e.detail.value }) },
  onCronInput(e) { this.setData({ cron: e.detail.value }) },

  // Query by record ID
  async queryByRecord() {
    const id = this.data.recordId.trim()
    if (!id) {
      wx.showToast({ title: '请输入记录ID', icon: 'none' })
      return
    }
    wx.navigateTo({ url: `/pages/tracking-detail/index?recordId=${id}` })
  },

  // Query by company + number
  async queryManual() {
    const { companyIndex, trackingNo, companyCodes } = this.data
    const no = trackingNo.trim()
    if (!no) {
      wx.showToast({ title: '请输入快递单号', icon: 'none' })
      return
    }
    const company = companyCodes[companyIndex] || ''
    if (!company) {
      wx.showToast({ title: '请选择快递公司', icon: 'none' })
      return
    }
    this.setData({ loading: true })
    try {
      const res = await get(`/api/tracking/${company}/${no}`)
      wx.navigateTo({
        url: `/pages/tracking-detail/index?data=${encodeURIComponent(JSON.stringify(res.data))}`,
      })
    } catch (e) {
      // handled
    } finally {
      this.setData({ loading: false })
    }
  },

  // Save cron
  async saveCron() {
    const cron = this.data.cron.trim()
    if (!cron) {
      wx.showToast({ title: '请输入cron表达式', icon: 'none' })
      return
    }
    try {
      await put('/api/tracking/cron', { cron })
      wx.showToast({ title: '定时任务已更新', icon: 'success' })
    } catch (e) {}
  },
})
