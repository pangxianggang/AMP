# 🚀 GitHub Pages 部署指南

**5 分钟让 AMP 官网全球可访问！**

---

## ✅ 前提条件

- [x] 已安装 Git
- [x] 有 GitHub 账号
- [x] 网站文件在 `website/` 目录

---

## 📝 部署步骤

### 步骤 1: 推送到 GitHub

```bash
# 1. 进入项目目录
cd "C:\Users\Administrator\Desktop\AMPAgent Memory Protocol"

# 2. 关联 GitHub 仓库
# 在 GitHub 创建仓库后，替换下面的 URL
git remote add origin https://github.com/你的用户名/amp.git

# 3. 推送代码
git branch -M main
git push -u origin main
```

**预期输出**:
```
Enumerating objects: 58, done.
Counting objects: 100% (58/58), done.
Writing objects: 100% (58/58), done.
Total 58 (delta 0), reused 0 (delta 0)
To https://github.com/你的用户名/amp.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

---

### 步骤 2: 开启 GitHub Pages

1. **访问仓库设置**
   ```
   https://github.com/你的用户名/amp/settings/pages
   ```

2. **配置 Pages**
   - **Source**: Deploy from a branch
   - **Branch**: main
   - **Folder**: `/website`
   - 点击 **Save**

3. **等待部署**
   - 通常 1-2 分钟完成
   - 页面会显示部署进度

---

### 步骤 3: 获取网站地址

部署完成后，你会看到：

```
✅ Your site is live at:
https://你的用户名.github.io/amp/
```

**恭喜！网站现在全球可访问了！** 🎉

---

## 🌐 自定义域名（可选）

### 购买域名

推荐域名：
- `amp-protocol.vercel.app` (~$12/年)
- `amp-protocol.io` (~$35/年)
- `amp-protocol.com` (~$12/年)

购买平台：
- [Namecheap](https://namecheap.com)
- [GoDaddy](https://godaddy.com)
- [阿里云](https://aliyun.com)

### 配置 DNS

1. **在域名商处添加 DNS 记录**

   ```
   类型：CNAME
   主机：www
   值：你的用户名.github.io
   TTL：自动
   ```

2. **在 GitHub 配置域名**
   - 访问：https://github.com/你的用户名/amp/settings/pages
   - Custom domain: `amp-protocol.vercel.app`
   - 点击 **Save**

3. **启用 HTTPS**
   - 勾选 **Enforce HTTPS**
   - 等待证书生效（约 5 分钟）

---

## 📊 部署状态检查

### 查看部署日志

1. 访问：https://github.com/你的用户名/amp/actions
2. 查看最新的 Pages 部署
3. 点击查看详情

### 测试网站

```bash
# 使用 curl 测试
curl -I https://你的用户名.github.io/amp/

# 预期输出：
# HTTP/2 200
# content-type: text/html
```

---

## 🔄 更新网站

每次推送代码后，GitHub Pages 会自动更新：

```bash
# 修改网站文件
# 例如：website/index.html

# 提交并推送
git add website/
git commit -m "更新网站内容"
git push

# GitHub Pages 会自动重新部署！
```

**部署时间**: 通常 1-2 分钟

---

## ⚙️ 高级配置

### 添加 CNAME 文件

创建 `website/CNAME` 文件：

```
amp-protocol.vercel.app
```

提交后 GitHub 会自动配置域名。

### 自定义 404 页面

创建 `website/404.html`：

```html
<!DOCTYPE html>
<html>
<head>
    <title>404 - Page Not Found</title>
</head>
<body>
    <h1>404</h1>
    <p>页面未找到</p>
    <a href="/">返回首页</a>
</body>
</html>
```

### 配置 robots.txt

创建 `website/robots.txt`：

```
User-agent: *
Allow: /

