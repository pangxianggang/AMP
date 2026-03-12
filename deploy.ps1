# AMP 自动部署脚本
# 使用方法：在 PowerShell 中运行 .\deploy.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 AMP GitHub Pages 自动部署脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤 1: 配置 Git 用户信息
Write-Host "📝 步骤 1: 配置 Git 用户信息..." -ForegroundColor Yellow
git config --global user.name "AMP Team"
git config --global user.email "13378455743@163.com"
Write-Host "✅ Git 用户信息已配置" -ForegroundColor Green
Write-Host ""

# 步骤 2: 检查是否已关联远程仓库
Write-Host "📝 步骤 2: 检查远程仓库..." -ForegroundColor Yellow
$remoteUrl = git remote get-url origin 2>$null

if ($remoteUrl) {
    Write-Host "✅ 已关联远程仓库：$remoteUrl" -ForegroundColor Green
} else {
    Write-Host "⚠️  未关联远程仓库" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "请先在 GitHub 创建仓库，然后运行：" -ForegroundColor Cyan
    Write-Host "git remote add origin https://github.com/你的用户名/amp.git" -ForegroundColor White
    Write-Host ""
    Write-Host "按任意键退出..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit
}

Write-Host ""

# 步骤 3: 推送代码到 GitHub
Write-Host "📝 步骤 3: 推送代码到 GitHub..." -ForegroundColor Yellow
git branch -M main
$pushResult = git push -u origin main 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 代码推送成功！" -ForegroundColor Green
} else {
    Write-Host "❌ 推送失败，请检查网络连接" -ForegroundColor Red
    Write-Host $pushResult
    Write-Host ""
    Write-Host "按任意键退出..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit
}

Write-Host ""

# 步骤 4: 显示 GitHub Pages 配置指南
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🎉 代码推送成功！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 下一步：开启 GitHub Pages" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. 访问以下地址（复制浏览器打开）:" -ForegroundColor Cyan
$repoUrl = $remoteUrl -replace "git@", "https://" -replace ".git$", ""
Write-Host "   $repoUrl/settings/pages" -ForegroundColor White
Write-Host ""
Write-Host "2. 配置 Pages:" -ForegroundColor Cyan
Write-Host "   - Source: Deploy from a branch" -ForegroundColor White
Write-Host "   - Branch: main" -ForegroundColor White
Write-Host "   - Folder: /website" -ForegroundColor White
Write-Host "   - 点击 Save" -ForegroundColor White
Write-Host ""
Write-Host "3. 等待 1-2 分钟，网站将自动部署！" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 网站地址:" -ForegroundColor Yellow
$username = ($remoteUrl -split '/')[3]
Write-Host "   https://$username.github.io/amp/" -ForegroundColor Green
Write-Host ""
Write-Host "📧 网站邮箱：13378455743@163.com" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✨ 部署即将完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "按任意键打开 GitHub 页面设置..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# 自动打开 GitHub Pages 设置页面
Start-Process "$repoUrl/settings/pages"

Write-Host ""
Write-Host "🎉 祝您部署成功！" -ForegroundColor Green
Write-Host ""
