"""
title: Batch Install Plugins from GitHub
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
version: 1.0.0
description: One-click batch install plugins from GitHub repositories to your OpenWebUI instance.
"""

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DEFAULT_REPO = "Fu-Jie/openwebui-extensions"
DEFAULT_BRANCH = "main"
DEFAULT_TIMEOUT = 20
DEFAULT_SKIP_KEYWORDS = "test,verify,example,template,mock"
GITHUB_TIMEOUT = 30.0
CONFIRMATION_TIMEOUT = 120.0  # 2 minutes for user confirmation
GITHUB_API = "https://api.github.com"
GITHUB_RAW = "https://raw.githubusercontent.com"
SELF_EXCLUDE_HINT = "batch-install-plugins"
SELF_EXCLUDE_TERMS = (
    SELF_EXCLUDE_HINT,
    "batch install plugins from github",
)
DOCSTRING_PATTERN = re.compile(r'^\s*"""\n(.*?)\n"""', re.DOTALL)
CLASS_PATTERN = re.compile(r'^class (Tools|Filter|Pipe|Action)\s*[\(:]', re.MULTILINE)
EMOJI_PATTERN = re.compile(r'[\U00010000-\U0010ffff]', re.UNICODE)

TRANSLATIONS = {
    "en-US": {
        "status_fetching": "Fetching plugin list from GitHub...",
        "status_installing": "Installing [{type}] {title}...",
        "status_done": "Installation complete: {success}/{total} plugins installed.",
        "status_list_title": "Available Plugins ({count} total)",
        "list_item": "- [{type}] {title}",
        "err_no_api_key": "Authentication required. Please ensure you are logged in.",
        "err_connection": "Cannot connect to OpenWebUI. Is it running?",
        "success_updated": "Updated: {title}",
        "success_created": "Created: {title}",
        "failed": "Failed: {title} - {error}",
        "error_timeout": "request timed out",
        "error_http_status": "status {status}: {message}",
        "error_request_failed": "request failed: {error}",
        "confirm_title": "Confirm Installation",
        "confirm_message": "Found {count} plugins to install:\n\n{plugin_list}{hint}\n\nDo you want to proceed with installation?",
        "confirm_excluded_hint": "\n\n(Excluded: {excluded})",
        "confirm_copy_exclude_hint": "\n\nCopy to exclude plugins:\n```\nexclude_keywords={keywords}\n```",
        "confirm_cancelled": "Installation cancelled by user.",
        "err_confirm_unavailable": "Confirmation timed out or failed. Installation cancelled.",
        "err_no_plugins": "No installable plugins found.",
        "err_no_match": "No plugins match the specified types.",
    },
    "zh-CN": {
        "status_fetching": "正在从 GitHub 获取插件列表...",
        "status_installing": "正在安装 [{type}] {title}...",
        "status_done": "安装完成：成功安装 {success}/{total} 个插件。",
        "status_list_title": "可用插件（共 {count} 个）",
        "list_item": "- [{type}] {title}",
        "err_no_api_key": "需要认证。请确保已登录。",
        "err_connection": "无法连接 OpenWebUI。请检查是否正在运行？",
        "success_updated": "已更新：{title}",
        "success_created": "已创建：{title}",
        "failed": "失败：{title} - {error}",
        "error_timeout": "请求超时",
        "error_http_status": "状态 {status}：{message}",
        "error_request_failed": "请求失败：{error}",
        "confirm_title": "确认安装",
        "confirm_message": "发现 {count} 个插件待安装：\n\n{plugin_list}{hint}\n\n是否继续安装？",
        "confirm_excluded_hint": "\n\n（已排除：{excluded}）",
        "confirm_copy_exclude_hint": "\n\n复制以下内容可排除插件：\n```\nexclude_keywords={keywords}\n```",
        "confirm_cancelled": "用户取消安装。",
        "err_confirm_unavailable": "确认操作超时或失败，已取消安装。",
        "err_no_plugins": "未发现可安装的插件。",
        "err_no_match": "没有符合指定类型的插件。",
    },
    "zh-HK": {
        "status_fetching": "正在從 GitHub 取得外掛列表...",
        "status_installing": "正在安裝 [{type}] {title}...",
        "status_done": "安裝完成：成功安裝 {success}/{total} 個外掛。",
        "status_list_title": "可用外掛（共 {count} 個）",
        "list_item": "- [{type}] {title}",
        "err_no_api_key": "需要驗證。請確保已登入。",
        "err_connection": "無法連線至 OpenWebUI。請檢查是否正在執行？",
        "success_updated": "已更新：{title}",
        "success_created": "已建立：{title}",
        "failed": "失敗：{title} - {error}",
        "error_timeout": "請求逾時",
        "error_http_status": "狀態 {status}：{message}",
        "error_request_failed": "請求失敗：{error}",
        "confirm_title": "確認安裝",
        "confirm_message": "發現 {count} 個外掛待安裝：\n\n{plugin_list}{hint}\n\n是否繼續安裝？",
        "confirm_excluded_hint": "\n\n（已排除：{excluded}）",
        "confirm_copy_exclude_hint": "\n\n複製以下內容可排除外掛：\n```\nexclude_keywords={keywords}\n```",
        "confirm_cancelled": "用戶取消安裝。",
        "err_confirm_unavailable": "確認操作逾時或失敗，已取消安裝。",
        "err_no_plugins": "未發現可安裝的外掛。",
        "err_no_match": "沒有符合指定類型的外掛。",
    },
    "zh-TW": {
        "status_fetching": "正在從 GitHub 取得外掛列表...",
        "status_installing": "正在安裝 [{type}] {title}...",
        "status_done": "安裝完成：成功安裝 {success}/{total} 個外掛。",
        "status_list_title": "可用外掛（共 {count} 個）",
        "list_item": "- [{type}] {title}",
        "err_no_api_key": "需要驗證。請確保已登入。",
        "err_connection": "無法連線至 OpenWebUI。請檢查是否正在執行？",
        "success_updated": "已更新：{title}",
        "success_created": "已建立：{title}",
        "failed": "失敗：{title} - {error}",
        "error_timeout": "請求逾時",
        "error_http_status": "狀態 {status}：{message}",
        "error_request_failed": "請求失敗：{error}",
        "confirm_title": "確認安裝",
        "confirm_message": "發現 {count} 個外掛待安裝：\n\n{plugin_list}{hint}\n\n是否繼續安裝？",
        "confirm_excluded_hint": "\n\n（已排除：{excluded}）",
        "confirm_copy_exclude_hint": "\n\n複製以下內容可排除外掛：\n```\nexclude_keywords={keywords}\n```",
        "confirm_cancelled": "用戶取消安裝。",
        "err_confirm_unavailable": "確認操作逾時或失敗，已取消安裝。",
        "err_no_plugins": "未發現可安裝的外掛。",
        "err_no_match": "沒有符合指定類型的外掛。",
    },
    "ko-KR": {
        "status_fetching": "GitHub에서 플러그인 목록을 가져오는 중...",
        "status_installing": "[{type}] {title} 설치 중...",
        "status_done": "설치 완료: {success}/{total}개 플러그인 설치됨.",
        "status_list_title": "사용 가능한 플러그인 (총 {count}개)",
        "list_item": "- [{type}] {title}",
        "err_no_api_key": "인증이 필요합니다. 로그인되어 있는지 확인하세요.",
        "err_connection": "OpenWebUI에 연결할 수 없습니다. 실행 중인가요?",
        "success_updated": "업데이트됨: {title}",
        "success_created": "생성됨: {title}",
        "failed": "실패: {title} - {error}",
        "error_timeout": "요청 시간이 초과되었습니다",
        "error_http_status": "상태 {status}: {message}",
        "error_request_failed": "요청 실패: {error}",
        "confirm_title": "설치 확인",
        "confirm_message": "설치할 플러그인 {count}개를 발견했습니다:\n\n{plugin_list}{hint}\n\n설치를 계속하시겠습니까?",
        "confirm_excluded_hint": "\n\n(제외됨: {excluded})",
        "confirm_copy_exclude_hint": "\n\n플러그인을 제외하려면 아래를 복사하세요:\n```\nexclude_keywords={keywords}\n```",
        "confirm_cancelled": "사용자가 설치를 취소했습니다.",
        "err_confirm_unavailable": "확인 요청이 시간 초과되었거나 실패하여 설치를 취소했습니다.",
        "err_no_plugins": "설치 가능한 플러그인을 찾을 수 없습니다.",
        "err_no_match": "지정된 유형과 일치하는 플러그인이 없습니다.",
    },
    "ja-JP": {
        "status_fetching": "GitHubからプラグインリストを取得中...",
        "status_installing": "[{type}] {title} をインストール中...",
        "status_done": "インストール完了: {success}/{total}個のプラグインがインストールされました。",
        "status_list_title": "利用可能なプラグイン (合計{count}個)",
        "list_item": "- [{type}] {title}",
        "err_no_api_key": "認証が必要です。ログインしていることを確認してください。",
        "err_connection": "OpenWebUIに接続できません。実行中ですか？",
        "success_updated": "更新: {title}",
        "success_created": "作成: {title}",
        "failed": "失敗: {title} - {error}",
        "error_timeout": "リクエストがタイムアウトしました",
        "error_http_status": "ステータス {status}: {message}",
        "error_request_failed": "リクエスト失敗: {error}",
        "confirm_title": "インストール確認",
        "confirm_message": "インストールするプラグインが{count}個見つかりました:\n\n{plugin_list}{hint}\n\nインストールを続行しますか？",
        "confirm_excluded_hint": "\n\n（除外: {excluded}）",
        "confirm_copy_exclude_hint": "\n\nプラグインを除外するには次をコピーしてください:\n```\nexclude_keywords={keywords}\n```",
        "confirm_cancelled": "ユーザーがインストールをキャンセルしました。",
        "err_confirm_unavailable": "確認がタイムアウトしたか失敗したため、インストールをキャンセルしました。",
        "err_no_plugins": "インストール可能なプラグインが見つかりません。",
        "err_no_match": "指定されたタイプのプラグインがありません。",
    },
    "fr-FR": {
        "status_fetching": "Récupération de la liste des plugins depuis GitHub...",
        "status_installing": "Installation de [{type}] {title}...",
        "status_done": "Installation terminée: {success}/{total} plugins installés.",
        "status_list_title": "Plugins disponibles ({count} au total)",
        "list_item": "- [{type}] {title}",
        "err_no_api_key": "Authentification requise. Veuillez vous assurer d'être connecté.",
        "err_connection": "Impossible de se connecter à OpenWebUI. Est-il en cours d'exécution?",
        "success_updated": "Mis à jour: {title}",
        "success_created": "Créé: {title}",
        "failed": "Échec: {title} - {error}",
        "error_timeout": "délai d'attente de la requête dépassé",
        "error_http_status": "statut {status} : {message}",
        "error_request_failed": "échec de la requête : {error}",
        "confirm_title": "Confirmer l'installation",
        "confirm_message": "{count} plugins à installer:\n\n{plugin_list}{hint}\n\nVoulez-vous procéder à l'installation?",
        "confirm_excluded_hint": "\n\n(Exclus : {excluded})",
        "confirm_copy_exclude_hint": "\n\nCopiez ceci pour exclure des plugins :\n```\nexclude_keywords={keywords}\n```",
        "confirm_cancelled": "Installation annulée par l'utilisateur.",
        "err_confirm_unavailable": "La confirmation a expiré ou a échoué. Installation annulée.",
        "err_no_plugins": "Aucun plugin installable trouvé.",
        "err_no_match": "Aucun plugin ne correspond aux types spécifiés.",
    },
    "de-DE": {
        "status_fetching": "Plugin-Liste wird von GitHub abgerufen...",
        "status_installing": "[{type}] {title} wird installiert...",
        "status_done": "Installation abgeschlossen: {success}/{total} Plugins installiert.",
        "status_list_title": "Verfügbare Plugins (insgesamt {count})",
        "list_item": "- [{type}] {title}",
        "err_no_api_key": "Authentifizierung erforderlich. Bitte stellen Sie sicher, dass Sie angemeldet sind.",
        "err_connection": "Verbindung zu OpenWebUI nicht möglich. Läuft es?",
        "success_updated": "Aktualisiert: {title}",
        "success_created": "Erstellt: {title}",
        "failed": "Fehlgeschlagen: {title} - {error}",
        "error_timeout": "Zeitüberschreitung bei der Anfrage",
        "error_http_status": "Status {status}: {message}",
        "error_request_failed": "Anfrage fehlgeschlagen: {error}",
        "confirm_title": "Installation bestätigen",
        "confirm_message": "{count} Plugins zur Installation gefunden:\n\n{plugin_list}{hint}\n\nMöchten Sie mit der Installation fortfahren?",
        "confirm_excluded_hint": "\n\n(Ausgeschlossen: {excluded})",
        "confirm_copy_exclude_hint": "\n\nZum Ausschließen von Plugins kopieren:\n```\nexclude_keywords={keywords}\n```",
        "confirm_cancelled": "Installation vom Benutzer abgebrochen.",
        "err_confirm_unavailable": "Bestätigung abgelaufen oder fehlgeschlagen. Installation abgebrochen.",
        "err_no_plugins": "Keine installierbaren Plugins gefunden.",
        "err_no_match": "Keine Plugins entsprechen den angegebenen Typen.",
    },
    "es-ES": {
        "status_fetching": "Obteniendo lista de plugins de GitHub...",
        "status_installing": "Instalando [{type}] {title}...",
        "status_done": "Instalación completada: {success}/{total} plugins instalados.",
        "status_list_title": "Plugins disponibles ({count} en total)",
        "list_item": "- [{type}] {title}",
        "err_no_api_key": "Se requiere autenticación. Asegúrese de haber iniciado sesión.",
        "err_connection": "No se puede conectar a OpenWebUI. ¿Está en ejecución?",
        "success_updated": "Actualizado: {title}",
        "success_created": "Creado: {title}",
        "failed": "Fallido: {title} - {error}",
        "error_timeout": "la solicitud agotó el tiempo de espera",
        "error_http_status": "estado {status}: {message}",
        "error_request_failed": "solicitud fallida: {error}",
        "confirm_title": "Confirmar instalación",
        "confirm_message": "Se encontraron {count} plugins para instalar:\n\n{plugin_list}{hint}\n\n¿Desea continuar con la instalación?",
        "confirm_excluded_hint": "\n\n(Excluidos: {excluded})",
        "confirm_copy_exclude_hint": "\n\nCopia esto para excluir plugins:\n```\nexclude_keywords={keywords}\n```",
        "confirm_cancelled": "Instalación cancelada por el usuario.",
        "err_confirm_unavailable": "La confirmación expiró o falló. Instalación cancelada.",
        "err_no_plugins": "No se encontraron plugins instalables.",
        "err_no_match": "No hay plugins que coincidan con los tipos especificados.",
    },
    "it-IT": {
        "status_fetching": "Recupero lista plugin da GitHub...",
        "status_installing": "Installazione di [{type}] {title}...",
        "status_done": "Installazione completata: {success}/{total} plugin installati.",
        "status_list_title": "Plugin disponibili ({count} totali)",
        "list_item": "- [{type}] {title}",
        "err_no_api_key": "Autenticazione richiesta. Assicurati di aver effettuato l'accesso.",
        "err_connection": "Impossibile connettersi a OpenWebUI. È in esecuzione?",
        "success_updated": "Aggiornato: {title}",
        "success_created": "Creato: {title}",
        "failed": "Fallito: {title} - {error}",
        "error_timeout": "richiesta scaduta",
        "error_http_status": "stato {status}: {message}",
        "error_request_failed": "richiesta non riuscita: {error}",
        "confirm_title": "Conferma installazione",
        "confirm_message": "Trovati {count} plugin da installare:\n\n{plugin_list}{hint}\n\nVuoi procedere con l'installazione?",
        "confirm_excluded_hint": "\n\n(Esclusi: {excluded})",
        "confirm_copy_exclude_hint": "\n\nCopia questo per escludere plugin:\n```\nexclude_keywords={keywords}\n```",
        "confirm_cancelled": "Installazione annullata dall'utente.",
        "err_confirm_unavailable": "La conferma è scaduta o non è riuscita. Installazione annullata.",
        "err_no_plugins": "Nessun plugin installabile trovato.",
        "err_no_match": "Nessun plugin corrisponde ai tipi specificati.",
    },
    "vi-VN": {
        "status_fetching": "Đang lấy danh sách plugin từ GitHub...",
        "status_installing": "Đang cài đặt [{type}] {title}...",
        "status_done": "Cài đặt hoàn tất: {success}/{total} plugin đã được cài đặt.",
        "status_list_title": "Plugin khả dụng ({count} tổng cộng)",
        "list_item": "- [{type}] {title}",
        "err_no_api_key": "Yêu cầu xác thực. Vui lòng đảm bảo bạn đã đăng nhập.",
        "err_connection": "Không thể kết nối đến OpenWebUI. Có đang chạy không?",
        "success_updated": "Đã cập nhật: {title}",
        "success_created": "Đã tạo: {title}",
        "failed": "Thất bại: {title} - {error}",
        "error_timeout": "yêu cầu đã hết thời gian chờ",
        "error_http_status": "trạng thái {status}: {message}",
        "error_request_failed": "yêu cầu thất bại: {error}",
        "confirm_title": "Xác nhận cài đặt",
        "confirm_message": "Tìm thấy {count} plugin để cài đặt:\n\n{plugin_list}{hint}\n\nBạn có muốn tiếp tục cài đặt không?",
        "confirm_excluded_hint": "\n\n(Đã loại trừ: {excluded})",
        "confirm_copy_exclude_hint": "\n\nSao chép nội dung sau để loại trừ plugin:\n```\nexclude_keywords={keywords}\n```",
        "confirm_cancelled": "Người dùng đã hủy cài đặt.",
        "err_confirm_unavailable": "Xác nhận đã hết thời gian chờ hoặc thất bại. Đã hủy cài đặt.",
        "err_no_plugins": "Không tìm thấy plugin nào có thể cài đặt.",
        "err_no_match": "Không có plugin nào khớp với các loại được chỉ định.",
    },
}

