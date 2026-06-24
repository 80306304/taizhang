const { login, register } = require('../../utils/auth')

Page({
  data: {
    currentTab: 'login', // 'login' | 'register'
    username: '',
    password: '',
    confirmPassword: '',
    inviteCode: '',
    submitting: false,
    errorMsg: '',
  },

  onLoad() {
    // 如果已登录，直接跳转
    const app = getApp()
    if (app.globalData.isLoggedIn) {
      wx.switchTab({ url: '/pages/dashboard/index' })
    }
  },

  switchTab(e) {
    this.setData({ currentTab: e.currentTarget.dataset.tab, errorMsg: '' })
  },

  onUsernameInput(e) { this.setData({ username: e.detail.value, errorMsg: '' }) },
  onPasswordInput(e) { this.setData({ password: e.detail.value, errorMsg: '' }) },
  onConfirmInput(e)  { this.setData({ confirmPassword: e.detail.value, errorMsg: '' }) },
  onInviteInput(e)   { this.setData({ inviteCode: e.detail.value, errorMsg: '' }) },

  async doLogin() {
    const { username, password } = this.data
    if (!username || username.length < 2) {
      this.setData({ errorMsg: '请输入用户名（至少2个字符）' })
      return
    }
    if (!password || password.length < 6) {
      this.setData({ errorMsg: '请输入密码（至少6位）' })
      return
    }
    this.setData({ submitting: true, errorMsg: '' })
    try {
      await login(username, password)
      wx.switchTab({ url: '/pages/dashboard/index' })
    } catch (e) {
      this.setData({ errorMsg: e.message || '登录失败' })
    } finally {
      this.setData({ submitting: false })
    }
  },

  async doRegister() {
    const { username, password, confirmPassword, inviteCode } = this.data
    if (!username || username.length < 2) {
      this.setData({ errorMsg: '请输入用户名（至少2个字符）' })
      return
    }
    if (!inviteCode) {
      this.setData({ errorMsg: '请输入注册码' })
      return
    }
    if (!password || password.length < 6) {
      this.setData({ errorMsg: '请输入密码（至少6位）' })
      return
    }
    if (password !== confirmPassword) {
      this.setData({ errorMsg: '两次输入的密码不一致' })
      return
    }
    this.setData({ submitting: true, errorMsg: '' })
    try {
      await register(username, password, inviteCode)
      wx.showToast({ title: '注册成功，请登录', icon: 'success' })
      this.setData({ currentTab: 'login', password: '', confirmPassword: '', inviteCode: '' })
    } catch (e) {
      this.setData({ errorMsg: e.message || '注册失败' })
    } finally {
      this.setData({ submitting: false })
    }
  },
})
