const { get, put, del, post } = require('../../utils/api')
const { isAdmin } = require('../../utils/auth')

Page({
  data: {
    users: [],
    usersTotal: 0,
    usersPage: 1,
    codes: [],
    codesTotal: 0,
    codesPage: 1,
    loading: true,
    isAdmin: false,
  },

  onLoad() {
    if (!isAdmin()) {
      wx.showToast({ title: '需要管理员权限', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1500)
      return
    }
    this.setData({ isAdmin: true })
    this.loadUsers()
    this.loadCodes()
  },

  // ===== Users =====
  async loadUsers(page) {
    page = page || 1
    try {
      const res = await get('/api/admin/users', { page, page_size: 20 })
      this.setData({
        users: res.data || [],
        usersTotal: res.total || 0,
        usersPage: page,
        loading: false,
      })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  onUsersLoadMore() {
    if (this.data.users.length < this.data.usersTotal) {
      this.loadUsers(this.data.usersPage + 1)
    }
  },

  toggleRole(e) {
    const { id, role } = e.currentTarget.dataset
    const newRole = role === 'admin' ? 'user' : 'admin'
    wx.showModal({
      title: '修改角色',
      content: `确定将该用户${newRole === 'admin' ? '升为管理员' : '降为普通用户'}？`,
      success: async (res) => {
        if (res.confirm) {
          try {
            await put(`/api/admin/users/${id}/role`, { role: newRole })
            wx.showToast({ title: '角色已更新', icon: 'success' })
            this.loadUsers(this.data.usersPage)
          } catch (e) {}
        }
      },
    })
  },

  deleteUser(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '删除用户',
      content: '确定要删除此用户吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await del(`/api/admin/users/${id}`)
            wx.showToast({ title: '用户已删除', icon: 'success' })
            this.loadUsers(this.data.usersPage)
          } catch (e) {}
        }
      },
    })
  },

  // ===== Invite Codes =====
  async loadCodes(page) {
    page = page || 1
    try {
      const res = await get('/api/admin/invite-codes', { page, page_size: 20 })
      this.setData({
        codes: res.data || [],
        codesTotal: res.total || 0,
        codesPage: page,
      })
    } catch (e) {}
  },

  onCodesLoadMore() {
    if (this.data.codes.length < this.data.codesTotal) {
      this.loadCodes(this.data.codesPage + 1)
    }
  },

  async generateCode() {
    try {
      const res = await post('/api/admin/invite-codes')
      wx.showToast({ title: '注册码已生成', icon: 'success' })
      this.loadCodes(1)
    } catch (e) {}
  },

  copyCode(e) {
    const code = e.currentTarget.dataset.code
    wx.setClipboardData({
      data: code,
      success() { wx.showToast({ title: '已复制', icon: 'success' }) },
    })
  },

  deleteCode(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '删除注册码',
      content: '确定要删除此注册码？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await del(`/api/admin/invite-codes/${id}`)
            wx.showToast({ title: '已删除', icon: 'success' })
            this.loadCodes(this.data.codesPage)
          } catch (e) {}
        }
      },
    })
  },
})
