# Web发票处理器 API 规范手册

## 概述

Web发票处理器提供RESTful API接口，支持PDF发票文件的批量处理和布局优化。API采用会话机制进行用户隔离，支持异步任务处理，提供实时状态跟踪和文件下载功能。

## 基础信息

- **API版本**: v1.0.0
- **基础URL**: `https://your-domain.com/api` (HTTPS) 或 `http://localhost:8000/api` (开发环境)
- **认证方式**: 基于会话ID的认证
- **数据格式**: JSON
- **字符编码**: UTF-8
- **时区**: 北京时间 (UTC+8)

## 认证机制

### 会话管理

所有API请求都需要在HTTP头部包含会话ID：

```http
X-Session-ID: your-session-id
```

### 创建会话

**端点**: `POST /api/session`

**请求示例**:
```bash
curl -X POST https://your-domain.com/api/session \
  -H "Content-Type: application/json"
```

**响应示例**:
```json
{
  "session_id": "session_abc123_1703123456789",
  "created_at": "2024-12-18T10:30:45+08:00",
  "expires_in_hours": 72
}
```

## API 端点详细说明

### 1. 健康检查

#### 1.1 系统健康状态

**端点**: `GET /api/health`

**描述**: 检查系统各组件的健康状态

**请求示例**:
```bash
curl -X GET https://your-domain.com/api/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "services": {
    "redis": "healthy",
    "file_storage": "healthy"
  },
  "timestamp": 1703123456.789
}
```

### 2. 文件上传

#### 2.1 上传PDF文件或ZIP压缩包

**端点**: `POST /api/upload/`

**描述**: 上传PDF文件或包含PDF文件的ZIP压缩包进行处理

**请求头**:
```http
Content-Type: multipart/form-data
X-Session-ID: your-session-id
```

**请求参数**:
- `files`: 文件列表（支持PDF和ZIP格式）

**文件限制**:
- 最大文件大小: 50MB
- 支持格式: PDF, ZIP
- 支持的MIME类型: `application/pdf`, `application/zip`, `application/x-zip-compressed`, `application/octet-stream`

**请求示例**:
```bash
curl -X POST https://your-domain.com/api/upload/ \
  -H "X-Session-ID: session_abc123_1703123456789" \
  -F "files=@invoice1.pdf" \
  -F "files=@invoices.zip"
```

**响应示例**:
```json
{
  "taskId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Successfully uploaded 2 file(s) and queued for processing",
  "fileCount": 2,
  "createdAt": "2024-12-18T10:30:45+08:00"
}
```

#### 2.2 获取上传限制信息

**端点**: `GET /api/upload/limits`

**描述**: 获取文件上传的限制和配置信息

**请求示例**:
```bash
curl -X GET https://your-domain.com/api/upload/limits
```

**响应示例**:
```json
{
  "max_file_size": 52428800,
  "max_file_size_mb": 50.0,
  "allowed_content_types": [
    "application/pdf",
    "application/zip",
    "application/x-zip-compressed",
    "application/octet-stream"
  ],
  "allowed_extensions": [".pdf", ".zip"]
}
```

### 3. 任务管理

#### 3.1 获取任务状态

**端点**: `GET /api/task/{task_id}/status`

**描述**: 获取指定任务的当前状态和处理进度

**路径参数**:
- `task_id`: 任务唯一标识符

**请求示例**:
```bash
curl -X GET https://your-domain.com/api/task/550e8400-e29b-41d4-a716-446655440000/status \
  -H "X-Session-ID: session_abc123_1703123456789"
```

**响应示例**:
```json
{
  "taskId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "createdAt": "2024-12-18T10:30:45+08:00",
  "updatedAt": "2024-12-18T10:32:15+08:00",
  "completedAt": "2024-12-18T10:32:15+08:00",
  "fileCount": 2,
  "downloadUrls": [
    "/api/download/550e8400-e29b-41d4-a716-446655440000/processed_invoices.pdf"
  ]
}
```

**任务状态说明**:
- `queued`: 已排队等待处理
- `processing`: 正在处理中
- `completed`: 处理完成
- `failed`: 处理失败
- `expired`: 已过期

#### 3.2 获取任务详细进度

**端点**: `GET /api/task/{task_id}/progress`

**描述**: 获取任务的实时处理进度和详细信息

**请求示例**:
```bash
curl -X GET https://your-domain.com/api/task/550e8400-e29b-41d4-a716-446655440000/progress \
  -H "X-Session-ID: session_abc123_1703123456789"
```

