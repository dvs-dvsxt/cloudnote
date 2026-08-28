import os
import json
import hashlib
import hmac
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import rsa, padding, x25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

# ==================== 调试日志 ====================
DEBUG_CRYPTO = True  # 加密模块调试开关

def crypto_log(msg, level="INFO"):
    if DEBUG_CRYPTO:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[CRYPTO][{timestamp}] [{level}] {msg}")
        import sys
        sys.stdout.flush()

# ==================== 哈希工具 ====================

def compute_data_hash(data, algorithm='sha256'):
    if isinstance(data, str):
        data = data.encode('utf-8')
    hash_func = hashlib.new(algorithm)
    hash_func.update(data)
    return hash_func.hexdigest()

def verify_data_hash(data, expected_hash, algorithm='sha256'):
    actual_hash = compute_data_hash(data, algorithm)
    return hmac.compare_digest(actual_hash.lower(), expected_hash.lower())

# ==================== 密码强度检查 ====================

COMMON_PASSWORDS = [
    'password', '123456', '12345678', '1234', 'qwerty', '12345',
    'dragon', 'baseball', 'football', 'letmein', 'monkey', 'mustang',
    'access', 'shadow', 'master', 'michael', 'superman', '696969',
    '123abc', 'apple', 'passw0rd', 'password1', 'login', 'admin',
    'welcome', 'sunshine', 'loveme', 'solo', 'starwars', 'freedom'
]

def is_password_strong(password, strict=True):
    """
    检查密码强度
    strict=True: 强度要求（长度≥16，大小写+数字+特殊字符）
    strict=False: 仅检查不为空
    """
    if not password:
        return False
    if not strict:
        return len(password) > 0
    if len(password) < 16:
        crypto_log(f"密码长度不足: {len(password)} < 16", "WARN")
        return False
    if password.lower() in COMMON_PASSWORDS:
        crypto_log("密码为常见弱密码", "WARN")
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    result = has_upper and has_lower and has_digit and has_special
    if not result:
        crypto_log(f"密码复杂度不足 - 大写:{has_upper}, 小写:{has_lower}, 数字:{has_digit}, 特殊:{has_special}", "WARN")
    return result

def generate_strong_password(length=32):
    import random
    import string
    if length < 32:
        length = 32
    chars = string.ascii_letters + string.digits + string.punctuation
    while True:
        password = ''.join(random.SystemRandom().choice(chars) for _ in range(length))
        if is_password_strong(password, strict=True):
            return password

# ==================== 密钥派生 ====================

def derive_key_from_password(password, salt, dklen=32):
    if isinstance(password, str):
        password = password.encode('utf-8')
    crypto_log(f"派生密钥 - 盐长度: {len(salt)}字节, 迭代次数: 100000")
    return hashlib.pbkdf2_hmac('sha256', password, salt, 100000, dklen=dklen)

# ==================== AES 加密/解密核心 ====================

def generate_aes_key(key_size=32):
    return os.urandom(key_size)

def aes_encrypt(data, aes_key):
    iv = os.urandom(16)
    crypto_log(f"AES-GCM加密 - IV长度: {len(iv)}字节, 密钥长度: {len(aes_key)}字节, 数据长度: {len(data)}字节")
    cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = sym_padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    crypto_log(f"AES加密完成 - 密文长度: {len(ciphertext)}字节, Tag长度: {len(encryptor.tag)}字节")
    return ciphertext, iv, encryptor.tag

def aes_decrypt(ciphertext, aes_key, iv, tag):
    crypto_log(f"AES-GCM解密 - IV长度: {len(iv)}字节, 密钥长度: {len(aes_key)}字节, 密文长度: {len(ciphertext)}字节, Tag长度: {len(tag)}字节")
    cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = sym_padding.PKCS7(128).unpadder()
    result = unpadder.update(decrypted_padded) + unpadder.finalize()
    crypto_log(f"AES解密完成 - 解密后长度: {len(result)}字节")
    return result

