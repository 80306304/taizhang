const { get } = require('../../utils/api')
const { trackingInfo } = require('../../utils/util')

Page({
  data: {
    result: null,
    loading: true,
    error: '',
  },

  async onLoad(options) {
    if (options.recordId) {
      await this.loadByRecordId(parseInt(options.recordId))
    } else if (options.data) {
      try {
        const data = JSON.parse(decodeURIComponent(options.data))
        this.setData({ result: data, loading: false })
      } catch (e) {
        this.setData({ error: '数据解析失败', loading: false })
      }
    }
  },

  async loadByRecordId(recordId) {
    try {
      const res = await get(`/api/tracking/status/${recordId}`)
      if (res.error) {
        this.setData({ error: res.error, loading: false })
        return
      }
      const data = res.data || {}
      // Transform history into timeline items
      if (data.history) {
        data.timeline = data.history.map(h => ({ time: h.time, context: h.context }))
      }
      this.setData({ result: data, loading: false })
    } catch (e) {
      this.setData({ error: e.message || '查询失败', loading: false })
    }
  },
})
