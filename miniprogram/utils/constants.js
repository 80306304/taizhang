// 后端 API 基础地址
// 开发阶段可在 project.config.json 设置 urlCheck: false 使用 HTTP
// 生产环境必须使用 HTTPS 且在微信后台配置合法域名
const BASE_URL = 'http://47.96.254.155:8000'

// 快递状态码映射
const TRACKING_STATE_MAP = {
  '0': { text: '查询出错', color: 'danger' },
  '1': { text: '暂无记录', color: 'gray' },
  '2': { text: '运输中',   color: 'info' },
  '3': { text: '已签收',   color: 'success' },
  '4': { text: '问题件',   color: 'warning' },
  '5': { text: '疑难件',   color: 'warning' },
  '6': { text: '退件签收', color: 'danger' },
}

// 快递公司代码 -> 中文名
const COMPANY_NAMES = {
  jd: '京东快递',
  shunfeng: '顺丰速运',
  yuantong: '圆通速递',
  zhongtong: '中通快递',
  shentong: '申通快递',
  ems: 'EMS',
  yunda: '韵达快递',
  youzhengguonei: '邮政国内小包',
  jitu: '极兔速递',
  zhaijisong: '宅急送',
}

// 每页条数
const PAGE_SIZE = 20

module.exports = {
  BASE_URL,
  TRACKING_STATE_MAP,
  COMPANY_NAMES,
  PAGE_SIZE,
}
