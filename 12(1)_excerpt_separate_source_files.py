import os
import shutil

def read_file_list(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def build_file_index(root_dir):
    index = {}
    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            if file in index:
                print(f"Warning: Duplicate file name found: {file}")
            index[file] = os.path.join(dirpath, file)
    return index

def copy_preserving_structure(full_path, root_src, root_dst):
    relative_path = os.path.relpath(full_path, root_src)
    target_path = os.path.join(root_dst, relative_path)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    shutil.copy2(full_path, target_path)

def main():
    source_root = '4_output_human'
    split_dir = 'split_data'
    creation_root = '5_training_source'

    train_files = read_file_list(os.path.join(split_dir, 'train.txt'))
    file_index = build_file_index(source_root)

    for fname in train_files:
        if fname in file_index:
            copy_preserving_structure(file_index[fname], source_root, creation_root)
        else:
            print(f"Warning: {fname} in train.txt not found in {source_root}")

if __name__ == "__main__":
    main()