**响应示例**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "progress": 75,
  "status": "processing",
  "updated_at": "2024-12-18T10:31:30+08:00",
  "stage": "Processing PDF files",
  "estimated_remaining_seconds": 30,
  "estimated_completion_at": "2024-12-18T10:32:00+08:00",
  "progress_rate_per_minute": 25.5
}
```

#### 3.3 获取会话所有任务

**端点**: `GET /api/task/`

**描述**: 获取当前会话的所有任务列表

**查询参数**:
- `status` (可选): 按状态筛选任务

**请求示例**:
```bash
curl -X GET "https://your-domain.com/api/task/?status=completed" \
  -H "X-Session-ID: session_abc123_1703123456789"
```

**响应示例**:
```json
{
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "progress": 100,
      "created_at": "2024-12-18T10:30:45+08:00",
      "updated_at": "2024-12-18T10:32:15+08:00",
      "completed_at": "2024-12-18T10:32:15+08:00",
      "file_count": 2
    }
  ],
  "total_count": 1,
  "session_id": "session_abc123_1703123456789"
}
```

#### 3.4 启动异步处理

**端点**: `POST /api/task/{task_id}/start`

**描述**: 手动启动已排队任务的异步处理

**请求示例**:
```bash
curl -X POST https://your-domain.com/api/task/550e8400-e29b-41d4-a716-446655440000/start \
  -H "X-Session-ID: session_abc123_1703123456789"
```

**响应示例**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Task queued for asynchronous processing",
  "started_at": "2024-12-18T10:30:50+08:00"
}
```

#### 3.5 取消任务

**端点**: `POST /api/task/{task_id}/cancel`

**描述**: 取消正在处理或排队中的任务

**请求示例**:
```bash
curl -X POST https://your-domain.com/api/task/550e8400-e29b-41d4-a716-446655440000/cancel \
  -H "X-Session-ID: session_abc123_1703123456789"
```

**响应示例**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "message": "Task cancelled successfully",
  "cancelled_at": "2024-12-18T10:31:00+08:00"
}
```

#### 3.6 重试失败任务

**端点**: `POST /api/task/{task_id}/retry`

**描述**: 重新处理失败的任务

**请求示例**:
```bash
curl -X POST https://your-domain.com/api/task/550e8400-e29b-41d4-a716-446655440000/retry \
  -H "X-Session-ID: session_abc123_1703123456789"
```

**响应示例**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Task queued for retry",
  "retried_at": "2024-12-18T10:35:00+08:00"
}
```

#### 3.7 删除任务

**端点**: `DELETE /api/task/{task_id}`

**描述**: 删除任务及其相关文件

**请求示例**:
```bash
curl -X DELETE https://your-domain.com/api/task/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-Session-ID: session_abc123_1703123456789"
```

**响应示例**:
```json
{
  "message": "Task 550e8400-e29b-41d4-a716-446655440000 deleted successfully",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "files_cleaned": true
}
```

#### 3.8 获取任务统计信息

**端点**: `GET /api/task/statistics`

**描述**: 获取当前会话的任务统计信息

**请求示例**:
```bash
curl -X GET https://your-domain.com/api/task/statistics \
  -H "X-Session-ID: session_abc123_1703123456789"
```

**响应示例**:
```json
{
  "total_tasks": 5,
  "status_counts": {
    "queued": 1,
    "processing": 0,
    "completed": 3,
    "failed": 1,
    "expired": 0
  },
  "avg_processing_time_seconds": 45.2,
  "session_id": "session_abc123_1703123456789"
}
```

### 4. 文件下载

#### 4.1 下载处理结果

**端点**: `GET /api/download/{task_id}/{filename}`

**描述**: 下载任务处理完成后的结果文件

**路径参数**:
- `task_id`: 任务唯一标识符
- `filename`: 文件名

**查询参数**:
- `inline` (可选): 设置为true时在浏览器中预览，false时下载文件
- `session` (可选): 会话ID（用于iframe访问）

**请求示例**:
```bash
# 下载文件
curl -X GET https://your-domain.com/api/download/550e8400-e29b-41d4-a716-446655440000/processed_invoices.pdf \
  -H "X-Session-ID: session_abc123_1703123456789" \
  -o processed_invoices.pdf

# 预览文件
curl -X GET "https://your-domain.com/api/download/550e8400-e29b-41d4-a716-446655440000/processed_invoices.pdf?inline=true" \
  -H "X-Session-ID: session_abc123_1703123456789"
```

**响应**: 文件内容（二进制数据）

**响应头**:
```http
Content-Type: application/pdf
Content-Disposition: attachment; filename="processed_invoices.pdf"
Cache-Control: no-cache, no-store, must-revalidate
```

#### 4.2 检查文件可用性

**端点**: `HEAD /api/download/{task_id}/{filename}`

**描述**: 检查文件是否可用于下载，不返回文件内容

