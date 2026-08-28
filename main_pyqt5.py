#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
云笔记应用程序 - 安全加密笔记系统
====================================

作者: dvs (dvsxt)
版本: 5.0
日期: 2026-06-10

版本 5.0 核心改进：
============================================================================
1. 现代化GUI设计
   - 全新的暗色/亮色主题支持
   - 圆角卡片设计
   - 自适应布局，支持窗口缩放
   - 流畅的动画效果

2. 美观的界面元素
   - 渐变按钮
   - 半透明效果
   - 阴影和光效
   - 平滑过渡动画

3. 完全自适应尺寸
   - 移除所有固定尺寸
   - 使用布局管理器自动调整
   - 支持不同分辨率屏幕

4. 加密配置自动提取与复用（解决保存时重复弹窗问题）
   - 打开加密文件时，根据用户输入的密码自动检测强度模式
   - 密码长度≥16且包含大小写字母+数字+特殊字符 → 高强度模式
   - 否则自动判定为低强度模式
   - 保存时直接使用检测到的配置，无需重新配置或重新输入密码

5. 智能密码强度检测（仅提示，不阻止）
   - 实时显示密码强度等级（极弱/弱/中等/强/极强）
   - 使用弱密码时弹出警告，但用户可选择继续使用
   - 尊重用户选择，不强求使用高强度密码

6. 云端 API 支持
   - 默认使用官方测试服务器 https://noteapi.dvssvc.site/api
   - 可自行部署服务端，源码在 https://gitcode.com/dvsxt/cloudnote

7. 双路径密钥存储
   - 密钥优先存储在用户目录 ~/.cloudnote/keys/
   - 同时备份到程序目录 .keys/ 防止丢失

依赖安装：
   pip install PyQt5 requests cryptography

快捷键：
   Ctrl+N           新建文本文件
   Ctrl+Shift+N     新建加密笔记
   Ctrl+O           打开文件
   Ctrl+Shift+O     从云端打开
   Ctrl+S           保存
   Ctrl+Shift+S     另存为加密笔记
   Ctrl+E           加密当前文件
"""

import sys
import os
import json
import tempfile
import traceback
from datetime import datetime

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import requests

import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

from DVT_RFSA import *

# ============================================================================
# 调试配置
# ============================================================================

DEBUG = False

def debug_log(msg: str, level: str = "INFO") -> None:
    if DEBUG:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{level}] {msg}")
        sys.stdout.flush()

def debug_error(msg: str) -> None:
    if DEBUG:
        debug_log(msg, "ERROR")
        traceback.print_exc()

# ============================================================================
# 全局样式表 - 现代化设计
# ============================================================================

DARK_STYLE = """
/* 全局样式 */
QWidget {
    background-color: #1e1e2f;
    color: #cdd6f4;
    font-family: 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
    font-size: 13px;
}

/* 主窗口 */
QMainWindow {
    background-color: #1e1e2f;
}

/* 菜单栏 */
QMenuBar {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    padding: 4px 0px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 8px 12px;
    border-radius: 6px;
    margin: 0px 2px;
}

QMenuBar::item:selected {
    background-color: #313244;
}

/* 菜单 */
QMenu {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 8px;
    padding: 8px;
}

QMenu::item {
    padding: 8px 32px 8px 24px;
    border-radius: 6px;
    margin: 2px;
}

QMenu::item:selected {
    background-color: #89b4fa;
    color: #1e1e2f;
}

QMenu::separator {
    height: 1px;
    background-color: #313244;
    margin: 4px 8px;
}

/* 标签页 */
QTabWidget::pane {
    border: none;
    background-color: #1e1e2f;
    border-radius: 12px;
}

QTabWidget::tab-bar {
    alignment: left;
}

QTabBar::tab {
    background-color: #181825;
    border: none;
    border-radius: 8px 8px 0px 0px;
    padding: 10px 20px;
    margin-right: 4px;
    color: #a6adc8;
}

QTabBar::tab:selected {
    background-color: #313244;
    color: #89b4fa;
}

QTabBar::tab:hover:!selected {
    background-color: #282838;
}

QTabBar::close-button {
    image: url(none);
    subcontrol-position: right;
    margin-left: 8px;
}

QTabBar::close-button:hover {
    background-color: #f38ba8;
    border-radius: 4px;
}

/* 文本编辑区 */
QTextEdit {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 12px;
    padding: 12px;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2f;
}

QTextEdit:focus {
    border: 1px solid #89b4fa;
}

/* 按钮 */
QPushButton {
    background-color: #313244;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #45475a;
}

QPushButton:pressed {
    background-color: #89b4fa;
    color: #1e1e2f;
}

QPushButton:disabled {
    background-color: #282838;
    color: #6c7086;
}

/* 主要按钮 */
QPushButton[primary="true"] {
    background-color: #89b4fa;
    color: #1e1e2f;
}

QPushButton[primary="true"]:hover {
    background-color: #b4befe;
}

/* 危险按钮 */
QPushButton[danger="true"] {
    background-color: #f38ba8;
    color: #1e1e2f;
}

QPushButton[danger="true"]:hover {
    background-color: #eba0ac;
}

/* 输入框 */
QLineEdit {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 8px;
    padding: 10px 12px;
}

QLineEdit:focus {
    border: 1px solid #89b4fa;
}

/* 组合框 */
QComboBox {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 8px;
    padding: 8px 12px;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #cdd6f4;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 8px;
    selection-background-color: #313244;
}

/* 复选框 */
QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    background-color: #181825;
    border: 1px solid #313244;
}

QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border: 1px solid #89b4fa;
}

/* 单选按钮 */
QRadioButton {
    spacing: 8px;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    background-color: #181825;
    border: 1px solid #313244;
}

QRadioButton::indicator:checked {
    background-color: #89b4fa;
    border: 1px solid #89b4fa;
}

/* 分组框 */
QGroupBox {
    border: 1px solid #313244;
    border-radius: 12px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: 500;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
}

/* 滚动条 */
QScrollBar:vertical {
    background-color: #181825;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #6c7086;
}

QScrollBar:horizontal {
    background-color: #181825;
    height: 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #45475a;
    border-radius: 5px;
    min-width: 30px;
}

/* 状态栏 */
QStatusBar {
    background-color: #181825;
    border-top: 1px solid #313244;
    padding: 4px 8px;
}

/* 树形控件 */
QTreeWidget {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 12px;
    outline: none;
}

QTreeWidget::item {
    padding: 8px;
    border-radius: 6px;
}

QTreeWidget::item:hover {
    background-color: #282838;
}

QTreeWidget::item:selected {
    background-color: #313244;
}

/* 工具栏 */
QToolBar {
    background-color: #181825;
    border: none;
    border-radius: 12px;
    spacing: 4px;
    padding: 4px;
}

QToolBar QToolButton {
    background-color: transparent;
    border-radius: 6px;
    padding: 6px 12px;
}

QToolBar QToolButton:hover {
    background-color: #313244;
}

/* 标签 */
QLabel {
    color: #cdd6f4;
}

/* 进度条 */
QProgressBar {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #89b4fa;
    border-radius: 5px;
}

/* 消息框 */
QMessageBox {
    background-color: #1e1e2f;
}

QMessageBox QPushButton {
    min-width: 80px;
}

/* 输入对话框 */
QInputDialog {
    background-color: #1e1e2f;
}
"""

LIGHT_STYLE = """
/* 全局样式 - 亮色主题 */
QWidget {
    background-color: #ffffff;
    color: #1e1e2f;
    font-family: 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #f5f7fa;
}

QMenuBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e1e4e8;
    padding: 4px 0px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 8px 12px;
    border-radius: 6px;
    margin: 0px 2px;
}

QMenuBar::item:selected {
    background-color: #e1e4e8;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #e1e4e8;
    border-radius: 8px;
    padding: 8px;
}

QMenu::item {
    padding: 8px 32px 8px 24px;
    border-radius: 6px;
    margin: 2px;
}

QMenu::item:selected {
    background-color: #89b4fa;
    color: #1e1e2f;
}

QTabWidget::pane {
    border: none;
    background-color: #f5f7fa;
    border-radius: 12px;
}

QTabBar::tab {
    background-color: #e1e4e8;
    border: none;
    border-radius: 8px 8px 0px 0px;
    padding: 10px 20px;
    margin-right: 4px;
    color: #4a5568;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #89b4fa;
}

QTabBar::tab:hover:!selected {
    background-color: #cbd5e0;
}

QTextEdit {
    background-color: #ffffff;
    border: 1px solid #e1e4e8;
    border-radius: 12px;
    padding: 12px;
    selection-background-color: #89b4fa;
    selection-color: #ffffff;
}

QTextEdit:focus {
    border: 1px solid #89b4fa;
}

QPushButton {
    background-color: #e1e4e8;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #cbd5e0;
}

QPushButton:pressed {
    background-color: #89b4fa;
    color: #ffffff;
}

QPushButton[primary="true"] {
    background-color: #89b4fa;
    color: #ffffff;
}

QPushButton[primary="true"]:hover {
    background-color: #b4befe;
}

QPushButton[danger="true"] {
    background-color: #f38ba8;
    color: #ffffff;
}

QLineEdit {
    background-color: #ffffff;
    border: 1px solid #e1e4e8;
    border-radius: 8px;
    padding: 10px 12px;
}

QLineEdit:focus {
    border: 1px solid #89b4fa;
}

QComboBox {
    background-color: #ffffff;
    border: 1px solid #e1e4e8;
    border-radius: 8px;
    padding: 8px 12px;
}

QGroupBox {
    border: 1px solid #e1e4e8;
    border-radius: 12px;
    margin-top: 12px;
    padding-top: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    background-color: #ffffff;
    border: 1px solid #e1e4e8;
}

QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border: 1px solid #89b4fa;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    background-color: #ffffff;
    border: 1px solid #e1e4e8;
}

QRadioButton::indicator:checked {
    background-color: #89b4fa;
    border: 1px solid #89b4fa;
}

QStatusBar {
    background-color: #ffffff;
    border-top: 1px solid #e1e4e8;
}

QTreeWidget {
    background-color: #ffffff;
    border: 1px solid #e1e4e8;
    border-radius: 12px;
}

QTreeWidget::item:hover {
    background-color: #f0f2f5;
}

QTreeWidget::item:selected {
    background-color: #e1e4e8;
}

QToolBar {
    background-color: #ffffff;
    border: 1px solid #e1e4e8;
    border-radius: 12px;
}

QScrollBar:vertical {
    background-color: #f0f2f5;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #cbd5e0;
    border-radius: 5px;
}
"""

# ============================================================================
# 智能密码强度检测（仅提示，不阻止）
# ============================================================================

def check_password_strength(password: str) -> dict:
    if not password:
        return {
            'level': '未输入',
            'color': '#999999',
            'message': '请输入密码',
            'score': 0,
            'is_strong': False
        }
    
    length = len(password)
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    
    is_strong = (
        length >= 16 and
        has_upper and has_lower and
        has_digit and has_special
    )
    
    score = 0
    if length >= 6:
        score += 1
    if length >= 10:
        score += 1
    if length >= 14:
        score += 1
    if has_upper and has_lower:
        score += 1
    if has_digit:
        score += 1
    if has_special:
        score += 1
    
    common = ['123456', 'password', '12345678', 'qwerty', '12345', '123456789',
              '111111', '123123', 'abc123', 'password1', '111', '222', '333']
    if password.lower() in common:
        return {
            'level': '极弱',
            'color': '#d73a49',
            'message': '这是常见弱密码，极易被破解！',
            'score': 0,
            'is_strong': False
        }
    
    if score <= 2:
        return {
            'level': '极弱',
            'color': '#d73a49',
            'message': '密码强度极弱，容易被破解',
            'score': score,
            'is_strong': False
        }
    elif score <= 3:
        return {
            'level': '弱',
            'color': '#e36209',
            'message': '密码强度较弱，建议加强',
            'score': score,
            'is_strong': False
        }
    elif score <= 4:
        return {
            'level': '中等',
            'color': '#fb8532',
            'message': '密码强度中等，可继续使用',
            'score': score,
            'is_strong': False
        }
    elif score <= 5:
        return {
            'level': '强',
            'color': '#28a745',
            'message': '密码强度良好',
            'score': score,
            'is_strong': False
        }
    else:
        return {
            'level': '极强',
            'color': '#28a745',
            'message': '密码强度极高，非常安全',
            'score': score,
            'is_strong': True
        }

# ============================================================================
# 应用程序配置
# ============================================================================

API_BASE_URL = "https://noteapi.dvssvc.site/api"
APP_NAME = "CloudNote"

def get_app_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

APP_DIR = get_app_dir()
USER_KEY_DIR = os.path.expanduser(f"~/.{APP_NAME.lower()}/keys")
APP_KEY_DIR = os.path.join(APP_DIR, ".keys")

KEY_FILES = {
    'rsa_private': "global_rsa_private.pem",
    'rsa_public': "global_rsa_public.pem",
    'x25519_private': "global_x25519_private.bin",
    'x25519_public': "global_x25519_public.bin"
}

# ============================================================================
# 密钥路径管理
# ============================================================================

def get_key_path(key_name: str, prefer_user: bool = True) -> tuple:
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

def ensure_directory(dir_path: str) -> bool:
    try:
        os.makedirs(dir_path, exist_ok=True)
        if DEBUG:
            debug_log(f"目录已确保: {dir_path}")
        return True
    except Exception as e:
        debug_error(f"创建目录失败 {dir_path}: {e}")
        return False

# ============================================================================
# 全局密钥管理
# ============================================================================

def ensure_global_keys() -> None:
    if DEBUG:
        debug_log("开始检查/生成全局密钥...")
    
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
            debug_log(f"{key_type.upper()} - 用户目录: {user_exists}, 程序目录: {app_exists}")
        
        if not user_exists:
            if DEBUG:
                debug_log(f"生成{key_type.upper()}密钥对...")
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
                        debug_log(f"备份失败: {e}")
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
            except Exception as e:
                if DEBUG:
                    debug_log(f"备份失败: {e}")
    
    if DEBUG:
        debug_log("全局密钥检查完成")

def get_global_rsa_private() -> bytes:
    key_path, _ = get_key_path(KEY_FILES['rsa_private'])
    if not os.path.exists(key_path):
        ensure_global_keys()
        key_path, _ = get_key_path(KEY_FILES['rsa_private'])
    with open(key_path, 'rb') as f:
        return f.read()

def get_global_rsa_public() -> bytes:
    key_path, _ = get_key_path(KEY_FILES['rsa_public'])
    if not os.path.exists(key_path):
        ensure_global_keys()
        key_path, _ = get_key_path(KEY_FILES['rsa_public'])
    with open(key_path, 'rb') as f:
        return f.read()

def get_global_x25519_private() -> bytes:
    key_path, _ = get_key_path(KEY_FILES['x25519_private'])
    if not os.path.exists(key_path):
        ensure_global_keys()
        key_path, _ = get_key_path(KEY_FILES['x25519_private'])
    with open(key_path, 'rb') as f:
        return f.read()

def get_global_x25519_public() -> bytes:
    key_path, _ = get_key_path(KEY_FILES['x25519_public'])
    if not os.path.exists(key_path):
        ensure_global_keys()
        key_path, _ = get_key_path(KEY_FILES['x25519_public'])
    with open(key_path, 'rb') as f:
        return f.read()

# ============================================================================
# 加密笔记处理器
# ============================================================================

class EncryptedNoteHandler:
    
    @staticmethod
    def get_file_metadata(file_path: str) -> dict:
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            clean_data = remove_security_info(data)
            json_str = clean_data.decode('utf-8')
            info = json.loads(json_str)
            return {
                'has_password': info.get('has_password', False),
                'mode': info.get('mode', 'aes_rsa'),
                'single_key': info.get('single_key', False),
                'algorithm': info.get('algorithm', 'unknown'),
                'timestamp': info.get('timestamp', 'unknown')
            }
        except Exception as e:
            debug_error(f"获取文件元数据失败: {e}")
            return None
    
    @staticmethod
    def extract_encrypt_config(file_path: str, password: str = None, single_private: bytes = None) -> dict:
        """
        提取加密配置，根据用户输入的密码自动判断强度模式
        密码长度≥16且包含大小写字母+数字+特殊字符 → 高强度模式，否则低强度模式
        """
        try:
            metadata = EncryptedNoteHandler.get_file_metadata(file_path)
            if metadata is None:
                return None
            
            mode = metadata['mode']
            has_password = metadata['has_password']
            single_key = metadata['single_key']
            
            if 'x25519' in mode:
                algorithm = 'x25519'
            else:
                algorithm = 'rsa'
            
            key_mode = 'single' if single_key else 'global'
            
            # 根据密码自动判断强度模式
            strict_password = True
            if password:
                is_strong = (
                    len(password) >= 16 and
                    any(c.isupper() for c in password) and
                    any(c.islower() for c in password) and
                    any(c.isdigit() for c in password) and
                    any(not c.isalnum() for c in password)
                )
                strict_password = is_strong
                if DEBUG:
                    debug_log(f"密码强度检测: {'高强度' if is_strong else '低强度'} (长度={len(password)})")
            
            single_public = None
            if single_key and single_private is not None:
                pub_key_path = file_path + '.pub'
                if os.path.exists(pub_key_path):
                    try:
                        with open(pub_key_path, 'rb') as f:
                            single_public = f.read()
                    except Exception:
                        pass
            
            return {
                'algorithm': algorithm,
                'key_mode': key_mode,
                'use_password': has_password,
                'custom_password': password,
                'single_private': single_private,
                'single_public': single_public,
                'strict_password': strict_password
            }
        except Exception as e:
            debug_error(f"提取加密配置失败: {e}")
            return None
    
    @staticmethod
    def encrypt_content(content: str, algorithm: str, key_mode: str,
                        password: str = None, single_private: bytes = None,
                        single_public: bytes = None, strict_password: bool = True) -> tuple:
        if DEBUG:
            debug_log(f"开始加密 - 算法: {algorithm}, 密钥模式: {key_mode}, "
                     f"密码保护: {password is not None}, 强度模式: {'高强度' if strict_password else '低强度'}")
        
        data = content.encode('utf-8')
        private_key = None
        public_key = None
        
        try:
            if algorithm == 'rsa':
                if key_mode == 'global':
                    pub_pem = get_global_rsa_public()
                    if password:
                        encrypted = encrypt_text_aes_rsa_with_password(
                            data, pub_pem, password, add_header=True,
                            strict_password=strict_password
                        )
                    else:
                        encrypted = encrypt_text_aes_rsa(
                            data, pub_pem, add_header=True,
                            strict_password=strict_password
                        )
                else:
                    if single_private is None or single_public is None:
                        private_key, public_key = generate_rsa_key(4096)
                    else:
                        private_key = single_private
                        public_key = single_public
                    
                    if password:
                        encrypted = encrypt_text_aes_rsa_with_password(
                            data, public_key, password, add_header=True,
                            strict_password=strict_password
                        )
                    else:
                        encrypted = encrypt_text_aes_rsa(
                            data, public_key, add_header=True,
                            strict_password=strict_password
                        )
                    
                    json_str = remove_security_info(encrypted).decode('utf-8')
                    info = json.loads(json_str)
                    info['single_key'] = True
                    encrypted = add_security_info(
                        json.dumps(info).encode('utf-8'),
                        'aes_rsa', bool(password)
                    )
                    return encrypted, private_key, public_key
            
            else:
                if key_mode == 'global':
                    pub_raw = get_global_x25519_public()
                    if password:
                        encrypted = encrypt_text_aes_x25519(
                            data, pub_raw, password, add_header=True,
                            strict_password=strict_password
                        )
                    else:
                        encrypted = encrypt_text_aes_x25519(
                            data, pub_raw, add_header=True,
                            strict_password=strict_password
                        )
                else:
                    if single_private is None or single_public is None:
                        private_key, public_key = generate_x25519_keys()
                    else:
                        private_key = single_private
                        public_key = single_public
                    
                    if password:
                        encrypted = encrypt_text_aes_x25519(
                            data, public_key, password, add_header=True,
                            strict_password=strict_password
                        )
                    else:
                        encrypted = encrypt_text_aes_x25519(
                            data, public_key, add_header=True,
                            strict_password=strict_password
                        )
                    
                    json_str = remove_security_info(encrypted).decode('utf-8')
                    info = json.loads(json_str)
                    info['single_key'] = True
                    encrypted = add_security_info(
                        json.dumps(info).encode('utf-8'),
                        'aes_x25519', bool(password)
                    )
                    return encrypted, private_key, public_key
            
            return encrypted, private_key, public_key
            
        except Exception as e:
            debug_error(f"加密过程异常: {e}")
            raise Exception(f"加密失败: {str(e)}")

    @staticmethod
    def decrypt_file(file_path: str, password: str = None,
                     single_private: bytes = None) -> bytes:
        if DEBUG:
            debug_log(f"开始解密文件: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            clean_data = remove_security_info(data)
            json_str = clean_data.decode('utf-8')
            info = json.loads(json_str)
            mode = info.get('mode', 'aes_rsa')
            has_password = info.get('has_password', False)
            single_key = info.get('single_key', False)

            if mode in ['aes_rsa', 'aes_rsa_password_protected']:
                if single_key:
                    if single_private is None:
                        raise ValueError("单独密钥模式需要提供私钥文件")
                    priv = single_private
                else:
                    priv = get_global_rsa_private()
                    
                if has_password:
                    if password is None:
                        raise ValueError("此文件受密码保护，需要输入密码")
                    decrypted = decrypt_text_aes_rsa_with_password(
                        clean_data, priv, password, has_header=False
                    )
                else:
                    decrypted = decrypt_text_aes_rsa(
                        clean_data, priv, has_header=False
                    )
                    
            elif mode in ['aes_x25519', 'aes_x25519_password_protected']:
                if single_key:
                    if single_private is None:
                        raise ValueError("单独密钥模式需要提供私钥文件")
                    priv = single_private
                else:
                    priv = get_global_x25519_private()
                    
                if has_password:
                    if password is None:
                        raise ValueError("此文件受密码保护，需要输入密码")
                    decrypted = decrypt_text_aes_x25519(
                        clean_data, priv, password, has_header=False
                    )
                else:
                    decrypted = decrypt_text_aes_x25519(
                        clean_data, priv, has_header=False
                    )
            else:
                raise ValueError(f"未知加密模式: {mode}")
            
            if isinstance(decrypted, str):
                decrypted = decrypted.encode('utf-8')
            
            return decrypted
            
        except Exception as e:
            debug_error(f"解密过程异常: {e}")
            raise

# ============================================================================
# 通用解密函数
# ============================================================================

def decrypt_bjb_file(file_path: str, parent_window: QWidget,
                     is_cloud_file: bool = False,
                     cloud_filename: str = None) -> tuple:
    if DEBUG:
        debug_log(f"通用解密函数: {file_path}")
    
    display_name = cloud_filename if cloud_filename else os.path.basename(file_path)
    
    try:
        metadata = EncryptedNoteHandler.get_file_metadata(file_path)
        if metadata is None:
            QMessageBox.critical(parent_window, "文件错误", "无法读取文件元数据")
            return None, False, None
        
        has_password = metadata['has_password']
        single_key = metadata['single_key']
        mode = metadata['mode']
        
        single_private = None
        
        if single_key:
            key_file_path = file_path + '.key'
            if os.path.exists(key_file_path):
                try:
                    with open(key_file_path, 'rb') as f:
                        single_private = f.read()
                except Exception as e:
                    debug_error(f"读取密钥文件失败: {e}")
                    QMessageBox.critical(parent_window, "读取失败", f"无法读取密钥文件: {str(e)}")
                    return None, False, None
            else:
                msg = f"文件「{display_name}」使用单独密钥加密。\n\n请选择对应的私钥文件(.key)"
                if is_cloud_file:
                    msg = f"云端文件「{display_name}」使用单独密钥加密。\n\n服务器不存储您的私钥，请选择本地保存的.key文件。"
                
                key_file_path, ok = QFileDialog.getOpenFileName(
                    parent_window, "选择密钥文件 - " + display_name, "",
                    "密钥文件 (*.key);;所有文件 (*.*)"
                )
                
                if not ok or not key_file_path:
                    QMessageBox.warning(parent_window, "密钥缺失", "缺少私钥文件，无法解密")
                    return None, False, None
                
                try:
                    with open(key_file_path, 'rb') as f:
                        single_private = f.read()
                except Exception as e:
                    debug_error(f"读取密钥文件失败: {e}")
                    QMessageBox.critical(parent_window, "读取失败", f"无法读取密钥文件: {str(e)}")
                    return None, False, None
        
        entered_password = None
        
        if has_password:
            max_attempts = 3
            attempts = 0
            success = False
            
            while attempts < max_attempts and not success:
                pwd, ok = QInputDialog.getText(
                    parent_window, "输入密码 - " + display_name,
                    f"文件「{display_name}」受密码保护\n请输入密码 (尝试 {attempts + 1}/{max_attempts}):",
                    QLineEdit.Password
                )
                
                if not ok:
                    return None, False, None
                
                if pwd:
                    try:
                        decrypted = EncryptedNoteHandler.decrypt_file(
                            file_path, password=pwd, single_private=single_private
                        )
                        if isinstance(decrypted, bytes):
                            content = decrypted.decode('utf-8')
                        else:
                            content = str(decrypted)
                        entered_password = pwd
                        success = True
                    except Exception as e:
                        attempts += 1
                        if attempts < max_attempts:
                            QMessageBox.warning(parent_window, "密码错误",
                                f"密码错误，还剩 {max_attempts - attempts} 次尝试")
                        else:
                            QMessageBox.warning(parent_window, "解密失败", "多次密码错误，无法解密")
                            return None, False, None
                else:
                    attempts += 1
                    QMessageBox.warning(parent_window, "密码为空", "密码不能为空")
            
            if not success:
                return None, False, None
        else:
            try:
                decrypted = EncryptedNoteHandler.decrypt_file(
                    file_path, password=None, single_private=single_private
                )
                if isinstance(decrypted, bytes):
                    content = decrypted.decode('utf-8')
                else:
                    content = str(decrypted)
            except Exception as e:
                debug_error(f"解密失败: {e}")
                QMessageBox.critical(parent_window, "解密失败", str(e))
                return None, False, None
        
        encrypt_config = EncryptedNoteHandler.extract_encrypt_config(
            file_path, password=entered_password, single_private=single_private
        )
        
        return content, True, encrypt_config
        
    except Exception as e:
        debug_error(f"解密异常: {e}")
        QMessageBox.critical(parent_window, "解密失败", str(e))
        return None, False, None

# ============================================================================
# 云端 API 客户端
# ============================================================================

class CloudClient:
    
    def __init__(self):
        self.token = None
        self.user_id = None
        self.username = None

    def set_auth(self, token: str, user_id: int, username: str) -> None:
        self.token = token
        self.user_id = user_id
        self.username = username

    def clear_auth(self) -> None:
        self.token = None
        self.user_id = None
        self.username = None

    def _headers(self) -> dict:
        if self.token:
            return {'x-access-token': self.token}
        return {}

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
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
            QMessageBox.critical(None, "网络错误", "无法连接到服务器")
            return None
        except Exception as e:
            QMessageBox.critical(None, "网络错误", f"请求失败: {str(e)}")
            return None

    def register(self, username: str, email: str, password: str) -> dict:
        resp = self._request('POST', '/register',
                            json={'username': username, 'email': email, 'password': password})
        if resp and resp.status_code == 201:
            return resp.json()
        return None

    def login(self, email: str, password: str) -> dict:
        resp = self._request('POST', '/login',
                            json={'email': email, 'password': password})
        if resp and resp.status_code == 200:
            data = resp.json()
            self.set_auth(data['token'], data['user_id'], data['username'])
            return data
        return None

    def get_filetree(self, folder: str = '/') -> dict:
        resp = self._request('GET', '/filetree', params={'folder': folder})
        if resp and resp.status_code == 200:
            return resp.json()
        return None

    def create_folder(self, name: str, parent: str = '/') -> dict:
        resp = self._request('POST', '/create_folder',
                            json={'name': name, 'parent': parent})
        if resp and resp.status_code == 201:
            return resp.json()
        return None

    def upload_file(self, file_path: str, parent_folder: str = '/') -> dict:
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

    def download_file(self, file_id: int, target_path: str) -> bool:
        resp = self._request('GET', f'/download/{file_id}')
        if resp and resp.status_code == 200:
            with open(target_path, 'wb') as f:
                f.write(resp.content)
            return True
        return False

    def delete_item(self, item_id: int) -> bool:
        resp = self._request('DELETE', f'/delete/{item_id}')
        if resp:
            return resp.status_code == 200
        return False

    def rename_item(self, item_id: int, new_name: str) -> bool:
        resp = self._request('PUT', f'/rename/{item_id}',
                            json={'new_name': new_name})
        if resp:
            return resp.status_code == 200
        return False

    def move_item(self, item_id: int, target_folder: str) -> bool:
        resp = self._request('POST', '/move',
                            json={'item_id': item_id, 'target_folder': target_folder})
        if resp:
            return resp.status_code == 200
        return False

    def search_files(self, keyword: str) -> dict:
        resp = self._request('GET', '/search', params={'q': keyword})
        if resp and resp.status_code == 200:
            return resp.json()
        return None

    def get_storage_info(self) -> dict:
        resp = self._request('GET', '/storage_info')
        if resp and resp.status_code == 200:
            return resp.json()
        return None

    def get_user_info(self) -> dict:
        resp = self._request('GET', '/user_info')
        if resp and resp.status_code == 200:
            return resp.json()
        return None

# ============================================================================
# 现代化登录对话框
# ============================================================================

class LoginDialog(QDialog):
    
    def __init__(self, client: CloudClient, parent: QWidget = None):
        super().__init__(parent)
        self.client = client
        self.setWindowTitle("云笔记 - 登录")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 卡片容器
        card = QWidget()
        card.setObjectName("card")
        card.setStyleSheet("""
            #card {
                background-color: #1e1e2f;
                border-radius: 24px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Logo 和标题
        title_layout = QVBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)
        
        logo = QLabel("☁️")
        logo.setStyleSheet("font-size: 48px;")
        logo.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(logo)
        
        title = QLabel("云笔记")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #89b4fa;")
        title.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title)
        
        subtitle = QLabel("安全加密笔记系统")
        subtitle.setStyleSheet("font-size: 14px; color: #6c7086;")
        subtitle.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(subtitle)
        
        layout.addLayout(title_layout)

        # 输入框
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("电子邮箱")
        self.email_input.setMinimumHeight(45)
        layout.addWidget(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(45)
        layout.addWidget(self.password_input)

        # 记住我
        self.remember_check = QCheckBox("记住我")
        layout.addWidget(self.remember_check)

        # 登录按钮
        self.login_btn = QPushButton("登 录")
        self.login_btn.setProperty("primary", True)
        self.login_btn.setMinimumHeight(45)
        self.login_btn.clicked.connect(self._do_login)
        layout.addWidget(self.login_btn)

        # 注册链接
        register_btn = QPushButton("还没有账号？立即注册")
        register_btn.setStyleSheet("background: transparent; color: #89b4fa; border: none;")
        register_btn.clicked.connect(self._show_register)
        layout.addWidget(register_btn, alignment=Qt.AlignCenter)

        main_layout.addWidget(card)

        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 20px;
                color: #6c7086;
            }
            QPushButton:hover {
                color: #f38ba8;
            }
        """)
        close_btn.clicked.connect(self.reject)
        close_btn.setParent(self)
        close_btn.move(20, 20)

    def resizeEvent(self, event):
        close_btn = self.findChild(QPushButton)
        if close_btn:
            close_btn.move(self.width() - 52, 20)
        super().resizeEvent(event)

    def _do_login(self):
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

    def _show_register(self):
        dialog = RegisterDialog(self.client, self)
        dialog.exec_()

# ============================================================================
# 现代化注册对话框
# ============================================================================

class RegisterDialog(QDialog):
    
    def __init__(self, client: CloudClient, parent: QWidget = None):
        super().__init__(parent)
        self.client = client
        self.setWindowTitle("注册账号")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        card = QWidget()
        card.setObjectName("card")
        card.setStyleSheet("""
            #card {
                background-color: #1e1e2f;
                border-radius: 24px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        title = QLabel("📝 创建新账号")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #89b4fa;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名")
        self.username_input.setMinimumHeight(45)
        layout.addWidget(self.username_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("电子邮箱")
        self.email_input.setMinimumHeight(45)
        layout.addWidget(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码（至少6位）")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(45)
        layout.addWidget(self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("确认密码")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setMinimumHeight(45)
        layout.addWidget(self.confirm_input)

        self.register_btn = QPushButton("注 册")
        self.register_btn.setProperty("primary", True)
        self.register_btn.setMinimumHeight(45)
        self.register_btn.clicked.connect(self._do_register)
        layout.addWidget(self.register_btn)

        main_layout.addWidget(card)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 20px;
                color: #6c7086;
            }
            QPushButton:hover {
                color: #f38ba8;
            }
        """)
        close_btn.clicked.connect(self.reject)
        close_btn.setParent(self)
        close_btn.move(20, 20)

    def resizeEvent(self, event):
        close_btn = self.findChild(QPushButton)
        if close_btn:
            close_btn.move(self.width() - 52, 20)
        super().resizeEvent(event)

    def _do_register(self):
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

# ============================================================================
# 新建加密文件对话框 - 现代化设计
# ============================================================================

class NewEncryptedFileDialog(QDialog):
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("新建加密笔记")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.selected_algorithm = 'rsa'
        self.selected_key_mode = 'global'
        self.use_password = False
        self.strict_password = True
        self.custom_password = None
        self.single_private = None
        self.single_public = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        card = QWidget()
        card.setObjectName("card")
        card.setStyleSheet("""
            #card {
                background-color: #1e1e2f;
                border-radius: 24px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 标题栏
        title_layout = QHBoxLayout()
        title = QLabel("🔐 新建加密笔记")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #89b4fa;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 20px;
                color: #6c7086;
            }
            QPushButton:hover {
                color: #f38ba8;
            }
        """)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        layout.addLayout(title_layout)

        # 1. 加密算法
        group1 = QGroupBox("加密算法")
        group1.setStyleSheet("""
            QGroupBox {
                border: 1px solid #313244;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #89b4fa;
            }
        """)
        group1_layout = QVBoxLayout()
        self.radio_rsa = QRadioButton("RSA-4096 + AES-256-GCM")
        self.radio_x25519 = QRadioButton("X25519 + AES-256-GCM")
        self.radio_rsa.setChecked(True)
        group1_layout.addWidget(self.radio_rsa)
        group1_layout.addWidget(self.radio_x25519)
        group1.setLayout(group1_layout)
        layout.addWidget(group1)

        # 2. 密钥方式
        group2 = QGroupBox("密钥方式")
        group2.setStyleSheet("""
            QGroupBox {
                border: 1px solid #313244;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #89b4fa;
            }
        """)
        group2_layout = QVBoxLayout()
        self.radio_global = QRadioButton("默认加密（使用全局密钥对）")
        self.radio_single = QRadioButton("安全加密（为当前文件单独生成密钥对）")
        self.radio_global.setChecked(True)
        group2_layout.addWidget(self.radio_global)
        group2_layout.addWidget(self.radio_single)
        group2.setLayout(group2_layout)
        layout.addWidget(group2)

        # 3. 密码保护
        group3 = QGroupBox("密码保护（可选）")
        group3.setStyleSheet("""
            QGroupBox {
                border: 1px solid #313244;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #89b4fa;
            }
        """)
        group3_layout = QVBoxLayout()
        
        # 强度模式选择
        strength_layout = QHBoxLayout()
        strength_layout.addWidget(QLabel("密码强度要求:"))
        self.radio_strict = QRadioButton("高强度 (推荐)")
        self.radio_weak = QRadioButton("低强度 (不推荐)")
        self.radio_strict.setChecked(True)
        strength_layout.addWidget(self.radio_strict)
        strength_layout.addWidget(self.radio_weak)
        group3_layout.addLayout(strength_layout)
        
        self.checkbox_password = QCheckBox("启用密码保护")
        self.checkbox_password.toggled.connect(self._on_password_toggled)
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

        self.password_input.textChanged.connect(self._check_password_strength)
        self.radio_strict.toggled.connect(self._on_strength_mode_changed)
        self.radio_weak.toggled.connect(self._on_strength_mode_changed)
        
        group3.setLayout(group3_layout)
        layout.addWidget(group3)

        # 提示信息
        info_label = QLabel(
            "💡 提示：\n"
            "• 全局密钥：所有文件共用同一密钥\n"
            "• 单独密钥：每个文件独立生成密钥对\n"
            "• 密钥文件请妥善保管，丢失后将无法解密！"
        )
        info_label.setStyleSheet(
            "color: #a6adc8; font-size: 12px; background-color: #181825; "
            "padding: 12px; border-radius: 12px;"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        self.ok_btn = QPushButton("创建加密笔记")
        self.ok_btn.setProperty("primary", True)
        self.cancel_btn = QPushButton("取消")
        self.ok_btn.clicked.connect(self._accept_config)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        main_layout.addWidget(card)

    def _on_strength_mode_changed(self):
        self.strict_password = self.radio_strict.isChecked()
        if self.radio_strict.isChecked():
            self.password_input.setPlaceholderText(
                "请输入密码（至少16位，包含大小写字母、数字和特殊字符）"
            )
        else:
            self.password_input.setPlaceholderText(
                "请输入密码（无强度限制，但强烈建议使用强密码）"
            )
        self._check_password_strength()

    def _on_password_toggled(self, checked: bool):
        self.password_input.setEnabled(checked)
        self.confirm_input.setEnabled(checked)
        self.use_password = checked
        if checked:
            self._check_password_strength()
        else:
            self.password_strength_label.setText("")

    def _check_password_strength(self):
        if not self.use_password:
            self.password_strength_label.setText("")
            return
            
        pwd = self.password_input.text()
        strength = check_password_strength(pwd)
        
        self.password_strength_label.setText(f"🔐 密码强度: {strength['level']} - {strength['message']}")
        self.password_strength_label.setStyleSheet(f"color: {strength['color']}; font-size: 12px;")

    def _accept_config(self):
        self.selected_algorithm = 'x25519' if self.radio_x25519.isChecked() else 'rsa'
        self.selected_key_mode = 'single' if self.radio_single.isChecked() else 'global'
        self.strict_password = self.radio_strict.isChecked()

        if self.use_password:
            pwd = self.password_input.text()
            confirm = self.confirm_input.text()
            
            if not pwd or not confirm:
                QMessageBox.warning(self, "提示", "请输入密码")
                return
            if pwd != confirm:
                QMessageBox.warning(self, "错误", "两次输入的密码不一致")
                return
            
            strength = check_password_strength(pwd)
            if strength['level'] in ['极弱', '弱']:
                reply = QMessageBox.warning(
                    self, "密码强度不足",
                    f"您设置的密码强度为「{strength['level']}」，{strength['message']}\n\n"
                    "是否继续使用此密码？",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            
            self.custom_password = pwd

        if self.selected_key_mode == 'single':
            if self.selected_algorithm == 'rsa':
                self.single_private, self.single_public = generate_rsa_key(4096)
            else:
                self.single_private, self.single_public = generate_x25519_keys()

        self.accept()

    def get_config(self) -> dict:
        return {
            'algorithm': self.selected_algorithm,
            'key_mode': self.selected_key_mode,
            'use_password': self.use_password,
            'strict_password': self.strict_password,
            'custom_password': self.custom_password,
            'single_private': self.single_private,
            'single_public': self.single_public
        }

# ============================================================================
# 保存加密文件对话框 - 现代化设计
# ============================================================================

class SaveEncryptedFileDialog(QDialog):
    
    def __init__(self, content: str, algorithm: str, key_mode: str,
                 use_password: bool, strict_password: bool,
                 custom_password: str, single_private: bytes,
                 single_public: bytes, parent: QWidget = None):
        super().__init__(parent)
        self.content = content
        self.algorithm = algorithm
        self.key_mode = key_mode
        self.use_password = use_password
        self.strict_password = strict_password
        self.custom_password = custom_password
        self.single_private = single_private
        self.single_public = single_public
        self.setWindowTitle("保存加密笔记")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.selected_file_path = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        card = QWidget()
        card.setObjectName("card")
        card.setStyleSheet("""
            #card {
                background-color: #1e1e2f;
                border-radius: 24px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 标题栏
        title_layout = QHBoxLayout()
        title = QLabel("💾 保存加密笔记")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #89b4fa;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 20px;
                color: #6c7086;
            }
            QPushButton:hover {
                color: #f38ba8;
            }
        """)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        layout.addLayout(title_layout)

        if self.key_mode == 'single':
            info_label = QLabel(
                "⚠️ 您选择了【安全加密】模式，将为当前文件单独生成密钥对。\n"
                "密钥文件(.key)将与.bjb文件保存在同一目录，请妥善保管！\n"
                "丢失密钥文件后将无法解密！"
            )
            info_label.setStyleSheet(
                "color: #f9e2af; background-color: #313244; "
                "padding: 12px; border-radius: 12px;"
            )
            info_label.setWordWrap(True)
            layout.addWidget(info_label)

        # 文件选择
        layout.addWidget(QLabel("📁 保存位置:"))
        
        file_select_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("请选择保存位置...")
        self.file_path_input.setMinimumHeight(40)
        self.file_path_input.textChanged.connect(self._on_path_changed)
        file_select_layout.addWidget(self.file_path_input)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self._select_save_file)
        file_select_layout.addWidget(self.browse_btn)
        layout.addLayout(file_select_layout)

        # 加密信息
        info_group = QGroupBox("加密信息摘要")
        info_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #313244;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #89b4fa;
            }
        """)
        info_layout = QVBoxLayout()
        
        algo_text = "RSA-4096" if self.algorithm == 'rsa' else "X25519"
        key_text = "全局密钥" if self.key_mode == 'global' else "单独密钥(安全模式)"
        pwd_text = "已启用" if self.use_password else "未启用"
        strength_text = "高强度" if self.strict_password else "低强度"
        
        info_layout.addWidget(QLabel(f"🔐 加密算法: {algo_text} + AES-256-GCM"))
        info_layout.addWidget(QLabel(f"🔑 密钥方式: {key_text}"))
        info_layout.addWidget(QLabel(f"🔒 密码保护: {pwd_text}"))
        if self.use_password:
            info_layout.addWidget(QLabel(f"🔐 密码强度: {strength_text}"))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        self.ok_btn = QPushButton("保存文件")
        self.ok_btn.setProperty("primary", True)
        self.cancel_btn = QPushButton("取消")
        self.ok_btn.clicked.connect(self._do_save)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        main_layout.addWidget(card)

    def _on_path_changed(self, text: str):
        if text.strip():
            self.selected_file_path = text.strip()

    def _select_save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "保存加密笔记", "", "加密笔记 (*.bjb)")
        if file_path:
            if not file_path.endswith('.bjb'):
                file_path += '.bjb'
            self.selected_file_path = file_path
            self.file_path_input.setText(file_path)

    def _do_save(self):
        if not self.selected_file_path:
            QMessageBox.warning(self, "提示", "请选择保存位置")
            return
        
        if not self.selected_file_path.endswith('.bjb'):
            self.selected_file_path += '.bjb'

        try:
            encrypted_data, priv, pub = EncryptedNoteHandler.encrypt_content(
                self.content, self.algorithm, self.key_mode,
                self.custom_password, self.single_private, self.single_public,
                strict_password=self.strict_password
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

# ============================================================================
# 加密当前文件对话框 - 现代化设计
# ============================================================================

class EncryptCurrentFileDialog(QDialog):
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("加密当前文件")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.selected_algorithm = 'rsa'
        self.selected_key_mode = 'global'
        self.use_password = False
        self.strict_password = True
        self.custom_password = None
        self.single_private = None
        self.single_public = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        card = QWidget()
        card.setObjectName("card")
        card.setStyleSheet("""
            #card {
                background-color: #1e1e2f;
                border-radius: 24px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 标题栏
        title_layout = QHBoxLayout()
        title = QLabel("🔐 加密当前文件")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #89b4fa;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 20px;
                color: #6c7086;
            }
            QPushButton:hover {
                color: #f38ba8;
            }
        """)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        layout.addLayout(title_layout)

        info_label = QLabel("⚠️ 注意：加密后将生成新的.bjb文件，原文件不会被删除")
        info_label.setStyleSheet(
            "color: #f9e2af; background-color: #313244; "
            "padding: 12px; border-radius: 12px;"
        )
        layout.addWidget(info_label)

        # 1. 加密算法
        group1 = QGroupBox("加密算法")
        group1.setStyleSheet("""
            QGroupBox {
                border: 1px solid #313244;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #89b4fa;
            }
        """)
        group1_layout = QVBoxLayout()
        self.radio_rsa = QRadioButton("RSA-4096 + AES-256-GCM")
        self.radio_x25519 = QRadioButton("X25519 + AES-256-GCM")
        self.radio_rsa.setChecked(True)
        group1_layout.addWidget(self.radio_rsa)
        group1_layout.addWidget(self.radio_x25519)
        group1.setLayout(group1_layout)
        layout.addWidget(group1)

        # 2. 密钥方式
        group2 = QGroupBox("密钥方式")
        group2.setStyleSheet("""
            QGroupBox {
                border: 1px solid #313244;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #89b4fa;
            }
        """)
        group2_layout = QVBoxLayout()
        self.radio_global = QRadioButton("默认加密（使用全局密钥对）")
        self.radio_single = QRadioButton("安全加密（为当前文件单独生成密钥对）")
        self.radio_global.setChecked(True)
        group2_layout.addWidget(self.radio_global)
        group2_layout.addWidget(self.radio_single)
        group2.setLayout(group2_layout)
        layout.addWidget(group2)

        # 3. 密码保护
        group3 = QGroupBox("密码保护（可选）")
        group3.setStyleSheet("""
            QGroupBox {
                border: 1px solid #313244;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #89b4fa;
            }
        """)
        group3_layout = QVBoxLayout()
        
        strength_layout = QHBoxLayout()
        strength_layout.addWidget(QLabel("密码强度要求:"))
        self.radio_strict = QRadioButton("高强度 (推荐)")
        self.radio_weak = QRadioButton("低强度 (不推荐)")
        self.radio_strict.setChecked(True)
        strength_layout.addWidget(self.radio_strict)
        strength_layout.addWidget(self.radio_weak)
        group3_layout.addLayout(strength_layout)
        
        self.checkbox_password = QCheckBox("启用密码保护")
        self.checkbox_password.toggled.connect(self._on_password_toggled)
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

        self.password_input.textChanged.connect(self._check_password_strength)
        self.radio_strict.toggled.connect(self._on_strength_mode_changed)
        
        group3.setLayout(group3_layout)
        layout.addWidget(group3)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        self.ok_btn = QPushButton("加密并保存")
        self.ok_btn.setProperty("primary", True)
        self.cancel_btn = QPushButton("取消")
        self.ok_btn.clicked.connect(self._accept_config)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        main_layout.addWidget(card)

    def _on_strength_mode_changed(self):
        self.strict_password = self.radio_strict.isChecked()
        if self.radio_strict.isChecked():
            self.password_input.setPlaceholderText(
                "请输入密码（至少16位，包含大小写字母、数字和特殊字符）"
            )
        else:
            self.password_input.setPlaceholderText(
                "请输入密码（无强度限制，但强烈建议使用强密码）"
            )
        self._check_password_strength()

    def _on_password_toggled(self, checked: bool):
        self.password_input.setEnabled(checked)
        self.confirm_input.setEnabled(checked)
        self.use_password = checked
        if checked:
            self._check_password_strength()
        else:
            self.password_strength_label.setText("")

    def _check_password_strength(self):
        if not self.use_password:
            self.password_strength_label.setText("")
            return
            
        pwd = self.password_input.text()
        strength = check_password_strength(pwd)
        
        self.password_strength_label.setText(f"🔐 密码强度: {strength['level']} - {strength['message']}")
        self.password_strength_label.setStyleSheet(f"color: {strength['color']}; font-size: 12px;")

    def _accept_config(self):
        self.selected_algorithm = 'x25519' if self.radio_x25519.isChecked() else 'rsa'
        self.selected_key_mode = 'single' if self.radio_single.isChecked() else 'global'
        self.strict_password = self.radio_strict.isChecked()

        if self.use_password:
            pwd = self.password_input.text()
            confirm = self.confirm_input.text()
            
            if not pwd or not confirm:
                QMessageBox.warning(self, "提示", "请输入密码")
                return
            if pwd != confirm:
                QMessageBox.warning(self, "错误", "两次输入的密码不一致")
                return
            
            strength = check_password_strength(pwd)
            if strength['level'] in ['极弱', '弱']:
                reply = QMessageBox.warning(
                    self, "密码强度不足",
                    f"您设置的密码强度为「{strength['level']}」，{strength['message']}\n\n"
                    "是否继续使用此密码？",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            
            self.custom_password = pwd

        if self.selected_key_mode == 'single':
            if self.selected_algorithm == 'rsa':
                self.single_private, self.single_public = generate_rsa_key(4096)
            else:
                self.single_private, self.single_public = generate_x25519_keys()

        self.accept()

    def get_config(self) -> dict:
        return {
            'algorithm': self.selected_algorithm,
            'key_mode': self.selected_key_mode,
            'use_password': self.use_password,
            'strict_password': self.strict_password,
            'custom_password': self.custom_password,
            'single_private': self.single_private,
            'single_public': self.single_public
        }

# ============================================================================
# 编辑器选项卡
# ============================================================================

class EditorTab:
    
    def __init__(self, tab_widget: QTabWidget, index: int,
                 file_path: str = None, cloud_id: int = None,
                 is_new: bool = False, content: str = "",
                 file_type: str = "txt", encrypt_config: dict = None):
        
        self.tab_widget = tab_widget
        self.index = index
        self.file_path = file_path
        self.cloud_id = cloud_id
        self.is_new = is_new
        self.file_type = file_type
        self.encrypt_config = encrypt_config
        self.modified = False
        
        # 创建编辑器容器
        self.container = QWidget()
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(8, 8, 8, 8)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(content)
        self.text_edit.textChanged.connect(self._on_text_changed)

        font = QFont("Consolas", 12)
        self.text_edit.setFont(font)
        layout.addWidget(self.text_edit)

        self._update_tab_title()

    def _update_tab_title(self):
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

    def _on_text_changed(self):
        if not self.modified:
            self.modified = True
            self._update_tab_title()

    def get_content(self) -> str:
        return self.text_edit.toPlainText()

    def set_content(self, content: str):
        self.text_edit.setPlainText(content)
        self.modified = False
        self._update_tab_title()

    def mark_saved(self):
        self.modified = False
        self._update_tab_title()

# ============================================================================
# 云端文件树窗口 - 现代化设计
# ============================================================================

class CloudFileTreeDialog(QDialog):
    
    def __init__(self, client: CloudClient, parent: QWidget = None):
        super().__init__(parent)
        self.client = client
        self.setWindowTitle("云端文件管理")
        self.resize(1000, 700)
        self.current_folder = '/'
        self._setup_ui()
        self._load_filetree()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # 工具栏
        toolbar = QToolBar()
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #181825;
                border-radius: 12px;
                padding: 8px;
            }
        """)
        
        self.up_btn = QAction("⬆ 返回上级", self)
        self.up_btn.triggered.connect(self._go_up)
        toolbar.addAction(self.up_btn)
        toolbar.addSeparator()
        
        self.refresh_btn = QAction("🔄 刷新", self)
        self.refresh_btn.triggered.connect(self._load_filetree)
        toolbar.addAction(self.refresh_btn)
        toolbar.addSeparator()
        
        self.new_folder_btn = QAction("📁 新建文件夹", self)
        self.new_folder_btn.triggered.connect(self._create_folder)
        toolbar.addAction(self.new_folder_btn)
        toolbar.addSeparator()
        
        self.upload_btn = QAction("📤 上传文件", self)
        self.upload_btn.triggered.connect(self._upload_file)
        toolbar.addAction(self.upload_btn)
        
        layout.addWidget(toolbar)

        # 搜索栏
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索文件...")
        self.search_input.setMinimumHeight(36)
        self.search_input.returnPressed.connect(self._search_files)
        
        search_btn = QPushButton("搜索")
        search_btn.setProperty("primary", True)
        search_btn.clicked.connect(self._search_files)
        
        clear_btn = QPushButton("清除")
        clear_btn.clicked.connect(self._clear_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        search_layout.addWidget(clear_btn)
        layout.addWidget(search_widget)

        # 文件树
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["名称", "大小", "类型", "修改时间"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setIndentation(20)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemDoubleClicked.connect(self._on_item_double_click)
        layout.addWidget(self.tree)

        # 状态栏
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #a6adc8;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        layout.addWidget(status_widget)

        self._load_storage_info()

    def _load_storage_info(self):
        info = self.client.get_storage_info()
        if info:
            used_mb = info['total_size'] / (1024 * 1024)
            max_mb = info['max_size'] / (1024 * 1024)
            download_used_mb = info['download_used'] / (1024 * 1024)
            download_max_mb = info['download_max'] / (1024 * 1024)
            self.status_label.setText(
                f"📊 存储: {used_mb:.1f}MB / {max_mb:.0f}MB | "
                f"📥 今日下载: {download_used_mb:.1f}MB / {download_max_mb:.0f}MB"
            )

    def _load_filetree(self):
        data = self.client.get_filetree(self.current_folder)
        if not data:
            QMessageBox.warning(self, "错误", "加载文件树失败")
            return
        
        self.tree.clear()
        for item in data['items']:
            size_str = self._format_size(item['size']) if item['size'] else ""
            type_str = "📁 文件夹" if item['is_folder'] else ("🔒 加密笔记" if item.get('type') == 'bjb' else "📄 文本文件")
            tree_item = QTreeWidgetItem([
                item['name'], size_str, type_str, item['created_at']
            ])
            tree_item.setData(0, Qt.UserRole, item)
            self.tree.addTopLevelItem(tree_item)
        
        self._load_storage_info()

    def _format_size(self, size_bytes: int) -> str:
        if not size_bytes:
            return ""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"

    def _go_up(self):
        if self.current_folder != '/':
            parts = self.current_folder.rstrip('/').split('/')
            if len(parts) > 1:
                self.current_folder = '/' + '/'.join(parts[:-1])
            else:
                self.current_folder = '/'
            self._load_filetree()

    def _create_folder(self):
        name, ok = QInputDialog.getText(self, "新建文件夹", "请输入文件夹名称:")
        if ok and name:
            if '/' in name or '\\' in name:
                QMessageBox.warning(self, "错误", "文件夹名称不能包含路径分隔符")
                return
            res = self.client.create_folder(name, self.current_folder)
            if res:
                self._load_filetree()
            else:
                QMessageBox.warning(self, "错误", "创建失败")

    def _upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要上传的文件", "", "笔记本文件 (*.bjb *.txt)"
        )
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
                self._load_filetree()
            else:
                QMessageBox.warning(self, "错误", "上传失败")

    def _search_files(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            return
        data = self.client.search_files(keyword)
        if data:
            self.tree.clear()
            for item in data['items']:
                size_str = self._format_size(item['size']) if item['size'] else ""
                type_str = "📁 文件夹" if item['is_folder'] else ("🔒 加密笔记" if item.get('type') == 'bjb' else "📄 文本文件")
                tree_item = QTreeWidgetItem([
                    item['name'], size_str, type_str, ""
                ])
                tree_item.setData(0, Qt.UserRole, item)
                self.tree.addTopLevelItem(tree_item)
            self.status_label.setText(f"🔍 搜索到 {len(data['items'])} 个结果")

    def _clear_search(self):
        self.search_input.clear()
        self._load_filetree()

    def _on_item_double_click(self, item: QTreeWidgetItem, col: int):
        data = item.data(0, Qt.UserRole)
        if data['is_folder']:
            if self.search_input.text():
                self._clear_search()
            if data['parent'] != '/':
                self.current_folder = f"{data['parent']}/{data['name']}"
            else:
                self.current_folder = f"/{data['name']}"
            self._load_filetree()
        else:
            self._download_and_open(data)

    def _download_and_open(self, file_info: dict):
        temp_dir = tempfile.gettempdir()
        local_path = os.path.join(temp_dir, f"cloud_{file_info['id']}_{file_info['name']}")
        
        if self.client.download_file(file_info['id'], local_path):
            ext = os.path.splitext(file_info['name'])[1].lower()
            
            if ext == '.txt':
                try:
                    with open(local_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    main_window = self.parent()
                    if isinstance(main_window, MainWindow):
                        tab = EditorTab(
                            main_window.tabs, main_window.tabs.count(),
                            file_path=local_path, cloud_id=file_info['id'],
                            file_type='txt', content=content
                        )
                        main_window.tabs.addTab(tab.container, os.path.basename(file_info['name']))
                        main_window.editor_tabs.append(tab)
                        main_window.tabs.setCurrentIndex(main_window.tabs.count() - 1)
                        self.accept()
                except Exception as e:
                    debug_error(f"读取文本文件失败: {e}")
                    QMessageBox.warning(self, "错误", f"读取文件失败: {str(e)}")
            else:
                content, success, encrypt_config = decrypt_bjb_file(
                    local_path, self, is_cloud_file=True, cloud_filename=file_info['name']
                )
                
                if success and content is not None:
                    main_window = self.parent()
                    if isinstance(main_window, MainWindow):
                        tab = EditorTab(
                            main_window.tabs, main_window.tabs.count(),
                            file_path=local_path, cloud_id=file_info['id'],
                            file_type='bjb', content=content, encrypt_config=encrypt_config
                        )
                        main_window.tabs.addTab(tab.container, os.path.basename(file_info['name']))
                        main_window.editor_tabs.append(tab)
                        main_window.tabs.setCurrentIndex(main_window.tabs.count() - 1)
                        self.accept()
        else:
            QMessageBox.warning(self, "错误", "下载失败")

    def _show_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return
        
        data = item.data(0, Qt.UserRole)
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: #313244;
            }
        """)
        
        rename_action = menu.addAction("✏️ 重命名")
        delete_action = menu.addAction("🗑️ 删除")
        move_action = menu.addAction("📂 移动")
        download_action = menu.addAction("💾 下载")
        
        action = menu.exec_(self.tree.viewport().mapToGlobal(pos))
        
        if action == rename_action:
            new_name, ok = QInputDialog.getText(self, "重命名", "新名称:", text=data['name'])
            if ok and new_name:
                if self.client.rename_item(data['id'], new_name):
                    self._load_filetree()
                else:
                    QMessageBox.warning(self, "错误", "重命名失败")
        elif action == delete_action:
            if QMessageBox.question(self, "确认", f"确定删除 {data['name']} 吗？") == QMessageBox.Yes:
                if self.client.delete_item(data['id']):
                    self._load_filetree()
                else:
                    QMessageBox.warning(self, "错误", "删除失败")
        elif action == move_action:
            target, ok = QInputDialog.getText(self, "移动", "目标文件夹路径 (例如 /folder):")
            if ok and target:
                if self.client.move_item(data['id'], target):
                    self._load_filetree()
                else:
                    QMessageBox.warning(self, "错误", "移动失败")
        elif action == download_action:
            save_path, _ = QFileDialog.getSaveFileName(self, "保存文件", data['name'])
            if save_path:
                if self.client.download_file(data['id'], save_path):
                    QMessageBox.information(self, "成功", "下载完成")
                else:
                    QMessageBox.warning(self, "错误", "下载失败")