# ==================== RSA 密钥生成 ====================

def generate_rsa_key(key_size=4096):
    crypto_log(f"生成RSA-{key_size}密钥对...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    crypto_log(f"RSA密钥生成完成 - 私钥长度: {len(private_pem)}字节, 公钥长度: {len(public_pem)}字节")
    return private_pem, public_pem

# ==================== X25519 密钥生成 ====================

def generate_x25519_keys():
    crypto_log("生成X25519密钥对...")
    private_key = x25519.X25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    crypto_log(f"X25519密钥生成完成 - 私钥长度: {len(private_bytes)}字节, 公钥长度: {len(public_bytes)}字节")
    return private_bytes, public_bytes

def load_x25519_private_key(private_bytes):
    return x25519.X25519PrivateKey.from_private_bytes(private_bytes)

def load_x25519_public_key(public_bytes):
    return x25519.X25519PublicKey.from_public_bytes(public_bytes)

# ==================== 模式1: AES + RSA (混合加密) ====================

def encrypt_aes_rsa(data, rsa_public_key, password=None, strict_password=True):
    """
    AES + RSA 混合加密
    data: bytes 或 str
    rsa_public_key: PEM格式RSA公钥 (bytes)
    password: 可选，用户密码
    strict_password: True=高强度密码要求，False=低强度（不推荐）
    """
    crypto_log("=" * 50)
    crypto_log(f"开始 AES+RSA 加密 - 密码保护: {password is not None}, 严格模式: {strict_password}")
    
    if isinstance(data, str):
        data = data.encode('utf-8')
    crypto_log(f"原始数据长度: {len(data)}字节")
    
    # 生成随机AES密钥
    aes_key = generate_aes_key()
    crypto_log(f"AES密钥已生成: {aes_key.hex()[:16]}...")
    
    # AES加密数据
    ciphertext, iv, tag = aes_encrypt(data, aes_key)
    
    # RSA加密AES密钥
    public_key = serialization.load_pem_public_key(rsa_public_key, backend=default_backend())
    encrypted_aes_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    crypto_log(f"RSA加密AES密钥完成 - 长度: {len(encrypted_aes_key)}字节")
    
    result = {
        'algorithm': 'AES-RSA-Hybrid',
        'mode': 'aes_rsa',
        'encrypted_aes_key': encrypted_aes_key.hex(),
        'iv': iv.hex(),
        'tag': tag.hex(),
        'ciphertext': ciphertext.hex(),
        'timestamp': datetime.utcnow().isoformat(),
        'original_hash': compute_data_hash(data),
        'hash_algorithm': 'sha256'
    }
    
    if password:
        crypto_log(f"处理密码保护 - 密码长度: {len(password)}")
        if strict_password and not is_password_strong(password, strict=True):
            raise ValueError("密码强度不足：需要至少16字符，包含大小写字母、数字和特殊字符")
        
        salt = os.urandom(16)
        pwd_key = derive_key_from_password(password, salt)
        crypto_log(f"密码派生密钥完成 - 盐: {salt.hex()[:16]}..., 派生密钥: {pwd_key.hex()[:16]}...")
        
        result_json = json.dumps(result)
        pwd_iv = os.urandom(12)
        pwd_cipher = Cipher(algorithms.AES(pwd_key), modes.GCM(pwd_iv), backend=default_backend())
        pwd_encryptor = pwd_cipher.encryptor()
        encrypted_result = pwd_encryptor.update(result_json.encode()) + pwd_encryptor.finalize()
        crypto_log(f"双层加密完成 - 加密负载长度: {len(encrypted_result)}字节")
        
        final_result = {
            'has_password': True,
            'mode': 'aes_rsa_password_protected',
            'pwd_salt': salt.hex(),
            'pwd_iv': pwd_iv.hex(),
            'pwd_tag': pwd_encryptor.tag.hex(),
            'encrypted_payload': encrypted_result.hex(),
            'timestamp': datetime.utcnow().isoformat()
        }
    else:
        final_result = result
        final_result['has_password'] = False
    
    crypto_log(f"加密完成 - 最终数据长度: {len(json.dumps(final_result))}字节")
    crypto_log("=" * 50)
    return json.dumps(final_result).encode('utf-8')

def decrypt_aes_rsa(encrypted_data, rsa_private_key, password=None):
    """
    解密 AES+RSA 加密的数据
    """
    crypto_log("=" * 50)
    crypto_log("开始 AES+RSA 解密")
    
    if isinstance(encrypted_data, str):
        encrypted_data = encrypted_data.encode('utf-8')
    crypto_log(f"加密数据长度: {len(encrypted_data)}字节")
    
    data = json.loads(encrypted_data.decode('utf-8'))
    crypto_log(f"解析JSON - has_password: {data.get('has_password', False)}, mode: {data.get('mode', 'unknown')}")
    
    if data.get('has_password', False):
        crypto_log("检测到密码保护模式")
        if not password:
            raise ValueError("此数据受密码保护，请输入密码")
        
        crypto_log(f"尝试密码解密 - 密码长度: {len(password)}")
        crypto_log(f"密码前4位: {password[:4] if len(password) >= 4 else password}")
        
        try:
            salt = bytes.fromhex(data['pwd_salt'])
            pwd_iv = bytes.fromhex(data['pwd_iv'])
            pwd_tag = bytes.fromhex(data['pwd_tag'])
            encrypted_payload = bytes.fromhex(data['encrypted_payload'])
            
            crypto_log(f"盐: {salt.hex()[:16]}...")
            crypto_log(f"IV: {pwd_iv.hex()}")
            crypto_log(f"Tag: {pwd_tag.hex()}")
            crypto_log(f"加密负载长度: {len(encrypted_payload)}字节")
            
            pwd_key = derive_key_from_password(password, salt)
            crypto_log(f"派生密钥: {pwd_key.hex()[:16]}...")
            
            pwd_cipher = Cipher(algorithms.AES(pwd_key), modes.GCM(pwd_iv, pwd_tag), backend=default_backend())
            pwd_decryptor = pwd_cipher.decryptor()
            decrypted_json = pwd_decryptor.update(encrypted_payload) + pwd_decryptor.finalize()
            crypto_log("密码层解密成功！")
            
            inner_data = json.loads(decrypted_json.decode())
            crypto_log(f"内层数据解析成功 - mode: {inner_data.get('mode', 'unknown')}")
        except Exception as e:
            crypto_log(f"密码解密失败: {e}", "ERROR")
            raise ValueError(f"密码错误或数据损坏: {str(e)}")
    else:
        crypto_log("无密码保护模式")
        inner_data = data
    
    # RSA解密AES密钥
    crypto_log("加载RSA私钥...")
    private_key = serialization.load_pem_private_key(rsa_private_key, password=None, backend=default_backend())
    encrypted_aes_key = bytes.fromhex(inner_data['encrypted_aes_key'])
    crypto_log(f"RSA解密AES密钥 - 加密密钥长度: {len(encrypted_aes_key)}字节")
    aes_key = private_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    crypto_log(f"AES密钥恢复成功: {aes_key.hex()[:16]}...")
    
    # AES解密
    iv = bytes.fromhex(inner_data['iv'])
    tag = bytes.fromhex(inner_data['tag'])
    ciphertext = bytes.fromhex(inner_data['ciphertext'])
    crypto_log(f"AES解密 - IV: {iv.hex()}, Tag: {tag.hex()}, 密文长度: {len(ciphertext)}字节")
    
    decrypted = aes_decrypt(ciphertext, aes_key, iv, tag)
    
    # 哈希校验
    original_hash = inner_data.get('original_hash')
    if original_hash:
        crypto_log(f"验证哈希 - 期望: {original_hash[:16]}...")
        if not verify_data_hash(decrypted, original_hash, inner_data.get('hash_algorithm', 'sha256')):
            crypto_log("哈希验证失败！数据可能被篡改", "ERROR")
            raise ValueError("哈希验证失败！数据可能已被篡改")
        crypto_log("哈希验证通过")
    
    crypto_log(f"解密成功 - 数据长度: {len(decrypted)}字节")
    crypto_log("=" * 50)
    return decrypted

# ==================== 模式2: AES + X25519 (混合加密) ====================

def encrypt_aes_x25519(data, recipient_public_key, password=None, strict_password=True):
    """
    AES + X25519 混合加密
    strict_password: True=高强度密码要求，False=低强度（不推荐）
    """
    crypto_log("=" * 50)
    crypto_log(f"开始 AES+X25519 加密 - 密码保护: {password is not None}, 严格模式: {strict_password}")
    
    if isinstance(data, str):
        data = data.encode('utf-8')
    crypto_log(f"原始数据长度: {len(data)}字节")
    
    # 生成临时X25519密钥对
    ephemeral_private = x25519.X25519PrivateKey.generate()
    ephemeral_public = ephemeral_private.public_key()
    ephemeral_public_bytes = ephemeral_public.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    crypto_log(f"临时密钥对生成 - 公钥: {ephemeral_public_bytes.hex()[:16]}...")
    
    # 加载接收方公钥
    recipient_pub = load_x25519_public_key(recipient_public_key)
    
    # 计算共享密钥
    shared_secret = ephemeral_private.exchange(recipient_pub)
    crypto_log(f"ECDH共享密钥计算完成 - 长度: {len(shared_secret)}字节")
    
    # 使用HKDF派生AES密钥
    aes_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'aes-x25519-encryption',
        backend=default_backend()
    ).derive(shared_secret)
    crypto_log(f"AES密钥派生完成: {aes_key.hex()[:16]}...")
    
    # AES加密数据
    ciphertext, iv, tag = aes_encrypt(data, aes_key)
    
    result = {
        'algorithm': 'AES-X25519-Hybrid',
        'mode': 'aes_x25519',
        'ephemeral_public': ephemeral_public_bytes.hex(),
        'iv': iv.hex(),
        'tag': tag.hex(),
        'ciphertext': ciphertext.hex(),
        'timestamp': datetime.utcnow().isoformat(),
        'original_hash': compute_data_hash(data),
        'hash_algorithm': 'sha256'
    }
    
    if password:
        crypto_log(f"处理密码保护 - 密码长度: {len(password)}")
        if strict_password and not is_password_strong(password, strict=True):
            raise ValueError("密码强度不足：需要至少16字符，包含大小写字母、数字和特殊字符")
        
        salt = os.urandom(16)
        pwd_key = derive_key_from_password(password, salt)
        crypto_log(f"密码派生密钥完成 - 盐: {salt.hex()[:16]}..., 派生密钥: {pwd_key.hex()[:16]}...")
        
        result_json = json.dumps(result)
        pwd_iv = os.urandom(12)
        pwd_cipher = Cipher(algorithms.AES(pwd_key), modes.GCM(pwd_iv), backend=default_backend())
        pwd_encryptor = pwd_cipher.encryptor()
        encrypted_result = pwd_encryptor.update(result_json.encode()) + pwd_encryptor.finalize()
        crypto_log(f"双层加密完成 - 加密负载长度: {len(encrypted_result)}字节")
        
        final_result = {
            'has_password': True,
            'mode': 'aes_x25519_password_protected',
            'pwd_salt': salt.hex(),
            'pwd_iv': pwd_iv.hex(),
            'pwd_tag': pwd_encryptor.tag.hex(),
            'encrypted_payload': encrypted_result.hex(),
            'timestamp': datetime.utcnow().isoformat()
        }
    else:
        final_result = result
        final_result['has_password'] = False
    
    crypto_log(f"加密完成 - 最终数据长度: {len(json.dumps(final_result))}字节")
    crypto_log("=" * 50)
    return json.dumps(final_result).encode('utf-8')