**请求示例**:
```bash
curl -I https://your-domain.com/api/download/550e8400-e29b-41d4-a716-446655440000/processed_invoices.pdf \
  -H "X-Session-ID: session_abc123_1703123456789"
```

**响应头**:
```http
HTTP/1.1 200 OK
Content-Length: 1048576
Content-Type: application/pdf
Cache-Control: no-cache, no-store, must-revalidate
```

### 5. 队列管理

#### 5.1 获取队列统计

**端点**: `GET /api/task/queue/stats`

**描述**: 获取任务队列的统计信息

**请求示例**:
```bash
curl -X GET https://your-domain.com/api/task/queue/stats \
  -H "X-Session-ID: session_abc123_1703123456789"
```

**响应示例**:
```json
{
  "queued_tasks": 3,
  "processing_tasks": 2,
  "completed_tasks_today": 15,
  "failed_tasks_today": 1,
  "average_processing_time": 42.5,
  "queue_health": "healthy"
}
```

#### 5.2 队列健康检查

**端点**: `POST /api/task/queue/health`

**描述**: 执行队列系统的健康检查

**请求示例**:
```bash
curl -X POST https://your-domain.com/api/task/queue/health \
  -H "X-Session-ID: session_abc123_1703123456789"
```

**响应示例**:
```json
{
  "healthy": true,
  "redis_connection": "ok",
  "celery_workers": 2,
  "queue_size": 3,
  "timestamp": "2024-12-18T10:30:45+08:00"
}
```

## 错误处理

### 错误响应格式

所有错误响应都遵循统一格式：

```json
{
  "error": true,
  "code": "ERROR_CODE",
  "message": "Human readable error message"
}
```

### 常见错误代码

| HTTP状态码 | 错误代码 | 描述 |
|-----------|---------|------|
| 400 | MISSING_SESSION_ID | 缺少会话ID |
| 400 | INVALID_FILE_TYPE | 不支持的文件类型 |
| 400 | FILE_SIZE_EXCEEDED | 文件大小超出限制 |
| 401 | INVALID_SESSION | 无效或过期的会话 |
| 403 | ACCESS_DENIED | 访问被拒绝 |
| 404 | TASK_NOT_FOUND | 任务不存在 |
| 404 | FILE_NOT_FOUND | 文件不存在 |
| 429 | RATE_LIMIT_EXCEEDED | 请求频率超出限制 |
| 500 | INTERNAL_SERVER_ERROR | 服务器内部错误 |
| 503 | SERVICE_UNAVAILABLE | 服务不可用 |

### 错误示例

```json
{
  "error": true,
  "code": "MISSING_SESSION_ID",
  "message": "Session ID is required"
}
```

## 使用流程

### 典型的API调用流程

1. **创建会话**
   ```bash
   curl -X POST https://your-domain.com/api/session
   ```

2. **上传文件**
   ```bash
   curl -X POST https://your-domain.com/api/upload/ \
     -H "X-Session-ID: session_abc123_1703123456789" \
     -F "files=@invoice.pdf"
   ```

3. **监控任务状态**
   ```bash
   curl -X GET https://your-domain.com/api/task/{task_id}/status \
     -H "X-Session-ID: session_abc123_1703123456789"
   ```

4. **下载结果**
   ```bash
   curl -X GET https://your-domain.com/api/download/{task_id}/{filename} \
     -H "X-Session-ID: session_abc123_1703123456789" \
     -o result.pdf
   ```

## 限制和配额

### 文件限制
- 单个文件最大大小: 50MB
- 单次上传最大文件数: 无限制（建议不超过100个）
- 支持的文件格式: PDF, ZIP

### 会话限制
- 会话有效期: 72小时
- 单个会话最大任务数: 无限制
- 文件保存期限: 24小时

### 速率限制
- API请求频率: 100请求/分钟/会话
- 并发处理任务数: 4个/系统

## SDK和示例代码

### Python示例

