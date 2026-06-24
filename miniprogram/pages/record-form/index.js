const { get, post, put } = require('../../utils/api')

Page({
  data: {
    isEdit: false,
    recordId: null,
    form: {
      customer: '',
      product: '',
      cost_price: '',
      buy_price: '',
      other_income: '0',
      actual_profit: '',
      tracking_no: '',
      tracking_company: '',
      is_returned: 0,
      returned_at: '',
      created_at: '',
      note: '',
    },
    companies: [], // [{code, name}]
    companyNames: [],
    companyCodes: [],
    companyIndex: 0,
    submitting: false,
    previewProfit: '0.00',
  },

  async onLoad(options) {
    // Load companies list
    try {
      const res = await get('/api/tracking/companies')
      const data = res.data || {}
      const codes = Object.keys(data)
      const names = codes.map(c => data[c])
      this.setData({ companies: data, companyCodes: codes, companyNames: names })
    } catch (e) {}

    // Edit mode: load existing record
    if (options.id) {
      this.setData({ isEdit: true, recordId: parseInt(options.id) })
      wx.setNavigationBarTitle({ title: '编辑记录' })
      await this.loadRecord(options.id)
    } else {
      wx.setNavigationBarTitle({ title: '新增记录' })
    }

    // Parse mode: pre-fill from smart input
    if (options.parsed) {
      try {
        const parsed = JSON.parse(decodeURIComponent(options.parsed))
        const form = { ...this.data.form }
        if (parsed.customer) form.customer = parsed.customer
        if (parsed.product) form.product = parsed.product
        if (parsed.cost_price) form.cost_price = String(parsed.cost_price)
        if (parsed.buy_price) form.buy_price = String(parsed.buy_price)
        if (parsed.other_income) form.other_income = String(parsed.other_income)
        if (parsed.tracking_no) form.tracking_no = parsed.tracking_no
        if (parsed.tracking_company) {
          const idx = this.data.companyCodes.indexOf(parsed.tracking_company)
          if (idx >= 0) this.setData({ companyIndex: idx })
          form.tracking_company = parsed.tracking_company
        }
        if (parsed.is_returned) form.is_returned = parsed.is_returned
        if (parsed.created_at) form.created_at = parsed.created_at.slice(0, 10)
        if (parsed.note) form.note = parsed.note
        this.setData({ form })
        this.updatePreviewProfit()
      } catch (e) {}
    }
  },

  async loadRecord(id) {
    try {
      // Fetch all records and find by id (no single-record endpoint)
      const res = await get('/api/records', { search: '', page: 1, page_size: 100 })
      const record = (res.data || []).find(r => r.id === parseInt(id))
      if (!record) {
        wx.showToast({ title: '记录不存在', icon: 'none' })
        setTimeout(() => wx.navigateBack(), 1500)
        return
      }
      const form = {
        customer: record.customer || '',
        product: record.product || '',
        cost_price: String(record.cost_price || ''),
        buy_price: String(record.buy_price || ''),
        other_income: String(record.other_income || '0'),
        actual_profit: String(record.actual_profit || ''),
        tracking_no: record.tracking_no || '',
        tracking_company: record.tracking_company || '',
        is_returned: record.is_returned || 0,
        returned_at: (record.returned_at || '').slice(0, 10),
        created_at: (record.created_at || '').slice(0, 10),
        note: record.note || '',
      }
      const idx = this.data.companyCodes.indexOf(record.tracking_company)
      if (idx >= 0) this.setData({ companyIndex: idx })
      this.setData({ form })
      this.updatePreviewProfit()
    } catch (e) {
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  // Input handlers
  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
    if (field === 'cost_price' || field === 'buy_price' || field === 'other_income') {
      this.updatePreviewProfit()
    }
  },

  onReturnChange(e) {
    this.setData({ 'form.is_returned': e.detail.value === '0' ? 0 : 1 })
  },

  onCompanyChange(e) {
    const idx = e.detail.value
    this.setData({
      companyIndex: idx,
      'form.tracking_company': this.data.companyCodes[idx],
    })
  },

  onDateChange(e) {
    this.setData({ 'form.created_at': e.detail.value })
  },

  onReturnDateChange(e) {
    this.setData({ 'form.returned_at': e.detail.value })
  },

  updatePreviewProfit() {
    const cost = parseFloat(this.data.form.cost_price) || 0
    const buy = parseFloat(this.data.form.buy_price) || 0
    const other = parseFloat(this.data.form.other_income) || 0
    this.setData({ previewProfit: (buy - cost + other).toFixed(2) })
  },

  async doSave() {
    const { form, isEdit, recordId } = this.data

    // Basic validation
    if (!form.customer && !form.product) {
      wx.showToast({ title: '请输入客户或商品', icon: 'none' })
      return
    }

    const data = {
      customer: form.customer,
      product: form.product,
      cost_price: parseFloat(form.cost_price) || 0,
      buy_price: parseFloat(form.buy_price) || 0,
      other_income: parseFloat(form.other_income) || 0,
      actual_profit: parseFloat(form.actual_profit) || 0,
      tracking_no: form.tracking_no,
      tracking_company: form.tracking_company,
      is_returned: form.is_returned,
      returned_at: form.returned_at || null,
      note: form.note,
    }
    if (form.created_at) data.created_at = form.created_at

    this.setData({ submitting: true })
    try {
      if (isEdit) {
        await put(`/api/records/${recordId}`, data)
        wx.showToast({ title: '更新成功', icon: 'success' })
      } else {
        await post('/api/records', data)
        wx.showToast({ title: '创建成功', icon: 'success' })
      }
      setTimeout(() => wx.navigateBack(), 800)
    } catch (e) {
      // handled by api.js
    } finally {
      this.setData({ submitting: false })
    }
  },

  doCancel() {
    wx.navigateBack()
  },
})