FALLBACK_MAP = {"zh": "zh-CN", "zh-TW": "zh-TW", "zh-HK": "zh-HK", "en": "en-US", "ko": "ko-KR", "ja": "ja-JP", "fr": "fr-FR", "de": "de-DE", "es": "es-ES", "it": "it-IT", "vi": "vi-VN"}


def _resolve_language(user_language: str) -> str:
    value = str(user_language or "").strip()
    if not value:
        return "en-US"
    normalized = value.replace("_", "-")
    if normalized in TRANSLATIONS:
        return normalized
    lower_fallback = {k.lower(): v for k, v in FALLBACK_MAP.items()}
    base = normalized.split("-")[0].lower()
    return lower_fallback.get(base, "en-US")


def _t(lang: str, key: str, **kwargs) -> str:
    lang_key = _resolve_language(lang)
    text = TRANSLATIONS.get(lang_key, TRANSLATIONS["en-US"]).get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text


async def _emit_status(emitter: Optional[Any], description: str, done: bool = False) -> None:
    if emitter:
        await emitter(
            {"type": "status", "data": {"description": description, "done": done}}
        )


async def _emit_notification(
    emitter: Optional[Any],
    content: str,
    ntype: str = "info",
) -> None:
    if emitter:
        await emitter(
            {"type": "notification", "data": {"type": ntype, "content": content}}
        )


