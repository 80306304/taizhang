const { upload, download } = require('../../utils/api')

Page({
  data: {
    selectedFile: null, // {name, size, path}
    importing: false,
    result: null,
  },

  onLoad() {},

  // Download template
  async downloadTemplate() {
    wx.showLoading({ title: '下载中...' })
    try {
      const filePath = await download('/api/records/import/template')
      wx.openDocument({
        filePath,
        showMenu: true,
        success() {
          wx.showToast({ title: '模板已打开', icon: 'success' })
        },
        fail() {
          wx.showToast({ title: '请安装WPS等应用打开', icon: 'none' })
        },
      })
    } catch (e) {
      wx.showToast({ title: '下载失败', icon: 'none' })
    } finally {
      wx.hideLoading()
    }
  },

  // Choose file from WeChat chat
  chooseFile() {
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['xlsx', 'xls'],
      success: (res) => {
        const file = res.tempFiles[0]
        this.setData({
          selectedFile: {
            name: file.name,
            size: (file.size / 1024).toFixed(1) + ' KB',
            path: file.path,
          },
          result: null,
        })
      },
      fail: () => {
        // User cancelled
      },
    })
  },

  // Upload and import
  async doImport() {
    if (!this.data.selectedFile) {
      wx.showToast({ title: '请先选择文件', icon: 'none' })
      return
    }
    this.setData({ importing: true, result: null })
    try {
      const res = await upload('/api/records/import', this.data.selectedFile.path)
      const data = res.data || {}
      this.setData({
        result: {
          success: true,
          message: data.message || '导入完成',
          imported: data.imported || 0,
          skipped: data.skipped || 0,
          errors: data.errors || [],
        },
      })
      wx.showToast({ title: data.message || '导入成功', icon: 'success' })
    } catch (e) {
      this.setData({
        result: { success: false, message: e.message || '导入失败' },
      })
    } finally {
      this.setData({ importing: false })
    }
  },

  clearFile() {
    this.setData({ selectedFile: null, result: null })
  },
})
