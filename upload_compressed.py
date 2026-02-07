#!/usr/bin/env python3
"""
上传压缩的 chunks 文件到 GitHub
"""

import requests
import base64
from pathlib import Path

def upload_file(file_path, repo, token):
    """上传单个文件"""
    file_name = Path(file_path).name
    url = f"https://api.github.com/repos/{repo}/contents/data/{file_name}"
    
    headers = {"Authorization": f"token {token}"}
    
    # 检查文件是否存在
    check = requests.get(url, headers=headers)
    existing_sha = check.json().get('sha') if check.status_code == 200 else None
    
    # 读取文件
    with open(file_path, 'rb') as f:
        content = base64.b64encode(f.read()).decode('utf-8')
    
    data = {
        "message": f"Add {file_name}",
        "content": content
    }
    if existing_sha:
        data["sha"] = existing_sha
    
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print(f"✅ {file_name} 上传成功 ({len(content)//1024//1024}MB)")
        return True
    else:
        print(f"❌ {file_name} 失败: {response.status_code}")
        return False

if __name__ == "__main__":
    repo = "ahfungon/snowsword-wiki"
    token = "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"
    data_dir = Path("/Users/ahfun/.openclaw/workspace/snowsword-wiki/data")
    
    print("开始上传压缩的 chunks 文件...\n")
    
    for file in sorted(data_dir.glob("chunks_small_*.gz")):
        upload_file(file, repo, token)

    print("\n全部上传完成！")
