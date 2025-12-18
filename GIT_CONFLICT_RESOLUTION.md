# Git 合并冲突解决方案

## 🐛 问题描述

在执行 `git pull` 时遇到合并冲突错误：

```
error: Pulling is not possible because you have unmerged files.
hint: Fix them up in the work tree, and then use 'git add/rm <file>'
hint: as appropriate to mark resolution and make a commit.
fatal: Exiting because of an unresolved conflict.
```

## 🔍 问题分析

通过 `git status` 发现有3个文件存在合并冲突：

```
Unmerged paths:
  (use "git add <file>..." to mark resolution)
        both added:      RELEASE_GUIDE.md
        both added:      test_release_flow.py
        both added:      verify_release_config.py
```

**冲突原因**：
- 本地分支：使用新的英文文件名 (`invoice_pretty.exe` 等)
- 远程分支：使用旧的中文文件名 (`PDF发票拼版打印系统.exe` 等)
- 两个分支都添加了相同的文件，但内容不同

## 🔧 解决步骤

### 1. 检查冲突状态
```bash
git status
```

### 2. 解决每个文件的冲突

对于每个冲突文件，找到冲突标记并手动解决：

```
<<<<<<< HEAD
本地版本的内容
=======
远程版本的内容
>>>>>>> commit_hash
```

### 3. 冲突解决策略

**保留本地版本**（新的英文文件名）：
- `invoice_pretty.exe` ✅
- `invoice_pretty_portable.zip` ✅
- `invoice_pretty_intel.dmg` ✅
- `invoice_pretty_arm64.dmg` ✅

**删除远程版本**（旧的中文文件名）：
- `PDF发票拼版打印系统.exe` ❌
- `PDF发票拼版打印系统-便携版.zip` ❌
- `PDF发票拼版打印系统-intel.dmg` ❌
- `PDF发票拼版打印系统-arm64.dmg` ❌

### 4. 具体修复内容

#### RELEASE_GUIDE.md
```diff
- - **`PDF发票拼版打印系统.exe`** - 单文件可执行程序
+ - **`invoice_pretty.exe`** - 单文件可执行程序
```

#### test_release_flow.py
```diff
- 'PDF发票拼版打印系统.exe',
+ 'invoice_pretty.exe',
```

#### verify_release_config.py
```diff
- 'PDF发票拼版打印系统.exe',
+ 'invoice_pretty.exe',
```

### 5. 标记冲突已解决
```bash
git add RELEASE_GUIDE.md test_release_flow.py verify_release_config.py
```

### 6. 完成合并
```bash
git commit -m "解决合并冲突：保留新的英文文件名 (invoice_pretty)"
```

### 7. 推送到远程
```bash
git push
```

## ✅ 解决结果

```bash
git status
# Output: On branch main
# Your branch is up to date with 'origin/main'.
# nothing to commit, working tree clean
```

## 💡 预防措施

### 1. 定期同步
```bash
# 在开始工作前先拉取最新代码
git pull origin main
```

### 2. 小步提交
```bash
# 频繁提交，减少冲突范围
git add .
git commit -m "描述性提交信息"
git push
```

### 3. 沟通协调
- 团队成员之间协调修改同一文件的时间
- 使用分支策略避免直接在main分支上冲突

## 🔧 常用冲突解决命令

### 查看冲突状态
```bash
git status
git diff
```

### 解决冲突的选项
```bash
# 保留本地版本
git checkout --ours <file>

# 保留远程版本  
git checkout --theirs <file>

# 手动编辑解决
# 编辑文件，删除冲突标记，保留需要的内容
```

### 取消合并
```bash
# 如果想放弃合并，回到合并前状态
git merge --abort
```

### 重新开始
```bash
# 如果完全搞乱了，可以重置到远程状态
git reset --hard origin/main
```

## 📋 最佳实践

1. **冲突预防**：
   - 经常拉取最新代码
   - 使用功能分支开发
   - 及时推送本地更改

2. **冲突解决**：
   - 仔细阅读冲突内容
   - 理解两个版本的差异
   - 选择正确的版本或合并内容
   - 测试解决后的代码

3. **团队协作**：
   - 沟通重大更改
   - 使用Pull Request审查
   - 建立代码审查流程

---

**总结**: 通过手动解决冲突标记，保留了新的英文文件名配置，成功完成了合并并推送到远程仓库。现在所有文件都使用统一的 `invoice_pretty` 命名格式。