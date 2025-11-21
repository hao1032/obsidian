import logging

# 设置日志
log = logging.getLogger("mkdocs")


def delete_table_columns_by_names(markdown_content, columns_to_delete):
    """
    遍历 Markdown 内容，根据列名列表删除整个表格中的指定列。

    :param markdown_content: 原始 Markdown 字符串
    :param columns_to_delete: 要删除的列名列表 (List[str])
    :return: 修改后的 Markdown 字符串
    """
    new_markdown_lines = []
    lines = markdown_content.splitlines()

    # 存储当前表格需要删除的列索引列表
    target_indices = []

    # 状态机：0=未找到表头, 1=找到表头, 2=找到分隔线
    table_state = 0

    for line in lines:
        stripped_line = line.strip()

        # --- 1. 识别表头行 (状态 0 -> 1) ---
        # 只有在未处理表格状态下，且行以 | 开头和结尾，才被视为潜在表头
        if table_state == 0 and stripped_line.startswith('|') and stripped_line.endswith('|'):

            # 提取表头单元格
            header_cells = [c.strip() for c in stripped_line.split('|')][1:-1]

            current_indices = []
            found_names = []

            # 遍历需要删除的列名，查找它们在表头中的位置
            for col_name in columns_to_delete:
                try:
                    # 假设完全匹配 (可根据需求改为 header_cell in col_name 等模糊匹配)
                    idx = header_cells.index(col_name.strip())
                    current_indices.append(idx)
                    found_names.append(col_name)
                except ValueError:
                    # 表格中没有这个列名，忽略
                    pass

            if current_indices:
                # 关键步骤：必须倒序排列索引！
                # 因为如果先删除了索引 1，原本的索引 3 就会变成 2。
                # 倒序删除（先删后面的）可以避免索引位移问题。
                current_indices.sort(reverse=True)
                target_indices = current_indices
                print(f"✅ 在表格中找到列 {found_names}，准备删除索引: {target_indices}")
                table_state = 1  # 标记进入表格处理
            else:
                # 这个表格不包含我们要删除的任何列，保持 table_state = 0，当作普通文本处理
                target_indices = []

        # --- 2. 处理表格行 (表头、分隔线、数据) ---
        if target_indices and stripped_line.startswith('|') and stripped_line.endswith('|'):

            # 提取单元格
            cells = [c.strip() for c in stripped_line.split('|')][1:-1]

            # 为了安全，检查最大索引是否超出当前行长度
            if len(cells) > max(target_indices):

                # 倒序删除指定索引的单元格
                for idx in target_indices:
                    del cells[idx]

                # 重新拼接行
                new_line = '| ' + ' | '.join(cells) + ' |'
                new_markdown_lines.append(new_line)

                # 状态流转：表头 -> 分隔线 -> 数据
                if table_state == 1:
                    table_state = 2

                continue  # 以此行代替原行，进入下一循环
            else:
                # 单元格数量异常（比如某一行特别短），重置状态
                target_indices = []
                table_state = 0

        # --- 3. 非表格行 或 表格结束 ---
        new_markdown_lines.append(line)

        # 如果遇到非表格行（不以|开头），重置状态
        if table_state > 0 and not stripped_line.startswith('|'):
            target_indices = []
            table_state = 0

    return '\n'.join(new_markdown_lines)


def transform_table(markdown_content):
    """
    专门针对竞赛时间表的转换逻辑：
    将 5列 表格转换为 2列 (名称, 时间详情)
    """
    new_lines = []
    lines = markdown_content.splitlines()

    # 状态机
    # 0: 寻找表头
    # 1: 处理分隔线
    # 2: 处理数据行
    state = 0

    # 这里的列名必须和 MD 文件里的完全一致
    # 我们将把这些列合并到 "时间" 列中
    TARGET_HEADERS = ["上次报名截止", "上次考试", "下次报名截止", "下次考试"]
    PIVOT_HEADER = "名称"

    # 存储列索引的映射 {index: "列名"}
    col_map = {}
    pivot_idx = -1

    for line in lines:
        stripped = line.strip()

        # --- 1. 识别表头 ---
        if state == 0:
            if stripped.startswith('|') and stripped.endswith('|'):
                # 去除首尾 | 并分割
                cells = [c.strip() for c in stripped.split('|')][1:-1]

                # 检查这个表格是否包含我们要处理的所有关键列
                # 使用集合判断，只要包含这些列即可触发（顺序不重要）
                if PIVOT_HEADER in cells and all(h in cells for h in TARGET_HEADERS):
                    print("⚡ 发现竞赛时间表，正在转换结构...")

                    # 记录索引位置
                    pivot_idx = cells.index(PIVOT_HEADER)
                    col_map = {}
                    for h in TARGET_HEADERS:
                        if h in cells:
                            col_map[cells.index(h)] = h

                    # 构造新表头
                    new_lines.append(f"| {PIVOT_HEADER} | 时间 |")
                    state = 1
                    continue  # 进入下一行

            # 如果不是目标表格，保持原样
            new_lines.append(line)

        # --- 2. 处理分隔线 ---
        elif state == 1:
            # 直接替换为两列的分隔线
            if stripped.startswith('|'):
                new_lines.append("| :--- | :--- |")  # 左对齐
                state = 2
            else:
                # 异常情况，重置
                new_lines.append(line)
                state = 0

        # --- 3. 处理数据行 ---
        elif state == 2:
            if stripped.startswith('|'):
                cells = [c.strip() for c in stripped.split('|')][1:-1]

                # 获取名称列
                name_val = ""
                if pivot_idx < len(cells):
                    name_val = cells[pivot_idx]

                # 拼接时间详情
                details_parts = []

                # 按照 TARGET_HEADERS 的定义顺序来显示，确保逻辑清晰
                # (而不是按照原表格的物理顺序)
                for target_h in TARGET_HEADERS:
                    # 找到该列在当前行对应的索引
                    current_col_idx = -1
                    for idx, name in col_map.items():
                        if name == target_h:
                            current_col_idx = idx
                            break

                    if current_col_idx != -1 and current_col_idx < len(cells):
                        val = cells[current_col_idx].strip()
                        # 只有当单元格有内容时才显示
                        if val and val != "-":
                            # 这里是核心：使用 HTML 标签 <br> 来换行，** 加粗标签
                            details_parts.append(f"**{target_h}**：{val}")

                # 用 <br> 连接所有部分
                final_details = "<br>".join(details_parts)

                # 构造新行
                new_lines.append(f"| {name_val} | {final_details} |")

            else:
                # 表格结束
                new_lines.append(line)
                state = 0

    return "\n".join(new_lines)


def on_page_markdown(markdown, page, config, files):
    """
    MkDocs 钩子函数
    """
    # 检查开关
    if page.meta.get('enable_hook', False):
        # 允许用户在 YAML 中写成列表，或者单字符串
        raw_config = page.meta.get('columns_to_delete')
        target_columns = []

        if raw_config:
            if isinstance(raw_config, list):
                # 如果是 YAML list: ['col1', 'col2']
                target_columns = [str(c).strip() for c in raw_config]
            elif isinstance(raw_config, str):
                # 如果是 YAML string: "col1" 或 "col1, col2"
                if ',' in raw_config:
                    target_columns = [c.strip() for c in raw_config.split(',')]
                else:
                    target_columns = [raw_config.strip()]

        if target_columns:
            print(f"ℹ️ 处理文件: {page.file.src_path} | 目标删除列: {target_columns}")
            markdown = delete_table_columns_by_names(markdown, target_columns)

        markdown = transform_table(markdown)

    return markdown