#!/usr/bin/env python3
"""
手机号解密工具
"""

import hashlib
import logging
import time
from typing import Dict, List, Optional

import requests

from .constants import MOBILE_DECRYPT_SERVICE_URL

logger = logging.getLogger(__name__)

_DECRYPT_PATH = "/feign/generatekey/decryptMobile"


def _get_decrypt_url() -> str:
    """从配置文件获取解密服务URL"""
    return f"{MOBILE_DECRYPT_SERVICE_URL}{_DECRYPT_PATH}"


def _gen_token(timestamp: int, cipher_mobile: str) -> str:
    """生成token: md5(timestamp + cipherMobile)"""
    s = f"{timestamp}{cipher_mobile}"
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def decrypt_mobile(cipher_mobile: str, key_id: int) -> Optional[str]:
    """
    手机号解密，必须传密文手机号和key_id（来自ES）。
    token自动用md5(timestamp + cipherMobile)生成。
    """
    if not cipher_mobile or not key_id:
        return None
    try:
        timestamp = int(time.time() * 1000)
        token = _gen_token(timestamp, cipher_mobile)
        data = {
            "cipherMobile": cipher_mobile,
            "keyId": key_id,
            "timestamp": timestamp,
            "token": token,
        }
        decrypt_url = _get_decrypt_url()
        resp = requests.post(decrypt_url, json=data, timeout=5)
        resp.raise_for_status()
        result = resp.json()
        if isinstance(result, dict):
            return result.get("mobile") or result.get("data") or result.get("result")
        elif isinstance(result, str):
            return result
        return None
    except Exception as e:
        logger.warning(f"手机号解密失败: {e}")
        return None


def decrypt_mobile_batch(cipher_keyid_list: List[Dict[str, int]]) -> Dict[str, Optional[str]]:
    """
    批量手机号解密，参数为 [{'cipherMobile': xxx, 'keyId': xxx}, ...]
    返回 {密文: 明文或None}
    """
    return {
        item["cipherMobile"]: decrypt_mobile(item["cipherMobile"], item["keyId"])
        for item in cipher_keyid_list
    }
