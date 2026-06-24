const { checkAuth } = require('./utils/auth')

App({
  globalData: {
    user: null,
    token: '',
    isLoggedIn: false,
  },

  async onLaunch() {
    // 启动时验证本地 token
    await checkAuth()
  },
})
