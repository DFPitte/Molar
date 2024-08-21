import os
import subprocess
import json
import tarfile
import shutil

def process_jsonl_files(output_subdir):
    total_entries = 0
    fields = set()
    samples = []
    
    jsonl_files = sorted([f for f in os.listdir(output_subdir) if f.endswith('.jsonl')])
    
    for jsonl_file in jsonl_files:
        file_path = os.path.join(output_subdir, jsonl_file)
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            total_entries += len(lines)
            
            for i, line in enumerate(lines):
                if i < 10:
                    samples.append(line.strip())
                
                try:
                    data = json.loads(line)
                    fields.update(data.keys())
                except json.JSONDecodeError:
                    print(f"Error decoding JSON in file {jsonl_file}, line {i+1}")
    
    folder_name = os.path.basename(output_subdir)
    info_dict = {
        "文件夹路径": "/"+folder_name,
        "条目数": total_entries,
        "字段": list(fields),
        "10条样例": samples[:10]
    }
    
    # 将字典保存为JSON文件
    info_file_path = os.path.join(output_subdir, f"{folder_name}.json")
    with open(info_file_path, 'w', encoding='utf-8') as f:
        json.dump(info_dict, f, ensure_ascii=False, indent=4)
    
    return info_file_path

def create_tarfile(output_subdir):
    folder_name = os.path.basename(output_subdir)
    tar_filename = f"{folder_name}.tar.gz"
    tar_filepath = os.path.join(output_subdir, tar_filename)
    
    with tarfile.open(tar_filepath, "w:gz") as tar:
        for file in os.listdir(output_subdir):
            if file.endswith('.jsonl'):
                file_path = os.path.join(output_subdir, file)
                tar.add(file_path, arcname=file)
    
    return tar_filepath

def process_single_file(file_path, output_subdir, bandzip_path):
    try:
        # 构建BandZip命令
        command = [bandzip_path, 'x', '-o:', file_path,output_subdir]
        
        # 执行解压命令
        subprocess.run(command, check=True)
        print(f"成功处理 {file_path} 到 {output_subdir}")
        
        # 获取当前文件夹中的最大索引
        existing_files = [f for f in os.listdir(output_subdir) if f.endswith('.jsonl')]
        max_index = max([int(f.split('.')[0]) for f in existing_files] + [0])
        
        # 重命名新解压的文件
        extracted_files = [f for f in os.listdir(output_subdir) if f not in existing_files and not f.endswith('.json') and not f.endswith('.tar.gz')]
        for extracted_file in sorted(extracted_files):
            max_index += 1
            old_path = os.path.join(output_subdir, extracted_file)
            new_name = f"{max_index}.jsonl"
            new_path = os.path.join(output_subdir, new_name)
            os.rename(old_path, new_path)
            print(f"将文件重命名为 {new_name}")
    
    except subprocess.CalledProcessError as e:
        print(f"处理 {file_path} 时出错: {e}")
    except Exception as e:
        print(f"处理 {file_path} 时发生未知错误: {e}")

def process_and_rename_files(root_folder, output_folder, start_folder=None, end_folder=None):
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 注意：请将下面的路径替换为你的BandZip可执行文件的实际路径
    bandzip_path = r"C:\Program Files\Bandizip\Bandizip.exe"

    resume_processing = bool(start_folder)
    stop_processing = False

    # 遍历根文件夹下的所有子文件夹
    for dirpath, dirnames, filenames in os.walk(root_folder):
        folder_name = os.path.basename(dirpath)

        if resume_processing:
            if folder_name == start_folder:
                resume_processing = False
            else:
                continue

        if stop_processing:
            break

        if end_folder and folder_name == end_folder:
            stop_processing = True

        # 计算相对路径
        rel_path = os.path.relpath(dirpath, root_folder)
        # 在输出文件夹中创建对应的子文件夹
        output_subdir = os.path.join(output_folder, rel_path)
        if not os.path.exists(output_subdir):
            os.makedirs(output_subdir)

        print(f"正在处理文件夹: {folder_name}")

        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            process_single_file(file_path, output_subdir, bandzip_path)

        # 处理完所有文件后，处理JSONL文件并创建信息文件
        info_file_path = process_jsonl_files(output_subdir)
        print(f"信息文件已保存至: {info_file_path}")

        # 创建tar.gz文件
        tar_filepath = create_tarfile(output_subdir)
        print(f"文件夹已打包为: {tar_filepath}")
        
        # 删除原始JSONL文件
        for file in os.listdir(output_subdir):
            if file.endswith('.jsonl'):
                os.remove(os.path.join(output_subdir, file))
        print(f"原始JSONL文件已删除")

def get_subdirectories(folder):
    return [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]

# 获取当前脚本所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 设置根文件夹为当前目录下的 "未清洗" 文件夹
root_folder = os.path.join(current_dir, "未清洗")

# 设置输出文件夹为当前目录下的 "output" 文件夹
output_folder = os.path.join(current_dir, "output")

# 确保根文件夹存在
if not os.path.exists(root_folder):
    print(f"错误：'未清洗'文件夹不存在于 {current_dir}")
    exit(1)

# 获取所有子文件夹
subdirectories = get_subdirectories(root_folder)

# 打印可用的文件夹
print("可用的文件夹：")
for i, directory in enumerate(subdirectories, 1):
    print(f"{i}. {directory}")

# 用户选择起始文件夹
while True:
    start_choice = input("\n请选择开始处理的文件夹编号（输入0从头开始处理）: ")
    if start_choice == "0":
        start_folder = None
        start_index = 0
        break
    try:
        start_index = int(start_choice) - 1
        if 0 <= start_index < len(subdirectories):
            start_folder = subdirectories[start_index]
            break
        else:
            print("无效的编号，请重新输入。")
    except ValueError:
        print("请输入一个有效的数字。")

# 用户选择结束文件夹
while True:
    end_choice = input("\n请选择结束处理的文件夹编号（输入0处理到最后）: ")
    if end_choice == "0":
        end_folder = None
        break
    try:
        end_index = int(end_choice) - 1
        if start_index <= end_index < len(subdirectories):
            end_folder = subdirectories[end_index]
            break
        else:
            print("无效的编号，请重新输入。")
    except ValueError:
        print("请输入一个有效的数字。")

if start_folder:
    print(f"将从文件夹 '{start_folder}' 开始处理")
else:
    print("将从头开始处理")

if end_folder:
    print(f"将在处理完文件夹 '{end_folder}' 后结束")
else:
    print("将处理到最后一个文件夹")

process_and_rename_files(root_folder, output_folder, start_folder, end_folder)