def decrypt_aes_x25519(encrypted_data, recipient_private_key, password=None):
    """
    解密 AES+X25519 加密的数据
    """
    crypto_log("=" * 50)
    crypto_log("开始 AES+X25519 解密")
    
    if isinstance(encrypted_data, str):
        encrypted_data = encrypted_data.encode('utf-8')
    crypto_log(f"加密数据长度: {len(encrypted_data)}字节")
    
    data = json.loads(encrypted_data.decode('utf-8'))
    crypto_log(f"解析JSON - has_password: {data.get('has_password', False)}, mode: {data.get('mode', 'unknown')}")
    
    if data.get('has_password', False):
        crypto_log("检测到密码保护模式")
        if not password:
            raise ValueError("此数据受密码保护，请输入密码")
        
        crypto_log(f"尝试密码解密 - 密码长度: {len(password)}")
        crypto_log(f"密码前4位: {password[:4] if len(password) >= 4 else password}")
        crypto_log(f"密码后4位: {password[-4:] if len(password) >= 4 else password}")
        
        try:
            salt = bytes.fromhex(data['pwd_salt'])
            pwd_iv = bytes.fromhex(data['pwd_iv'])
            pwd_tag = bytes.fromhex(data['pwd_tag'])
            encrypted_payload = bytes.fromhex(data['encrypted_payload'])
            
            crypto_log(f"盐: {salt.hex()}")
            crypto_log(f"IV: {pwd_iv.hex()}")
            crypto_log(f"Tag: {pwd_tag.hex()}")
            crypto_log(f"加密负载长度: {len(encrypted_payload)}字节")
            
            pwd_key = derive_key_from_password(password, salt)
            crypto_log(f"派生密钥: {pwd_key.hex()}")
            
            pwd_cipher = Cipher(algorithms.AES(pwd_key), modes.GCM(pwd_iv, pwd_tag), backend=default_backend())
            pwd_decryptor = pwd_cipher.decryptor()
            decrypted_json = pwd_decryptor.update(encrypted_payload) + pwd_decryptor.finalize()
            crypto_log("密码层解密成功！")
            
            inner_data = json.loads(decrypted_json.decode())
            crypto_log(f"内层数据解析成功 - mode: {inner_data.get('mode', 'unknown')}")
        except Exception as e:
            crypto_log(f"密码解密失败: {type(e).__name__}: {e}", "ERROR")
            raise ValueError(f"密码错误或数据损坏: {str(e)}")
    else:
        crypto_log("无密码保护模式")
        inner_data = data
    
    # 加载临时公钥和接收方私钥
    crypto_log("加载临时公钥和接收方私钥...")
    ephemeral_public_bytes = bytes.fromhex(inner_data['ephemeral_public'])
    crypto_log(f"临时公钥: {ephemeral_public_bytes.hex()}")
    ephemeral_public = load_x25519_public_key(ephemeral_public_bytes)
    recipient_private = load_x25519_private_key(recipient_private_key)
    
    # 计算共享密钥
    shared_secret = recipient_private.exchange(ephemeral_public)
    crypto_log(f"ECDH共享密钥计算完成 - 长度: {len(shared_secret)}字节")
    
    # 派生AES密钥
    aes_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'aes-x25519-encryption',
        backend=default_backend()
    ).derive(shared_secret)
    crypto_log(f"AES密钥派生完成: {aes_key.hex()[:16]}...")
    
    # AES解密
    iv = bytes.fromhex(inner_data['iv'])
    tag = bytes.fromhex(inner_data['tag'])
    ciphertext = bytes.fromhex(inner_data['ciphertext'])
    crypto_log(f"AES解密 - IV: {iv.hex()}, Tag: {tag.hex()}, 密文长度: {len(ciphertext)}字节")
    
    decrypted = aes_decrypt(ciphertext, aes_key, iv, tag)
    
    # 哈希校验
    original_hash = inner_data.get('original_hash')
    if original_hash:
        crypto_log(f"验证哈希 - 期望: {original_hash[:16]}...")
        if not verify_data_hash(decrypted, original_hash, inner_data.get('hash_algorithm', 'sha256')):
            crypto_log("哈希验证失败！数据可能被篡改", "ERROR")
            raise ValueError("哈希验证失败！数据可能已被篡改")
        crypto_log("哈希验证通过")
    
    crypto_log(f"解密成功 - 数据长度: {len(decrypted)}字节")
    crypto_log("=" * 50)
    return decrypted

