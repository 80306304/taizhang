/**
 * 认证管理工具
 */
const { post, get } = require('./api')

/**
 * 登录
 */
async function login(username, password) {
  const res = await post('/api/auth/login', { username, password })
  const { access_token, user } = res
  // 存储 token 和用户信息
  wx.setStorageSync('token', access_token)
  wx.setStorageSync('user', user)
  // 更新全局状态
  const app = getApp()
  app.globalData.token = access_token
  app.globalData.user = user
  app.globalData.isLoggedIn = true
  return user
}

/**
 * 注册
 */
async function register(username, password, inviteCode) {
  return await post('/api/auth/register', {
    username,
    password,
    invite_code: inviteCode,
  })
}

/**
 * 登出
 */
function logout() {
  wx.removeStorageSync('token')
  wx.removeStorageSync('user')
  const app = getApp()
  app.globalData.user = null
  app.globalData.token = ''
  app.globalData.isLoggedIn = false
  wx.reLaunch({ url: '/pages/login/index' })
}

/**
 * 检查登录状态（在 app.onLaunch 调用）
 * 返回 user 对象或 null
 */
async function checkAuth() {
  const token = wx.getStorageSync('token')
  if (!token) return null

  try {
    const res = await get('/api/auth/me')
    const user = res.data
    wx.setStorageSync('user', user)
    const app = getApp()
    app.globalData.token = token
    app.globalData.user = user
    app.globalData.isLoggedIn = true
    return user
  } catch (e) {
    // token 无效，清除
    wx.removeStorageSync('token')
    wx.removeStorageSync('user')
    return null
  }
}

/**
 * 获取当前用户（从缓存快速读取）
 */
function getCurrentUser() {
  const app = getApp()
  return app.globalData.user || wx.getStorageSync('user') || null
}

/**
 * 是否管理员
 */
function isAdmin() {
  const user = getCurrentUser()
  return user && user.role === 'admin'
}

module.exports = { login, register, logout, checkAuth, getCurrentUser, isAdmin }
