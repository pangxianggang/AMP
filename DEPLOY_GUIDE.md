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