# ==================== 模式3: AES + RSA + 自定义密码 ====================

def encrypt_aes_rsa_with_password(data, rsa_public_key, password, strict_password=True):
    """
    AES + RSA + 自定义密码（双层保护）
    strict_password: True=高强度密码要求，False=低强度（不推荐）
    """
    crypto_log(f"调用加密函数(带密码) - 严格模式: {strict_password}")
    if not password:
        raise ValueError("密码模式必须提供密码")
    return encrypt_aes_rsa(data, rsa_public_key, password, strict_password)

def decrypt_aes_rsa_with_password(encrypted_data, rsa_private_key, password):
    if not password:
        raise ValueError("密码模式必须提供密码")
    return decrypt_aes_rsa(encrypted_data, rsa_private_key, password)

# ==================== 安全信息头生成 ====================

def add_security_info(encrypted_data, mode, has_password=False, original_hash=None, hash_algorithm='sha256'):
    mode_display = {
        'aes_rsa': 'AES+RSA 混合加密',
        'aes_rsa_password': 'AES+RSA+自定义密码 双层加密',
        'aes_x25519': 'AES+X25519 混合加密'
    }.get(mode, mode)
    
    hash_info = ""
    if original_hash:
        hash_info = f"原始数据哈希: {original_hash}\n哈希算法: {hash_algorithm}\n哈希状态: 已嵌入加密数据"
    else:
        hash_info = "哈希状态: 已嵌入加密数据（自动计算）"
    
    info = f"""
=== DVT_RFSA 加密算法 ===
版本: 3.0
模式: {mode_display}
开发者: VSD Security Team
日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== 安全信息 ===
加密强度: 极高
破解概率: 接近于零 (使用量子计算机前)
算法组合: 
  - AES+RSA模式: RSA-4096 + AES-256-GCM
  - AES+X25519模式: X25519密钥交换 + AES-256-GCM
  - AES+RSA+密码模式: RSA-4096 + AES-256-GCM + 用户密码二次加密
密钥熵: ≥256位 (高强度模式)
密码保护: {'是 (双层加密)' if has_password else '否'}
{hash_info}

=== 哈希校验 ===
完整性保护: SHA-256 哈希校验
校验方式: 解密后自动验证原始数据完整性
防篡改: 哈希值嵌入加密数据结构

=== X25519 识别信息 ===
X25519曲线: Curve25519
密钥交换: ECDH over Curve25519
共享密钥派生: HKDF-SHA256
前向安全性: 支持（临时密钥对）

=== 免责声明 ===
1. 使用低强度密码可能导致数据泄露
2. 请妥善保管您的密钥和密码
3. 开发者不对因密码强度不足导致的数据泄露负责
4. 哈希校验仅用于完整性验证，不替代数字签名

=== DVT_RFSA Encryption Algorithm ===
Version: 3.0
Mode: {mode_display}
Developer: VSD Security Team
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== Security Information ===
Encryption Strength: Extremely High
Cracking Probability: Near Zero (pre-quantum)
Algorithm Combination:
  - AES+RSA Mode: RSA-4096 + AES-256-GCM
  - AES+X25519 Mode: X25519 Key Exchange + AES-256-GCM
  - AES+RSA+Password Mode: RSA-4096 + AES-256-GCM + User Password Double Encryption
Key Entropy: ≥256 bits (high strength mode)
Password Protection: {'Yes (Double Layer)' if has_password else 'No'}
{hash_info.replace('原始数据哈希', 'Original Data Hash').replace('哈希算法', 'Hash Algorithm').replace('哈希状态', 'Hash Status')}

=== Hash Verification ===
Integrity Protection: SHA-256 Hash Verification
Verification Method: Automatic verification after decryption
Tamper Resistance: Hash embedded in encrypted data structure

=== X25519 Identification ===
X25519 Curve: Curve25519
Key Exchange: ECDH over Curve25519
Shared Secret Derivation: HKDF-SHA256
Forward Secrecy: Supported (ephemeral key pair)

=== Disclaimer ===
1. Using weak passwords may lead to data breaches
2. Please keep your keys and passwords secure
3. The developer is not responsible for data breaches caused by weak passwords
4. Hash verification only ensures integrity, not a substitute for digital signatures

=== 数据开始 ===
{encrypted_data.decode('utf-8') if isinstance(encrypted_data, bytes) else encrypted_data}
=== 数据结束 ===
"""
    return info.encode('utf-8')

