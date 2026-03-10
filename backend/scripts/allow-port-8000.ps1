# 允许本机 8000 端口入站（解决小程序请求 502）
# 请以管理员身份运行 PowerShell，然后执行: .\scripts\allow-port-8000.ps1

$ruleName = "ItemFinder-Backend-8000"
$port = 8000

$existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "规则已存在，先删除旧规则..."
    Remove-NetFirewallRule -DisplayName $ruleName
}

New-NetFirewallRule -DisplayName $ruleName `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort $port `
    -Action Allow `
    -Profile Any

Write-Host "已添加防火墙规则: 允许 TCP 入站端口 $port"
Write-Host "请用浏览器访问 http://你的本机IP:8000/health 验证后端是否可达"
