"""讯飞虚拟人（数字人）服务 —— 服务端签发鉴权 signedUrl。

凭证（AVATAR_API_KEY / AVATAR_API_SECRET）只在本模块用于 HMAC-SHA256 签名，
signedUrl 是限时的连接地址，随 camelCase 资源 ID 返回给前端；密钥永不外发。
签名规范见讯飞开放平台「AI虚拟人技术 API 文档」：
https://www.xfyun.cn/doc/tts/virtual_human/API.html
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import urllib.parse
from datetime import datetime, timezone
from email.utils import format_datetime

from app.config import get_settings


def build_signed_url(
    api_key: str,
    api_secret: str,
    host: str,
    path: str,
    now: datetime | None = None,
) -> str:
    """按讯飞鉴权规范生成旧协议虚拟人握手地址（wss://avatar.cn.../v1/interact）。

    三个查询参数：host / date（RFC1123 GMT）/ authorization。
    authorization = base64('api_key="...", algorithm="hmac-sha256", headers="host date request-line", signature="..."')
    signature      = base64(HMAC-SHA256("host: {host}\\ndate: {date}\\nGET {path} HTTP/1.1", api_secret))
    （WebSocket 握手请求行方法须用 GET —— 签名规范与 vms 同款，仅 host/path 不同。）
    """
    date = format_datetime(now or datetime.now(timezone.utc), usegmt=True)

    signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
    signature_sha = hmac.new(api_secret.encode(), signature_origin.encode(), hashlib.sha256).digest()
    signature = base64.b64encode(signature_sha).decode()

    authorization_origin = (
        f'api_key="{api_key}", algorithm="hmac-sha256", '
        f'headers="host date request-line", signature="{signature}"'
    )
    authorization = base64.b64encode(authorization_origin.encode()).decode()

    query = urllib.parse.urlencode(
        {"host": host, "date": date, "authorization": authorization}
    )
    # 旧协议虚拟人 SDK 用 wss 握手（见 SDK 文档 17.2 安全接入示例）。
    # vms2d REST 用 https POST，此处不再是该路线。
    return f"wss://{host}{path}?{query}"


def avatar_config() -> dict:
    """返回数字人前端所需配置（camelCase）。

    分层判定：
      personaReady —— 资源 ID（appId/sceneId/avatarId/voiceId）齐备，即可引用真实形象/音色
                      （演示模式用它们标识真实 persona、挑选最接近的音色）。
      configured   —— 资源 ID + apiKey/apiSecret 齐备，才签发 signedUrl 走真实 SDK。
    资源 ID 非机密（参考项目即放在前端 env）；apiKey/apiSecret 只用于签名，永不外发。
    """
    s = get_settings()
    resource_ids = (s.AVATAR_APP_ID, s.AVATAR_SCENE_ID, s.AVATAR_AVATAR_ID, s.AVATAR_VOICE_ID)
    persona_ready = all(resource_ids)
    creds_ready = persona_ready and bool(s.AVATAR_API_KEY and s.AVATAR_API_SECRET)

    payload: dict = {"configured": creds_ready, "personaReady": persona_ready}
    if persona_ready:
        payload.update({
            "appId": s.AVATAR_APP_ID,
            "sceneId": s.AVATAR_SCENE_ID,
            "avatarId": s.AVATAR_AVATAR_ID,
            "voiceId": s.AVATAR_VOICE_ID,
        })
    if creds_ready:
        payload["signedUrl"] = build_signed_url(
            s.AVATAR_API_KEY, s.AVATAR_API_SECRET, s.AVATAR_HOST, s.AVATAR_START_PATH
        )
    return payload