Sitemap: https://你的用户名.github.io/amp/sitemap.xml
```

---

## 📈 访问统计

### GitHub Traffic

访问：https://github.com/你的用户名/amp/traffic

查看：
- 访客数量
- 页面浏览量
- 来源网站
- 热门内容

### Google Analytics（可选）

在网站 `<head>` 中添加：

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

---

## ❓ 常见问题

### Q: 部署后看不到更新？

**A**: 
1. 清除浏览器缓存（Ctrl+Shift+R）
2. 检查 GitHub Actions 是否完成
3. 等待 2-3 分钟

### Q: 自定义域名不生效？

**A**:
1. 检查 DNS 是否生效（dig 或 nslookup）
2. 等待 DNS 传播（最多 48 小时）
3. 检查 CNAME 文件是否正确

### Q: HTTPS 证书错误？

**A**:
1. 在 Settings → Pages 启用 Enforce HTTPS
2. 等待证书生效（5-10 分钟）
3. 如果持续报错，检查域名配置

### Q: 如何回滚部署？

**A**:
```bash
# 回滚到之前的提交
git revert HEAD
git push
```

---

## 📞 需要帮助？

- **GitHub Pages 文档**: https://pages.github.com/
- **GitHub Community**: https://github.community/
- **AMP Issues**: https://github.com/你的用户名/amp/issues
- **邮箱**: 13378455743@163.com

---

## 🎉 完成清单

- [ ] 创建 GitHub 仓库
- [ ] 推送代码到 GitHub
- [ ] 开启 GitHub Pages
- [ ] 选择 `/website` 文件夹
- [ ] 等待部署完成
- [ ] 测试网站访问
- [ ] （可选）配置自定义域名
- [ ] （可选）添加 Google Analytics
- [ ] 分享网站链接！

---

**部署完成后，全世界都能看到 AMP 官网了！** 🌍

**网站地址**: `https://你的用户名.github.io/amp/`

---

*Every AI deserves to remember.*


---

## Additional Notes from 手动部署指南.md

# 🚀 AMP 手动部署指南

**由于网络连接问题，请按以下步骤手动部署**

---

## ⚡ 快速部署（推荐）

### 第 1 步：打开 Git Bash 或 PowerShell

```powershell
cd "C:\Users\Administrator\Desktop\AMPAgent Memory Protocol"
```

### 第 2 步：推送代码到 GitHub

**方式 A：使用 HTTPS（推荐）**

```powershell
# 如果提示输入密码，使用 Personal Access Token
# 获取 Token: https://github.com/settings/tokens

git push -u origin main
```

**方式 B：使用 SSH（如果您配置了 SSH）**

```powershell
# 先更改远程地址
git remote set-url origin git@github.com:pangxianggang/AMP.git

# 然后推送
git push -u origin main
```

---

## 🔑 如果遇到认证问题

### 获取 Personal Access Token

1. 访问：https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. Note: 输入 `AMP Deployment`
4. 勾选权限：
   - ✅ repo (Full control of private repositories)
   - ✅ workflow
   - ✅ write:packages
5. 点击 "Generate token"
6. **复制 Token**（只显示一次！）

### 使用 Token 推送

```powershell
# 推送时会提示输入用户名和密码
# Username: pangxianggang
# Password: 粘贴刚才复制的 Token（不会显示）
git push -u origin main
```

---

## 🌐 开启 GitHub Pages

### 推送成功后

1. **访问仓库设置**
   ```
   https://github.com/pangxianggang/AMP/settings/pages
   ```

2. **配置 Pages**
   - Source: Deploy from a branch
   - Branch: **main**
   - Folder: **/website** ⚠️（重要！）
   - 点击 **Save**

3. **等待 1-2 分钟**

4. **完成！**
   
   网站地址：
   ```
   https://pangxianggang.github.io/AMP/
   ```

---

## 📊 检查部署状态

### 查看推送是否成功

访问：https://github.com/pangxianggang/AMP

应该看到所有文件。

### 查看 Pages 部署状态

访问：https://github.com/pangxianggang/AMP/actions

应该看到 "Pages build and deployment" 正在进行。

---

