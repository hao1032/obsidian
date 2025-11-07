# 网盘文件列表

<div id="breadcrumb" style="margin-bottom: 20px; padding: 10px; background: #f5f5f5; border-radius: 5px;">
    <a href="?path=/" id="rootLink">根目录</a>
    <span id="pathDisplay"></span>
</div>

<div id="loading">正在加载数据...</div>
<div id="error" style="display: none; color: red;"></div>

<!-- 静态表格作为回退 -->
<table>
  <thead>
    <tr>
      <th>名称</th>
      <th>修改时间</th>
      <th>大小</th>
      <th>类型</th>
    </tr>
  </thead>
  <tbody id="tableBody">
    <tr><td colspan="4">加载中...</td></tr>
  </tbody>
</table>

<script>
// 获取 URL 中的 path 参数
function getPathFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('path') || '/';
}

// 更新 URL
function updateURL(path) {
    const newUrl = new URL(window.location);
    if (path === '/') {
        newUrl.searchParams.delete('path');
    } else {
        newUrl.searchParams.set('path', path);
    }
    window.history.pushState({}, '', newUrl);
}

// 获取父级路径
function getParentPath(path) {
    if (path === '/') return '/';
    const paths = path.split('/').filter(p => p);
    paths.pop();
    return paths.length > 0 ? '/' + paths.join('/') : '/';
}

// 加载数据
function loadData(path) {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('error').style.display = 'none';
    
    // 更新面包屑
    updateBreadcrumb(path);
    
    fetch(`https://lbepan.luoboedu.com?path=${encodeURIComponent(path)}`)
        .then(response => response.text())
        .then(text => {
            // 双重解析处理
            const firstParse = JSON.parse(text);
            const data = typeof firstParse === 'string' ? JSON.parse(firstParse) : firstParse;
            
            document.getElementById('loading').style.display = 'none';
            
            if (data.list && data.list.length > 0) {
                renderTable(data.list, path);
            } else {
                document.getElementById('error').textContent = '当前文件夹为空';
                document.getElementById('error').style.display = 'block';
            }
        })
        .catch(error => {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('error').textContent = '加载失败: ' + error.message;
            document.getElementById('error').style.display = 'block';
        });
}

// 渲染表格
function renderTable(list, currentPath) {
    const tbody = document.getElementById('tableBody');
    let html = '';
    
    // 添加上一级目录（如果不是根目录）
    if (currentPath !== '/') {
        const parentPath = getParentPath(currentPath);
        html += `
            <tr>
                <td>📁 <a href="javascript:void(0)" onclick="navigateTo('${parentPath}')">../ （返回上一级）</a></td>
                <td>-</td>
                <td>-</td>
                <td>文件夹</td>
            </tr>
        `;
    }
    
    // 添加文件列表
    list.forEach(item => {
        if (item.is_dir) {
            html += `
                <tr>
                    <td>📁 <a href="javascript:void(0)" onclick="navigateTo('${item.path}')">${item.name}</a></td>
                    <td>${item.time}</td>
                    <td>${item.size}</td>
                    <td>文件夹</td>
                </tr>
            `;
        } else {
            html += `
                <tr>
                    <td>📄 ${item.name}</td>
                    <td>${item.time}</td>
                    <td>${item.size}</td>
                    <td>文件</td>
                </tr>
            `;
        }
    });
    
    tbody.innerHTML = html;
}

// 更新面包屑导航
function updateBreadcrumb(path) {
    const pathDisplay = document.getElementById('pathDisplay');
    if (path === '/') {
        pathDisplay.innerHTML = '';
        return;
    }
    
    const paths = path.split('/').filter(p => p);
    let breadcrumbHtml = '';
    let currentPath = '';
    
    paths.forEach((folder, index) => {
        currentPath += '/' + folder;
        breadcrumbHtml += ` / <a href="javascript:void(0)" onclick="navigateTo('${currentPath}')">${folder}</a>`;
    });
    
    pathDisplay.innerHTML = breadcrumbHtml;
}

// 导航到指定路径
function navigateTo(path) {
    updateURL(path);
    loadData(path);
}

// 监听浏览器前进后退
window.addEventListener('popstate', function() {
    const path = getPathFromURL();
    loadData(path);
});

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    const path = getPathFromURL();
    loadData(path);

    document$.subscribe(function() {
      var tables = document.querySelectorAll("article table:not([class])")
      tables.forEach(function(table) {
        new Tablesort(table)
      })
    })


});
</script>