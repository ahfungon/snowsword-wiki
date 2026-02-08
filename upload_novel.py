#!/usr/bin/env python3
"""
分块上传大文件到 GitHub
"""

import requests
import base64
import os
from pathlib import Path

def upload_large_file(file_path, repo, token, chunk_size=1024*1024):
    """分块上传大文件"""
    file_name = Path(file_path).name
    url = f"https://api.github.com/repos/{repo}/contents/data/{file_name}"
    
    # 先检查文件是否存在
    headers = {"Authorization": f"token {token}"}
    check_resp = requests.get(url, headers=headers)
    
    if check_resp.status_code == 200:
        existing_sha = check_resp.json().get('sha')
        print(f"文件已存在，SHA: {existing_sha}")
    else:
        existing_sha = None
        print(f"文件不存在，准备上传")
    
    # 读取文件
    with open(file_path, 'rb') as f:
        content = f.read()
    
    print(f"文件大小: {len(content)} 字节")
    
    # GitHub API 限制：内容必须 base64 编码且小于 100MB
    # 14MB 应该可以一次性上传
    encoded = base64.b64encode(content).decode('utf-8')
    
    data = {
        "message": f"Add {file_name}",
        "content": encoded
    }
    
    if existing_sha:
        data["sha"] = existing_sha
    
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print(f"✅ {file_name} 上传成功")
        return True
    else:
        print(f"❌ {file_name} 上传失败: {response.status_code}")
        print(response.text[:500])
        return False

if __name__ == "__main__":
    repo = "ahfungon/snowsword-wiki"
    token = "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"
    file_path = "/Users/ahfun/.openclaw/workspace/snowsword-wiki/data/雪中悍刀行.txt"
    
    upload_large_file(file_path, repo, token)
