import os
import json
import re
import argparse
from collections import defaultdict

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Generate download pages for XPlane files')
    parser.add_argument('scan_dir', 
                       help='Directory to scan for .tar.gz files')
    parser.add_argument('--output-dir', '-o',
                       default='.',
                       help='Directory to output generated files (default: current directory)')
    return parser.parse_args()

def scan_files(directory):
    """扫描目录下的所有 .tar.gz 文件并按类型分类"""
    files = defaultdict(list)
    version_pattern = re.compile(r'([^-]+)-v(\d+\.\d+\.\d+)-([^.]+)\.tar\.gz')
    
    print(f"Scanning directory: {directory}")
    for file in os.listdir(directory):
        if file.endswith('.tar.gz'):
            match = version_pattern.match(file)
            if match:
                project, version, platform = match.groups()
                key = f"{project}-{platform}"
                files[key].append({
                    'filename': file,
                    'version': version,
                    'project': project,
                    'platform': platform
                })
                print(f"Found file: {file}")
            else:
                print(f"Warning: File {file} doesn't match the expected pattern")
    
    return files

def version_sort(version_str):
    """版本号排序辅助函数"""
    return [int(x) for x in version_str.split('.')]

def generate_versions_json(files):
    """生成 versions.json 文件"""
    versions = {}
    
    for key, file_list in files.items():
        # 按版本号排序，获取最新版本
        latest_file = sorted(file_list, key=lambda x: version_sort(x['version']))[-1]
        versions[key] = {
            'latest': latest_file['filename']
        }
    
    return versions

def generate_redirects(files):
    """生成 Netlify _redirects 文件内容"""
    redirects = []
    for key, value in files.items():
        target_file = value['latest']
        redirects.append(f"/{key}/latest /{target_file} 302")
    return "\n".join(redirects)

def generate_index_html():
    """生成 index.html 模板"""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>XPlane Downloads</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        .download-section {
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #fff;
        }
        .download-link {
            display: inline-block;
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 3px;
            margin: 10px 0;
            transition: background-color 0.3s ease;
        }
        .download-link:hover {
            background-color: #45a049;
        }
        .command-container {
            display: flex;
            align-items: center;
            margin: 10px 0;
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 3px;
            border: 1px solid #ddd;
        }
        .download-command {
            flex-grow: 1;
            font-family: monospace;
            margin-right: 10px;
            word-break: break-all;
        }
        .copy-button {
            padding: 5px 15px;
            background-color: #666;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 14px;
            min-width: 60px;
            transition: background-color 0.3s ease;
        }
        .copy-button:hover {
            background-color: #555;
        }
        .copy-button.copied {
            background-color: #4CAF50;
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }
        h2 {
            color: #444;
            margin-top: 0;
        }
        p {
            color: #666;
            margin: 10px 0 5px 0;
        }
    </style>
</head>
<body>
    <h1>XPlane Downloads</h1>
    <div id="download-containers"></div>

    <script>
        function copyCommand(commandId, button) {
            const commandElement = document.getElementById(commandId);
            const text = commandElement.textContent;
            
            // 创建临时文本区域
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            
            try {
                document.execCommand('copy');
                button.textContent = '已复制!';
                button.classList.add('copied');
                setTimeout(() => {
                    button.textContent = '复制';
                    button.classList.remove('copied');
                }, 2000);
            } catch (err) {
                console.error('复制失败:', err);
                button.textContent = '复制失败';
                setTimeout(() => {
                    button.textContent = '复制';
                }, 2000);
            }
            
            document.body.removeChild(textarea);
        }

        fetch('versions.json')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('download-containers');
                let commandCounter = 0;
                
                for (const [key, value] of Object.entries(data)) {
                    const section = document.createElement('div');
                    section.className = 'download-section';
                    
                    const displayName = key
                        .replace('XPlaneUDP-', 'XPlaneUDP for ')
                        .replace('xp_plugin-', 'XP Plugin for ')
                        .replace('-x86_64', ' x86_64');

                    const curlCommand = `curl -L ${window.location.origin}/${key}/latest -o ${value.latest}`;
                    const wgetCommand = `wget ${window.location.origin}/${key}/latest -O ${value.latest}`;

                    const curlId = `command-${commandCounter++}`;
                    const wgetId = `command-${commandCounter++}`;

                    section.innerHTML = `
                        <h2>${displayName}</h2>
                        <p>Latest version: ${value.latest}</p>
                        <a href="${value.latest}" class="download-link">Download Latest</a>
                        <p>或使用命令行下载:</p>
                        <div class="command-container">
                            <div class="download-command" id="${curlId}">${curlCommand}</div>
                            <button class="copy-button" onclick="copyCommand('${curlId}', this)">复制</button>
                        </div>
                        <div class="command-container">
                            <div class="download-command" id="${wgetId}">${wgetCommand}</div>
                            <button class="copy-button" onclick="copyCommand('${wgetId}', this)">复制</button>
                        </div>
                    `;
                    
                    container.appendChild(section);
                }
            })
            .catch(error => {
                console.error('Error loading versions:', error);
                document.getElementById('download-containers').innerHTML = 
                    '<p>Error loading download information. Please try again later.</p>';
            });
    </script>
</body>
</html>
'''

def main():
    args = parse_args()
    
    # 扫描文件
    files = scan_files(args.scan_dir)
    
    if not files:
        print("No valid .tar.gz files found in the specified directory")
        return
    
    # 生成 versions.json
    versions = generate_versions_json(files)
    json_path = os.path.join(args.output_dir, 'versions.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(versions, f, indent=2)
    print(f"Generated {json_path}")
    
    # 生成 _redirects 文件
    redirects_path = os.path.join(args.output_dir, '_redirects')
    with open(redirects_path, 'w', encoding='utf-8') as f:
        f.write(generate_redirects(versions))
    print(f"Generated {redirects_path}")
    
    # 生成 index.html
    index_path = os.path.join(args.output_dir, 'index.html')
    if not os.path.exists(index_path):
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(generate_index_html())
        print(f"Generated {index_path}")
    else:
        print(f"{index_path} already exists, skipping...")

if __name__ == '__main__':
    main()
