"""讯飞虚拟人签名服务单元测试 —— 纯函数，不依赖 DB / 网络。"""

import base64
import hashlib
import hmac
import re
import urllib.parse
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from app.services.avatar_service import avatar_config, build_signed_url

HOST = "vms.cn-huadong-1.xf-yun.com"
PATH = "/v1/private/vms2d_start"
API_KEY = "a4d63d4b"
API_SECRET = "secret-32-char-abcdefghijklmnop"
NOW = datetime(2026, 8, 30, 12, 0, 0, tzinfo=timezone.utc)


def _fake_settings(**kw):
    base = {
        "AVATAR_APP_ID": "", "AVATAR_API_KEY": "", "AVATAR_API_SECRET": "",
        "AVATAR_SCENE_ID": "", "AVATAR_AVATAR_ID": "", "AVATAR_VOICE_ID": "",
        "AVATAR_HOST": HOST, "AVATAR_START_PATH": PATH,
    }
    base.update(kw)
    return SimpleNamespace(**base)


class TestBuildSignedUrl:
    def test_returns_expected_host_path(self):
        url = build_signed_url(API_KEY, API_SECRET, HOST, PATH, now=NOW)
        assert url.startswith(f"wss://{HOST}{PATH}?")
        params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        assert params["host"] == [HOST]

    def test_date_is_rfc1123_gmt(self):
        url = build_signed_url(API_KEY, API_SECRET, HOST, PATH, now=NOW)
        date = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["date"][0]
        assert date == "Sun, 30 Aug 2026 12:00:00 GMT"

    def test_authorization_roundtrips_signature(self):
        url = build_signed_url(API_KEY, API_SECRET, HOST, PATH, now=NOW)
        params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        authorization = base64.b64decode(params["authorization"][0]).decode()
        assert f'api_key="{API_KEY}"' in authorization
        assert 'algorithm="hmac-sha256"' in authorization
        assert 'headers="host date request-line"' in authorization

        signature = re.search(r'signature="([^"]+)"', authorization).group(1)
        signature_origin = f"host: {HOST}\ndate: {params['date'][0]}\nGET {PATH} HTTP/1.1"
        expected = base64.b64encode(
            hmac.new(API_SECRET.encode(), signature_origin.encode(), hashlib.sha256).digest()
        ).decode()
        assert signature == expected

    def test_timestamp_changes_signature(self):
        later = datetime(2026, 8, 30, 12, 5, 0, tzinfo=timezone.utc)
        url1 = build_signed_url(API_KEY, API_SECRET, HOST, PATH, now=NOW)
        url2 = build_signed_url(API_KEY, API_SECRET, HOST, PATH, now=later)
        assert url1 != url2


class TestAvatarConfig:
    def test_no_credentials_returns_both_false(self):
        with patch("app.services.avatar_service.get_settings",
                   return_value=_fake_settings()):
            assert avatar_config() == {"configured": False, "personaReady": False}

    def test_partial_credentials_still_both_false(self):
        with patch("app.services.avatar_service.get_settings",
                   return_value=_fake_settings(AVATAR_API_KEY=API_KEY)):
            assert avatar_config() == {"configured": False, "personaReady": False}

    def test_resource_ids_without_creds_exposes_real_persona(self):
        """资源 ID 齐备但无密钥 → personaReady=True，返回真实形象/音色 ID，不发 signedUrl。"""
        with patch("app.services.avatar_service.get_settings", return_value=_fake_settings(
            AVATAR_APP_ID="app-1",
            AVATAR_SCENE_ID="scene-1",
            AVATAR_AVATAR_ID="111306001",
            AVATAR_VOICE_ID="x4_yezi",
        )):
            cfg = avatar_config()
        assert cfg == {
            "configured": False,
            "personaReady": True,
            "appId": "app-1",
            "sceneId": "scene-1",
            "avatarId": "111306001",
            "voiceId": "x4_yezi",
        }
        assert "signedUrl" not in cfg

    def test_full_credentials_returns_signed_url_and_ids(self):
        with patch("app.services.avatar_service.get_settings", return_value=_fake_settings(
            AVATAR_APP_ID="app-1",
            AVATAR_API_KEY=API_KEY,
            AVATAR_API_SECRET=API_SECRET,
            AVATAR_SCENE_ID="scene-1",
            AVATAR_AVATAR_ID="111306001",
            AVATAR_VOICE_ID="x4_yezi",
        )):
            cfg = avatar_config()
        assert cfg["configured"] is True
        assert cfg["personaReady"] is True
        assert cfg["appId"] == "app-1"
        assert cfg["sceneId"] == "scene-1"
        assert cfg["avatarId"] == "111306001"
        assert cfg["voiceId"] == "x4_yezi"
        assert cfg["signedUrl"].startswith(f"wss://{HOST}{PATH}?")

    def test_config_never_exposes_secrets(self):
        with patch("app.services.avatar_service.get_settings", return_value=_fake_settings(
            AVATAR_APP_ID="app-1",
            AVATAR_API_KEY=API_KEY,
            AVATAR_API_SECRET=API_SECRET,
            AVATAR_SCENE_ID="scene-1",
            AVATAR_AVATAR_ID="111306001",
            AVATAR_VOICE_ID="x4_yezi",
        )):
            cfg = avatar_config()
        blob = str(cfg)
        assert API_SECRET not in blob
        assert "apiKey" not in blob and "api_key" not in blob