def remove_security_info(data):
    crypto_log("移除安全信息头...")
    if isinstance(data, bytes):
        data_str = data.decode('utf-8')
    else:
        data_str = data
    
    start_marker = "=== 数据开始 ==="
    end_marker = "=== 数据结束 ==="
    start_idx = data_str.find(start_marker)
    end_idx = data_str.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        crypto_log("未找到安全头标记，返回原始数据")
        if isinstance(data, bytes):
            return data
        else:
            return data.encode('utf-8')
    
    actual_data = data_str[start_idx + len(start_marker):end_idx].strip()
    crypto_log(f"安全头移除完成 - 数据长度: {len(actual_data)}字节")
    return actual_data.encode('utf-8')

# ==================== 文件加密/解密封装 ====================

def encrypt_file_aes_rsa(input_file, output_file, rsa_public_key, password=None, add_header=True, strict_password=True):
    with open(input_file, 'rb') as f:
        data = f.read()
    encrypted = encrypt_aes_rsa(data, rsa_public_key, password, strict_password)
    if add_header:
        encrypted = add_security_info(encrypted, 'aes_rsa', bool(password))
    with open(output_file, 'wb') as f:
        f.write(encrypted)

def decrypt_file_aes_rsa(input_file, output_file, rsa_private_key, password=None, has_header=True):
    with open(input_file, 'rb') as f:
        data = f.read()
    if has_header:
        data = remove_security_info(data)
    decrypted = decrypt_aes_rsa(data, rsa_private_key, password)
    with open(output_file, 'wb') as f:
        f.write(decrypted)

