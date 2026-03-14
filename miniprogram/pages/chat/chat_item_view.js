function normalizeMatchedItems(items, resolveStaticUrl) {
  const list = Array.isArray(items) ? items : []
  const resolver = typeof resolveStaticUrl === 'function' ? resolveStaticUrl : (path) => path || ''

  return list.map((item) => ({
    ...item,
    photo_path: item && item.photo_path ? resolver(item.photo_path) : ''
  }))
}

function shouldShowResultActions() {
  return false
}

module.exports = {
  normalizeMatchedItems,
  shouldShowResultActions
}