async def _finalize_message(
    emitter: Optional[Any],
    message: str,
    notification_type: Optional[str] = None,
) -> str:
    await _emit_status(emitter, message, done=True)
    if notification_type:
        await _emit_notification(emitter, message, ntype=notification_type)
    return message


async def _emit_frontend_debug_log(
    event_call: Optional[Any],
    title: str,
    data: Dict[str, Any],
    level: str = "debug",
) -> None:
    if not event_call:
        return

    console_method = level if level in {"debug", "log", "warn", "error"} else "debug"
    js_code = f"""
        try {{
            const payload = {json.dumps(data, ensure_ascii=False)};
            const runtime = {{
                href: typeof window !== "undefined" ? window.location.href : "",
                origin: typeof window !== "undefined" ? window.location.origin : "",
                lang: (
                    (typeof document !== "undefined" && document.documentElement && document.documentElement.lang) ||
                    (typeof localStorage !== "undefined" && (localStorage.getItem("locale") || localStorage.getItem("language"))) ||
                    (typeof navigator !== "undefined" && navigator.language) ||
                    ""
                ),
                readyState: (typeof document !== "undefined" && document.readyState) || "",
            }};
            const merged = Object.assign({{ frontend: runtime }}, payload);
            console.groupCollapsed(
                "%c" + {json.dumps(f"[Batch Install] {title}", ensure_ascii=False)},
                "color:#2563eb;font-weight:bold;"
            );
            console.{console_method}(merged);
            if (merged.base_url && runtime.origin && merged.base_url !== runtime.origin) {{
                console.warn("[Batch Install] Frontend origin differs from backend target", {{
                    frontend_origin: runtime.origin,
                    backend_target: merged.base_url,
                }});
            }}
            console.groupEnd();
            return true;
        }} catch (e) {{
            console.error("[Batch Install] Failed to emit frontend debug log", e);
            return false;
        }}
    """

    try:
        await asyncio.wait_for(
            event_call({"type": "execute", "data": {"code": js_code}}),
            timeout=2.0,
        )
    except asyncio.TimeoutError:
        logger.warning("Frontend debug log timed out: %s", title)
    except Exception as exc:
        logger.warning("Frontend debug log failed for %s: %s", title, exc)


