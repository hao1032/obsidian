import logging

# 设置日志，以便在控制台看到输出
log = logging.getLogger("mkdocs")


def delete_table_column_by_name(markdown_content, column_name_to_delete):
    """
    遍历 Markdown 内容，根据列名删除整个表格中的指定列。

    :param markdown_content: 原始 Markdown 字符串
    :param column_name_to_delete: 要删除的列的名称
    :return: 修改后的 Markdown 字符串
    """
    new_markdown_lines = []
    lines = markdown_content.splitlines()
    column_index_to_delete = -1

    # 状态机：0=未找到表头, 1=找到表头, 2=找到分隔线
    table_state = 0

    for line in lines:
        stripped_line = line.strip()

        # 1. 尝试识别表头行（第一次遇到以 | 开始和结束的行）
        if table_state == 0 and stripped_line.startswith('|') and stripped_line.endswith('|'):

            # 提取表头单元格，并去除两边的空字符串
            header_cells = [c.strip() for c in stripped_line.split('|')][1:-1]

            # 查找目标列名的索引
            try:
                # 忽略大小写和空格进行匹配
                # 这里假设用户在 Meta-data 中填写的列名与表头中的列名是精确匹配的
                match_name = column_name_to_delete.strip()
                column_index_to_delete = header_cells.index(match_name)
                print(f"✅ 找到要删除的列: '{column_name_to_delete}'，索引为: {column_index_to_delete}")
            except ValueError:
                # 如果找不到，就跳过这个表格的处理
                column_index_to_delete = -1
                print(f"⚠️ 找不到列名 '{column_name_to_delete}'，跳过表格处理。")

            table_state = 1  # 标记为已找到表头

        # 2. 处理表头行、分隔线和数据行
        if column_index_to_delete != -1 and stripped_line.startswith('|') and stripped_line.endswith('|'):

            # 提取有效内容单元格
            cells = [c.strip() for c in stripped_line.split('|')][1:-1]

            # 确保行不是空的，且索引有效
            if len(cells) > column_index_to_delete:

                # 删除目标索引的单元格
                del cells[column_index_to_delete]

                # 重新拼接行，注意保留原始的对齐格式（对于分隔线）
                new_line = '| ' + ' | '.join(cells) + ' |'
                new_markdown_lines.append(new_line)

                # 如果是表头或数据行，下一行可能是分隔线或下一个表格/内容
                if table_state == 1:
                    table_state = 2  # 找到分隔线，下一行就是数据

                continue  # 已处理，进入下一行

            # 如果单元格数量不够，说明表格结束或者有问题，重置状态
            column_index_to_delete = -1
            table_state = 0

        # 3. 非表格行或表格处理完毕后的行
        new_markdown_lines.append(line)

        # 如果遇到非表格行，且我们已处于表格处理状态，则认为表格已结束
        if table_state > 0 and not stripped_line.startswith('|'):
            # 遇到表格后的第一个非表格行，重置删除索引，等待下一个表格
            column_index_to_delete = -1
            table_state = 0

    return '\n'.join(new_markdown_lines)

def on_page_markdown(markdown, page, config, files):
    """
    该函数会在每个页面处理 Markdown 内容时被调用。
    :param markdown: 原始 Markdown 字符串
    :param page: 当前页面的对象 (包含 title, url 等信息)
    :param config: 全局配置对象
    :param files: 所有文件列表
    :return: 返回修改后的 Markdown (如果不修改则返回 markdown 或 None)
    """

    # page.meta 是一个字典，包含了文件头部的 YAML 数据

    # 检查是否存在 'enable_my_hook' 且为 True
    if page.meta.get('enable_hook', False):
        # 从 Markdown 文件的 Meta-data (YAML Front Matter) 中获取列名
        column_to_remove = page.meta.get('column_to_remove').strip()
        if column_to_remove:
            # 如果 Meta-data 中指定了要删除的列名
            print(f"ℹ️ 正在处理文件: {page.file.src_path}。从 Meta-data 读取到要删除的列: '{column_to_remove}'")

            # 调用核心处理函数
            return delete_table_column_by_name(markdown, column_to_remove)

    # 如果没有标记，直接忽略，不做处理
    return markdown