def encrypt_file_aes_rsa_with_password(input_file, output_file, rsa_public_key, password, add_header=True, strict_password=True):
    with open(input_file, 'rb') as f:
        data = f.read()
    encrypted = encrypt_aes_rsa_with_password(data, rsa_public_key, password, strict_password)
    if add_header:
        encrypted = add_security_info(encrypted, 'aes_rsa_password', True)
    with open(output_file, 'wb') as f:
        f.write(encrypted)

def decrypt_file_aes_rsa_with_password(input_file, output_file, rsa_private_key, password, has_header=True):
    with open(input_file, 'rb') as f:
        data = f.read()
    if has_header:
        data = remove_security_info(data)
    decrypted = decrypt_aes_rsa_with_password(data, rsa_private_key, password)
    with open(output_file, 'wb') as f:
        f.write(decrypted)

def encrypt_file_aes_x25519(input_file, output_file, recipient_public_key, password=None, add_header=True, strict_password=True):
    with open(input_file, 'rb') as f:
        data = f.read()
    encrypted = encrypt_aes_x25519(data, recipient_public_key, password, strict_password)
    if add_header:
        encrypted = add_security_info(encrypted, 'aes_x25519', bool(password))
    with open(output_file, 'wb') as f:
        f.write(encrypted)

def decrypt_file_aes_x25519(input_file, output_file, recipient_private_key, password=None, has_header=True):
    with open(input_file, 'rb') as f:
        data = f.read()
    if has_header:
        data = remove_security_info(data)
    decrypted = decrypt_aes_x25519(data, recipient_private_key, password)
    with open(output_file, 'wb') as f:
        f.write(decrypted)