async def _get_user_context(
    __user__: Optional[dict],
    __event_call__: Optional[Any] = None,
    __request__: Optional[Any] = None,
) -> Dict[str, str]:
    if isinstance(__user__, (list, tuple)):
        user_data = __user__[0] if __user__ else {}
    elif isinstance(__user__, dict):
        user_data = __user__
    else:
        user_data = {}
    user_language = user_data.get("language", "en-US")
    if __request__ and hasattr(__request__, "headers"):
        accept_lang = __request__.headers.get("accept-language", "")
        if accept_lang:
            user_language = accept_lang.split(",")[0].split(";")[0]
    if __event_call__:
        try:
            js_code = """
                try {
                    return (
                        document.documentElement.lang ||
                        localStorage.getItem('locale') ||
                        localStorage.getItem('language') ||
                        navigator.language ||
                        'en-US'
                    );
                } catch (e) {
                    return 'en-US';
                }
            """
            frontend_lang = await asyncio.wait_for(
                __event_call__({"type": "execute", "data": {"code": js_code}}),
                timeout=2.0,
            )
            if frontend_lang and isinstance(frontend_lang, str):
                user_language = frontend_lang
        except asyncio.TimeoutError:
            logger.warning("Frontend language detection timed out.")
        except Exception as exc:
            logger.warning("Frontend language detection failed: %s", exc)
    return {
        "user_id": str(user_data.get("id", "")).strip(),
        "user_name": user_data.get("name", "User"),
        "user_language": user_language,
    }


class PluginCandidate:
    def __init__(
        self,
        plugin_type: str,
        file_path: str,
        metadata: Dict[str, str],
        content: str,
        function_id: str,
    ):
        self.plugin_type = plugin_type
        self.file_path = file_path
        self.metadata = metadata
        self.content = content
        self.function_id = function_id

    @property
    def title(self) -> str:
        return self.metadata.get("title", Path(self.file_path).stem)

    @property
    def version(self) -> str:
        return self.metadata.get("version", "unknown")


