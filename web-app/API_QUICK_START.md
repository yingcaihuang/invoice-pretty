# Web发票处理器 API 快速开始指南

## 🚀 5分钟快速上手

### 1. 获取会话ID

```bash
# 创建会话
curl -X POST https://your-domain.com/api/session

# 响应
{
  "session_id": "session_abc123_1703123456789",
  "created_at": "2024-12-18T10:30:45+08:00",
  "expires_in_hours": 72
}
```

### 2. 上传PDF文件

```bash
# 上传单个PDF文件
curl -X POST https://your-domain.com/api/upload/ \
  -H "X-Session-ID: session_abc123_1703123456789" \
  -F "files=@invoice.pdf"

# 上传多个文件
curl -X POST https://your-domain.com/api/upload/ \
  -H "X-Session-ID: session_abc123_1703123456789" \
  -F "files=@invoice1.pdf" \
  -F "files=@invoice2.pdf" \
  -F "files=@invoices.zip"

# 响应
{
  "taskId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Successfully uploaded 1 file(s) and queued for processing",
  "fileCount": 1,
  "createdAt": "2024-12-18T10:30:45+08:00"
}
```

### 3. 检查处理状态

```bash
# 获取任务状态
curl -X GET https://your-domain.com/api/task/550e8400-e29b-41d4-a716-446655440000/status \
  -H "X-Session-ID: session_abc123_1703123456789"

# 处理中的响应
{
  "taskId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 75,
  "createdAt": "2024-12-18T10:30:45+08:00",
  "updatedAt": "2024-12-18T10:31:30+08:00",
  "fileCount": 1
}

# 完成后的响应
{
  "taskId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "createdAt": "2024-12-18T10:30:45+08:00",
  "updatedAt": "2024-12-18T10:32:15+08:00",
  "completedAt": "2024-12-18T10:32:15+08:00",
  "fileCount": 1,
  "downloadUrls": [
    "/api/download/550e8400-e29b-41d4-a716-446655440000/processed_invoices.pdf"
  ]
}
```

### 4. 下载处理结果

```bash
# 下载文件
curl -X GET https://your-domain.com/api/download/550e8400-e29b-41d4-a716-446655440000/processed_invoices.pdf \
  -H "X-Session-ID: session_abc123_1703123456789" \
  -o result.pdf

# 在浏览器中预览
curl -X GET "https://your-domain.com/api/download/550e8400-e29b-41d4-a716-446655440000/processed_invoices.pdf?inline=true" \
  -H "X-Session-ID: session_abc123_1703123456789"
```

## 📋 常用API端点

| 功能 | 方法 | 端点 | 说明 |
|------|------|------|------|
| 创建会话 | POST | `/api/session` | 获取会话ID |
| 上传文件 | POST | `/api/upload/` | 上传PDF或ZIP文件 |
| 任务状态 | GET | `/api/task/{id}/status` | 获取处理状态 |
| 任务进度 | GET | `/api/task/{id}/progress` | 获取详细进度 |
| 下载文件 | GET | `/api/download/{id}/{filename}` | 下载结果文件 |
| 任务列表 | GET | `/api/task/` | 获取所有任务 |
| 删除任务 | DELETE | `/api/task/{id}` | 删除任务和文件 |
| 系统状态 | GET | `/api/health` | 检查系统健康 |

## 🔧 Python 快速示例