# ==================== 文本加密/解密封装 ====================

def encrypt_text_aes_rsa(text, rsa_public_key, password=None, add_header=True, strict_password=True):
    if isinstance(text, str):
        text = text.encode('utf-8')
    encrypted = encrypt_aes_rsa(text, rsa_public_key, password, strict_password)
    if add_header:
        encrypted = add_security_info(encrypted, 'aes_rsa', bool(password))
    return encrypted

def decrypt_text_aes_rsa(encrypted_text, rsa_private_key, password=None, has_header=True):
    if has_header:
        encrypted_text = remove_security_info(encrypted_text)
    if isinstance(encrypted_text, str):
        encrypted_text = encrypted_text.encode('utf-8')
    decrypted = decrypt_aes_rsa(encrypted_text, rsa_private_key, password)
    if isinstance(decrypted, bytes):
        return decrypted.decode('utf-8')
    return str(decrypted)

def encrypt_text_aes_rsa_with_password(text, rsa_public_key, password, add_header=True, strict_password=True):
    if isinstance(text, str):
        text = text.encode('utf-8')
    encrypted = encrypt_aes_rsa_with_password(text, rsa_public_key, password, strict_password)
    if add_header:
        encrypted = add_security_info(encrypted, 'aes_rsa_password', True)
    return encrypted

