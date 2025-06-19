import hashlib

def md5_hash(original_string: str):
    md5 = hashlib.md5()
    md5.update(original_string.encode('utf-8'))
    return md5.hexdigest()