const test = require('node:test')
const assert = require('node:assert/strict')

const {
  normalizeMatchedItems,
  shouldShowResultActions
} = require('./chat_item_view')

test('normalizeMatchedItems should resolve photo path and keep empty when missing', () => {
  const items = normalizeMatchedItems(
    [
      { id: 1, name: '护照', location: '主卧抽屉', photo_path: '/uploads/a.jpg' },
      { id: 2, name: '钥匙', location: '玄关柜', photo_path: '' }
    ],
    (path) => `http://127.0.0.1:8000${path}`
  )

  assert.equal(items[0].photo_path, 'http://127.0.0.1:8000/uploads/a.jpg')
  assert.equal(items[1].photo_path, '')
})

test('shouldShowResultActions should always return false', () => {
  assert.equal(shouldShowResultActions([]), false)
  assert.equal(shouldShowResultActions([{ id: 1 }]), false)
})