```python
import requests
import time

class InvoiceProcessorClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session_id = None
    
    def create_session(self):
        """创建新会话"""
        response = requests.post(f"{self.base_url}/api/session")
        response.raise_for_status()
        data = response.json()
        self.session_id = data['session_id']
        return data
    
    def upload_files(self, file_paths):
        """上传文件"""
        files = []
        for path in file_paths:
            files.append(('files', open(path, 'rb')))
        
        headers = {'X-Session-ID': self.session_id}
        response = requests.post(
            f"{self.base_url}/api/upload/",
            headers=headers,
            files=files
        )
        response.raise_for_status()
        return response.json()
    
    def get_task_status(self, task_id):
        """获取任务状态"""
        headers = {'X-Session-ID': self.session_id}
        response = requests.get(
            f"{self.base_url}/api/task/{task_id}/status",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, task_id, timeout=300):
        """等待任务完成"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            if status['status'] == 'completed':
                return status
            elif status['status'] == 'failed':
                raise Exception(f"Task failed: {status.get('message', 'Unknown error')}")
            time.sleep(2)
        raise TimeoutError("Task did not complete within timeout")
    
    def download_file(self, task_id, filename, output_path):
        """下载文件"""
        headers = {'X-Session-ID': self.session_id}
        response = requests.get(
            f"{self.base_url}/api/download/{task_id}/{filename}",
            headers=headers,
            stream=True
        )
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

# 使用示例
client = InvoiceProcessorClient("https://your-domain.com")

# 创建会话
session = client.create_session()
print(f"Created session: {session['session_id']}")

# 上传文件
upload_result = client.upload_files(["invoice1.pdf", "invoice2.pdf"])
task_id = upload_result['taskId']
print(f"Uploaded files, task ID: {task_id}")

# 等待处理完成
result = client.wait_for_completion(task_id)
print(f"Task completed: {result}")

# 下载结果
if result['downloadUrls']:
    filename = result['downloadUrls'][0].split('/')[-1]
    client.download_file(task_id, filename, "processed_result.pdf")
    print("Downloaded result file")
```

### JavaScript示例

```javascript
class InvoiceProcessorClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.sessionId = null;
    }

    async createSession() {
        const response = await fetch(`${this.baseUrl}/api/session`, {
            method: 'POST'
        });
        const data = await response.json();
        this.sessionId = data.session_id;
        return data;
    }

    async uploadFiles(files) {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });

        const response = await fetch(`${this.baseUrl}/api/upload/`, {
            method: 'POST',
            headers: {
                'X-Session-ID': this.sessionId
            },
            body: formData
        });
        return await response.json();
    }

    async getTaskStatus(taskId) {
        const response = await fetch(`${this.baseUrl}/api/task/${taskId}/status`, {
            headers: {
                'X-Session-ID': this.sessionId
            }
        });
        return await response.json();
    }

    async waitForCompletion(taskId, timeout = 300000) {
        const startTime = Date.now();
        while (Date.now() - startTime < timeout) {
            const status = await this.getTaskStatus(taskId);
            if (status.status === 'completed') {
                return status;
            } else if (status.status === 'failed') {
                throw new Error(`Task failed: ${status.message || 'Unknown error'}`);
            }
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        throw new Error('Task did not complete within timeout');
    }

    getDownloadUrl(taskId, filename) {
        return `${this.baseUrl}/api/download/${taskId}/${filename}`;
    }
}

// 使用示例
const client = new InvoiceProcessorClient('https://your-domain.com');

async function processInvoices() {
    try {
        // 创建会话
        const session = await client.createSession();
        console.log('Created session:', session.session_id);

        // 上传文件
        const fileInput = document.getElementById('fileInput');
        const uploadResult = await client.uploadFiles(fileInput.files);
        console.log('Upload result:', uploadResult);

        // 等待处理完成
        const result = await client.waitForCompletion(uploadResult.taskId);
        console.log('Task completed:', result);

        // 创建下载链接
        if (result.downloadUrls && result.downloadUrls.length > 0) {
            const filename = result.downloadUrls[0].split('/').pop();
            const downloadUrl = client.getDownloadUrl(uploadResult.taskId, filename);
            
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = filename;
            link.click();
        }
    } catch (error) {
        console.error('Error processing invoices:', error);
    }
}
```

## 最佳实践

### 1. 会话管理
- 在应用启动时创建会话并保存会话ID
- 定期检查会话有效性
- 在会话过期前重新创建会话

### 2. 错误处理
- 始终检查HTTP状态码
- 实现重试机制处理临时错误
- 记录详细的错误信息用于调试

### 3. 文件上传
- 在上传前验证文件类型和大小
- 使用分块上传处理大文件
- 显示上传进度给用户

### 4. 任务监控
- 使用轮询方式监控任务状态
- 设置合理的轮询间隔（建议2-5秒）
- 实现超时机制避免无限等待

### 5. 性能优化
- 使用HTTP/2连接复用
- 实现客户端缓存机制
- 并行处理多个任务

## 版本更新

### v1.0.0 (当前版本)
- 初始API版本
- 支持PDF和ZIP文件上传
- 异步任务处理
- 会话管理
- 文件下载和预览

### 计划功能
- API密钥认证
- Webhook通知
- 批量操作API
- 更多文件格式支持

## 技术支持

如有技术问题或建议，请通过以下方式联系：

- 文档: [README.md](README.md)
- 部署指南: [HTTPS.md](HTTPS.md)
- 生产环境: [PRODUCTION.md](PRODUCTION.md)

---

*最后更新: 2024年12月18日*