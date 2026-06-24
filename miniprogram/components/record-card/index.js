const { formatMoney, profitClass, trackingInfo } = require('../../utils/util')

Component({
  properties: {
    record: { type: Object, value: {} },
    showActions: { type: Boolean, value: true },
    compact: { type: Boolean, value: false },
  },

  methods: {
    formatMoney,
    profitClass,
    trackingInfo,

    onTap() {
      this.triggerEvent('tap', { id: this.data.record.id })
    },

    onEdit() {
      this.triggerEvent('edit', { id: this.data.record.id })
    },

    onDelete() {
      this.triggerEvent('delete', { id: this.data.record.id })
    },

    onReturn() {
      this.triggerEvent('return', { id: this.data.record.id })
    },

    onTracking() {
      this.triggerEvent('tracking', { id: this.data.record.id })
    },
  },
})
