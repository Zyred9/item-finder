function getCategoryIcon(categoryNameOrCode) {
  if (!categoryNameOrCode) {
    return '/assets/icons/map-pin.svg'
  }
  
  const text = String(categoryNameOrCode).toLowerCase()
  
  // 食品饮料类
  if (text.includes('food') || text.includes('食品') || text.includes('饮料') || text.includes('零食') || text.includes('调味') || text.includes('粮油')) {
    return '/assets/icons/food.svg'
  }
  
  // 药品健康类
  if (text.includes('medicine') || text.includes('药') || text.includes('保健') || text.includes('医疗')) {
    return '/assets/icons/medicine.svg'
  }
  
  // 服饰鞋包类
  if (text.includes('clothing') || text.includes('衣服') || text.includes('鞋') || text.includes('包') || text.includes('服饰')) {
    return '/assets/icons/clothing.svg'
  }
  
  // 数码家电类
  if (text.includes('electronics') || text.includes('电子') || text.includes('数码') || text.includes('家电') || text.includes('手机') || text.includes('电脑')) {
    return '/assets/icons/electronics.svg'
  }
  
  // 证件文件类
  if (text.includes('document') || text.includes('证件') || text.includes('文件') || text.includes('卡') || text.includes('票据')) {
    return '/assets/icons/document.svg'
  }
  
  // 生活用品类（默认）
  return '/assets/icons/home.svg'
}

/**
 * 计算过期状态
 * @param {Object} item - 物品对象（可能包含 extension.expire_date）
 * @returns {Object} - { expiry_status: 'expired' | 'expiring' | null, expiry_label: string }
 */
function calculateExpiryStatus(item) {
  if (!item || !item.extension || !item.extension.expire_date) {
    return { expiry_status: null, expiry_label: null }
  }

  const expireDateStr = item.extension.expire_date
  if (!expireDateStr) {
    return { expiry_status: null, expiry_label: null }
  }

  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const expireDate = new Date(expireDateStr)
  if (isNaN(expireDate.getTime())) {
    return { expiry_status: null, expiry_label: null }
  }

  const diffTime = expireDate - today
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays < 0) {
    // 已过期
    return {
      expiry_status: 'expired',
      expiry_label: `已过期${Math.abs(diffDays)}天`
    }
  } else if (diffDays <= 60) {
    // 临期（60 天内）
    return {
      expiry_status: 'expiring',
      expiry_label: diffDays === 0 ? '今日过期' : `临期${diffDays}天`
    }
  }

  return { expiry_status: null, expiry_label: null }
}

function normalizeMatchedItems(items, resolveStaticUrl) {
  const list = Array.isArray(items) ? items : []
  const resolver = typeof resolveStaticUrl === 'function' ? resolveStaticUrl : (path) => path || ''

  return list.map((item) => {
    const expiryInfo = calculateExpiryStatus(item)
    return {
      ...item,
      photo_path: item && item.photo_path ? resolver(item.photo_path) : '',
      category_icon: getCategoryIcon(item.category_name),
      expiry_status: expiryInfo.expiry_status,
      expiry_label: expiryInfo.expiry_label
    }
  })
}

function shouldShowResultActions() {
  return false
}

module.exports = {
  normalizeMatchedItems,
  shouldShowResultActions
}
