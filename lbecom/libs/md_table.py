import re


class MarkdownTableEditor:
    """
    用于解析、编辑和重新生成 Markdown 表格的类。

    主要功能：
    1. 解析 Markdown 源代码中的所有表格。
    2. 通过关键字定位特定的表格。
    3. 获取表格的尺寸、行头和列头列表。
    4. 通过行头和列头访问或修改单元格值。
    5. 重建更新后的 Markdown 源代码。
    """

    def __init__(self, markdown_source: str):
        self.markdown_source = markdown_source
        # 解析结果存储在这里，每个元素是一个表格的字典
        self.tables_data = self._parse_markdown()

    # --- 内部解析方法 ---

    def _split_table_cell(self, line: str) -> list:
        """从原始表格行中提取单元格内容。"""
        # 移除首尾的 | 和空格，然后按 | 分割
        # 使用非贪婪匹配和处理可能存在的转义 |
        cells = [cell.strip() for cell in re.split(r'(?<!\\)\|', line.strip()) if cell.strip() or cell.strip() == '']
        if cells and cells[0] == '':
            cells = cells[1:]
        if cells and cells[-1] == '':
            cells = cells[:-1]
        return cells

    def _process_table_lines(self, table: dict):
        """解析原始行，提取头部、分隔线和数据。"""
        raw_lines = table['raw_lines']

        if len(raw_lines) < 2:
            return

        # 第1行是 Header
        header_line = raw_lines[0]
        table['header'] = self._split_table_cell(header_line)

        # 第2行是 Alignment
        alignment_line = raw_lines[1]
        align_cells = self._split_table_cell(alignment_line)

        alignment = []
        for cell in align_cells:
            # 检查对齐方式
            if cell.endswith(':') and cell.startswith(':'):
                alignment.append('center')
            elif cell.endswith(':'):
                alignment.append('right')
            elif cell.startswith(':'):
                alignment.append('left')
            else:
                alignment.append('none')  # 默认或未指定
        table['alignment'] = alignment

        # 剩下的行是 Data
        for data_line in raw_lines[2:]:
            table['data'].append(self._split_table_cell(data_line))

        # 修正列数不一致的问题
        num_cols = len(table['header'])
        table['alignment'] = table['alignment'][:num_cols]
        for row in table['data']:
            # 截断或填充
            if len(row) < num_cols:
                row.extend([''] * (num_cols - len(row)))
            elif len(row) > num_cols:
                row[:] = row[:num_cols]

    def _parse_markdown(self):
        """
        解析 Markdown 源代码，提取所有表格及其在源文件中的位置。
        """
        lines = self.markdown_source.splitlines()
        tables = []
        in_table = False
        current_table = None

        # 正则表达式匹配 Markdown 表格的行 | ... | ... |
        table_line_pattern = re.compile(r'^\s*\|.*\|\s*$')

        for i, line in enumerate(lines):
            is_table_line = table_line_pattern.match(line)

            if is_table_line:
                if not in_table:
                    # 表格开始
                    in_table = True
                    current_table = {
                        'start': i,
                        'raw_lines': [line],
                        'header': [],
                        'alignment': [],
                        'data': []
                    }
                else:
                    # 表格持续
                    current_table['raw_lines'].append(line)

            # 如果不在表格中，或者表格行中断
            if in_table and (not is_table_line or i == len(lines) - 1):
                # 表格结束，处理和存储表格数据
                current_table['end'] = i if not is_table_line else i + 1
                self._process_table_lines(current_table)
                tables.append(current_table)
                in_table = False
                current_table = None

        return tables

    # --- 用户接口: 定位与查询 ---

    def find_table_by_keyword(self, keyword: str) -> dict or None:
        """
        通过指定关键字（在表格内容中）定位表格。
        返回找到的第一个表格数据结构，否则返回 None。
        """
        for table in self.tables_data:
            # 在头部中查找
            if keyword in table['header']:
                return table
            # 在数据行中查找
            for row in table['data']:
                if keyword in row:
                    return table
        return None

    def get_table_dimensions(self, table: dict) -> tuple:
        """获取表格的行数和列数（不包括头部和分隔线）。"""
        num_rows = len(table['data'])
        num_cols = len(table['header'])
        return num_rows, num_cols

    def get_column_headers(self, table: dict) -> list:
        """
        获取表格的列头列表 (即表格的 Header 行)。
        """
        return table.get('header', [])

    def get_row_headers(self, table: dict) -> list:
        """
        获取表格的行头列表。
        - 约定：假设表格数据行 (data) 的第一列作为行头。
        """
        row_headers = []
        for row in table['data']:
            if row:
                row_headers.append(row[0])  # 获取每行的第一个单元格作为行头
        return row_headers

    def get_cell_value(self, table: dict, row_header: str, col_header: str) -> str or None:
        """
        通过行头和列头获取对应单元格的值。
        - 假设第一列是行头。
        """
        try:
            col_index = table['header'].index(col_header)
        except ValueError:
            return None  # 列头不存在

        for row in table['data']:
            if row and row[0] == row_header:  # 假设第一列是行头
                # 检查索引是否越界
                if col_index < len(row):
                    return row[col_index]
                else:
                    return ''  # 单元格为空
        return None  # 行头不存在

    # --- 用户接口: 修改 ---

    def set_cell_value(self, table: dict, row_header: str, col_header: str, new_value: str) -> bool:
        """
        通过行头和列头修改对应单元格的值。
        - 假设第一列是行头。
        """
        try:
            col_index = table['header'].index(col_header)
        except ValueError:
            return False  # 列头不存在

        for row in table['data']:
            if row and row[0] == row_header:  # 假设第一列是行头
                # 确保行有足够的列
                if col_index >= len(row):
                    # 扩展行以适应新值
                    row.extend([''] * (col_index - len(row) + 1))

                row[col_index] = new_value
                # 标记需要重新生成 raw_lines
                table['needs_update'] = True
                return True

        return False  # 行头不存在

    # --- 重建 Markdown 方法 ---

    def _reconstruct_table_line(self, cells: list) -> str:
        """将单元格列表重建成 Markdown 表格行。"""
        # 注意：这里只进行简单的重建，不处理列宽对齐问题
        line = '| ' + ' | '.join(cells) + ' |'
        return line

    def _reconstruct_alignment_line(self, alignments: list, num_cols: int) -> str:
        """重构分隔线（对齐线）。"""
        align_cells = []
        for i in range(num_cols):
            align = alignments[i] if i < len(alignments) else 'none'

            # 至少三个 '-' 才能识别为分隔线
            if align == 'left':
                align_cells.append(':---')
            elif align == 'right':
                align_cells.append('---:')
            elif align == 'center':
                align_cells.append(':--:')
            else:
                align_cells.append('----')  # 默认或未指定

        return '|' + '|'.join(align_cells) + '|'

    def rebuild_markdown(self) -> str:
        """
        使用编辑后的表格数据重建完整的 Markdown 源代码。
        """
        lines = self.markdown_source.splitlines()
        output_lines = []
        last_end = 0

        for table in self.tables_data:
            # 复制表格之前的内容
            output_lines.extend(lines[last_end:table['start']])

            # 重建表格行

            # 1. Header
            header_line = self._reconstruct_table_line(table['header'])
            output_lines.append(header_line)

            # 2. Alignment Line
            alignment_line = self._reconstruct_alignment_line(table['alignment'], len(table['header']))
            output_lines.append(alignment_line)

            # 3. Data Rows
            for row in table['data']:
                data_line = self._reconstruct_table_line(row)
                output_lines.append(data_line)

            # 跳过原始表格的所有行
            last_end = table['end']

        # 复制表格之后的内容
        output_lines.extend(lines[last_end:])

        return '\n'.join(output_lines)