```python
import requests
import time

# 1. 创建会话
response = requests.post("https://your-domain.com/api/session")
session_id = response.json()["session_id"]
headers = {"X-Session-ID": session_id}

# 2. 上传文件
with open("invoice.pdf", "rb") as f:
    files = {"files": f}
    response = requests.post(
        "https://your-domain.com/api/upload/",
        headers=headers,
        files=files
    )
task_id = response.json()["taskId"]

# 3. 等待处理完成
while True:
    response = requests.get(
        f"https://your-domain.com/api/task/{task_id}/status",
        headers=headers
    )
    status = response.json()
    
    if status["status"] == "completed":
        print("处理完成!")
        break
    elif status["status"] == "failed":
        print("处理失败:", status.get("message"))
        break
    
    print(f"处理进度: {status['progress']}%")
    time.sleep(2)

# 4. 下载结果
if status["status"] == "completed":
    download_url = status["downloadUrls"][0]
    filename = download_url.split("/")[-1]
    
    response = requests.get(
        f"https://your-domain.com{download_url}",
        headers=headers
    )
    
    with open(f"result_{filename}", "wb") as f:
        f.write(response.content)
    print("文件下载完成!")
```

## 🌐 JavaScript 快速示例

```javascript
// 1. 创建会话
const sessionResponse = await fetch("https://your-domain.com/api/session", {
    method: "POST"
});
const session = await sessionResponse.json();
const sessionId = session.session_id;

// 2. 上传文件
const formData = new FormData();
formData.append("files", fileInput.files[0]);

const uploadResponse = await fetch("https://your-domain.com/api/upload/", {
    method: "POST",
    headers: {
        "X-Session-ID": sessionId
    },
    body: formData
});
const uploadResult = await uploadResponse.json();
const taskId = uploadResult.taskId;

// 3. 监控处理状态
const checkStatus = async () => {
    const response = await fetch(`https://your-domain.com/api/task/${taskId}/status`, {
        headers: {
            "X-Session-ID": sessionId
        }
    });
    const status = await response.json();
    
    if (status.status === "completed") {
        console.log("处理完成!");
        return status;
    } else if (status.status === "failed") {
        throw new Error("处理失败: " + status.message);
    } else {
        console.log(`处理进度: ${status.progress}%`);
        setTimeout(checkStatus, 2000);
    }
};

const result = await checkStatus();

// 4. 下载结果
if (result.downloadUrls && result.downloadUrls.length > 0) {
    const downloadUrl = `https://your-domain.com${result.downloadUrls[0]}`;
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = "result.pdf";
    link.click();
}
```

## ⚠️ 重要注意事项

### 认证要求
- 所有API请求必须包含 `X-Session-ID` 头部
- 会话有效期为72小时
- 文件保存期限为24小时

### 文件限制
- 最大文件大小: 50MB
- 支持格式: PDF, ZIP
- 单次最多上传100个文件

### 错误处理
```javascript
// 检查响应状态
if (!response.ok) {
    const error = await response.json();
    console.error("API错误:", error.message);
    throw new Error(error.message);
}
```

### 轮询最佳实践
```python
# 使用指数退避算法
import time

def wait_for_completion(task_id, headers, max_wait=300):
    start_time = time.time()
    wait_time = 1
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"/api/task/{task_id}/status", headers=headers)
        status = response.json()
        
        if status["status"] in ["completed", "failed"]:
            return status
            
        time.sleep(min(wait_time, 10))  # 最大等待10秒
        wait_time *= 1.5  # 指数增长
    
    raise TimeoutError("任务超时")
```

## 🔍 调试技巧

### 1. 检查系统健康
```bash
curl -X GET https://your-domain.com/api/health
```

### 2. 获取详细进度
```bash
curl -X GET https://your-domain.com/api/task/{task_id}/progress \
  -H "X-Session-ID: your-session-id"
```

### 3. 查看所有任务
```bash
curl -X GET https://your-domain.com/api/task/ \
  -H "X-Session-ID: your-session-id"
```

### 4. 检查文件可用性
```bash
curl -I https://your-domain.com/api/download/{task_id}/{filename} \
  -H "X-Session-ID: your-session-id"
```

## 📞 获取帮助

- 完整API文档: [API_SPECIFICATION.md](API_SPECIFICATION.md)
- 部署指南: [README.md](README.md)
- HTTPS配置: [HTTPS.md](HTTPS.md)

---

*快速开始指南 - 让您在5分钟内开始使用Web发票处理器API*