# ============================================================================
# 主窗口 - 现代化设计
# ============================================================================

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.client = CloudClient()
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.tabs.setDocumentMode(True)
        self.setCentralWidget(self.tabs)
        self.setWindowTitle("云笔记 - 安全加密笔记")
        self.setMinimumSize(800, 600)
        
        self._setup_menu()
        self._setup_statusbar()
        self._setup_theme_switcher()
        
        self.editor_tabs = []
        self.current_editor = None
        
        self.current_theme = "dark"
        self._apply_theme("dark")

        ensure_global_keys()
        self._check_login()

    def _setup_theme_switcher(self):
        # 添加主题切换按钮到菜单栏右侧
        theme_action = QAction("🌓 切换主题", self)
        theme_action.triggered.connect(self._toggle_theme)
        
        # 找到帮助菜单并添加主题切换
        for menu in self.menuBar().actions():
            if menu.text() == "帮助":
                menu.menu().addSeparator()
                menu.menu().addAction(theme_action)
                break
        else:
            # 如果没有帮助菜单，创建帮助菜单
            help_menu = self.menuBar().addMenu("帮助")
            help_menu.addAction(theme_action)

    def _toggle_theme(self):
        if self.current_theme == "dark":
            self.current_theme = "light"
        else:
            self.current_theme = "dark"
        self._apply_theme(self.current_theme)

    def _apply_theme(self, theme: str):
        if theme == "dark":
            self.setStyleSheet(DARK_STYLE)
        else:
            self.setStyleSheet(LIGHT_STYLE)

    def _setup_menu(self):
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")

        new_txt_action = QAction("新建文本文件", self)
        new_txt_action.setShortcut(QKeySequence("Ctrl+N"))
        new_txt_action.setIconText("📄")
        new_txt_action.triggered.connect(lambda: self._new_file('txt'))
        file_menu.addAction(new_txt_action)

        new_bjb_action = QAction("新建加密笔记", self)
        new_bjb_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        new_bjb_action.setIconText("🔒")
        new_bjb_action.triggered.connect(lambda: self._new_file('bjb'))
        file_menu.addAction(new_bjb_action)

        file_menu.addSeparator()

        open_action = QAction("打开文件", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._open_local_file_dialog)
        file_menu.addAction(open_action)

        open_cloud_action = QAction("从云端打开", self)
        open_cloud_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_cloud_action.triggered.connect(self._open_cloud_file_dialog)
        file_menu.addAction(open_cloud_action)

        file_menu.addSeparator()

        save_action = QAction("保存", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._save_current_tab)
        file_menu.addAction(save_action)

        save_as_action = QAction("另存为", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self._save_as_current_tab)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 加密菜单
        encrypt_menu = menubar.addMenu("加密")

        encrypt_current_action = QAction("加密当前文件", self)
        encrypt_current_action.setShortcut(QKeySequence("Ctrl+E"))
        encrypt_current_action.triggered.connect(self._encrypt_current_file)
        encrypt_menu.addAction(encrypt_current_action)

        encrypt_menu.addSeparator()

        txt_to_bjb_action = QAction("另存为加密笔记", self)
        txt_to_bjb_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        txt_to_bjb_action.triggered.connect(self._convert_txt_to_bjb)
        encrypt_menu.addAction(txt_to_bjb_action)

        # 云端菜单
        cloud_menu = menubar.addMenu("云端")

        manage_cloud_action = QAction("管理云端文件", self)
        manage_cloud_action.triggered.connect(self._show_cloud_manager)
        cloud_menu.addAction(manage_cloud_action)

        upload_action = QAction("上传当前文件到云端", self)
        upload_action.triggered.connect(self._upload_current_tab)
        cloud_menu.addAction(upload_action)

        cloud_menu.addSeparator()

        logout_action = QAction("退出登录", self)
        logout_action.triggered.connect(self._logout)
        cloud_menu.addAction(logout_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self._about)
        help_menu.addAction(about_action)

    def _setup_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 创建状态栏标签
        self.storage_label = QLabel("")
        self.user_label = QLabel("")
        
        self.status_bar.addWidget(self.user_label)
        self.status_bar.addPermanentWidget(self.storage_label)

    def _update_storage_info(self):
        if self.client.token:
            info = self.client.get_storage_info()
            if info:
                used_mb = info['total_size'] / (1024 * 1024)
                max_mb = info['max_size'] / (1024 * 1024)
                self.storage_label.setText(f"📁 {used_mb:.1f}MB / {max_mb:.0f}MB")

    def _check_login(self):
        settings = QSettings("CloudNote", "User")
        token = settings.value("token")
        user_id = settings.value("user_id")
        username = settings.value("username")

        if token and user_id and username:
            self.client.set_auth(token, int(user_id), username)
            user_info = self.client.get_user_info()
            if user_info:
                self.user_label.setText(f"👤 {username}")
                self.status_bar.showMessage(f"欢迎回来，{username}", 3000)
                self._update_storage_info()
                return
            else:
                settings.clear()
                self.client.clear_auth()

        dialog = LoginDialog(self.client, self)
        if dialog.exec_() == QDialog.Accepted:
            self.user_label.setText(f"👤 {self.client.username}")
            self.status_bar.showMessage(f"欢迎 {self.client.username}", 3000)
            self._update_storage_info()
        else:
            sys.exit(0)

    def _logout(self):
        self.client.clear_auth()
        settings = QSettings("CloudNote", "User")
        settings.clear()
        self.user_label.setText("")
        self.storage_label.setText("")
        self.status_bar.showMessage("已退出登录", 3000)
        
        while self.tabs.count() > 0:
            self._close_tab(0)
        
        self._check_login()

    def _new_file(self, file_type: str):
        if file_type == 'txt':
            tab = EditorTab(
                self.tabs, self.tabs.count(),
                file_type='txt', is_new=True, content=""
            )
            self.tabs.addTab(tab.container, "未命名")
            self.editor_tabs.append(tab)
            self.tabs.setCurrentIndex(self.tabs.count() - 1)
        else:
            tab = EditorTab(
                self.tabs, self.tabs.count(),
                file_type='bjb', is_new=True, content=""
            )
            self.tabs.addTab(tab.container, "未命名加密笔记")
            self.editor_tabs.append(tab)
            self.tabs.setCurrentIndex(self.tabs.count() - 1)
            
            dialog = NewEncryptedFileDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                config = dialog.get_config()
                tab.encrypt_config = config
                self._save_as_current_tab()
            else:
                self._close_tab(self.tabs.currentIndex())

    def _open_local_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "", "笔记本文件 (*.bjb *.txt)"
        )
        if file_path:
            self._open_local_file(file_path)

    def _open_local_file(self, file_path: str, cloud_id: int = None):
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tab = EditorTab(
                    self.tabs, self.tabs.count(),
                    file_path=file_path, cloud_id=cloud_id,
                    file_type='txt', content=content
                )
                self.tabs.addTab(tab.container, os.path.basename(file_path))
                self.editor_tabs.append(tab)
                self.tabs.setCurrentIndex(self.tabs.count() - 1)
            except Exception as e:
                debug_error(f"读取文件失败: {e}")
                QMessageBox.critical(self, "错误", f"读取文件失败: {str(e)}")

        elif ext == '.bjb':
            content, success, encrypt_config = decrypt_bjb_file(
                file_path, self, is_cloud_file=False
            )
            
            if success and content is not None:
                tab = EditorTab(
                    self.tabs, self.tabs.count(),
                    file_path=file_path, cloud_id=cloud_id,
                    file_type='bjb', content=content, encrypt_config=encrypt_config
                )
                self.tabs.addTab(tab.container, os.path.basename(file_path))
                self.editor_tabs.append(tab)
                self.tabs.setCurrentIndex(self.tabs.count() - 1)

    def _open_cloud_file_dialog(self):
        if not self.client.token:
            QMessageBox.warning(self, "提示", "请先登录")
            self._check_login()
            return
        
        dialog = CloudFileTreeDialog(self.client, self)
        dialog.exec_()

    def _save_current_tab(self):
        idx = self.tabs.currentIndex()
        if idx < 0 or idx >= len(self.editor_tabs):
            return
        
        tab = self.editor_tabs[idx]
        content = tab.get_content()

        if tab.is_new:
            self._save_as_current_tab()
            return

        if tab.file_path and os.path.exists(tab.file_path):
            try:
                if tab.file_type == 'txt':
                    with open(tab.file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    tab.mark_saved()
                    self.status_bar.showMessage(f"已保存: {os.path.basename(tab.file_path)}", 3000)
                    
                else:
                    if tab.encrypt_config:
                        config = tab.encrypt_config
                        
                        encrypted_data, _, _ = EncryptedNoteHandler.encrypt_content(
                            content,
                            config.get('algorithm', 'rsa'),
                            config.get('key_mode', 'global'),
                            config.get('custom_password'),
                            config.get('single_private'),
                            config.get('single_public'),
                            strict_password=config.get('strict_password', True)
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
                                config.get('single_public'),
                                strict_password=config.get('strict_password', True)
                            )
                            
                            with open(tab.file_path, 'wb') as f:
                                f.write(encrypted_data)
                            
                            tab.mark_saved()
                            self.status_bar.showMessage(f"已保存: {os.path.basename(tab.file_path)}", 3000)
            except Exception as e:
                debug_error(f"保存失败: {e}")
                QMessageBox.critical(self, "保存失败", str(e))
        else:
            self._save_as_current_tab()

    def _save_as_current_tab(self):
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
            if not tab.encrypt_config:
                dialog = NewEncryptedFileDialog(self)
                if dialog.exec_() != QDialog.Accepted:
                    return
                config = dialog.get_config()
                tab.encrypt_config = config
            else:
                config = tab.encrypt_config

            save_dialog = SaveEncryptedFileDialog(
                content,
                config['algorithm'],
                config['key_mode'],
                config.get('use_password', False),
                config.get('strict_password', True),
                config.get('custom_password'),
                config.get('single_private'),
                config.get('single_public'),
                self
            )
            
            if save_dialog.exec_() == QDialog.Accepted:
                tab.file_type = 'bjb'
                tab.is_new = False
                if save_dialog.selected_file_path:
                    tab.file_path = save_dialog.selected_file_path
                tab.mark_saved()

    def _encrypt_current_file(self):
        idx = self.tabs.currentIndex()
        if idx < 0 or idx >= len(self.editor_tabs):
            QMessageBox.warning(self, "提示", "没有打开的文件")
            return
        
        tab = self.editor_tabs[idx]
        content = tab.get_content()
        
        if not content.strip():
            ret = QMessageBox.question(
                self, "确认", "文件内容为空，是否继续加密？",
                QMessageBox.Yes | QMessageBox.No
            )
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
                content,
                config['algorithm'],
                config['key_mode'],
                config['custom_password'],
                config.get('single_private'),
                config.get('single_public'),
                strict_password=config.get('strict_password', True)
            )
            
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            if config['key_mode'] == 'single' and priv:
                key_path = file_path + '.key'
                with open(key_path, 'wb') as f:
                    f.write(priv)
                QMessageBox.information(
                    self, "加密成功",
                    f"文件已加密保存为:\n{file_path}\n\n"
                    f"密钥文件已保存为:\n{key_path}\n\n"
                    f"请妥善保管密钥文件！"
                )
            else:
                QMessageBox.information(
                    self, "加密成功",
                    f"文件已加密保存为:\n{file_path}\n\n"
                    f"使用全局密钥加密，无需额外保存密钥文件。"
                )
            
            ret = QMessageBox.question(
                self, "打开文件",
                "是否在新选项卡中打开加密后的文件？",
                QMessageBox.Yes | QMessageBox.No
            )
            if ret == QMessageBox.Yes:
                self._open_local_file(file_path)
                
        except Exception as e:
            debug_error(f"加密失败: {e}")
            QMessageBox.critical(self, "加密失败", str(e))

    def _convert_txt_to_bjb(self):
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
                content,
                config['algorithm'],
                config['key_mode'],
                config['custom_password'],
                config.get('single_private'),
                config.get('single_public'),
                strict_password=config.get('strict_password', True)
            )
            
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            if config['key_mode'] == 'single' and priv:
                key_path = file_path + '.key'
                with open(key_path, 'wb') as f:
                    f.write(priv)
                QMessageBox.information(
                    self, "转换成功",
                    f"文件已转换为加密笔记:\n{file_path}\n\n"
                    f"密钥文件已保存为:\n{key_path}\n\n"
                    f"请妥善保管密钥文件！"
                )
            else:
                QMessageBox.information(
                    self, "转换成功",
                    f"文件已转换为加密笔记:\n{file_path}\n\n"
                    f"使用全局密钥加密，无需额外保存密钥文件。"
                )
            
            ret = QMessageBox.question(
                self, "打开文件",
                "是否在新选项卡中打开加密后的文件？",
                QMessageBox.Yes | QMessageBox.No
            )
            if ret == QMessageBox.Yes:
                self._open_local_file(file_path)
                
        except Exception as e:
            debug_error(f"转换失败: {e}")
            QMessageBox.critical(self, "转换失败", str(e))

    def _upload_current_tab(self):
        if not self.client.token:
            QMessageBox.warning(self, "提示", "请先登录")
            self._check_login()
            return

        idx = self.tabs.currentIndex()
        if idx < 0 or idx >= len(self.editor_tabs):
            return
        
        tab = self.editor_tabs[idx]

        if tab.is_new or not tab.file_path:
            QMessageBox.warning(self, "提示", "请先保存文件到本地")
            return

        if tab.modified:
            ret = QMessageBox.question(
                self, "提示", "文件未保存，是否先保存？",
                QMessageBox.Yes | QMessageBox.No
            )
            if ret == QMessageBox.Yes:
                self._save_current_tab()

        folder, ok = QInputDialog.getText(
            self, "上传到云端", "请输入云端目录路径 (默认为 /):", text="/"
        )
        if not ok:
            return
        if not folder:
            folder = "/"

        res = self.client.upload_file(tab.file_path, folder)
        if res:
            QMessageBox.information(self, "成功", "文件已上传到云端")
        else:
            QMessageBox.warning(self, "错误", "上传失败")

    def _show_cloud_manager(self):
        if not self.client.token:
            QMessageBox.warning(self, "提示", "请先登录")
            self._check_login()
            return
        
        dialog = CloudFileTreeDialog(self.client, self)
        dialog.exec_()

    def _on_tab_changed(self, index: int):
        if index >= 0 and index < len(self.editor_tabs):
            self.current_editor = self.editor_tabs[index]
        else:
            self.current_editor = None

    def _close_tab(self, index: int):
        if index < 0 or index >= len(self.editor_tabs):
            return
        
        tab = self.editor_tabs[index]
        
        if tab.modified:
            ret = QMessageBox.question(
                self, "提示", "文件已修改，是否保存？",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if ret == QMessageBox.Yes:
                self._save_current_tab()
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

    def _about(self):
        QMessageBox.about(
            self, "关于云笔记",
            "<h2>☁️ 云笔记 v5.0</h2>"
            "<p><b>作者:</b> dvs (dvsxt)</p>"
            "<br>"
            "<h3>✨ 版本 5.0 新特性</h3>"
            "<ul>"
            "<li>🎨 全新的现代化界面设计</li>"
            "<li>🌓 支持暗色/亮色主题切换</li>"
            "<li>📱 完全自适应布局，支持窗口缩放</li>"
            "<li>✨ 圆角卡片设计和流畅动画效果</li>"
            "</ul>"
            "<br>"
            "<h3>🔐 功能特性</h3>"
            "<ul>"
            "<li>支持 .txt 文本文件</li>"
            "<li>支持 .bjb 加密笔记</li>"
            "<li>云端同步功能</li>"
            "<li>多选项卡编辑</li>"
            "<li>加密当前文件</li>"
            "<li>TXT转BJB加密</li>"
            "<li>端到端加密：服务器不存储私钥</li>"
            "</ul>"
            "<br>"
            "<h3>⚡ 快捷键</h3>"
            "<ul>"
            "<li>Ctrl+N: 新建文本</li>"
            "<li>Ctrl+Shift+N: 新建加密笔记</li>"
            "<li>Ctrl+E: 加密当前文件</li>"
            "<li>Ctrl+Shift+S: 另存为加密笔记</li>"
            "<li>Ctrl+S: 保存</li>"
            "<li>Ctrl+O: 打开文件</li>"
            "</ul>"
            "<br>"
            f"<p><b>密钥存储位置：</b><br>"
            f"用户目录: {USER_KEY_DIR}<br>"
            f"程序目录: {APP_KEY_DIR}</p>"
        )

# ============================================================================
# 程序入口
# ============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    ensure_global_keys()

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()