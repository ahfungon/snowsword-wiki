#!/usr/bin/env python3
"""
上传分块文件到 GitHub
"""

import requests
import base64
import os
from pathlib import Path

def upload_file(file_path, repo, token):
    """上传单个文件到 GitHub"""
    file_name = Path(file_path).name
    url = f"https://api.github.com/repos/{repo}/contents/data/{file_name}"
    
    # 读取并编码文件
    with open(file_path, 'rb') as f:
        content = base64.b64encode(f.read()).decode('utf-8')
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "message": f"Add {file_name}",
        "content": content
    }
    
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print(f"✅ {file_name} 上传成功")
        return True
    else:
        print(f"❌ {file_name} 上传失败: {response.status_code}")
        print(response.text[:200])
        return False

if __name__ == "__main__":
    repo = "ahfungon/snowsword-wiki"
    token = "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"
    data_dir = Path("/Users/ahfun/.openclaw/workspace/snowsword-wiki/data")
    
    # 上传所有分块文件
    for file in sorted(data_dir.glob("chunks_part_*")):
        upload_file(file, repo, token)
        print()