def decrypt_text_aes_rsa_with_password(encrypted_text, rsa_private_key, password, has_header=True):
    if has_header:
        encrypted_text = remove_security_info(encrypted_text)
    if isinstance(encrypted_text, str):
        encrypted_text = encrypted_text.encode('utf-8')
    decrypted = decrypt_aes_rsa_with_password(encrypted_text, rsa_private_key, password)
    if isinstance(decrypted, bytes):
        return decrypted.decode('utf-8')
    return str(decrypted)

def encrypt_text_aes_x25519(text, recipient_public_key, password=None, add_header=True, strict_password=True):
    if isinstance(text, str):
        text = text.encode('utf-8')
    encrypted = encrypt_aes_x25519(text, recipient_public_key, password, strict_password)
    if add_header:
        encrypted = add_security_info(encrypted, 'aes_x25519', bool(password))
    return encrypted

def decrypt_text_aes_x25519(encrypted_text, recipient_private_key, password=None, has_header=True):
    if has_header:
        encrypted_text = remove_security_info(encrypted_text)
    if isinstance(encrypted_text, str):
        encrypted_text = encrypted_text.encode('utf-8')
    decrypted = decrypt_aes_x25519(encrypted_text, recipient_private_key, password)
    if isinstance(decrypted, bytes):
        return decrypted.decode('utf-8')
    return str(decrypted)

# ==================== 导出API ====================

__all__ = [
    'generate_rsa_key',
    'generate_x25519_keys',
    'generate_strong_password',
    'is_password_strong',
    'compute_data_hash',
    'verify_data_hash',
    'encrypt_aes_rsa',
    'decrypt_aes_rsa',
    'encrypt_file_aes_rsa',
    'decrypt_file_aes_rsa',
    'encrypt_text_aes_rsa',
    'decrypt_text_aes_rsa',
    'encrypt_aes_rsa_with_password',
    'decrypt_aes_rsa_with_password',
    'encrypt_file_aes_rsa_with_password',
    'decrypt_file_aes_rsa_with_password',
    'encrypt_text_aes_rsa_with_password',
    'decrypt_text_aes_rsa_with_password',
    'encrypt_aes_x25519',
    'decrypt_aes_x25519',
    'encrypt_file_aes_x25519',
    'decrypt_file_aes_x25519',
    'encrypt_text_aes_x25519',
    'decrypt_text_aes_x25519',
    'add_security_info',
    'remove_security_info',
]