def extract_metadata(content: str) -> Dict[str, str]:
    match = DOCSTRING_PATTERN.search(content)
    if not match:
        return {}
    metadata: Dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip().lower()] = value.strip()
    return metadata


def detect_plugin_type(content: str) -> Optional[str]:
    if "\nclass Tools:" in content or "\nclass Tools (" in content:
        return "tool"
    if "\nclass Filter:" in content or "\nclass Filter (" in content:
        return "filter"
    if "\nclass Pipe:" in content or "\nclass Pipe (" in content:
        return "pipe"
    if "\nclass Action:" in content or "\nclass Action (" in content:
        return "action"
    return None


def has_valid_class(content: str) -> bool:
    return CLASS_PATTERN.search(content) is not None


def has_emoji(text: str) -> bool:
    return bool(EMOJI_PATTERN.search(text))


def should_skip_file(file_path: str, is_default_repo: bool, skip_keywords: str = "test") -> Optional[str]:
    stem = Path(file_path).stem.lower()
    if is_default_repo and stem.endswith("_cn"):
        return "localized _cn file"
    if skip_keywords:
        keywords = [k.strip().lower() for k in skip_keywords.split(",") if k.strip()]
        for kw in keywords:
            if kw in stem:
                return f"contains '{kw}'"
    return None


def slugify_function_id(value: str) -> str:
    cleaned = EMOJI_PATTERN.sub("", value)
    slug = re.sub(r"[^a-z0-9_\u4e00-\u9fff]+", "_", cleaned.lower()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    return slug or "plugin"


def build_function_id(file_path: str, metadata: Dict[str, str]) -> str:
    if metadata.get("id"):
        return slugify_function_id(metadata["id"])
    if metadata.get("title"):
        return slugify_function_id(metadata["title"])
    return slugify_function_id(Path(file_path).stem)


def build_payload(candidate: PluginCandidate) -> Dict[str, object]:
    manifest = dict(candidate.metadata)
    manifest.setdefault("title", candidate.title)
    manifest.setdefault("author", "Fu-Jie")
    manifest.setdefault("author_url", "https://github.com/Fu-Jie/openwebui-extensions")
    manifest.setdefault("funding_url", "https://github.com/open-webui")
    manifest.setdefault(
        "description", f"{candidate.plugin_type.title()} plugin: {candidate.title}"
    )
    manifest.setdefault("version", "1.0.0")
    manifest["type"] = candidate.plugin_type
    if candidate.plugin_type == "tool":
        return {
            "id": candidate.function_id,
            "name": manifest["title"],
            "meta": {
                "description": manifest["description"],
                "manifest": {},
            },
            "content": candidate.content,
            "access_grants": [],
        }
    return {
        "id": candidate.function_id,
        "name": manifest["title"],
        "meta": {
            "description": manifest["description"],
            "manifest": manifest,
            "type": candidate.plugin_type,
        },
        "content": candidate.content,
    }


def build_api_urls(base_url: str, candidate: PluginCandidate) -> Tuple[str, str]:
    if candidate.plugin_type == "tool":
        return (
            f"{base_url}/api/v1/tools/id/{candidate.function_id}/update",
            f"{base_url}/api/v1/tools/create",
        )
    return (
        f"{base_url}/api/v1/functions/id/{candidate.function_id}/update",
        f"{base_url}/api/v1/functions/create",
    )


def _response_message(response: httpx.Response) -> str:
    try:
        return json.dumps(response.json(), ensure_ascii=False)
    except ValueError:
        return response.text[:500]


def _matches_self_plugin(candidate: PluginCandidate) -> bool:
    haystack = f"{candidate.title} {candidate.file_path}".lower()
    return any(term in haystack for term in SELF_EXCLUDE_TERMS)


def _candidate_debug_data(candidate: PluginCandidate) -> Dict[str, str]:
    return {
        "title": candidate.title,
        "type": candidate.plugin_type,
        "file_path": candidate.file_path,
        "function_id": candidate.function_id,
        "version": candidate.version,
    }


def _filter_candidates(
    candidates: List[PluginCandidate],
    plugin_types: List[str],
    repo: str,
    exclude_keywords: str = "",
) -> List[PluginCandidate]:
    allowed_types = {item.strip().lower() for item in plugin_types if item.strip()}
    filtered = [c for c in candidates if c.plugin_type.lower() in allowed_types]

    if repo.lower() == DEFAULT_REPO.lower():
        filtered = [c for c in filtered if not _matches_self_plugin(c)]

    exclude_list = [item.strip().lower() for item in exclude_keywords.split(",") if item.strip()]
    if exclude_list:
        filtered = [
            c
            for c in filtered
            if not any(
                keyword in c.title.lower() or keyword in c.file_path.lower()
                for keyword in exclude_list
            )
        ]

    return filtered


def _build_confirmation_hint(lang: str, repo: str, exclude_keywords: str) -> str:
    is_default_repo = repo.lower() == DEFAULT_REPO.lower()
    excluded_parts: List[str] = []

    if exclude_keywords:
        excluded_parts.append(exclude_keywords)
    if is_default_repo:
        excluded_parts.append(SELF_EXCLUDE_HINT)

    if excluded_parts:
        return _t(lang, "confirm_excluded_hint", excluded=", ".join(excluded_parts))

    return _t(lang, "confirm_copy_exclude_hint", keywords=SELF_EXCLUDE_HINT)


async def _request_confirmation(
    event_call: Optional[Any],
    lang: str,
    message: str,
) -> Tuple[bool, Optional[str]]:
    if not event_call:
        return True, None

    try:
        confirmed = await asyncio.wait_for(
            event_call(
                {
                    "type": "confirmation",
                    "data": {
                        "title": _t(lang, "confirm_title"),
                        "message": message,
                    },
                }
            ),
            timeout=CONFIRMATION_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning("Installation confirmation timed out.")
        return False, _t(lang, "err_confirm_unavailable")
    except Exception as exc:
        logger.warning("Installation confirmation failed: %s", exc)
        return False, _t(lang, "err_confirm_unavailable")

    return bool(confirmed), None


def parse_github_url(url: str) -> Optional[Tuple[str, str, str]]:
    match = re.match(
        r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/tree/([^/]+))?/?$",
        url,
    )
    if not match:
        return None
    owner, repo, branch = match.group(1), match.group(2), (match.group(3) or DEFAULT_BRANCH)
    return owner, repo, branch


async def fetch_github_tree(
    client: httpx.AsyncClient, owner: str, repo: str, branch: str
) -> List[Dict]:
    api_url = f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    try:
        resp = await client.get(api_url, headers={"User-Agent": "OpenWebUI-Tool"})
        resp.raise_for_status()
        data = resp.json()
        tree = data.get("tree", [])
        return tree if isinstance(tree, list) else []
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Failed to fetch GitHub tree from %s: %s", api_url, exc)
        return []


async def fetch_github_file(
    client: httpx.AsyncClient, owner: str, repo: str, branch: str, path: str
) -> Optional[str]:
    raw_url = f"{GITHUB_RAW}/{owner}/{repo}/{branch}/{path}"
    try:
        resp = await client.get(raw_url, headers={"User-Agent": "OpenWebUI-Tool"})
        resp.raise_for_status()
        return resp.text
    except httpx.HTTPError as exc:
        logger.warning("Failed to fetch GitHub file from %s: %s", raw_url, exc)
        return None


async def discover_plugins(
    url: str,
    skip_keywords: str = "test",
) -> Tuple[List[PluginCandidate], List[Tuple[str, str]]]:
    parsed = parse_github_url(url)
    if not parsed:
        return [], [("url", "invalid github url")]
    owner, repo, branch = parsed

    is_default_repo = (owner.lower() == "fu-jie" and repo.lower() == "openwebui-extensions")

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(GITHUB_TIMEOUT), follow_redirects=True
    ) as client:
        tree = await fetch_github_tree(client, owner, repo, branch)
        if not tree:
            return [], [("url", "failed to fetch repository tree")]

        candidates: List[PluginCandidate] = []
        skipped: List[Tuple[str, str]] = []

        for item in tree:
            item_path = item.get("path", "")
            if item.get("type") != "blob":
                continue
            if not item_path.endswith(".py"):
                continue

            file_name = item_path.split("/")[-1]
            skip_reason = should_skip_file(file_name, is_default_repo, skip_keywords)
            if skip_reason:
                skipped.append((item_path, skip_reason))
                continue

            content = await fetch_github_file(client, owner, repo, branch, item_path)
            if not content:
                skipped.append((item_path, "fetch failed"))
                continue

            if not has_valid_class(content):
                skipped.append((item_path, "no valid class"))
                continue

            metadata = extract_metadata(content)
            if not metadata:
                skipped.append((item_path, "missing docstring"))
                continue

            if "title" not in metadata or "description" not in metadata:
                skipped.append((item_path, "missing title/description"))
                continue

            if has_emoji(metadata.get("title", "")):
                skipped.append((item_path, "title contains emoji"))
                continue

            if is_default_repo and not metadata.get("openwebui_id"):
                skipped.append((item_path, "missing openwebui_id"))
                continue

            plugin_type = detect_plugin_type(content)
            if not plugin_type:
                skipped.append((item_path, "unknown plugin type"))
                continue

            candidates.append(
                PluginCandidate(
                    plugin_type=plugin_type,
                    file_path=item_path,
                    metadata=metadata,
                    content=content,
                    function_id=build_function_id(item_path, metadata),
                )
            )

    candidates.sort(key=lambda x: (x.plugin_type, x.file_path))
    return candidates, skipped


