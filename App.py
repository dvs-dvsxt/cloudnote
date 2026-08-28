#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
云笔记应用程序
支持本地和云端文件管理，支持文本文件(.txt)和加密笔记(.bjb)
"""

import sys
import os
import json
import tempfile
import uuid
import hashlib
import traceback
from datetime import datetime

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import requests

# 导入加密模块
from DVT_RFSA import *

# ==================== 调试日志配置 ====================
DEBUG = True  # True=记录日志, False=不记录日志

def debug_log(msg, level="INFO"):
    """调试日志函数 - 通过全局变量DEBUG控制"""
    if DEBUG:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{level}] {msg}")
        sys.stdout.flush()

def debug_error(msg):
    """错误日志（带堆栈）"""
    if DEBUG:
        debug_log(msg, "ERROR")
        traceback.print_exc()

# ==================== 配置 ====================
API_BASE_URL = "https://noteapi.dvssvc.site/api"
APP_NAME = "CloudNote"

# 获取程序所在目录
def get_app_dir():
    """获取程序所在目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

APP_DIR = get_app_dir()

# 定义密钥目录
USER_KEY_DIR = os.path.expanduser(f"~/.{APP_NAME.lower()}/keys")
APP_KEY_DIR = os.path.join(APP_DIR, ".keys")

if DEBUG:
    debug_log(f"程序目录: {APP_DIR}")
    debug_log(f"用户密钥目录: {USER_KEY_DIR}")
    debug_log(f"程序密钥目录: {APP_KEY_DIR}")

# 密钥文件名定义
KEY_FILES = {
    'rsa_private': "global_rsa_private.pem",
    'rsa_public': "global_rsa_public.pem",
    'x25519_private': "global_x25519_private.bin",
    'x25519_public': "global_x25519_public.bin"
}

def get_key_path(key_name, prefer_user=True):
    """获取密钥文件路径"""
    if prefer_user:
        search_dirs = [USER_KEY_DIR, APP_KEY_DIR]
        dir_names = ['user', 'app']
    else:
        search_dirs = [APP_KEY_DIR, USER_KEY_DIR]
        dir_names = ['app', 'user']
    
    for dir_path, dir_type in zip(search_dirs, dir_names):
        file_path = os.path.join(dir_path, key_name)
        if os.path.exists(file_path):
            if DEBUG:
                debug_log(f"找到密钥 {key_name} 在 {dir_type} 目录: {file_path}")
            return file_path, dir_type
    
    return os.path.join(USER_KEY_DIR, key_name), 'user'

def ensure_directory(dir_path):
    """确保目录存在"""
    try:
        os.makedirs(dir_path, exist_ok=True)
        if DEBUG:
            debug_log(f"目录已确保: {dir_path}")
        return True
    except Exception as e:
        debug_error(f"创建目录失败 {dir_path}: {e}")
        return False

# ==================== 全局密钥管理（双路径） ====================
def ensure_global_keys():
    """确保全局密钥对存在"""
    if DEBUG:
        debug_log("开始检查/生成全局密钥（双路径模式）...")
    
    ensure_directory(USER_KEY_DIR)
    ensure_directory(APP_KEY_DIR)
    
    key_pairs = [
        ('rsa', KEY_FILES['rsa_private'], KEY_FILES['rsa_public'], generate_rsa_key, 4096),
        ('x25519', KEY_FILES['x25519_private'], KEY_FILES['x25519_public'], generate_x25519_keys, None)
    ]
    
    for key_type, priv_file, pub_file, gen_func, key_size in key_pairs:
        user_priv = os.path.join(USER_KEY_DIR, priv_file)
        user_pub = os.path.join(USER_KEY_DIR, pub_file)
        user_exists = os.path.exists(user_priv) and os.path.exists(user_pub)
        
        app_priv = os.path.join(APP_KEY_DIR, priv_file)
        app_pub = os.path.join(APP_KEY_DIR, pub_file)
        app_exists = os.path.exists(app_priv) and os.path.exists(app_pub)
        
        if DEBUG:
            debug_log(f"{key_type.upper()}密钥对 - 用户目录存在: {user_exists}, 程序目录存在: {app_exists}")
        
        if not user_exists:
            if DEBUG:
                debug_log(f"开始生成{key_type.upper()}密钥对到用户目录...")
            try:
                if key_size:
                    priv, pub = gen_func(key_size)
                else:
                    priv, pub = gen_func()
                
                with open(user_priv, 'wb') as f:
                    f.write(priv)
                with open(user_pub, 'wb') as f:
                    f.write(pub)
                
                try:
                    with open(app_priv, 'wb') as f:
                        f.write(priv)
                    with open(app_pub, 'wb') as f:
                        f.write(pub)
                except Exception as e:
                    if DEBUG:
                        debug_log(f"备份到程序目录失败: {e}")
            except Exception as e:
                debug_error(f"{key_type.upper()}密钥生成失败: {e}")
                raise
        
        elif user_exists and not app_exists:
            try:
                with open(user_priv, 'rb') as f:
                    priv = f.read()
                with open(user_pub, 'rb') as f:
                    pub = f.read()
                with open(app_priv, 'wb') as f:
                    f.write(priv)
                with open(app_pub, 'wb') as f:
                    f.write(pub)
                if DEBUG:
                    debug_log(f"{key_type.upper()}密钥备份成功")
            except Exception as e:
                if DEBUG:
                    debug_log(f"备份失败: {e}")
    
    if DEBUG:
        debug_log("全局密钥检查/生成完成")

def get_global_rsa_private():
    key_path, source = get_key_path(KEY_FILES['rsa_private'])
    if not os.path.exists(key_path):
        ensure_global_keys()
        key_path, source = get_key_path(KEY_FILES['rsa_private'])
    with open(key_path, 'rb') as f:
        return f.read()

def get_global_rsa_public():
    key_path, source = get_key_path(KEY_FILES['rsa_public'])
    if not os.path.exists(key_path):
        ensure_global_keys()
        key_path, source = get_key_path(KEY_FILES['rsa_public'])
    with open(key_path, 'rb') as f:
        return f.read()

def get_global_x25519_private():
    key_path, source = get_key_path(KEY_FILES['x25519_private'])
    if not os.path.exists(key_path):
        ensure_global_keys()
        key_path, source = get_key_path(KEY_FILES['x25519_private'])
    with open(key_path, 'rb') as f:
        return f.read()

def get_global_x25519_public():
    key_path, source = get_key_path(KEY_FILES['x25519_public'])
    if not os.path.exists(key_path):
        ensure_global_keys()
        key_path, source = get_key_path(KEY_FILES['x25519_public'])
    with open(key_path, 'rb') as f:
        return f.read()

