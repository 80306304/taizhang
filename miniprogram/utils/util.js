/**
 * 通用工具函数
 */

/**
 * 格式化金额（保留2位小数，千分位）
 */
function formatMoney(val) {
  if (val === null || val === undefined || isNaN(val)) return '0.00'
  const num = Number(val)
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

/**
 * 格式化日期为简短形式
 */
function formatDate(str) {
  if (!str) return '-'
  // "2026-06-18 14:30:00" -> "06-18 14:30"
  const parts = str.split(' ')
  const datePart = parts[0] || ''
  const timePart = parts[1] || ''
  const md = datePart.slice(5) // "06-18"
  const hm = timePart.slice(0, 5) // "14:30"
  return hm ? `${md} ${hm}` : md
}

/**
 * 格式化日期为完整形式
 */
function formatDateFull(str) {
  if (!str) return '-'
  return str.slice(0, 16) // "2026-06-18 14:30"
}

/**
 * 获取当前日期字符串 YYYY-MM-DD
 */
function today() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/**
 * 获取本季度第一天
 */
function quarterStart() {
  const d = new Date()
  const q = Math.floor(d.getMonth() / 3) * 3
  return `${d.getFullYear()}-${String(q + 1).padStart(2, '0')}-01`
}

/**
 * 获取本年第一天
 */
function yearStart() {
  return `${new Date().getFullYear()}-01-01`
}

/**
 * 获取本月第一天
 */
function monthStart() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`
}

/**
 * 根据时间周期构建日期参数
 */
function buildDateParams(period, dateFrom, dateTo) {
  switch (period) {
    case 'month': return { date_from: monthStart(), date_to: today() }
    case 'quarter': return { date_from: quarterStart(), date_to: today() }
    case 'year': return { date_from: yearStart(), date_to: today() }
    case 'custom': return { date_from: dateFrom || '', date_to: dateTo || '' }
    default: return {}
  }
}

/**
 * 防抖函数
 */
function debounce(fn, delay = 300) {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn.apply(this, args), delay)
  }
}

/**
 * 利润样式类
 */
function profitClass(val) {
  if (val > 0) return 'profit-positive'
  if (val < 0) return 'profit-negative'
  return 'profit-zero'
}

/**
 * 快递状态文本和颜色
 */
function trackingInfo(state) {
  const map = {
    '0': { text: '查询出错', color: 'danger' },
    '1': { text: '暂无记录', color: 'gray' },
    '2': { text: '运输中',   color: 'info' },
    '3': { text: '已签收',   color: 'success' },
    '4': { text: '问题件',   color: 'warning' },
    '5': { text: '疑难件',   color: 'warning' },
    '6': { text: '退件签收', color: 'danger' },
  }
  return map[String(state)] || { text: '未查询', color: 'gray' }
}

module.exports = {
  formatMoney,
  formatDate,
  formatDateFull,
  today,
  monthStart,
  quarterStart,
  yearStart,
  buildDateParams,
  debounce,
  profitClass,
  trackingInfo,
}
