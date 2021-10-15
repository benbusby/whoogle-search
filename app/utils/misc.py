import hashlib
import os


def gen_file_hash(path: str, static_file: str) -> str:
    file_contents = open(os.path.join(path, static_file), 'rb').read()
    file_hash = hashlib.md5(file_contents).hexdigest()[:8]
    filename_split = os.path.splitext(static_file)

    return filename_split[0] + '.' + file_hash + filename_split[-1]


def read_config_bool(var: str) -> bool:
    val = os.getenv(var, '0')
    if val.isdigit():
        return bool(int(val))
    return False
