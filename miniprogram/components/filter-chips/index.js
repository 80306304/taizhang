Component({
  properties: {
    options: { type: Array, value: [] }, // [{value, label}]
    value: { type: String, value: '' },
  },

  methods: {
    onSelect(e) {
      const val = e.currentTarget.dataset.value
      this.triggerEvent('change', { value: val })
    },
  },
})
