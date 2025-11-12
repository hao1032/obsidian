document.addEventListener('DOMContentLoaded', function() {
    const loadingElement = document.getElementById('loading');
    const errorElement = document.getElementById('error');
    const tableElement = document.getElementById('panTable');
    const tableBody = document.getElementById('tableBody');

    // 从 URL 获取初始路径
    let currentPath = getPathFromURL() || '/';
    let currentData = []; // 存储当前数据用于排序
    let sortState = { column: null, direction: 'asc' }; // 排序状态

    // 初始化加载
    loadData(currentPath);

    // 监听浏览器前进后退按钮
    window.addEventListener('popstate', function(event) {
        const path = getPathFromURL() || '/';
        if (path !== currentPath) {
            currentPath = path;
            loadData(currentPath, false);
        }
    });

    function getPathFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('path') || '/';
    }

    function updateURL(path, updateHistory = true) {
        const newUrl = new URL(window.location);
        if (path === '/') {
            newUrl.searchParams.delete('path');
        } else {
            newUrl.searchParams.set('path', path);
        }

        if (updateHistory) {
            window.history.pushState({ path: path }, '', newUrl);
        } else {
            window.history.replaceState({ path: path }, '', newUrl);
        }
    }

    function loadData(path, updateHistory = true) {
        loadingElement.style.display = 'block';
        errorElement.style.display = 'none';
        tableElement.style.display = 'none';

        console.log('正在加载路径:', path);

        // 更新 URL
        updateURL(path, updateHistory);

        fetch(`https://lbepan.luoboedu.com?path=${encodeURIComponent(path)}`)
            .then(response => response.text())
            .then(text => {
                console.log('原始响应:', text);

                // 双重解析处理
                let data;
                try {
                    const firstParse = JSON.parse(text);
                    data = typeof firstParse === 'string' ? JSON.parse(firstParse) : firstParse;
                } catch (e) {
                    throw new Error('数据解析失败: ' + e.message);
                }

                loadingElement.style.display = 'none';

                if (data.list && data.list.length > 0) {
                    currentData = data.list; // 保存数据用于排序
                    renderTable(currentData, path);
                    tableElement.style.display = 'table';
                    updateBreadcrumb(path);
                    updateSortIcons(); // 更新排序图标
                } else {
                    currentData = [];
                    errorElement.textContent = '当前文件夹为空';
                    errorElement.style.display = 'block';
                    updateBreadcrumb(path);
                }
            })
            .catch(error => {
                loadingElement.style.display = 'none';
                errorElement.textContent = '加载失败: ' + error.message;
                errorElement.style.display = 'block';
                console.error('错误详情:', error);
            });
    }

    function renderTable(list, currentPath) {
        tableBody.innerHTML = '';

        // 添加上一级目录（如果不是根目录）
        if (currentPath !== '/') {
            const parentRow = document.createElement('tr');
            const parentPath = getParentPath(currentPath);

            parentRow.innerHTML = `
                <td>📁 <a href="javascript:void(0)" class="folder-link" data-path="${parentPath}">../ （返回上一级）</a></td>
                <td>-</td>
                <td>-</td>
                <td>文件夹</td>
            `;
            tableBody.appendChild(parentRow);
        }

        list.forEach(item => {
            const row = document.createElement('tr');

            // 如果是文件夹，名称可点击
            const nameCell = item.is_dir ?
                `📁 <a href="javascript:void(0)" class="folder-link" data-path="${item.path}">${item.name}</a>` :
                `📄 ${item.name}`;

            row.innerHTML = `
                <td>${nameCell}</td>
                <td>${item.time}</td>
                <td>${item.size}</td>
                <td>${item.is_dir ? '文件夹' : '文件'}</td>
            `;

            tableBody.appendChild(row);
        });

        // 添加点击事件监听
        addFolderClickListeners();
    }

    function addFolderClickListeners() {
        const folderLinks = document.querySelectorAll('.folder-link');
        folderLinks.forEach(link => {
            link.addEventListener('click', function() {
                const path = this.getAttribute('data-path');
                navigateTo(path);
            });
        });
    }

    function navigateTo(path) {
        currentPath = path;
        loadData(path);
    }

    function getParentPath(path) {
        if (path === '/') return '/';
        const paths = path.split('/').filter(p => p);
        paths.pop();
        return paths.length > 0 ? '/' + paths.join('/') : '/';
    }

    function updateBreadcrumb(path) {
        const breadcrumb = document.getElementById('breadcrumb');
        if (breadcrumb) {
            const paths = path.split('/').filter(p => p);
            let breadcrumbHtml = '<a href="javascript:void(0)" class="breadcrumb-link" data-path="/">根目录</a>';

            let currentPath = '';
            paths.forEach((folder, index) => {
                currentPath += '/' + folder;
                breadcrumbHtml += ` / <a href="javascript:void(0)" class="breadcrumb-link" data-path="${currentPath}">${folder}</a>`;
            });

            breadcrumb.innerHTML = breadcrumbHtml;

            document.querySelectorAll('.breadcrumb-link').forEach(link => {
                link.addEventListener('click', function() {
                    const path = this.getAttribute('data-path');
                    navigateTo(path);
                });
            });
        }

        updatePageTitle(path);
    }

    function updatePageTitle(path) {
        if (path === '/') {
            document.title = '网盘文件列表 - 根目录';
        } else {
            const folderName = path.split('/').filter(p => p).pop();
            document.title = `网盘文件列表 - ${folderName}`;
        }
    }

    // 排序功能
    function sortTable(column) {
        if (currentData.length === 0) return;

        // 切换排序方向或设置新列
        if (sortState.column === column) {
            sortState.direction = sortState.direction === 'asc' ? 'desc' : 'asc';
        } else {
            sortState.column = column;
            sortState.direction = 'asc';
        }

        // 执行排序
        const sortedData = [...currentData].sort((a, b) => {
            let valueA, valueB;

            switch (column) {
                case 'name':
                    valueA = a.name.toLowerCase();
                    valueB = b.name.toLowerCase();
                    break;
                case 'time':
                    valueA = new Date(a.time);
                    valueB = new Date(b.time);
                    break;
                case 'size':
                    // 转换大小为字节数进行比较
                    valueA = parseSizeToBytes(a.size);
                    valueB = parseSizeToBytes(b.size);
                    break;
                case 'type':
                    valueA = a.is_dir ? 0 : 1; // 文件夹在前
                    valueB = b.is_dir ? 0 : 1;
                    break;
                default:
                    return 0;
            }

            if (valueA < valueB) return sortState.direction === 'asc' ? -1 : 1;
            if (valueA > valueB) return sortState.direction === 'asc' ? 1 : -1;
            return 0;
        });

        // 重新渲染表格
        renderTable(sortedData, currentPath);
        updateSortIcons();
    }

    function parseSizeToBytes(size) {
        if (!size || size === '0.0 B') return 0;

        const units = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024,
            'TB': 1024 * 1024 * 1024 * 1024
        };

        const match = size.match(/^([\d.]+)\s*([KMGTP]?B)$/i);
        if (match) {
            const value = parseFloat(match[1]);
            const unit = match[2].toUpperCase();
            return value * (units[unit] || 1);
        }

        return 0;
    }

    function updateSortIcons() {
        // 移除所有排序图标
        document.querySelectorAll('.sortable').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
        });

        // 添加当前排序状态的图标
        if (sortState.column) {
            const currentTh = document.querySelector(`.sortable[data-column="${sortState.column}"]`);
            if (currentTh) {
                currentTh.classList.add(sortState.direction === 'asc' ? 'sort-asc' : 'sort-desc');
            }
        }
    }

    // 添加表头点击事件
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('sortable') || e.target.closest('.sortable')) {
            const th = e.target.classList.contains('sortable') ? e.target : e.target.closest('.sortable');
            const column = th.getAttribute('data-column');
            sortTable(column);
        }
    });
});