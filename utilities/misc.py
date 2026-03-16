import os


def ensure_folder(folder_path):
    """
    确保文件夹存在，如果不存在则创建

    参数:
        folder_path: 要检查/创建的文件夹路径

    返回:
        bool: 成功返回True，失败返回False
    """
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"文件夹已创建: {folder_path}")
        else:
            print(f"文件夹已存在: {folder_path}")
        return True
    except Exception as e:
        print(f"操作失败: {e}")
        return False