## ⚠️ 常见问题

### Q: 推送时提示 "Permission denied"

**A**: 使用 Personal Access Token
```
https://github.com/settings/tokens
```

### Q: 推送时提示 "Empty reply from server"

**A**: 网络问题，稍后重试
```powershell
# 重试推送
git push -u origin main
```

### Q: Pages 部署失败

**A**: 检查是否选择了正确的文件夹
- Branch: main
- Folder: /website

---

## 📞 需要帮助？

- **GitHub 文档**: https://docs.github.com/pages
- **仓库地址**: https://github.com/pangxianggang/AMP
- **邮箱**: 13378455743@163.com

---

## 🎉 部署完成后

**网站地址**: 
```
https://pangxianggang.github.io/AMP/
```

**分享链接**:
- Twitter
- 朋友圈
- 技术社区
- Product Hunt

---

*Every AI deserves to remember.*


---

## Additional Notes from 网站部署最终方案.md

# 🌐 GitHub Pages 部署最终解决方案

**问题**: GitHub Pages 无法访问

**原因**: 
1. GitHub Actions 未启用
2. 文件夹设置不正确
3. 网络连接不稳定

---

## ✅ 解决方案（3 选 1）

### 方案 A：使用根目录（推荐）⭐⭐⭐

**步骤**:

1. **在 GitHub Pages 设置页面**:
   https://github.com/pangxianggang/AMP/settings/pages

2. **配置**:
   ```
   Source: Deploy from a branch
   Branch: main
   Folder: / (root)  ← 选择根目录
   ```

3. **点击 Save**

4. **等待 2-3 分钟**

5. **访问**:
   ```
   https://pangxianggang.github.io/AMP/website/index.html
   ```

---

### 方案 B：启用 GitHub Actions（备选）⭐⭐

**步骤**:

1. **访问 Actions**:
   https://github.com/pangxianggang/AMP/actions

2. **启用 Actions**:
   - 点击 "set up a workflow yourself"
   - 或者选择一个模板

3. **创建简单的部署工作流**:
   - 选择 "Static HTML"
   - 点击 "Configure"
   - 点击 "Start commit"
   - 点击 "Commit changes"

4. **等待部署完成**

5. **访问**:
   ```
   https://pangxianggang.github.io/AMP/
   ```

---

### 方案 C：手动推送（最复杂）⭐

**步骤**:

1. **在本地执行**:
   ```powershell
   cd "C:\Users\Administrator\Desktop\AMPAgent Memory Protocol"
   git push --set-upstream origin main
   ```

2. **如果失败，检查网络**

3. **重试直到成功**

4. **然后在 GitHub Pages 设置中选择**:
   - Branch: main
   - Folder: /website

---

## 🎯 我的建议

**使用方案 A：选择根目录，然后访问 `/website/index.html`**

**原因**:
- ✅ 最简单
- ✅ 不需要启用 Actions
- ✅ 立即生效

**访问地址**:
```
https://pangxianggang.github.io/AMP/website/index.html
```

---

## 📋 完整检查清单

- [ ] 访问 GitHub Pages 设置
- [ ] 选择 main 分支
- [ ] 选择 / (root) 文件夹
- [ ] 点击 Save
- [ ] 等待 2-3 分钟
- [ ] 访问 https://pangxianggang.github.io/AMP/website/index.html
- [ ] 确认网站正常显示

---

## 🐛 如果还是不行

### 检查网络
```powershell
ping github.com
ping pangxianggang.github.io
```

### 清除浏览器缓存
```
Ctrl + Shift + Delete
选择"缓存的图像和文件"
点击"清除数据"
```

### 使用隐私模式
```
Ctrl + Shift + N (Chrome)
Ctrl + Shift + P (Firefox)
```

---

## 📞 需要帮助？

如果以上方案都不行，请告诉我：
1. GitHub Pages 设置的截图
2. 访问网站时的错误信息
3. 浏览器控制台错误（F12）

---

*Every AI deserves to remember.*