class ListParams(BaseModel):
    repo: str = Field(
        default=DEFAULT_REPO,
        description="GitHub repository (owner/repo)",
    )
    plugin_types: List[str] = Field(
        default=["pipe", "action", "filter", "tool"],
        description="Plugin types to list (pipe, action, filter, tool)",
    )


class InstallParams(BaseModel):
    repo: str = Field(
        default=DEFAULT_REPO,
        description="GitHub repository (owner/repo)",
    )
    plugin_types: List[str] = Field(
        default=["pipe", "action", "filter", "tool"],
        description="Plugin types to install (pipe, action, filter, tool)",
    )
    timeout: int = Field(
        default=DEFAULT_TIMEOUT,
        description="Request timeout in seconds",
    )


class Tools:
    class Valves(BaseModel):
        SKIP_KEYWORDS: str = Field(
            default=DEFAULT_SKIP_KEYWORDS,
            description="Comma-separated keywords to skip (e.g., 'test,verify,example')",
        )
        TIMEOUT: int = Field(
            default=DEFAULT_TIMEOUT,
            description="Request timeout in seconds",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def list_plugins(
        self,
        __user__: Optional[dict] = None,
        __event_call__: Optional[Any] = None,
        __request__: Optional[Any] = None,
        valves: Optional[Any] = None,
        repo: str = DEFAULT_REPO,
        plugin_types: List[str] = ["pipe", "action", "filter", "tool"],
    ) -> str:
        user_ctx = await _get_user_context(__user__, __event_call__, __request__)
        lang = user_ctx.get("user_language", "en-US")

        skip_keywords = DEFAULT_SKIP_KEYWORDS
        if valves and hasattr(valves, "SKIP_KEYWORDS") and valves.SKIP_KEYWORDS:
            skip_keywords = valves.SKIP_KEYWORDS

        repo_url = f"https://github.com/{repo}"
        candidates, _ = await discover_plugins(repo_url, skip_keywords)

        if not candidates:
            return _t(lang, "err_no_plugins")

        filtered = _filter_candidates(candidates, plugin_types, repo)
        if not filtered:
            return _t(lang, "err_no_match")

        lines = [f"## {_t(lang, 'status_list_title', count=len(filtered))}\n"]
        for c in filtered:
            lines.append(
                _t(lang, "list_item", type=c.plugin_type, title=c.title)
            )
        return "\n".join(lines)

    async def install_all_plugins(
        self,
        __user__: Optional[dict] = None,
        __event_call__: Optional[Any] = None,
        __request__: Optional[Any] = None,
        __event_emitter__: Optional[Any] = None,
        emitter: Optional[Any] = None,
        valves: Optional[Any] = None,
        repo: str = DEFAULT_REPO,
        plugin_types: List[str] = ["pipe", "action", "filter", "tool"],
        exclude_keywords: str = "",
        timeout: int = DEFAULT_TIMEOUT,
    ) -> str:
        user_ctx = await _get_user_context(__user__, __event_call__, __request__)
        lang = user_ctx.get("user_language", "en-US")
        event_emitter = __event_emitter__ or emitter

        skip_keywords = DEFAULT_SKIP_KEYWORDS
        if valves and hasattr(valves, "SKIP_KEYWORDS") and valves.SKIP_KEYWORDS:
            skip_keywords = valves.SKIP_KEYWORDS

        if valves and hasattr(valves, "TIMEOUT") and valves.TIMEOUT:
            timeout = valves.TIMEOUT
        timeout = max(int(timeout), 1)

        # Resolve base_url for OpenWebUI API calls
        # Priority: request.base_url (with smart fallback to 8080) > env vars (for advanced users)
        base_url = None
        fallback_base_url = "http://localhost:8080"
        
        # First try request.base_url (works for domains, localhost, normal deployments)
        if __request__ and hasattr(__request__, "base_url"):
            base_url = str(__request__.base_url).rstrip("/")
            logger.info("[Batch Install] Primary base_url from request: %s", base_url)
        else:
            base_url = fallback_base_url
            logger.info("[Batch Install] Using fallback base_url: %s", base_url)
        
        # Check for environment variable override (for container mapping issues)
        env_override = os.getenv("OPENWEBUI_URL") or os.getenv("OPENWEBUI_API_BASE_URL")
        if env_override:
            base_url = env_override.rstrip("/")
            logger.info("[Batch Install] Environment variable override applied: %s", base_url)
        
        logger.info("[Batch Install] Initial base_url: %s", base_url)

        api_key = ""
        if __request__ and hasattr(__request__, "headers"):
            auth = __request__.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                api_key = auth.split(" ", 1)[1]

        if not api_key:
            api_key = os.getenv("OPENWEBUI_API_KEY", "")

        if not api_key:
            return await _finalize_message(
                event_emitter, _t(lang, "err_no_api_key"), notification_type="error"
            )

        base_url = base_url.rstrip("/")

        await _emit_status(event_emitter, _t(lang, "status_fetching"), done=False)

        repo_url = f"https://github.com/{repo}"
        candidates, _ = await discover_plugins(repo_url, skip_keywords)

        if not candidates:
            return await _finalize_message(
                event_emitter, _t(lang, "err_no_plugins"), notification_type="error"
            )

        filtered = _filter_candidates(candidates, plugin_types, repo, exclude_keywords)

        if not filtered:
            return await _finalize_message(
                event_emitter, _t(lang, "err_no_match"), notification_type="warning"
            )

        plugin_list = "\n".join([f"- [{c.plugin_type}] {c.title}" for c in filtered])
        hint_msg = _build_confirmation_hint(lang, repo, exclude_keywords)
        confirm_msg = _t(
            lang,
            "confirm_message",
            count=len(filtered),
            plugin_list=plugin_list,
            hint=hint_msg,
        )

        confirmed, confirm_error = await _request_confirmation(
            __event_call__, lang, confirm_msg
        )
        if confirm_error:
            return await _finalize_message(
                event_emitter, confirm_error, notification_type="warning"
            )
        if not confirmed:
            return await _finalize_message(
                event_emitter,
                _t(lang, "confirm_cancelled"),
                notification_type="info",
            )

        await _emit_frontend_debug_log(
            __event_call__,
            "Starting OpenWebUI install requests",
            {
                "repo": repo,
                "base_url": base_url,
                "note": "Backend uses default port 8080 (containerized environment)",
                "plugin_count": len(filtered),
                "plugin_types": plugin_types,
                "exclude_keywords": exclude_keywords,
                "timeout": timeout,
                "has_api_key": bool(api_key),
            },
            level="debug",
        )

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        success_count = 0
        results: List[str] = []
        attempted_fallback = False  # Track if we've already tried fallback

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout), follow_redirects=True
        ) as client:
            for candidate in filtered:
                await _emit_status(
                    event_emitter,
                    _t(
                        lang,
                        "status_installing",
                        type=candidate.plugin_type,
                        title=candidate.title,
                    ),
                    done=False,
                )

                payload = build_payload(candidate)
                update_url, create_url = build_api_urls(base_url, candidate)

                try:
                    await _emit_frontend_debug_log(
                        __event_call__,
                        "Posting plugin install request",
                        {
                            "base_url": base_url,
                            "update_url": update_url,
                            "create_url": create_url,
                            "candidate": _candidate_debug_data(candidate),
                        },
                        level="debug",
                    )
                    update_response = await client.post(
                        update_url,
                        headers=headers,
                        json=payload,
                    )
                    if 200 <= update_response.status_code < 300:
                        success_count += 1
                        results.append(_t(lang, "success_updated", title=candidate.title))
                        continue

                    await _emit_frontend_debug_log(
                        __event_call__,
                        "Update endpoint returned non-2xx; trying create endpoint",
                        {
                            "base_url": base_url,
                            "update_url": update_url,
                            "create_url": create_url,
                            "update_status": update_response.status_code,
                            "update_message": _response_message(update_response),
                            "candidate": _candidate_debug_data(candidate),
                        },
                        level="warn",
                    )
                    create_response = await client.post(
                        create_url,
                        headers=headers,
                        json=payload,
                    )
                    if 200 <= create_response.status_code < 300:
                        success_count += 1
                        results.append(_t(lang, "success_created", title=candidate.title))
                        continue

                    create_error = _response_message(create_response)
                    await _emit_frontend_debug_log(
                        __event_call__,
                        "Create endpoint returned non-2xx",
                        {
                            "base_url": base_url,
                            "update_url": update_url,
                            "create_url": create_url,
                            "update_status": update_response.status_code,
                            "create_status": create_response.status_code,
                            "create_message": create_error,
                            "candidate": _candidate_debug_data(candidate),
                        },
                        level="error",
                    )
                    error_msg = (
                        _t(
                            lang,
                            "error_http_status",
                            status=create_response.status_code,
                            message=create_error,
                        )
                    )
                    results.append(
                        _t(lang, "failed", title=candidate.title, error=error_msg)
                    )
                except httpx.TimeoutException:
                    await _emit_frontend_debug_log(
                        __event_call__,
                        "OpenWebUI request timed out",
                        {
                            "base_url": base_url,
                            "update_url": update_url,
                            "create_url": create_url,
                            "timeout": timeout,
                            "candidate": _candidate_debug_data(candidate),
                        },
                        level="warn",
                    )
                    results.append(
                        _t(
                            lang,
                            "failed",
                            title=candidate.title,
                            error=_t(lang, "error_timeout"),
                        )
                    )
                except httpx.ConnectError as exc:
                    # Smart fallback: if connection fails and we haven't tried fallback yet, switch to 8080
                    if not attempted_fallback and base_url != fallback_base_url and not env_override:
                        logger.warning(
                            "[Batch Install] Connection to %s failed; attempting fallback to %s",
                            base_url,
                            fallback_base_url,
                        )
                        attempted_fallback = True
                        base_url = fallback_base_url
                        
                        await _emit_frontend_debug_log(
                            __event_call__,
                            "Primary base_url failed; switching to fallback",
                            {
                                "failed_base_url": base_url,
                                "fallback_base_url": fallback_base_url,
                                "candidate": _candidate_debug_data(candidate),
                                "error": str(exc),
                            },
                            level="warn",
                        )
                        
                        # Retry this candidate with the fallback base_url
                        logger.info("[Batch Install] Retrying plugin with fallback base_url: %s", candidate.title)
                        update_url, create_url = build_api_urls(base_url, candidate)
                        
                        try:
                            update_response = await client.post(
                                update_url,
                                headers=headers,
                                json=payload,
                            )
                            if 200 <= update_response.status_code < 300:
                                success_count += 1
                                results.append(_t(lang, "success_updated", title=candidate.title))
                                continue
                            
                            create_response = await client.post(
                                create_url,
                                headers=headers,
                                json=payload,
                            )
                            if 200 <= create_response.status_code < 300:
                                success_count += 1
                                results.append(_t(lang, "success_created", title=candidate.title))
                            else:
                                create_error = _response_message(create_response)
                                error_msg = _t(
                                    lang,
                                    "error_http_status",
                                    status=create_response.status_code,
                                    message=create_error,
                                )
                                results.append(
                                    _t(lang, "failed", title=candidate.title, error=error_msg)
                                )
                        except httpx.ConnectError as fallback_exc:
                            # Fallback also failed, cannot recover
                            logger.error("[Batch Install] Fallback retry failed: %s", fallback_exc)
                            await _emit_frontend_debug_log(
                                __event_call__,
                                "OpenWebUI connection failed (both primary and fallback)",
                                {
                                    "primary_base_url": base_url,
                                    "fallback_base_url": fallback_base_url,
                                    "candidate": _candidate_debug_data(candidate),
                                    "error": str(fallback_exc),
                                },
                                level="error",
                            )
                            return await _finalize_message(
                                event_emitter,
                                _t(lang, "err_connection"),
                                notification_type="error",
                            )
                        except Exception as retry_exc:
                            logger.error("[Batch Install] Fallback retry failed with other error: %s", retry_exc)
                            results.append(
                                _t(
                                    lang,
                                    "failed",
                                    title=candidate.title,
                                    error=_t(lang, "error_request_failed", error=str(retry_exc)),
                                )
                            )
                    else:
                        # Already tried fallback or env var is set, cannot recover
                        logger.error(
                            "OpenWebUI connection failed for %s (%s). "
                            "base_url=%s update_url=%s create_url=%s error=%s",
                            candidate.title,
                            candidate.function_id,
                            base_url,
                            update_url,
                            create_url,
                            exc,
                        )
                        await _emit_frontend_debug_log(
                            __event_call__,
                            "OpenWebUI connection failed",
                            {
                                "repo": repo,
                                "base_url": base_url,
                                "update_url": update_url,
                                "create_url": create_url,
                                "timeout": timeout,
                                "candidate": _candidate_debug_data(candidate),
                                "error_type": type(exc).__name__,
                                "error": str(exc),
                                "note": "This API request runs from the OpenWebUI backend process, so localhost refers to the server/container environment.",
                            },
                            level="error",
                        )
                        return await _finalize_message(
                            event_emitter,
                            _t(lang, "err_connection"),
                            notification_type="error",
                        )
                except httpx.HTTPError as exc:
                    await _emit_frontend_debug_log(
                        __event_call__,
                        "OpenWebUI request raised HTTPError",
                        {
                            "base_url": base_url,
                            "update_url": update_url,
                            "create_url": create_url,
                            "candidate": _candidate_debug_data(candidate),
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        },
                        level="error",
                    )
                    results.append(
                        _t(
                            lang,
                            "failed",
                            title=candidate.title,
                            error=_t(lang, "error_request_failed", error=str(exc)),
                        )
                    )

        summary = _t(lang, "status_done", success=success_count, total=len(filtered))
        output = "\n".join(results + [summary])
        notification_type = "success"
        if success_count == 0:
            notification_type = "error"
        elif success_count < len(filtered):
            notification_type = "warning"

        await _emit_status(event_emitter, summary, done=True)
        await _emit_notification(event_emitter, summary, ntype=notification_type)

        return output