if __name__ == '__main__':
    # ----------------------------------------------------
    #                      📌 示例用法
    # ----------------------------------------------------

    source_md = """
    # 文档标题
    
    这是一些文本。
    
    | 区域 | 人口 (百万) | 面积 (万km²) |
    | :--- | :---: | ---: |
    | 北京 | 21 | 1.6 |
    | 上海 | 24 | 0.6 |
    | 深圳 | 17 | 0.2 |
    
    另一段文字。
    """

    # 1. 初始化编辑器
    editor = MarkdownTableEditor(source_md)
    print("--- 原始 Markdown ---")
    print(source_md)
    print("-" * 30)

    # 2. 定位表格
    target_table = editor.find_table_by_keyword('上海')

    if target_table:
        print("✅ 已定位到包含 '上海' 的表格。")

        # 3. 获取信息
        rows, cols = editor.get_table_dimensions(target_table)
        print(f"   - 行数: {rows}, 列数: {cols}")

        column_headers = editor.get_column_headers(target_table)
        print(f"   - 列头: {column_headers}")

        row_headers = editor.get_row_headers(target_table)
        print(f"   - 行头: {row_headers}")

        # 4. 获取和修改单元格值

        # 获取 '上海' 在 '人口 (百万)' 列的值
        current_pop = editor.get_cell_value(target_table, '上海', '人口 (百万)')
        print(f"   - '上海'的原始人口: {current_pop} 百万")

        # 修改 '深圳' 的 '面积 (万km²)'
        new_area = '0.25 (修订)'
        if editor.set_cell_value(target_table, '深圳', '面积 (万km²)', new_area):
            print(f"   - 成功修改 '深圳' 的 '面积 (万km²)' 为: {new_area}")

        # 5. 重建 Markdown 源文件
        new_md = editor.rebuild_markdown()
        print("\n--- 📝 重建后的 Markdown ---")
        print(new_md)
    else:
        print("❌ 未找到目标表格。")