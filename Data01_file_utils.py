# """
# 文件操作工具模块，提供文件夹检查/创建、文件删除、文件列表获取等功能。
# """
import os
import shutil
import pandas as pd

def ensure_dir(directory):
#     """确保目录存在，不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"创建目录: {directory}")
    return directory

def clear_csv_files(directory):
#     """删除指定目录下所有csv文件"""
    if not os.path.exists(directory):
        return
    for filename in os.listdir(directory):
        if filename.lower().endswith('.csv'):
            file_path = os.path.join(directory, filename)
            ### os.remove(file_path)
            print(f"Data01_file_utils 未删除旧CSV文件: {file_path}")

def get_csv_files(directory):
#     """获取指定目录下所有csv文件路径列表"""
    if not os.path.exists(directory):
        return []
    files = []
    for filename in os.listdir(directory):
        if filename.lower().endswith('.csv'):
            files.append(os.path.join(directory, filename))
    return files

def read_stock_list(file_path):
    """
    读取股票清单文件（支持 CSV 或 Excel），返回带标准列名的 DataFrame。
    标准列名：['stock_code', 'start_date', 'end_date', 'data_type']
    日期列强制作为字符串，保留原始格式（如 YYYYMMDD）。
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在：{file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == '.csv':
            # 读取 CSV，假设第一行为列名，所有列作为字符串
            df = pd.read_csv(file_path, dtype=str)
        elif ext == '.xlsx':
            # 读取 Excel，假设第一行为列名，所有列作为字符串
            df = pd.read_excel(file_path, dtype=str)
        else:
            raise ValueError(f"不支持的文件格式：{ext}，请使用 .csv 或 .xlsx")
    except Exception as e:
        raise RuntimeError(f"读取文件失败：{e}")

    # 检查列数是否足够（至少4列）
    if df.shape[1] < 4:
        raise ValueError("文件必须包含至少4列数据")

    # 取前4列，并重命名为标准列名
    df = df.iloc[:, :4].copy()
    df.columns = ['stock_code', 'start_date', 'end_date', 'data_type']

    # 去除可能的空行
    df.dropna(how='all', inplace=True)

    # 检查是否有空值
    if df.isnull().any().any():
        raise ValueError("文件中存在空值，请确保每行都有完整数据")

    # 可选：验证日期格式（8位数字）
    # 这里简单示例，可根据需要加强校验
    for col in ['start_date', 'end_date']:
        # 转为字符串并去除空格
        df[col] = df[col].astype(str).str.strip()
        # 检查是否为8位数字
        mask = df[col].str.match(r'^\d{8}$')
        if not mask.all():
            invalid = df.loc[~mask, col].tolist()
            raise ValueError(f"日期列 {col} 包含非 YYYYMMDD 格式的数据：{invalid}")

    # 检查数据类型列是否合法
    valid_types = ['日数据', '分钟数据']
    if not df['data_type'].isin(valid_types).all():
        invalid = df.loc[~df['data_type'].isin(valid_types), 'data_type'].tolist()
        raise ValueError(f"数据类型列只能为 {valid_types}，发现：{invalid}")

    return df

def update_log_file(log_file, stock_code, start_date, end_date, data_type):
#     """
#     更新日志Excel文件。
#     log_file: 日志文件路径（区分日/分钟）
#     如果文件不存在，则创建并写入表头；如果存在，读取并更新。
#     比较规则：
#        如果本次起始日期早于记录中的起始日期，则更新起始日期
#        如果本次结束日期晚于记录中的结束日期，则更新结束日期
#     """
    # 定义列名
    columns = ['stock_code', 'start_date', 'end_date', 'data_type']
    
    # 尝试读取现有日志
    if os.path.exists(log_file):
        df_log = pd.read_excel(log_file, dtype={'stock_code': str})
    else:
        df_log = pd.DataFrame(columns=columns)
    
    # 查找是否已有该股票代码记录
    mask = df_log['stock_code'] == stock_code
    if mask.any():
        # 更新已有记录
        idx = df_log[mask].index[0]
        # 比较起始日期
        if pd.to_datetime(start_date) < pd.to_datetime(df_log.at[idx, 'start_date']):
            df_log.at[idx, 'start_date'] = start_date
        # 比较结束日期
        if pd.to_datetime(end_date) > pd.to_datetime(df_log.at[idx, 'end_date']):
            df_log.at[idx, 'end_date'] = end_date
        # 类型通常不变，但如果有变化可以更新
        df_log.at[idx, 'data_type'] = data_type
    else:
        # 添加新记录
        new_row = pd.DataFrame([[stock_code, start_date, end_date, data_type]], columns=columns)
        df_log = pd.concat([df_log, new_row], ignore_index=True)
    
    # 保存回Excel
    df_log.to_excel(log_file, index=False)