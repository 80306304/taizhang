/**
 * HTTP 请求封装
 * - 自动注入 JWT Authorization header
 * - 统一错误处理（401 自动跳转登录）
 * - 兼容后端 200+error 的响应模式
 */
const { BASE_URL } = require('./constants')

/**
 * 核心请求函数
 */
function request(method, path, data, options = {}) {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('token')
    const header = {
      'Content-Type': 'application/json',
      ...(options.header || {}),
    }
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    wx.request({
      url: `${BASE_URL}${path}`,
      method,
      data,
      header,
      timeout: 15000,
      success(res) {
        const { statusCode, data: body } = res

        // 401 未授权 → 清除登录态，跳转登录页
        if (statusCode === 401) {
          wx.removeStorageSync('token')
          wx.removeStorageSync('user')
          const app = getApp()
          if (app) {
            app.globalData.user = null
            app.globalData.token = ''
            app.globalData.isLoggedIn = false
          }
          wx.reLaunch({ url: '/pages/login/index' })
          reject(new Error('登录已过期，请重新登录'))
          return
        }

        // 403 权限不足
        if (statusCode === 403) {
          const msg = (body && body.detail) || '权限不足'
          wx.showToast({ title: msg, icon: 'none' })
          reject(new Error(msg))
          return
        }

        // 422 验证错误
        if (statusCode === 422) {
          let msg = '数据验证失败'
          if (body && body.detail && body.detail.length > 0) {
            const first = body.detail[0]
            msg = first.msg || msg
          }
          wx.showToast({ title: msg, icon: 'none' })
          reject(new Error(msg))
          return
        }

        // 其他 HTTP 错误
        if (statusCode >= 400) {
          const msg = (body && (body.detail || body.message)) || `请求失败 (${statusCode})`
          wx.showToast({ title: msg, icon: 'none' })
          reject(new Error(msg))
          return
        }

        // 200 但后端返回 error 字段（部分接口的业务错误）
        if (body && body.error) {
          wx.showToast({ title: body.error, icon: 'none' })
          reject(new Error(body.error))
          return
        }

        // 成功
        resolve(body)
      },
      fail(err) {
        wx.showToast({ title: '网络请求失败', icon: 'none' })
        reject(new Error(err.errMsg || '网络请求失败'))
      },
    })
  })
}

/**
 * GET 请求
 */
function get(path, params) {
  if (params) {
    const query = Object.entries(params)
      .filter(([, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
      .join('&')
    if (query) path = `${path}?${query}`
  }
  return request('GET', path)
}

/**
 * POST 请求
 */
function post(path, data) {
  return request('POST', path, data)
}

/**
 * PUT 请求
 */
function put(path, data) {
  return request('PUT', path, data)
}

/**
 * DELETE 请求
 */
function del(path) {
  return request('DELETE', path)
}

/**
 * 文件上传（用于 Excel 导入）
 * wx.uploadFile 不走 wx.request，需单独封装
 */
function upload(path, filePath) {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('token')
    wx.uploadFile({
      url: `${BASE_URL}${path}`,
      filePath,
      name: 'file',
      header: {
        Authorization: token ? `Bearer ${token}` : '',
      },
      success(res) {
        if (res.statusCode === 401) {
          wx.removeStorageSync('token')
          wx.reLaunch({ url: '/pages/login/index' })
          reject(new Error('登录已过期'))
          return
        }
        try {
          const body = JSON.parse(res.data)
          if (body.error) {
            wx.showToast({ title: body.error, icon: 'none' })
            reject(new Error(body.error))
            return
          }
          resolve(body)
        } catch (e) {
          reject(new Error('响应解析失败'))
        }
      },
      fail(err) {
        wx.showToast({ title: '上传失败', icon: 'none' })
        reject(new Error(err.errMsg || '上传失败'))
      },
    })
  })
}

/**
 * 文件下载
 */
function download(path) {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('token')
    wx.downloadFile({
      url: `${BASE_URL}${path}`,
      header: {
        Authorization: token ? `Bearer ${token}` : '',
      },
      success(res) {
        if (res.statusCode === 200) {
          resolve(res.tempFilePath)
        } else {
          reject(new Error('下载失败'))
        }
      },
      fail(err) {
        reject(new Error(err.errMsg || '下载失败'))
      },
    })
  })
}

module.exports = { request, get, post, put, del, upload, download }
