Component({
  properties: {
    total: { type: Number, value: 0 },
    page: { type: Number, value: 0 },
    pageSize: { type: Number, value: 20 },
    loading: { type: Boolean, value: false },
    hasMore: { type: Boolean, value: false },
  },

  methods: {
    onLoadMore() {
      if (this.data.loading || !this.data.hasMore) return
      this.triggerEvent('loadmore')
    },
  },
})