# ==================== 加密笔记处理 ====================
class EncryptedNoteHandler:
    @staticmethod
    def check_file_has_password(file_path):
        """检查加密文件是否有密码保护"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            clean_data = remove_security_info(data)
            json_str = clean_data.decode('utf-8')
            info = json.loads(json_str)
            return info.get('has_password', False), info.get('mode', 'aes_rsa')
        except Exception as e:
            debug_error(f"检查文件密码状态失败: {e}")
            return False, 'unknown'
    
    @staticmethod
    def encrypt_content(content: str, algorithm: str, key_mode: str, password: str = None, single_private=None, single_public=None):
        if DEBUG:
            debug_log(f"开始加密 - 算法: {algorithm}, 密钥模式: {key_mode}, 密码保护: {password is not None}")
            debug_log(f"内容长度: {len(content)} 字符")
        
        data = content.encode('utf-8')
        private_key = None
        public_key = None
        
        try:
            if algorithm == 'rsa':
                if key_mode == 'global':
                    pub_pem = get_global_rsa_public()
                    if password:
                        encrypted = encrypt_text_aes_rsa_with_password(data, pub_pem, password, add_header=True)
                    else:
                        encrypted = encrypt_text_aes_rsa(data, pub_pem, add_header=True)
                    private_key = None
                    public_key = None
                else:
                    if single_private is None or single_public is None:
                        private_key, public_key = generate_rsa_key(4096)
                    else:
                        private_key = single_private
                        public_key = single_public
                    
                    if password:
                        encrypted = encrypt_text_aes_rsa_with_password(data, public_key, password, add_header=True)
                    else:
                        encrypted = encrypt_text_aes_rsa(data, public_key, add_header=True)
                    
                    json_str = remove_security_info(encrypted).decode('utf-8')
                    info = json.loads(json_str)
                    info['single_key'] = True
                    encrypted = add_security_info(json.dumps(info).encode('utf-8'), 'aes_rsa', bool(password))
                    return encrypted, private_key, public_key
            else:
                if key_mode == 'global':
                    pub_raw = get_global_x25519_public()
                    if password:
                        encrypted = encrypt_text_aes_x25519(data, pub_raw, password, add_header=True)
                    else:
                        encrypted = encrypt_text_aes_x25519(data, pub_raw, add_header=True)
                    private_key = None
                    public_key = None
                else:
                    if single_private is None or single_public is None:
                        private_key, public_key = generate_x25519_keys()
                    else:
                        private_key = single_private
                        public_key = single_public
                    
                    if password:
                        encrypted = encrypt_text_aes_x25519(data, public_key, password, add_header=True)
                    else:
                        encrypted = encrypt_text_aes_x25519(data, public_key, add_header=True)
                    
                    json_str = remove_security_info(encrypted).decode('utf-8')
                    info = json.loads(json_str)
                    info['single_key'] = True
                    encrypted = add_security_info(json.dumps(info).encode('utf-8'), 'aes_x25519', bool(password))
                    return encrypted, private_key, public_key
            
            return encrypted, private_key, public_key
        except Exception as e:
            debug_error(f"加密过程异常: {e}")
            raise Exception(f"加密失败: {str(e)}")


    @staticmethod
    def decrypt_file(file_path, password: str = None, single_private: bytes = None):
        if DEBUG:
            debug_log(f"开始解密文件: {file_path}")
            debug_log(f"密码提供: {password is not None}, 单独私钥提供: {single_private is not None}")
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # 移除安全信息头，获取纯加密数据（bytes类型）
            clean_data = remove_security_info(data)
            
            # 将bytes转换为字符串用于JSON解析
            json_str = clean_data.decode('utf-8')
            info = json.loads(json_str)
            mode = info.get('mode', 'aes_rsa')
            has_password = info.get('has_password', False)
            single_key = info.get('single_key', False)

            if mode in ['aes_rsa', 'aes_rsa_password_protected']:
                if single_key:
                    if single_private is None:
                        raise ValueError("此文件使用单独RSA密钥加密，请选择对应的私钥文件(.key)")
                    priv = single_private
                else:
                    priv = get_global_rsa_private()
                    
                if has_password:
                    if password is None:
                        raise ValueError("此文件受密码保护，请输入密码")
                    # 重要：传入原始bytes数据，不要重新编码
                    decrypted = decrypt_text_aes_rsa_with_password(clean_data, priv, password, has_header=False)
                else:
                    decrypted = decrypt_text_aes_rsa(clean_data, priv, has_header=False)
                    
            elif mode in ['aes_x25519', 'aes_x25519_password_protected']:
                if single_key:
                    if single_private is None:
                        raise ValueError("此文件使用单独X25519密钥加密，请选择对应的私钥文件(.key)")
                    priv = single_private
                else:
                    priv = get_global_x25519_private()
                    
                if has_password:
                    if password is None:
                        raise ValueError("此文件受密码保护，请输入密码")
                    decrypted = decrypt_text_aes_x25519(clean_data, priv, password, has_header=False)
                else:
                    decrypted = decrypt_text_aes_x25519(clean_data, priv, has_header=False)
            else:
                raise ValueError(f"未知加密模式: {mode}")
            
            # decrypted 已经是 bytes 类型，直接返回
            if DEBUG:
                debug_log(f"解密成功，解密后数据大小: {len(decrypted)}字节")
            return decrypted
            
        except Exception as e:
            debug_error(f"解密过程异常: {e}")
            raise
# ==================== 云端API客户端 ====================
class CloudClient:
    def __init__(self):
        if DEBUG:
            debug_log("初始化CloudClient")
        self.token = None
        self.user_id = None
        self.username = None

    def set_auth(self, token, user_id, username):
        if DEBUG:
            debug_log(f"设置认证信息 - 用户: {username}, ID: {user_id}")
        self.token = token
        self.user_id = user_id
        self.username = username

    def clear_auth(self):
        if DEBUG:
            debug_log("清除认证信息")
        self.token = None
        self.user_id = None
        self.username = None

    def _headers(self):
        if self.token:
            return {'x-access-token': self.token}
        return {}

    def _request(self, method, endpoint, **kwargs):
        url = f"{API_BASE_URL}{endpoint}"
        headers = self._headers()
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
        try:
            resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)
            if resp.status_code == 401:
                return None
            return resp
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(None, "网络错误", "无法连接到服务器，请检查网络连接")
            return None
        except Exception as e:
            QMessageBox.critical(None, "网络错误", f"请求失败: {str(e)}")
            return None

    def register(self, username, email, password):
        resp = self._request('POST', '/register', json={'username': username, 'email': email, 'password': password})
        if resp and resp.status_code == 201:
            return resp.json()
        return None

    def login(self, email, password):
        resp = self._request('POST', '/login', json={'email': email, 'password': password})
        if resp and resp.status_code == 200:
            data = resp.json()
            self.set_auth(data['token'], data['user_id'], data['username'])
            return data
        return None

    def get_filetree(self, folder='/'):
        resp = self._request('GET', '/filetree', params={'folder': folder})
        if resp and resp.status_code == 200:
            return resp.json()
        return None

    def create_folder(self, name, parent='/'):
        resp = self._request('POST', '/create_folder', json={'name': name, 'parent': parent})
        if resp and resp.status_code == 201:
            return resp.json()
        return None

    def upload_file(self, file_path, parent_folder='/'):
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.txt', '.bjb']:
            QMessageBox.warning(None, "错误", "只支持上传 .txt 和 .bjb 文件")
            return None
        
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            data = {'parent_folder': parent_folder}
            resp = self._request('POST', '/upload', files=files, data=data)
        if resp and resp.status_code == 201:
            return resp.json()
        return None

    def download_file(self, file_id, target_path):
        resp = self._request('GET', f'/download/{file_id}')
        if resp and resp.status_code == 200:
            with open(target_path, 'wb') as f:
                f.write(resp.content)
            return True
        return False

    def delete_item(self, item_id):
        resp = self._request('DELETE', f'/delete/{item_id}')
        if resp:
            return resp.status_code == 200
        return False

    def rename_item(self, item_id, new_name):
        resp = self._request('PUT', f'/rename/{item_id}', json={'new_name': new_name})
        if resp:
            return resp.status_code == 200
        return False

    def move_item(self, item_id, target_folder):
        resp = self._request('POST', '/move', json={'item_id': item_id, 'target_folder': target_folder})
        if resp:
            return resp.status_code == 200
        return False

    def search_files(self, keyword):
        resp = self._request('GET', '/search', params={'q': keyword})
        if resp and resp.status_code == 200:
            return resp.json()
        return None

    def get_storage_info(self):
        resp = self._request('GET', '/storage_info')
        if resp and resp.status_code == 200:
            return resp.json()
        return None

    def get_user_info(self):
        resp = self._request('GET', '/user_info')
        if resp and resp.status_code == 200:
            return resp.json()
        return None


# ==================== 通用解密函数（本地和云端共用）====================
def decrypt_bjb_file(file_path, parent_window):
    """
    解密.bjb文件的通用函数
    返回: (content, success)
    """
    if DEBUG:
        debug_log(f"通用解密函数: {file_path}")
    
    try:
        # 检查是否有密钥文件
        key_file = file_path + '.key'
        single_private = None
        if os.path.exists(key_file):
            if DEBUG:
                debug_log(f"发现密钥文件: {key_file}")
            with open(key_file, 'rb') as f:
                single_private = f.read()
            if DEBUG:
                debug_log(f"密钥文件读取成功，长度: {len(single_private)}字节")
        
        # 检查文件是否有密码保护
        has_password, mode = EncryptedNoteHandler.check_file_has_password(file_path)
        if DEBUG:
            debug_log(f"文件密码状态: has_password={has_password}, mode={mode}")
        
        password = None
        
        # 如果有密码保护，弹出密码输入框
        if has_password:
            if DEBUG:
                debug_log("检测到密码保护，弹出密码输入框")
            
            max_attempts = 3
            attempts = 0
            success = False
            
            while attempts < max_attempts and not success:
                pwd, ok = QInputDialog.getText(
                    parent_window, "输入密码",
                    f"此文件受密码保护，请输入密码 (尝试 {attempts + 1}/{max_attempts}):",
                    QLineEdit.Password
                )
                if not ok:
                    if DEBUG:
                        debug_log("用户取消输入密码")
                    return None, False
                
                if pwd:
                    try:
                        if DEBUG:
                            debug_log(f"尝试密码解密 (长度: {len(pwd)})")
                        # 直接调用解密方法，传入密码
                        decrypted = EncryptedNoteHandler.decrypt_file(
                            file_path, password=pwd, single_private=single_private
                        )
                        content = decrypted.decode('utf-8')
                        success = True
                        if DEBUG:
                            debug_log("密码解密成功")
                    except Exception as e:
                        error_msg = str(e)
                        if DEBUG:
                            debug_log(f"密码解密失败: {error_msg}")
                        attempts += 1
                        if attempts < max_attempts:
                            QMessageBox.warning(parent_window, "密码错误",
                                f"密码错误，还剩 {max_attempts - attempts} 次尝试")
                        else:
                            QMessageBox.warning(parent_window, "解密失败",
                                "多次密码错误，无法解密文件")
                            return None, False
                else:
                    attempts += 1
                    QMessageBox.warning(parent_window, "密码为空", "密码不能为空")
            
            if not success:
                return None, False
        else:
            # 无密码保护，直接解密
            if DEBUG:
                debug_log("无密码保护，直接解密")
            decrypted = EncryptedNoteHandler.decrypt_file(
                file_path, password=None, single_private=single_private
            )
            content = decrypted.decode('utf-8')
        
        return content, True
        
    except Exception as e:
        debug_error(f"解密失败: {e}")
        QMessageBox.critical(parent_window, "解密失败", str(e))
        return None, False

# ==================== 登录对话框 ====================
class LoginDialog(QDialog):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        if DEBUG:
            debug_log("初始化登录对话框")
        self.client = client
        self.setWindowTitle("云笔记 - 登录")
        self.setFixedSize(400, 350)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        card = QWidget()
        card.setObjectName("card")
        card.setStyleSheet("""
            #card { background-color: white; border-radius: 16px; }
            QLineEdit { border: 1px solid #e1e4e8; border-radius: 10px; padding: 12px; font-size: 14px; }
            QPushButton { border-radius: 10px; padding: 12px; font-size: 14px; font-weight: 500; }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)

        title = QLabel("☁️ 云笔记")
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("电子邮箱")
        self.email_input.setMinimumHeight(45)
        card_layout.addWidget(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(45)
        card_layout.addWidget(self.password_input)

        self.remember_check = QCheckBox("记住我")
        card_layout.addWidget(self.remember_check)

        self.login_btn = QPushButton("登 录")
        self.login_btn.setMinimumHeight(45)
        self.login_btn.setStyleSheet("background-color: #0366d6; color: white; border: none;")
        self.login_btn.clicked.connect(self.do_login)
        card_layout.addWidget(self.login_btn)

        register_btn = QPushButton("还没有账号？立即注册")
        register_btn.setStyleSheet("background: transparent; color: #0366d6; border: none;")
        register_btn.clicked.connect(self.show_register)
        card_layout.addWidget(register_btn, alignment=Qt.AlignCenter)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("background: transparent; border: none; font-size: 20px;")
        close_btn.clicked.connect(self.reject)

        layout.addWidget(card)
        close_btn.setParent(self)
        close_btn.move(self.width() - 40, 15)

    def do_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        
        if not email or not password:
            QMessageBox.warning(self, "提示", "请填写邮箱和密码")
            return
        
        data = self.client.login(email, password)
        if data:
            if self.remember_check.isChecked():
                settings = QSettings("CloudNote", "User")
                settings.setValue("token", self.client.token)
                settings.setValue("user_id", self.client.user_id)
                settings.setValue("username", self.client.username)
            self.accept()
        else:
            QMessageBox.warning(self, "错误", "邮箱或密码错误")

    def show_register(self):
        dialog = RegisterDialog(self.client, self)
        dialog.exec_()


# ==================== 注册对话框 ====================
class RegisterDialog(QDialog):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        if DEBUG:
            debug_log("初始化注册对话框")
        self.client = client
        self.setWindowTitle("注册账号")
        self.setFixedSize(400, 450)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        card = QWidget()
        card.setObjectName("card")
        card.setStyleSheet("""
            #card { background-color: white; border-radius: 16px; }
            QLineEdit { border: 1px solid #e1e4e8; border-radius: 10px; padding: 12px; font-size: 14px; }
            QPushButton { border-radius: 10px; padding: 12px; font-size: 14px; font-weight: 500; }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(15)

        title = QLabel("📝 创建新账号")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名")
        self.username_input.setMinimumHeight(45)
        card_layout.addWidget(self.username_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("电子邮箱")
        self.email_input.setMinimumHeight(45)
        card_layout.addWidget(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码（至少6位）")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(45)
        card_layout.addWidget(self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("确认密码")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setMinimumHeight(45)
        card_layout.addWidget(self.confirm_input)

        self.register_btn = QPushButton("注 册")
        self.register_btn.setMinimumHeight(45)
        self.register_btn.setStyleSheet("background-color: #0366d6; color: white; border: none;")
        self.register_btn.clicked.connect(self.do_register)
        card_layout.addWidget(self.register_btn)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("background: transparent; border: none; font-size: 20px;")
        close_btn.clicked.connect(self.reject)

        layout.addWidget(card)
        close_btn.setParent(self)
        close_btn.move(self.width() - 40, 15)

    def do_register(self):
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        confirm = self.confirm_input.text().strip()

        if not all([username, email, password]):
            QMessageBox.warning(self, "提示", "请填写所有字段")
            return
        if password != confirm:
            QMessageBox.warning(self, "错误", "两次密码不一致")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "错误", "密码至少6位")
            return

        res = self.client.register(username, email, password)
        if res:
            QMessageBox.information(self, "成功", "注册成功，请登录")
            self.accept()
        else:
            QMessageBox.warning(self, "错误", "注册失败，用户名或邮箱已存在")


# ==================== 新建加密文件对话框 ====================
class NewEncryptedFileDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        if DEBUG:
            debug_log("初始化新建加密文件对话框")
        self.setWindowTitle("新建加密笔记")
        self.setFixedSize(600, 650)
        self.selected_algorithm = 'rsa'
        self.selected_key_mode = 'global'
        self.use_password = False
        self.custom_password = None
        self.single_private = None
        self.single_public = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title = QLabel("🔐 加密配置")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        group1 = QGroupBox("1. 选择加密算法")
        group1_layout = QVBoxLayout()
        self.radio_rsa = QRadioButton("RSA-4096 + AES-256-GCM")
        self.radio_x25519 = QRadioButton("X25519 + AES-256-GCM")
        self.radio_rsa.setChecked(True)
        group1_layout.addWidget(self.radio_rsa)
        group1_layout.addWidget(self.radio_x25519)
        group1.setLayout(group1_layout)
        layout.addWidget(group1)

        group2 = QGroupBox("2. 选择密钥方式")
        group2_layout = QVBoxLayout()
        self.radio_global = QRadioButton("默认加密（使用全局密钥对）")
        self.radio_single = QRadioButton("安全加密（为当前文件单独生成密钥对）")
        self.radio_global.setChecked(True)
        group2_layout.addWidget(self.radio_global)
        group2_layout.addWidget(self.radio_single)
        group2.setLayout(group2_layout)
        layout.addWidget(group2)

        group3 = QGroupBox("3. 额外密码保护（可选）")
        group3_layout = QVBoxLayout()
        self.checkbox_password = QCheckBox("启用双层加密")
        self.checkbox_password.toggled.connect(self.on_password_toggled)
        group3_layout.addWidget(self.checkbox_password)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码（至少16位，包含大小写字母、数字和特殊字符）")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setEnabled(False)
        group3_layout.addWidget(self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("确认密码")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setEnabled(False)
        group3_layout.addWidget(self.confirm_input)

        self.password_strength_label = QLabel("")
        self.password_strength_label.setStyleSheet("font-size: 12px;")
        group3_layout.addWidget(self.password_strength_label)

        self.password_input.textChanged.connect(self.check_password_strength)
        group3.setLayout(group3_layout)
        layout.addWidget(group3)

        info_label = QLabel("说明：\n• 默认加密：使用全局密钥对，所有文件共用同一密钥\n• 安全加密：每个文件独立生成密钥对，私钥保存为 .key 文件\n• 密钥文件请妥善保管，丢失后将无法解密文件！")
        info_label.setStyleSheet("color: #586069; font-size: 12px; background-color: #f6f8fa; padding: 10px; border-radius: 8px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        self.ok_btn.clicked.connect(self.accept_config)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def on_password_toggled(self, checked):
        if DEBUG:
            debug_log(f"密码保护开关: {checked}")
        self.password_input.setEnabled(checked)
        self.confirm_input.setEnabled(checked)
        self.use_password = checked

    def check_password_strength(self):
        pwd = self.password_input.text()
        if len(pwd) >= 16 and any(c.isupper() for c in pwd) and any(c.islower() for c in pwd) and any(c.isdigit() for c in pwd) and any(not c.isalnum() for c in pwd):
            self.password_strength_label.setText("✓ 密码强度：强")
            self.password_strength_label.setStyleSheet("color: green; font-size: 12px;")
        elif len(pwd) >= 12:
            self.password_strength_label.setText("⚠ 密码强度：中（建议至少16位）")
            self.password_strength_label.setStyleSheet("color: orange; font-size: 12px;")
        else:
            self.password_strength_label.setText("✗ 密码强度：弱（需要至少16位）")
            self.password_strength_label.setStyleSheet("color: red; font-size: 12px;")

    def accept_config(self):
        if DEBUG:
            debug_log("开始获取加密配置")
        
        if self.radio_rsa.isChecked():
            self.selected_algorithm = 'rsa'
        else:
            self.selected_algorithm = 'x25519'
        if DEBUG:
            debug_log(f"算法: {self.selected_algorithm}")

        if self.radio_global.isChecked():
            self.selected_key_mode = 'global'
        else:
            self.selected_key_mode = 'single'
        if DEBUG:
            debug_log(f"密钥模式: {self.selected_key_mode}")

        if self.use_password:
            pwd = self.password_input.text()
            confirm = self.confirm_input.text()
            
            if not pwd or not confirm:
                QMessageBox.warning(self, "提示", "请输入密码")
                return
            if pwd != confirm:
                QMessageBox.warning(self, "错误", "两次输入的密码不一致")
                return
            if not is_password_strong(pwd):
                QMessageBox.warning(self, "密码强度不足", "密码必须至少16位，包含大小写字母、数字和特殊字符")
                return
            self.custom_password = pwd
            if DEBUG:
                debug_log("密码验证通过")

        if self.selected_key_mode == 'single':
            if DEBUG:
                debug_log("生成单独密钥对")
            if self.selected_algorithm == 'rsa':
                self.single_private, self.single_public = generate_rsa_key(4096)
            else:
                self.single_private, self.single_public = generate_x25519_keys()

        if DEBUG:
            debug_log("加密配置获取完成")
        self.accept()

    def get_config(self):
        return {
            'algorithm': self.selected_algorithm,
            'key_mode': self.selected_key_mode,
            'use_password': self.use_password,
            'custom_password': self.custom_password,
            'single_private': self.single_private,
            'single_public': self.single_public
        }


# ==================== 保存加密文件对话框 ====================
class SaveEncryptedFileDialog(QDialog):
    def __init__(self, content, algorithm, key_mode, use_password, custom_password, single_private, single_public, parent=None):
        super().__init__(parent)
        if DEBUG:
            debug_log("初始化保存加密文件对话框")
        self.content = content
        self.algorithm = algorithm
        self.key_mode = key_mode
        self.use_password = use_password
        self.custom_password = custom_password
        self.single_private = single_private
        self.single_public = single_public
        self.setWindowTitle("保存加密笔记")
        self.setFixedSize(650, 400)
        self.selected_file_path = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        if self.key_mode == 'single':
            info_label = QLabel("⚠️ 您选择了【安全加密】模式，将为当前文件单独生成密钥对。\n密钥文件(.key)将与.bjb文件保存在同一目录，请妥善保管！\n丢失密钥文件后将无法解密！")
            info_label.setStyleSheet("color: #e36209; background-color: #fff5eb; padding: 10px; border-radius: 8px;")
            info_label.setWordWrap(True)
            layout.addWidget(info_label)

        layout.addWidget(QLabel("📁 保存位置和文件名："))
        
        file_select_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("请选择保存位置...")
        self.file_path_input.setMinimumHeight(35)
        self.file_path_input.textChanged.connect(self.on_path_changed)
        file_select_layout.addWidget(self.file_path_input)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.select_save_file)
        file_select_layout.addWidget(self.browse_btn)
        layout.addLayout(file_select_layout)

        info_group = QGroupBox("加密信息摘要")
        info_layout = QVBoxLayout()
        
        algo_text = "RSA-4096" if self.algorithm == 'rsa' else "X25519"
        key_text = "全局密钥" if self.key_mode == 'global' else "单独密钥(安全模式)"
        pwd_text = "已启用" if self.use_password else "未启用"
        
        info_layout.addWidget(QLabel(f"🔐 加密算法: {algo_text} + AES-256-GCM"))
        info_layout.addWidget(QLabel(f"🔑 密钥方式: {key_text}"))
        info_layout.addWidget(QLabel(f"🔒 密码保护: {pwd_text}"))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("💾 保存")
        self.ok_btn.setStyleSheet("background-color: #28a745; color: white;")
        self.cancel_btn = QPushButton("取消")
        self.ok_btn.clicked.connect(self.do_save)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def on_path_changed(self, text):
        if text.strip():
            self.selected_file_path = text.strip()

    def select_save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "保存加密笔记", "", "加密笔记 (*.bjb)")
        if file_path:
            if not file_path.endswith('.bjb'):
                file_path += '.bjb'
            self.selected_file_path = file_path
            self.file_path_input.setText(file_path)

    def do_save(self):
        if not self.selected_file_path:
            QMessageBox.warning(self, "提示", "请选择保存位置")
            return
        
        if not self.selected_file_path.endswith('.bjb'):
            self.selected_file_path += '.bjb'

        try:
            encrypted_data, priv, pub = EncryptedNoteHandler.encrypt_content(
                self.content, self.algorithm, self.key_mode,
                self.custom_password, self.single_private, self.single_public
            )
        except Exception as e:
            QMessageBox.critical(self, "加密失败", str(e))
            return

        try:
            with open(self.selected_file_path, 'wb') as f:
                f.write(encrypted_data)
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"无法保存.bjb文件: {str(e)}")
            return

        key_path = None
        if self.key_mode == 'single' and priv:
            key_path = self.selected_file_path + '.key'
            try:
                with open(key_path, 'wb') as f:
                    f.write(priv)
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"无法保存.key文件: {str(e)}")
                return

        msg = f"✅ 文件已保存！\n\n📄 .bjb文件：{self.selected_file_path}"
        if key_path:
            msg += f"\n🔑 .key文件：{key_path}\n\n⚠️ 请妥善保管密钥文件！"
        else:
            msg += "\n\n💡 提示：使用全局密钥，无需额外保存密钥文件。"
        
        QMessageBox.information(self, "保存成功", msg)
        self.accept()


# ==================== 云端文件树窗口 ====================
class CloudFileTreeDialog(QDialog):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        if DEBUG:
            debug_log("初始化云端文件树对话框")
        self.client = client
        self.setWindowTitle("云端文件管理")
        self.resize(900, 700)
        self.setup_ui()
        self.current_folder = '/'
        self.load_filetree()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        toolbar = QToolBar()
        self.up_btn = QAction("⬆ 返回上级", self)
        self.up_btn.triggered.connect(self.go_up)
        toolbar.addAction(self.up_btn)
        self.refresh_btn = QAction("🔄 刷新", self)
        self.refresh_btn.triggered.connect(self.load_filetree)
        toolbar.addAction(self.refresh_btn)
        self.new_folder_btn = QAction("📁 新建文件夹", self)
        self.new_folder_btn.triggered.connect(self.create_folder)
        toolbar.addAction(self.new_folder_btn)
        self.upload_btn = QAction("📤 上传文件", self)
        self.upload_btn.triggered.connect(self.upload_file)
        toolbar.addAction(self.upload_btn)
        layout.addWidget(toolbar)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索文件...")
        self.search_input.returnPressed.connect(self.search_files)
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.search_files)
        clear_btn = QPushButton("清除")
        clear_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        search_layout.addWidget(clear_btn)
        layout.addLayout(search_layout)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["名称", "大小", "类型", "修改时间"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemDoubleClicked.connect(self.on_item_double_click)
        layout.addWidget(self.tree)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.load_storage_info()

    def load_storage_info(self):
        info = self.client.get_storage_info()
        if info:
            used_mb = info['total_size'] / (1024 * 1024)
            max_mb = info['max_size'] / (1024 * 1024)
            download_used_mb = info['download_used'] / (1024 * 1024)
            download_max_mb = info['download_max'] / (1024 * 1024)
            self.status_label.setText(f"存储: {used_mb:.1f}MB / {max_mb:.0f}MB | 今日下载: {download_used_mb:.1f}MB / {download_max_mb:.0f}MB")

    def load_filetree(self):
        if DEBUG:
            debug_log(f"加载文件树: {self.current_folder}")
        data = self.client.get_filetree(self.current_folder)
        if not data:
            QMessageBox.warning(self, "错误", "加载文件树失败")
            return
        self.tree.clear()
        for item in data['items']:
            size_str = self.format_size(item['size']) if item['size'] else ""
            type_str = "文件夹" if item['is_folder'] else (item['type'] or "文件")
            tree_item = QTreeWidgetItem([item['name'], size_str, type_str, item['created_at']])
            tree_item.setData(0, Qt.UserRole, item)
            self.tree.addTopLevelItem(tree_item)
        self.load_storage_info()

    def format_size(self, size_bytes):
        if not size_bytes:
            return ""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"

    def go_up(self):
        if self.current_folder != '/':
            parts = self.current_folder.rstrip('/').split('/')
            if len(parts) > 1:
                self.current_folder = '/' + '/'.join(parts[:-1])
            else:
                self.current_folder = '/'
            self.load_filetree()

    def create_folder(self):
        name, ok = QInputDialog.getText(self, "新建文件夹", "请输入文件夹名称:")
        if ok and name:
            if '/' in name or '\\' in name:
                QMessageBox.warning(self, "错误", "文件夹名称不能包含路径分隔符")
                return
            res = self.client.create_folder(name, self.current_folder)
            if res:
                self.load_filetree()
            else:
                QMessageBox.warning(self, "错误", "创建失败")

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择要上传的文件", "", "笔记本文件 (*.bjb *.txt)")
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in ['.txt', '.bjb']:
                QMessageBox.warning(self, "错误", "只支持上传 .txt 和 .bjb 文件")
                return
            
            file_size = os.path.getsize(file_path)
            info = self.client.get_storage_info()
            if info and info['total_size'] + file_size > info['max_size']:
                QMessageBox.warning(self, "错误", "云端存储空间不足")
                return
            res = self.client.upload_file(file_path, self.current_folder)
            if res:
                QMessageBox.information(self, "成功", "上传成功")
                self.load_filetree()
            else:
                QMessageBox.warning(self, "错误", "上传失败")

    def search_files(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            return
        data = self.client.search_files(keyword)
        if data:
            self.tree.clear()
            for item in data['items']:
                size_str = self.format_size(item['size']) if item['size'] else ""
                type_str = "文件夹" if item['is_folder'] else (item['type'] or "文件")
                tree_item = QTreeWidgetItem([item['name'], size_str, type_str, ""])
                tree_item.setData(0, Qt.UserRole, item)
                self.tree.addTopLevelItem(tree_item)
            self.status_label.setText(f"搜索到 {len(data['items'])} 个结果")

    def clear_search(self):
        self.search_input.clear()
        self.load_filetree()

    def on_item_double_click(self, item, col):
        data = item.data(0, Qt.UserRole)
        if data['is_folder']:
            if self.search_input.text():
                self.clear_search()
            self.current_folder = data['parent'] + '/' + data['name'] if data['parent'] != '/' else '/' + data['name']
            self.load_filetree()
        else:
            self.download_and_open(data)

    def download_and_open(self, file_info):
        """下载并打开云端文件 - 修复：使用通用解密函数"""
        temp_dir = tempfile.gettempdir()
        local_path = os.path.join(temp_dir, f"cloud_{file_info['id']}_{file_info['name']}")
        
        if DEBUG:
            debug_log(f"下载文件到: {local_path}")
        
        if self.client.download_file(file_info['id'], local_path):
            if DEBUG:
                debug_log("下载成功")
            
            ext = os.path.splitext(file_info['name'])[1].lower()
            
            if ext == '.txt':
                # 文本文件直接打开
                try:
                    with open(local_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    main_window = self.parent()
                    if isinstance(main_window, MainWindow):
                        tab = EditorTab(main_window.tabs, main_window.tabs.count(),
                                       file_path=local_path, cloud_id=file_info['id'],
                                       file_type='txt', content=content)
                        main_window.tabs.addTab(tab.text_edit, os.path.basename(file_info['name']))
                        main_window.editor_tabs.append(tab)
                        main_window.tabs.setCurrentIndex(main_window.tabs.count() - 1)
                        self.accept()
                except Exception as e:
                    debug_error(f"读取文本文件失败: {e}")
                    QMessageBox.warning(self, "错误", f"读取文件失败: {str(e)}")
            else:
                # 加密文件使用通用解密函数
                content, success = decrypt_bjb_file(local_path, self)
                if success and content is not None:
                    main_window = self.parent()
                    if isinstance(main_window, MainWindow):
                        tab = EditorTab(main_window.tabs, main_window.tabs.count(),
                                       file_path=local_path, cloud_id=file_info['id'],
                                       file_type='bjb', content=content)
                        main_window.tabs.addTab(tab.text_edit, os.path.basename(file_info['name']))
                        main_window.editor_tabs.append(tab)
                        main_window.tabs.setCurrentIndex(main_window.tabs.count() - 1)
                        self.accept()
                else:
                    QMessageBox.warning(self, "错误", "解密失败")
        else:
            QMessageBox.warning(self, "错误", "下载失败")

    def show_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return
        data = item.data(0, Qt.UserRole)
        menu = QMenu()
        rename_action = menu.addAction("重命名")
        delete_action = menu.addAction("删除")
        move_action = menu.addAction("移动")
        download_action = menu.addAction("下载")
        action = menu.exec_(self.tree.viewport().mapToGlobal(pos))
        if action == rename_action:
            new_name, ok = QInputDialog.getText(self, "重命名", "新名称:", text=data['name'])
            if ok and new_name:
                if self.client.rename_item(data['id'], new_name):
                    self.load_filetree()
                else:
                    QMessageBox.warning(self, "错误", "重命名失败")
        elif action == delete_action:
            if QMessageBox.question(self, "确认", f"确定删除 {data['name']} 吗？") == QMessageBox.Yes:
                if self.client.delete_item(data['id']):
                    self.load_filetree()
                else:
                    QMessageBox.warning(self, "错误", "删除失败")
        elif action == move_action:
            target, ok = QInputDialog.getText(self, "移动", "目标文件夹路径 (例如 /folder):")
            if ok and target:
                if self.client.move_item(data['id'], target):
                    self.load_filetree()
                else:
                    QMessageBox.warning(self, "错误", "移动失败")
        elif action == download_action:
            save_path, _ = QFileDialog.getSaveFileName(self, "保存文件", data['name'])
            if save_path:
                if self.client.download_file(data['id'], save_path):
                    QMessageBox.information(self, "成功", "下载完成")
                else:
                    QMessageBox.warning(self, "错误", "下载失败")


# ==================== 编辑器选项卡 ====================
class EditorTab:
    def __init__(self, tab_widget, index, file_path=None, cloud_id=None, is_new=False,
                 content="", file_type="txt", encrypt_config=None):
        if DEBUG:
            debug_log(f"创建编辑器选项卡 - 类型: {file_type}, 新文件: {is_new}, 路径: {file_path}")
        self.tab_widget = tab_widget
        self.index = index
        self.file_path = file_path
        self.cloud_id = cloud_id
        self.is_new = is_new
        self.file_type = file_type
        self.encrypt_config = encrypt_config
        self.modified = False
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(content)
        self.text_edit.textChanged.connect(self.on_text_changed)

        font = QFont("Consolas", 12)
        self.text_edit.setFont(font)

        self.update_tab_title()

    def update_tab_title(self):
        if self.file_path:
            name = os.path.basename(self.file_path)
        elif self.cloud_id is not None:
            name = f"云端文件_{self.cloud_id}"
        else:
            name = "未命名"
        if self.file_type == 'bjb':
            name = f"🔒 {name}"
        if self.modified:
            name = "* " + name
        self.tab_widget.setTabText(self.index, name)

    def on_text_changed(self):
        if not self.modified:
            self.modified = True
            self.update_tab_title()

    def get_content(self):
        return self.text_edit.toPlainText()

    def set_content(self, content):
        self.text_edit.setPlainText(content)
        self.modified = False
        self.update_tab_title()

    def mark_saved(self):
        self.modified = False
        self.update_tab_title()


# ==================== 加密当前文件对话框 ====================
class EncryptCurrentFileDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        if DEBUG:
            debug_log("初始化加密当前文件对话框")
        self.setWindowTitle("加密当前文件")
        self.setFixedSize(600, 550)
        self.selected_algorithm = 'rsa'
        self.selected_key_mode = 'global'
        self.use_password = False
        self.custom_password = None
        self.single_private = None
        self.single_public = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title = QLabel("🔐 加密当前文件配置")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        info_label = QLabel("⚠️ 注意：加密后将生成新的.bjb文件，原文件不会被删除")
        info_label.setStyleSheet("color: #e36209; background-color: #fff5eb; padding: 8px; border-radius: 8px;")
        layout.addWidget(info_label)

        group1 = QGroupBox("1. 选择加密算法")
        group1_layout = QVBoxLayout()
        self.radio_rsa = QRadioButton("RSA-4096 + AES-256-GCM")
        self.radio_x25519 = QRadioButton("X25519 + AES-256-GCM")
        self.radio_rsa.setChecked(True)
        group1_layout.addWidget(self.radio_rsa)
        group1_layout.addWidget(self.radio_x25519)
        group1.setLayout(group1_layout)
        layout.addWidget(group1)

        group2 = QGroupBox("2. 选择密钥方式")
        group2_layout = QVBoxLayout()
        self.radio_global = QRadioButton("默认加密（使用全局密钥对）")
        self.radio_single = QRadioButton("安全加密（为当前文件单独生成密钥对）")
        self.radio_global.setChecked(True)
        group2_layout.addWidget(self.radio_global)
        group2_layout.addWidget(self.radio_single)
        group2.setLayout(group2_layout)
        layout.addWidget(group2)

        group3 = QGroupBox("3. 额外密码保护（可选）")
        group3_layout = QVBoxLayout()
        self.checkbox_password = QCheckBox("启用双层加密")
        self.checkbox_password.toggled.connect(self.on_password_toggled)
        group3_layout.addWidget(self.checkbox_password)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码（至少16位，包含大小写字母、数字和特殊字符）")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setEnabled(False)
        group3_layout.addWidget(self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("确认密码")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setEnabled(False)
        group3_layout.addWidget(self.confirm_input)

        self.password_strength_label = QLabel("")
        self.password_strength_label.setStyleSheet("font-size: 12px;")
        group3_layout.addWidget(self.password_strength_label)

        self.password_input.textChanged.connect(self.check_password_strength)
        group3.setLayout(group3_layout)
        layout.addWidget(group3)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("加密并保存")
        self.ok_btn.setStyleSheet("background-color: #28a745; color: white;")
        self.cancel_btn = QPushButton("取消")
        self.ok_btn.clicked.connect(self.accept_config)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def on_password_toggled(self, checked):
        if DEBUG:
            debug_log(f"密码保护开关: {checked}")
        self.password_input.setEnabled(checked)
        self.confirm_input.setEnabled(checked)
        self.use_password = checked

    def check_password_strength(self):
        pwd = self.password_input.text()
        if len(pwd) >= 16 and any(c.isupper() for c in pwd) and any(c.islower() for c in pwd) and any(c.isdigit() for c in pwd) and any(not c.isalnum() for c in pwd):
            self.password_strength_label.setText("✓ 密码强度：强")
            self.password_strength_label.setStyleSheet("color: green; font-size: 12px;")
        elif len(pwd) >= 12:
            self.password_strength_label.setText("⚠ 密码强度：中（建议至少16位）")
            self.password_strength_label.setStyleSheet("color: orange; font-size: 12px;")
        else:
            self.password_strength_label.setText("✗ 密码强度：弱（需要至少16位）")
            self.password_strength_label.setStyleSheet("color: red; font-size: 12px;")

    def accept_config(self):
        if DEBUG:
            debug_log("开始获取加密配置")
        
        if self.radio_rsa.isChecked():
            self.selected_algorithm = 'rsa'
        else:
            self.selected_algorithm = 'x25519'

        if self.radio_global.isChecked():
            self.selected_key_mode = 'global'
        else:
            self.selected_key_mode = 'single'

        if self.use_password:
            pwd = self.password_input.text()
            confirm = self.confirm_input.text()
            
            if not pwd or not confirm:
                QMessageBox.warning(self, "提示", "请输入密码")
                return
            if pwd != confirm:
                QMessageBox.warning(self, "错误", "两次输入的密码不一致")
                return
            if not is_password_strong(pwd):
                QMessageBox.warning(self, "密码强度不足", "密码必须至少16位，包含大小写字母、数字和特殊字符")
                return
            self.custom_password = pwd

        if self.selected_key_mode == 'single':
            if DEBUG:
                debug_log("生成单独密钥对")
            if self.selected_algorithm == 'rsa':
                self.single_private, self.single_public = generate_rsa_key(4096)
            else:
                self.single_private, self.single_public = generate_x25519_keys()

        self.accept()

    def get_config(self):
        return {
            'algorithm': self.selected_algorithm,
            'key_mode': self.selected_key_mode,
            'use_password': self.use_password,
            'custom_password': self.custom_password,
            'single_private': self.single_private,
            'single_public': self.single_public
        }


# ==================== 主窗口 ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        if DEBUG:
            debug_log("初始化主窗口")
        self.client = CloudClient()
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.setCentralWidget(self.tabs)
        self.setWindowTitle(f"云笔记 - 安全加密笔记")
        self.resize(1200, 800)
        self.setup_menu()
        self.setup_statusbar()
        self.editor_tabs = []
        self.pending_encrypt_config = None
        self.current_editor = None

        ensure_global_keys()
        self.check_login()

    def setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件")

        new_txt_action = QAction("新建文本文件(.txt)", self)
        new_txt_action.setShortcut(QKeySequence("Ctrl+N"))
        new_txt_action.triggered.connect(lambda: self.new_file('txt'))
        file_menu.addAction(new_txt_action)

        new_bjb_action = QAction("新建加密笔记(.bjb)...", self)
        new_bjb_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        new_bjb_action.triggered.connect(lambda: self.new_file('bjb'))
        file_menu.addAction(new_bjb_action)

        file_menu.addSeparator()

        open_action = QAction("打开文件...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_local_file_dialog)
        file_menu.addAction(open_action)

        open_cloud_action = QAction("从云端打开...", self)
        open_cloud_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_cloud_action.triggered.connect(self.open_cloud_file_dialog)
        file_menu.addAction(open_cloud_action)

        file_menu.addSeparator()

        save_action = QAction("保存", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_current_tab)
        file_menu.addAction(save_action)

        save_as_action = QAction("另存为...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_as_current_tab)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 加密菜单
        encrypt_menu = menubar.addMenu("加密")

        encrypt_current_action = QAction("🔐 加密当前文件...", self)
        encrypt_current_action.setShortcut(QKeySequence("Ctrl+E"))
        encrypt_current_action.triggered.connect(self.encrypt_current_file)
        encrypt_menu.addAction(encrypt_current_action)

        encrypt_menu.addSeparator()

        txt_to_bjb_action = QAction("📄 另存为加密笔记(.bjb)...", self)
        txt_to_bjb_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        txt_to_bjb_action.triggered.connect(self.convert_txt_to_bjb)
        encrypt_menu.addAction(txt_to_bjb_action)

        cloud_menu = menubar.addMenu("云端")

        manage_cloud_action = QAction("管理云端文件", self)
        manage_cloud_action.triggered.connect(self.show_cloud_manager)
        cloud_menu.addAction(manage_cloud_action)

        upload_action = QAction("上传当前文件到云端", self)
        upload_action.triggered.connect(self.upload_current_tab)
        cloud_menu.addAction(upload_action)

        cloud_menu.addSeparator()

        logout_action = QAction("退出登录", self)
        logout_action.triggered.connect(self.logout)
        cloud_menu.addAction(logout_action)

        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.about)
        help_menu.addAction(about_action)

    def setup_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.storage_label = QLabel("")
        self.status_bar.addPermanentWidget(self.storage_label)
        self.update_storage_info()

    def update_storage_info(self):
        if self.client.token:
            info = self.client.get_storage_info()
            if info:
                used_mb = info['total_size'] / (1024 * 1024)
                max_mb = info['max_size'] / (1024 * 1024)
                self.storage_label.setText(f"📁 {used_mb:.1f}MB / {max_mb:.0f}MB")

    def check_login(self):
        settings = QSettings("CloudNote", "User")
        token = settings.value("token")
        user_id = settings.value("user_id")
        username = settings.value("username")

        if token and user_id and username:
            self.client.set_auth(token, int(user_id), username)
            user_info = self.client.get_user_info()
            if user_info:
                self.status_bar.showMessage(f"欢迎回来，{username}")
                self.update_storage_info()
                return
            else:
                settings.clear()
                self.client.clear_auth()

        dialog = LoginDialog(self.client, self)
        if dialog.exec_() == QDialog.Accepted:
            self.status_bar.showMessage(f"欢迎 {self.client.username}")
            self.update_storage_info()
        else:
            sys.exit(0)

    def logout(self):
        self.client.clear_auth()
        settings = QSettings("CloudNote", "User")
        settings.clear()
        self.status_bar.showMessage("已退出登录")
        while self.tabs.count() > 0:
            self.close_tab(0)
        self.check_login()

    def new_file(self, file_type):
        if DEBUG:
            debug_log(f"新建文件: {file_type}")
        
        if file_type == 'txt':
            tab = EditorTab(self.tabs, self.tabs.count(), file_type='txt', is_new=True, content="")
            self.tabs.addTab(tab.text_edit, "未命名")
            self.editor_tabs.append(tab)
            self.tabs.setCurrentIndex(self.tabs.count() - 1)
        else:
            # 先创建选项卡，再显示配置对话框
            tab = EditorTab(self.tabs, self.tabs.count(), file_type='bjb', is_new=True, content="")
            self.tabs.addTab(tab.text_edit, "未命名加密笔记")
            self.editor_tabs.append(tab)
            self.tabs.setCurrentIndex(self.tabs.count() - 1)
            
            dialog = NewEncryptedFileDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                config = dialog.get_config()
                tab.encrypt_config = config
                self.save_as_current_tab()
            else:
                self.close_tab(self.tabs.currentIndex())

    def open_local_file_dialog(self):
        """打开本地文件对话框 - 只支持.bjb和.txt"""
        if DEBUG:
            debug_log("打开本地文件对话框")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "打开文件", 
            "", 
            "笔记本文件 (*.bjb *.txt)"
        )
        
        if file_path:
            if DEBUG:
                debug_log(f"用户选择文件: {file_path}")
            self.open_local_file(file_path)
        else:
            if DEBUG:
                debug_log("用户取消选择")

    def open_local_file(self, file_path, cloud_id=None):
        """打开本地文件 - 使用通用解密函数"""
        ext = os.path.splitext(file_path)[1].lower()
        if DEBUG:
            debug_log(f"打开本地文件: {file_path}, 类型: {ext}")

        if ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tab = EditorTab(self.tabs, self.tabs.count(),
                               file_path=file_path, cloud_id=cloud_id,
                               file_type='txt', content=content)
                self.tabs.addTab(tab.text_edit, os.path.basename(file_path))
                self.editor_tabs.append(tab)
                self.tabs.setCurrentIndex(self.tabs.count() - 1)
            except Exception as e:
                debug_error(f"读取文件失败: {e}")
                QMessageBox.critical(self, "错误", f"读取文件失败: {str(e)}")

        elif ext == '.bjb':
            # 使用通用解密函数
            content, success = decrypt_bjb_file(file_path, self)
            if success and content is not None:
                tab = EditorTab(self.tabs, self.tabs.count(),
                               file_path=file_path, cloud_id=cloud_id,
                               file_type='bjb', content=content)
                self.tabs.addTab(tab.text_edit, os.path.basename(file_path))
                self.editor_tabs.append(tab)
                self.tabs.setCurrentIndex(self.tabs.count() - 1)

    def open_cloud_file_dialog(self):
        if not self.client.token:
            QMessageBox.warning(self, "提示", "请先登录")
            self.check_login()
            return
        dialog = CloudFileTreeDialog(self.client, self)
        dialog.exec_()

    def save_current_tab(self):
        idx = self.tabs.currentIndex()
        if idx < 0 or idx >= len(self.editor_tabs):
            return
        tab = self.editor_tabs[idx]
        content = tab.get_content()

        if tab.is_new:
            self.save_as_current_tab()
            return

        if tab.file_path and os.path.exists(tab.file_path):
            try:
                if tab.file_type == 'txt':
                    with open(tab.file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    tab.mark_saved()
                    self.status_bar.showMessage(f"已保存: {os.path.basename(tab.file_path)}", 3000)
                else:
                    if hasattr(tab, 'encrypt_config') and tab.encrypt_config:
                        config = tab.encrypt_config
                        encrypted_data, _, _ = EncryptedNoteHandler.encrypt_content(
                            content, config['algorithm'], config['key_mode'],
                            config.get('custom_password'),
                            config.get('single_private'),
                            config.get('single_public')
                        )
                        with open(tab.file_path, 'wb') as f:
                            f.write(encrypted_data)
                        tab.mark_saved()
                        self.status_bar.showMessage(f"已保存: {os.path.basename(tab.file_path)}", 3000)
                    else:
                        dialog = NewEncryptedFileDialog(self)
                        if dialog.exec_() == QDialog.Accepted:
                            config = dialog.get_config()
                            tab.encrypt_config = config
                            encrypted_data, _, _ = EncryptedNoteHandler.encrypt_content(
                                content, config['algorithm'], config['key_mode'],
                                config.get('custom_password'),
                                config.get('single_private'),
                                config.get('single_public')
                            )
                            with open(tab.file_path, 'wb') as f:
                                f.write(encrypted_data)
                            tab.mark_saved()
                            self.status_bar.showMessage(f"已保存: {os.path.basename(tab.file_path)}", 3000)
                        else:
                            return
            except Exception as e:
                debug_error(f"保存失败: {e}")
                QMessageBox.critical(self, "保存失败", str(e))
        else:
            self.save_as_current_tab()

    def save_as_current_tab(self):
        idx = self.tabs.currentIndex()
        if idx < 0 or idx >= len(self.editor_tabs):
            return
        tab = self.editor_tabs[idx]
        content = tab.get_content()

        if tab.file_type == 'txt':
            file_path, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "文本文件 (*.txt)")
            if not file_path:
                return
            if not file_path.endswith('.txt'):
                file_path += '.txt'
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                tab.file_path = file_path
                tab.is_new = False
                tab.mark_saved()
                self.status_bar.showMessage(f"已保存: {os.path.basename(file_path)}", 3000)
            except Exception as e:
                debug_error(f"保存失败: {e}")
                QMessageBox.critical(self, "保存失败", str(e))
        else:
            if hasattr(tab, 'encrypt_config') and tab.encrypt_config:
                config = tab.encrypt_config
            else:
                dialog = NewEncryptedFileDialog(self)
                if dialog.exec_() != QDialog.Accepted:
                    return
                config = dialog.get_config()
                tab.encrypt_config = config

            save_dialog = SaveEncryptedFileDialog(
                content, config['algorithm'], config['key_mode'],
                config['use_password'], config.get('custom_password'),
                config.get('single_private'), config.get('single_public'),
                self
            )
            if save_dialog.exec_() == QDialog.Accepted:
                tab.file_type = 'bjb'
                tab.encrypt_config = config
                tab.is_new = False
                if save_dialog.selected_file_path:
                    tab.file_path = save_dialog.selected_file_path
                tab.mark_saved()

    def encrypt_current_file(self):
        """加密当前选项卡中的文件"""
        if DEBUG:
            debug_log("加密当前文件功能被调用")
        idx = self.tabs.currentIndex()
        
        if idx < 0 or idx >= len(self.editor_tabs):
            QMessageBox.warning(self, "提示", "没有打开的文件")
            return
        
        tab = self.editor_tabs[idx]
        content = tab.get_content()
        
        if not content.strip():
            ret = QMessageBox.question(self, "确认", "文件内容为空，是否继续加密？",
                                       QMessageBox.Yes | QMessageBox.No)
            if ret != QMessageBox.Yes:
                return
        
        dialog = EncryptCurrentFileDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return
        
        config = dialog.get_config()
        
        default_name = "encrypted_note.bjb"
        if tab.file_path:
            base_name = os.path.splitext(os.path.basename(tab.file_path))[0]
            default_name = f"{base_name}_encrypted.bjb"
        
        file_path, _ = QFileDialog.getSaveFileName(self, "保存加密文件", default_name, "加密笔记 (*.bjb)")
        if not file_path:
            return
        
        if not file_path.endswith('.bjb'):
            file_path += '.bjb'
        
        try:
            encrypted_data, priv, pub = EncryptedNoteHandler.encrypt_content(
                content, config['algorithm'], config['key_mode'],
                config['custom_password'],
                config.get('single_private'),
                config.get('single_public')
            )
            
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            if config['key_mode'] == 'single' and priv:
                key_path = file_path + '.key'
                with open(key_path, 'wb') as f:
                    f.write(priv)
                QMessageBox.information(self, "加密成功", 
                    f"文件已加密保存为:\n{file_path}\n\n"
                    f"密钥文件已保存为:\n{key_path}\n\n"
                    f"请妥善保管密钥文件！")
            else:
                QMessageBox.information(self, "加密成功", 
                    f"文件已加密保存为:\n{file_path}\n\n"
                    f"使用全局密钥加密，无需额外保存密钥文件。")
            
            ret = QMessageBox.question(self, "打开文件", 
                                       "是否在新选项卡中打开加密后的文件？",
                                       QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.open_local_file(file_path)
                
        except Exception as e:
            debug_error(f"加密失败: {e}")
            QMessageBox.critical(self, "加密失败", str(e))

    def convert_txt_to_bjb(self):
        """将当前文本文件转换为加密笔记"""
        if DEBUG:
            debug_log("TXT转BJB功能被调用")
        idx = self.tabs.currentIndex()
        
        if idx < 0 or idx >= len(self.editor_tabs):
            QMessageBox.warning(self, "提示", "没有打开的文件")
            return
        
        tab = self.editor_tabs[idx]
        
        if tab.file_type == 'bjb':
            QMessageBox.information(self, "提示", "当前文件已经是加密笔记格式")
            return
        
        content = tab.get_content()
        
        dialog = EncryptCurrentFileDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return
        
        config = dialog.get_config()
        
        default_name = os.path.splitext(os.path.basename(tab.file_path))[0] + ".bjb" if tab.file_path else "converted.bjb"
        file_path, _ = QFileDialog.getSaveFileName(self, "保存为加密笔记", default_name, "加密笔记 (*.bjb)")
        if not file_path:
            return
        
        if not file_path.endswith('.bjb'):
            file_path += '.bjb'
        
        try:
            encrypted_data, priv, pub = EncryptedNoteHandler.encrypt_content(
                content, config['algorithm'], config['key_mode'],
                config['custom_password'],
                config.get('single_private'),
                config.get('single_public')
            )
            
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            if config['key_mode'] == 'single' and priv:
                key_path = file_path + '.key'
                with open(key_path, 'wb') as f:
                    f.write(priv)
                QMessageBox.information(self, "转换成功", 
                    f"文件已转换为加密笔记:\n{file_path}\n\n"
                    f"密钥文件已保存为:\n{key_path}\n\n"
                    f"请妥善保管密钥文件！")
            else:
                QMessageBox.information(self, "转换成功", 
                    f"文件已转换为加密笔记:\n{file_path}\n\n"
                    f"使用全局密钥加密，无需额外保存密钥文件。")
            
            ret = QMessageBox.question(self, "打开文件", 
                                       "是否在新选项卡中打开加密后的文件？",
                                       QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.open_local_file(file_path)
                
        except Exception as e:
            debug_error(f"转换失败: {e}")
            QMessageBox.critical(self, "转换失败", str(e))

    def upload_current_tab(self):
        if not self.client.token:
            QMessageBox.warning(self, "提示", "请先登录")
            self.check_login()
            return

        idx = self.tabs.currentIndex()
        if idx < 0 or idx >= len(self.editor_tabs):
            return
        tab = self.editor_tabs[idx]

        if tab.is_new or not tab.file_path:
            QMessageBox.warning(self, "提示", "请先保存文件到本地")
            return

        if tab.modified:
            ret = QMessageBox.question(self, "提示", "文件未保存，是否先保存？", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.save_current_tab()

        folder, ok = QInputDialog.getText(self, "上传到云端", "请输入云端目录路径 (默认为 /):", text="/")
        if not ok:
            return
        if not folder:
            folder = "/"

        res = self.client.upload_file(tab.file_path, folder)
        if res:
            QMessageBox.information(self, "成功", "文件已上传到云端")
        else:
            QMessageBox.warning(self, "错误", "上传失败")

    def show_cloud_manager(self):
        if not self.client.token:
            QMessageBox.warning(self, "提示", "请先登录")
            self.check_login()
            return
        dialog = CloudFileTreeDialog(self.client, self)
        dialog.exec_()

    def on_tab_changed(self, index):
        """当前选项卡改变时的回调"""
        if index >= 0 and index < len(self.editor_tabs):
            self.current_editor = self.editor_tabs[index]
        else:
            self.current_editor = None

    def close_tab(self, index):
        """关闭指定索引的选项卡"""
        if index < 0 or index >= len(self.editor_tabs):
            return
        
        tab = self.editor_tabs[index]
        if tab.modified:
            ret = QMessageBox.question(self, "提示", "文件已修改，是否保存？", 
                                       QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if ret == QMessageBox.Yes:
                self.save_current_tab()
            elif ret == QMessageBox.Cancel:
                return
        
        self.tabs.removeTab(index)
        self.editor_tabs.pop(index)
        
        for i, t in enumerate(self.editor_tabs):
            t.index = i
        
        current_idx = self.tabs.currentIndex()
        if current_idx >= 0 and current_idx < len(self.editor_tabs):
            self.current_editor = self.editor_tabs[current_idx]
        else:
            self.current_editor = None

    def about(self):
        QMessageBox.about(self, "关于云笔记", 
            "云笔记 v2.0\n\n"
            "功能特性：\n"
            "• 支持 .txt 文本文件\n"
            "• 支持 .bjb 加密笔记\n"
            "• 云端同步功能\n"
            "• 多选项卡编辑\n"
            "• 加密当前文件\n"
            "• TXT转BJB加密\n\n"
            "加密模式：\n"
            "1. RSA-4096 + AES-256-GCM\n"
            "2. X25519 + AES-256-GCM\n\n"
            "密钥方式：\n"
            "• 默认加密：全局密钥对\n"
            "• 安全加密：单独生成密钥对\n\n"
            "快捷键：\n"
            "• Ctrl+N: 新建文本\n"
            "• Ctrl+Shift+N: 新建加密笔记\n"
            "• Ctrl+E: 加密当前文件\n"
            "• Ctrl+Shift+S: 另存为加密笔记\n"
            "• Ctrl+S: 保存\n"
            "• Ctrl+O: 打开文件\n\n"
            f"密钥存储位置：\n"
            f"• 用户目录: {USER_KEY_DIR}\n"
            f"• 程序目录: {APP_KEY_DIR}")


def main():
    if DEBUG:
        debug_log("=" * 50)
        debug_log("云笔记应用程序启动")
        debug_log("=" * 50)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    ensure_global_keys()

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
