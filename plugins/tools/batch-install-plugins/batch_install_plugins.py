"""
title: Batch Install Plugins from GitHub
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
version: 1.1.0
openwebui_id: c9fd6e80-d58f-4312-8fbb-214d86bbe599
description: One-click batch install plugins from one or more GitHub repositories to your OpenWebUI instance. If a user mentions multiple repositories in one request, combine them into a single tool call.
"""

import ast
import asyncio
import json
import logging
import os
import re
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

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
PROJECT_REPO_URL = "https://github.com/Fu-Jie/openwebui-extensions"
SELF_EXCLUDE_HINT = "batch-install-plugins"
SELF_EXCLUDE_TERMS = (
    SELF_EXCLUDE_HINT,
    "batch install plugins from github",
)
DOCSTRING_PATTERN = re.compile(r'^\s*(?P<quote>"""|\'\'\')\s*(.*?)\s*(?P=quote)', re.DOTALL)
CLASS_PATTERN = re.compile(r'^class (Tools|Filter|Pipe|Action)\s*[\(:]', re.MULTILINE)
EMOJI_PATTERN = re.compile(r'[\U00010000-\U0010ffff]', re.UNICODE)
METADATA_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")

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

SELECTION_DIALOG_TEXTS = {
    "en-US": {
        "select_all": "Select all",
        "clear_all": "Clear all",
        "quick_select": "Filter by type",
        "all_types": "All",
        "repo_filter": "Filter by repository",
        "all_repos": "All repositories",
        "search_label": "Search",
        "search_placeholder": "Search title, description, file path...",
        "no_results": "No plugins match the current filter.",
        "selected_count": "{count} selected",
        "install_selected": "Install Selected",
        "cancel": "Cancel",
        "star_repo": "Star Repo",
        "version_label": "Version",
        "file_label": "File",
        "description_label": "Description",
        "repo_label": "Repository",
    },
    "zh-CN": {
        "select_all": "全选",
        "clear_all": "清空",
        "quick_select": "按类型筛选",
        "all_types": "全部",
        "repo_filter": "按仓库筛选",
        "all_repos": "全部仓库",
        "search_label": "搜索",
        "search_placeholder": "搜索标题、描述、文件路径...",
        "no_results": "当前筛选条件下没有匹配的插件。",
        "selected_count": "已选 {count} 项",
        "install_selected": "安装所选插件",
        "cancel": "取消",
        "star_repo": "Star 仓库",
        "version_label": "版本",
        "file_label": "文件",
        "description_label": "描述",
        "repo_label": "仓库",
    },
    "zh-HK": {
        "select_all": "全選",
        "clear_all": "清空",
        "quick_select": "按類型篩選",
        "all_types": "全部",
        "repo_filter": "按倉庫篩選",
        "all_repos": "全部倉庫",
        "search_label": "搜尋",
        "search_placeholder": "搜尋標題、描述、檔案路徑...",
        "no_results": "目前篩選條件下沒有相符的外掛。",
        "selected_count": "已選 {count} 項",
        "install_selected": "安裝所選外掛",
        "cancel": "取消",
        "star_repo": "Star 倉庫",
        "version_label": "版本",
        "file_label": "檔案",
        "description_label": "描述",
        "repo_label": "倉庫",
    },
    "zh-TW": {
        "select_all": "全選",
        "clear_all": "清空",
        "quick_select": "按類型篩選",
        "all_types": "全部",
        "repo_filter": "按倉庫篩選",
        "all_repos": "全部倉庫",
        "search_label": "搜尋",
        "search_placeholder": "搜尋標題、描述、檔案路徑...",
        "no_results": "目前篩選條件下沒有符合的外掛。",
        "selected_count": "已選 {count} 項",
        "install_selected": "安裝所選外掛",
        "cancel": "取消",
        "star_repo": "Star 倉庫",
        "version_label": "版本",
        "file_label": "檔案",
        "description_label": "描述",
        "repo_label": "倉庫",
    },
    "ko-KR": {
        "select_all": "전체 선택",
        "clear_all": "선택 해제",
        "quick_select": "유형별 필터",
        "all_types": "전체",
        "repo_filter": "저장소별 필터",
        "all_repos": "전체 저장소",
        "search_label": "검색",
        "search_placeholder": "제목, 설명, 파일 경로 검색...",
        "no_results": "현재 필터와 일치하는 플러그인이 없습니다.",
        "selected_count": "{count}개 선택됨",
        "install_selected": "선택한 플러그인 설치",
        "cancel": "취소",
        "star_repo": "저장소 Star",
        "version_label": "버전",
        "file_label": "파일",
        "description_label": "설명",
        "repo_label": "저장소",
    },
    "ja-JP": {
        "select_all": "すべて選択",
        "clear_all": "クリア",
        "quick_select": "タイプで絞り込み",
        "all_types": "すべて",
        "repo_filter": "リポジトリで絞り込み",
        "all_repos": "すべてのリポジトリ",
        "search_label": "検索",
        "search_placeholder": "タイトル、説明、ファイルパスを検索...",
        "no_results": "現在の条件に一致するプラグインはありません。",
        "selected_count": "{count}件を選択",
        "install_selected": "選択したプラグインをインストール",
        "cancel": "キャンセル",
        "star_repo": "リポジトリにスター",
        "version_label": "バージョン",
        "file_label": "ファイル",
        "description_label": "説明",
        "repo_label": "リポジトリ",
    },
    "fr-FR": {
        "select_all": "Tout sélectionner",
        "clear_all": "Tout effacer",
        "quick_select": "Filtrer par type",
        "all_types": "Tous",
        "repo_filter": "Filtrer par dépôt",
        "all_repos": "Tous les dépôts",
        "search_label": "Rechercher",
        "search_placeholder": "Rechercher par titre, description, fichier...",
        "no_results": "Aucun plugin ne correspond au filtre actuel.",
        "selected_count": "{count} sélectionnés",
        "install_selected": "Installer la sélection",
        "cancel": "Annuler",
        "star_repo": "Star le dépôt",
        "version_label": "Version",
        "file_label": "Fichier",
        "description_label": "Description",
        "repo_label": "Dépôt",
    },
    "de-DE": {
        "select_all": "Alle auswählen",
        "clear_all": "Auswahl löschen",
        "quick_select": "Nach Typ filtern",
        "all_types": "Alle",
        "repo_filter": "Nach Repository filtern",
        "all_repos": "Alle Repositories",
        "search_label": "Suchen",
        "search_placeholder": "Titel, Beschreibung, Dateipfad durchsuchen...",
        "no_results": "Keine Plugins entsprechen dem aktuellen Filter.",
        "selected_count": "{count} ausgewählt",
        "install_selected": "Auswahl installieren",
        "cancel": "Abbrechen",
        "star_repo": "Repo mit Stern",
        "version_label": "Version",
        "file_label": "Datei",
        "description_label": "Beschreibung",
        "repo_label": "Repository",
    },
    "es-ES": {
        "select_all": "Seleccionar todo",
        "clear_all": "Limpiar",
        "quick_select": "Filtrar por tipo",
        "all_types": "Todos",
        "repo_filter": "Filtrar por repositorio",
        "all_repos": "Todos los repositorios",
        "search_label": "Buscar",
        "search_placeholder": "Buscar por titulo, descripcion o archivo...",
        "no_results": "Ningun plugin coincide con el filtro actual.",
        "selected_count": "{count} seleccionados",
        "install_selected": "Instalar seleccionados",
        "cancel": "Cancelar",
        "star_repo": "Dar estrella",
        "version_label": "Versión",
        "file_label": "Archivo",
        "description_label": "Descripción",
        "repo_label": "Repositorio",
    },
    "it-IT": {
        "select_all": "Seleziona tutto",
        "clear_all": "Cancella",
        "quick_select": "Filtra per tipo",
        "all_types": "Tutti",
        "repo_filter": "Filtra per repository",
        "all_repos": "Tutti i repository",
        "search_label": "Cerca",
        "search_placeholder": "Cerca per titolo, descrizione o file...",
        "no_results": "Nessun plugin corrisponde al filtro attuale.",
        "selected_count": "{count} selezionati",
        "install_selected": "Installa selezionati",
        "cancel": "Annulla",
        "star_repo": "Metti una stella",
        "version_label": "Versione",
        "file_label": "File",
        "description_label": "Descrizione",
        "repo_label": "Repository",
    },
    "vi-VN": {
        "select_all": "Chọn tất cả",
        "clear_all": "Bỏ chọn",
        "quick_select": "Lọc theo loại",
        "all_types": "Tất cả",
        "repo_filter": "Lọc theo kho",
        "all_repos": "Tất cả kho",
        "search_label": "Tìm kiếm",
        "search_placeholder": "Tìm theo tiêu đề, mô tả, đường dẫn tệp...",
        "no_results": "Không có plugin nào khớp với bộ lọc hiện tại.",
        "selected_count": "Đã chọn {count}",
        "install_selected": "Cài đặt mục đã chọn",
        "cancel": "Hủy",
        "star_repo": "Star kho",
        "version_label": "Phiên bản",
        "file_label": "Tệp",
        "description_label": "Mô tả",
        "repo_label": "Kho",
    },
}


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


def _selection_t(lang: str, key: str, **kwargs) -> str:
    lang_key = _resolve_language(lang)
    text = SELECTION_DIALOG_TEXTS.get(
        lang_key, SELECTION_DIALOG_TEXTS["en-US"]
    ).get(key, SELECTION_DIALOG_TEXTS["en-US"][key])
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
        source_repo: str,
    ):
        self.plugin_type = plugin_type
        self.file_path = file_path
        self.metadata = metadata
        self.content = content
        self.function_id = function_id
        self.source_repo = source_repo

    @property
    def title(self) -> str:
        return self.metadata.get("title", Path(self.file_path).stem)

    @property
    def version(self) -> str:
        return self.metadata.get("version", "unknown")

    @property
    def selection_id(self) -> str:
        return f"{self.source_repo}::{self.file_path}::{self.function_id}"


def extract_metadata(content: str) -> Dict[str, str]:
    docstring = _extract_module_docstring(content)
    if not docstring:
        return {}

    metadata: Dict[str, str] = {}
    lines = docstring.splitlines()
    index = 0

    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()

        if not stripped or stripped.startswith("#"):
            index += 1
            continue

        if raw_line[:1].isspace() or ":" not in raw_line:
            index += 1
            continue

        key, value = raw_line.split(":", 1)
        key = key.strip().lower()
        if not METADATA_KEY_PATTERN.match(key):
            index += 1
            continue

        value = value.strip()
        if value and value[0] in {">", "|"}:
            block_lines, index = _consume_indented_block(lines, index + 1)
            metadata[key] = (
                _fold_yaml_block(block_lines)
                if value[0] == ">"
                else _preserve_yaml_block(block_lines)
            )
            continue

        metadata[key] = value
        index += 1

    return metadata


def _extract_module_docstring(content: str) -> str:
    normalized = content.lstrip("\ufeff")

    try:
        module = ast.parse(normalized)
    except SyntaxError:
        module = None

    if module is not None:
        docstring = ast.get_docstring(module, clean=False)
        if isinstance(docstring, str):
            return docstring

    fallback = normalized.replace("\r\n", "\n").replace("\r", "\n")
    match = DOCSTRING_PATTERN.search(fallback)
    return match.group(2) if match else ""


def _consume_indented_block(lines: List[str], start_index: int) -> Tuple[List[str], int]:
    block: List[str] = []
    index = start_index

    while index < len(lines):
        line = lines[index]
        if not line.strip():
            block.append("")
            index += 1
            continue
        if line[:1].isspace():
            block.append(line)
            index += 1
            continue
        break

    dedented = textwrap.dedent("\n".join(block)).splitlines()
    return dedented, index


def _fold_yaml_block(lines: List[str]) -> str:
    paragraphs: List[str] = []
    current: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(stripped)

    if current:
        paragraphs.append(" ".join(current))

    return "\n\n".join(paragraphs).strip()


def _preserve_yaml_block(lines: List[str]) -> str:
    return "\n".join(line.rstrip() for line in lines).strip()


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
        "source_repo": candidate.source_repo,
        "file_path": candidate.file_path,
        "function_id": candidate.function_id,
        "version": candidate.version,
    }


def _parse_repo_inputs(repo_value: str) -> List[str]:
    parts = re.split(r"[\n,;，；、]+", str(repo_value or DEFAULT_REPO))
    repos: List[str] = []
    seen: Set[str] = set()

    for part in parts:
        candidate = part.strip().strip("/")
        if not candidate:
            continue
        normalized = candidate.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        repos.append(candidate)

    return repos or [DEFAULT_REPO]


def _sort_candidates_by_repo_order(
    candidates: List[PluginCandidate],
    repos: List[str],
) -> List[PluginCandidate]:
    repo_order = {repo.lower(): index for index, repo in enumerate(repos)}
    fallback_index = len(repo_order)
    return sorted(
        candidates,
        key=lambda item: (
            repo_order.get(item.source_repo.lower(), fallback_index),
            item.source_repo.lower(),
            item.plugin_type,
            item.file_path,
        ),
    )


def _filter_candidates(
    candidates: List[PluginCandidate],
    plugin_types: List[str],
    repos: List[str],
    exclude_keywords: str = "",
) -> List[PluginCandidate]:
    allowed_types = {item.strip().lower() for item in plugin_types if item.strip()}
    filtered = [c for c in candidates if c.plugin_type.lower() in allowed_types]

    includes_default_repo = any(item.lower() == DEFAULT_REPO.lower() for item in repos)
    if includes_default_repo:
        filtered = [
            c
            for c in filtered
            if not (c.source_repo.lower() == DEFAULT_REPO.lower() and _matches_self_plugin(c))
        ]

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
    repo_list = _parse_repo_inputs(repo)
    is_default_repo = any(item.lower() == DEFAULT_REPO.lower() for item in repo_list)
    excluded_parts: List[str] = []

    if exclude_keywords:
        excluded_parts.append(exclude_keywords)
    if is_default_repo:
        excluded_parts.append(SELF_EXCLUDE_HINT)

    if excluded_parts:
        return _t(lang, "confirm_excluded_hint", excluded=", ".join(excluded_parts))

    return ""


def _build_selection_dialog_js(
    options: List[Dict[str, str]],
    ui_text: Dict[str, str],
) -> str:
    lines = [
        "return new Promise((resolve) => {",
        "    try {",
        f"        const options = {json.dumps(options, ensure_ascii=False)};",
        f"        const ui = {json.dumps(ui_text, ensure_ascii=False)};",
        "        const dialogId = 'batch-install-plugin-selector';",
        "        const body = typeof document !== 'undefined' ? document.body : null;",
        "        const existing = body ? document.getElementById(dialogId) : null;",
        "        if (existing) { existing.remove(); }",
        "        if (!body) {",
        "            resolve({ confirmed: false, error: 'document.body unavailable', selected_ids: [] });",
        "            return;",
        "        }",
        "        const selected = new Set(options.map((item) => item.id));",
        "        let activeFilter = '';",
        "        let activeRepoFilter = '';",
        "        let searchTerm = '';",
        "        const escapeHtml = (value) => String(value ?? '').replace(/[&<>\"']/g, (char) => ({",
        "            '&': '&amp;',",
        "            '<': '&lt;',",
        "            '>': '&gt;',",
        "            '\"': '&quot;',",
        "            \"'\": '&#39;',",
        "        }[char]));",
        "        const overlay = document.createElement('div');",
        "        overlay.id = dialogId;",
        "        overlay.style.cssText = [",
        "            'position:fixed',",
        "            'inset:0',",
        "            'padding:24px',",
        "            'background:rgba(15,23,42,0.52)',",
        "            'backdrop-filter:blur(3px)',",
        "            'display:flex',",
        "            'align-items:center',",
        "            'justify-content:center',",
        "            'z-index:9999',",
        "            'box-sizing:border-box',",
        "        ].join(';');",
        "        overlay.innerHTML = `",
        "            <div style=\"width:min(920px,100%);max-height:min(88vh,900px);overflow:hidden;border-radius:18px;background:#ffffff;box-shadow:0 30px 80px rgba(15,23,42,0.28);display:flex;flex-direction:column;font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif\">",
        "                <div style=\"padding:22px 24px 16px;border-bottom:1px solid #e5e7eb\">",
        "                    <div style=\"display:flex;justify-content:space-between;gap:14px;align-items:flex-start;flex-wrap:wrap\">",
        "                        <div>",
        "                            <div style=\"font-size:22px;font-weight:700;color:#0f172a\">${escapeHtml(ui.title)}</div>",
        "                            <div style=\"margin-top:8px;font-size:14px;color:#475569\">${escapeHtml(ui.list_title)}</div>",
        "                        </div>",
        "                        <a href=\"${escapeHtml(ui.project_repo_url)}\" target=\"_blank\" rel=\"noopener noreferrer\" title=\"${escapeHtml(ui.star_repo)}\" style=\"display:inline-flex;align-items:center;gap:8px;padding:8px 12px;border:1px solid #fde68a;border-radius:999px;background:#fffbeb;color:#92400e;font-size:13px;font-weight:700;text-decoration:none;box-shadow:0 1px 2px rgba(15,23,42,0.04)\">",
        "                            <svg width=\"15\" height=\"15\" viewBox=\"0 0 24 24\" fill=\"currentColor\" aria-hidden=\"true\"><path d=\"M12 2.75l2.85 5.78 6.38.93-4.61 4.49 1.09 6.35L12 17.31l-5.71 2.99 1.09-6.35-4.61-4.49 6.38-.93L12 2.75z\"></path></svg>",
        "                            <span>${escapeHtml(ui.star_repo)}</span>",
        "                        </a>",
        "                    </div>",
        "                    <div id=\"batch-install-plugin-selector-hint\" style=\"margin-top:14px;padding:12px 14px;border-radius:12px;background:#f8fafc;color:#334155;font-size:13px;line-height:1.5;white-space:pre-wrap\"></div>",
        "                </div>",
        "                <div style=\"padding:16px 24px 0;display:grid;gap:12px\">",
        "                    <div style=\"display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap\">",
        "                        <div style=\"display:flex;gap:8px;flex-wrap:wrap\">",
        "                        <button id=\"batch-install-plugin-selector-select-all\" style=\"padding:8px 12px;border:1px solid #cbd5e1;border-radius:10px;background:#fff;color:#0f172a;font-size:13px;cursor:pointer\">${escapeHtml(ui.select_all)}</button>",
        "                        <button id=\"batch-install-plugin-selector-clear-all\" style=\"padding:8px 12px;border:1px solid #cbd5e1;border-radius:10px;background:#fff;color:#0f172a;font-size:13px;cursor:pointer\">${escapeHtml(ui.clear_all)}</button>",
        "                        </div>",
        "                        <div id=\"batch-install-plugin-selector-count\" style=\"font-size:13px;font-weight:600;color:#475569\"></div>",
        "                    </div>",
        "                    <div style=\"display:grid;gap:10px\">",
        "                        <div style=\"display:flex;gap:10px;align-items:center;flex-wrap:wrap\">",
        "                            <div style=\"font-size:12px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.04em\">${escapeHtml(ui.quick_select)}</div>",
        "                            <div id=\"batch-install-plugin-selector-types\" style=\"display:flex;gap:8px;flex-wrap:wrap\"></div>",
        "                        </div>",
        "                        <div id=\"batch-install-plugin-selector-repo-row\" style=\"display:flex;gap:10px;align-items:center;flex-wrap:wrap\">",
        "                            <div style=\"font-size:12px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.04em\">${escapeHtml(ui.repo_filter)}</div>",
        "                            <div id=\"batch-install-plugin-selector-repos\" style=\"display:flex;gap:8px;flex-wrap:wrap\"></div>",
        "                        </div>",
        "                        <div style=\"display:grid;gap:6px\">",
        "                            <div style=\"font-size:12px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.04em\">${escapeHtml(ui.search_label)}</div>",
        "                            <input id=\"batch-install-plugin-selector-search\" type=\"text\" placeholder=\"${escapeHtml(ui.search_placeholder)}\" style=\"width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:12px;background:#fff;color:#0f172a;font-size:14px;outline:none;box-sizing:border-box\" />",
        "                        </div>",
        "                    </div>",
        "                </div>",
        "                <div id=\"batch-install-plugin-selector-list\" style=\"padding:16px 24px 0;overflow:auto;display:grid;gap:12px;flex:1;min-height:0\"></div>",
        "                <div style=\"padding:18px 24px 24px;border-top:1px solid #e5e7eb;margin-top:18px;display:flex;justify-content:flex-end;gap:12px;flex-wrap:wrap\">",
        "                    <button id=\"batch-install-plugin-selector-cancel\" style=\"padding:10px 16px;border:1px solid #cbd5e1;border-radius:10px;background:#fff;color:#0f172a;font-weight:600;cursor:pointer\">${escapeHtml(ui.cancel)}</button>",
        "                    <button id=\"batch-install-plugin-selector-submit\" style=\"padding:10px 16px;border:none;border-radius:10px;background:#0f172a;color:#fff;font-weight:600;cursor:pointer\">${escapeHtml(ui.install_selected)}</button>",
        "                </div>",
        "            </div>",
        "        `;",
        "        body.appendChild(overlay);",
        "        const previousOverflow = body.style.overflow;",
        "        body.style.overflow = 'hidden';",
        "        const listEl = overlay.querySelector('#batch-install-plugin-selector-list');",
        "        const countEl = overlay.querySelector('#batch-install-plugin-selector-count');",
        "        const hintEl = overlay.querySelector('#batch-install-plugin-selector-hint');",
        "        const typesEl = overlay.querySelector('#batch-install-plugin-selector-types');",
        "        const repoRowEl = overlay.querySelector('#batch-install-plugin-selector-repo-row');",
        "        const reposEl = overlay.querySelector('#batch-install-plugin-selector-repos');",
        "        const searchInput = overlay.querySelector('#batch-install-plugin-selector-search');",
        "        const submitBtn = overlay.querySelector('#batch-install-plugin-selector-submit');",
        "        const cancelBtn = overlay.querySelector('#batch-install-plugin-selector-cancel');",
        "        const selectAllBtn = overlay.querySelector('#batch-install-plugin-selector-select-all');",
        "        const clearAllBtn = overlay.querySelector('#batch-install-plugin-selector-clear-all');",
        "        const typeMap = options.reduce((groups, item) => {",
        "            if (!groups[item.type]) {",
        "                groups[item.type] = [];",
        "            }",
        "            groups[item.type].push(item);",
        "            return groups;",
        "        }, {});",
        "        const repoMap = options.reduce((groups, item) => {",
        "            if (!groups[item.repo]) {",
        "                groups[item.repo] = [];",
        "            }",
        "            groups[item.repo].push(item);",
        "            return groups;",
        "        }, {});",
        "        const typeEntries = Object.entries(typeMap);",
        "        const repoEntries = Object.entries(repoMap);",
        "        const matchesSearch = (item) => {",
        "            const haystack = [item.title, item.description, item.file_path, item.type, item.repo].join(' ').toLowerCase();",
        "            return !searchTerm || haystack.includes(searchTerm);",
        "        };",
        "        const getVisibleOptions = () => options.filter((item) => {",
        "            const matchesType = !activeFilter || item.type === activeFilter;",
        "            const matchesRepo = !activeRepoFilter || item.repo === activeRepoFilter;",
        "            return matchesType && matchesRepo && matchesSearch(item);",
        "        });",
        "        const syncSelectionToVisible = () => {",
        "            selected.clear();",
        "            getVisibleOptions().forEach((item) => selected.add(item.id));",
        "        };",
        "        const formatMultilineText = (value) => escapeHtml(value).replace(/\\n+/g, '<br />');",
        "        hintEl.textContent = ui.hint || '';",
        "        hintEl.style.display = ui.hint ? 'block' : 'none';",
        "        const renderTypeButtons = () => {",
        "            const scopedOptions = options.filter((item) => {",
        "                const matchesRepo = !activeRepoFilter || item.repo === activeRepoFilter;",
        "                return matchesRepo && matchesSearch(item);",
        "            });",
        "            const filterEntries = [['', scopedOptions], ...typeEntries.map(([type]) => [type, scopedOptions.filter((item) => item.type === type)])];",
        "            typesEl.innerHTML = filterEntries.map(([type, items]) => {",
        "                const isActive = activeFilter === type;",
        "                const background = isActive ? '#0f172a' : '#ffffff';",
        "                const color = isActive ? '#ffffff' : '#0f172a';",
        "                const border = isActive ? '#0f172a' : '#cbd5e1';",
        "                const label = type || ui.all_types;",
        "                return `",
        "                    <button type=\"button\" data-plugin-type=\"${escapeHtml(type)}\" style=\"padding:7px 12px;border:1px solid ${border};border-radius:999px;background:${background};color:${color};font-size:12px;font-weight:700;cursor:pointer;display:inline-flex;gap:8px;align-items:center\">",
        "                        <span>${escapeHtml(label)}</span>",
        "                        <span style=\"display:inline-flex;align-items:center;justify-content:center;min-width:20px;height:20px;padding:0 6px;border-radius:999px;background:${isActive ? 'rgba(255,255,255,0.16)' : '#e2e8f0'};color:${isActive ? '#ffffff' : '#334155'}\">${items.length}</span>",
        "                    </button>",
        "                `;",
        "            }).join('');",
        "            typesEl.querySelectorAll('button[data-plugin-type]').forEach((button) => {",
        "                button.addEventListener('click', () => {",
        "                    const pluginType = button.getAttribute('data-plugin-type') || '';",
        "                    activeFilter = activeFilter === pluginType ? '' : pluginType;",
        "                    syncSelectionToVisible();",
        "                    renderList();",
        "                });",
        "            });",
        "        };",
        "        const renderRepoButtons = () => {",
        "            if (repoEntries.length <= 1) {",
        "                repoRowEl.style.display = 'none';",
        "                reposEl.innerHTML = '';",
        "                activeRepoFilter = '';",
        "                return;",
        "            }",
        "            repoRowEl.style.display = 'flex';",
        "            const scopedOptions = options.filter((item) => {",
        "                const matchesType = !activeFilter || item.type === activeFilter;",
        "                return matchesType && matchesSearch(item);",
        "            });",
        "            const filterEntries = [['', scopedOptions], ...repoEntries.map(([repoName]) => [repoName, scopedOptions.filter((item) => item.repo === repoName)])];",
        "            reposEl.innerHTML = filterEntries.map(([repoName, items]) => {",
        "                const isActive = activeRepoFilter === repoName;",
        "                const background = isActive ? '#1d4ed8' : '#ffffff';",
        "                const color = isActive ? '#ffffff' : '#1d4ed8';",
        "                const border = isActive ? '#1d4ed8' : '#bfdbfe';",
        "                const label = repoName || ui.all_repos;",
        "                return `",
        "                    <button type=\"button\" data-plugin-repo=\"${escapeHtml(repoName)}\" style=\"padding:7px 12px;border:1px solid ${border};border-radius:999px;background:${background};color:${color};font-size:12px;font-weight:700;cursor:pointer;display:inline-flex;gap:8px;align-items:center\">",
        "                        <span>${escapeHtml(label)}</span>",
        "                        <span style=\"display:inline-flex;align-items:center;justify-content:center;min-width:20px;height:20px;padding:0 6px;border-radius:999px;background:${isActive ? 'rgba(255,255,255,0.16)' : '#dbeafe'};color:${isActive ? '#ffffff' : '#1e3a8a'}\">${items.length}</span>",
        "                    </button>",
        "                `;",
        "            }).join('');",
        "            reposEl.querySelectorAll('button[data-plugin-repo]').forEach((button) => {",
        "                button.addEventListener('click', () => {",
        "                    const repoName = button.getAttribute('data-plugin-repo') || '';",
        "                    activeRepoFilter = activeRepoFilter === repoName ? '' : repoName;",
        "                    syncSelectionToVisible();",
        "                    renderList();",
        "                });",
        "            });",
        "        };",
        "        const updateState = () => {",
        "            countEl.textContent = ui.selected_count.replace('{count}', String(selected.size));",
        "            submitBtn.disabled = selected.size === 0;",
        "            submitBtn.style.opacity = selected.size === 0 ? '0.45' : '1';",
        "            submitBtn.style.cursor = selected.size === 0 ? 'not-allowed' : 'pointer';",
        "            renderTypeButtons();",
        "            renderRepoButtons();",
        "        };",
        "        const renderOptionCard = (item) => {",
        "            const checked = selected.has(item.id) ? 'checked' : '';",
        "            const description = item.description ? `",
        "                <div style=\"display:grid;gap:4px\">",
        "                    <div style=\"font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.04em\">${escapeHtml(ui.description_label)}</div>",
        "                    <div style=\"font-size:13px;color:#334155;line-height:1.55;word-break:break-word\">${formatMultilineText(item.description)}</div>",
        "                </div>",
        "            ` : '';",
        "            return `",
        "                <label style=\"display:flex;gap:14px;align-items:flex-start;padding:14px;border:1px solid #e2e8f0;border-radius:14px;background:#fff;cursor:pointer\">",
        "                    <input type=\"checkbox\" data-plugin-id=\"${escapeHtml(item.id)}\" ${checked} style=\"margin-top:3px;width:16px;height:16px;accent-color:#0f172a;flex-shrink:0\" />",
        "                    <div style=\"min-width:0;display:grid;gap:6px\">",
        "                        <div style=\"display:flex;gap:10px;align-items:center;flex-wrap:wrap\">",
        "                            <span style=\"display:inline-flex;align-items:center;padding:2px 8px;border-radius:999px;background:#f1f5f9;color:#334155;font-size:12px;font-weight:700;text-transform:uppercase\">${escapeHtml(item.type)}</span>",
        "                            <span style=\"display:inline-flex;align-items:center;padding:2px 8px;border-radius:999px;background:#eff6ff;color:#1d4ed8;font-size:12px;font-weight:700\">${escapeHtml(item.repo)}</span>",
        "                            <span style=\"font-size:15px;font-weight:700;color:#0f172a;word-break:break-word\">${escapeHtml(item.title)}</span>",
        "                        </div>",
        "                        <div style=\"font-size:12px;color:#475569;word-break:break-word\">${escapeHtml(ui.version_label)}: ${escapeHtml(item.version)} · ${escapeHtml(ui.file_label)}: ${escapeHtml(item.file_path)}</div>",
        "                        ${description}",
        "                    </div>",
        "                </label>",
        "            `;",
        "        };",
        "        const renderList = () => {",
        "            const visibleOptions = getVisibleOptions();",
        "            if (!visibleOptions.length) {",
        "                listEl.innerHTML = `<div style=\"padding:24px;border:1px dashed #cbd5e1;border-radius:14px;background:#f8fafc;color:#475569;font-size:14px;text-align:center\">${escapeHtml(ui.no_results)}</div>`;",
        "                updateState();",
        "                return;",
        "            }",
        "            const groups = visibleOptions.reduce((bucket, item) => {",
        "                if (!bucket[item.repo]) {",
        "                    bucket[item.repo] = [];",
        "                }",
        "                bucket[item.repo].push(item);",
        "                return bucket;",
        "            }, {});",
        "            listEl.innerHTML = Object.entries(groups).map(([repoName, items]) => `",
        "                <section style=\"display:grid;gap:10px\">",
        "                    <div style=\"display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap;padding:0 2px\">",
        "                        <div style=\"display:inline-flex;align-items:center;gap:8px;padding:6px 12px;border-radius:999px;background:#eff6ff;color:#1d4ed8;font-size:12px;font-weight:700;word-break:break-word\">${escapeHtml(repoName)}</div>",
        "                        <div style=\"display:inline-flex;align-items:center;gap:8px;padding:4px 10px;border-radius:999px;background:#f8fafc;color:#475569;font-size:12px;font-weight:600\">${items.length}</div>",
        "                    </div>",
        "                    <div style=\"display:grid;gap:12px\">${items.map((item) => renderOptionCard(item)).join('')}</div>",
        "                </section>",
        "            `).join('');",
        "            listEl.querySelectorAll('input[data-plugin-id]').forEach((input) => {",
        "                input.addEventListener('change', () => {",
        "                    const pluginId = input.getAttribute('data-plugin-id') || '';",
        "                    if (input.checked) {",
        "                        selected.add(pluginId);",
        "                    } else {",
        "                        selected.delete(pluginId);",
        "                    }",
        "                    updateState();",
        "                });",
        "            });",
        "            updateState();",
        "        };",
        "        const cleanup = () => {",
        "            body.style.overflow = previousOverflow;",
        "            window.removeEventListener('keydown', onKeyDown, true);",
        "            overlay.remove();",
        "        };",
        "        const finish = (confirmed) => {",
        "            const selectedIds = confirmed ? options.filter((item) => selected.has(item.id)).map((item) => item.id) : [];",
        "            cleanup();",
        "            resolve({ confirmed, selected_ids: selectedIds });",
        "        };",
        "        const onKeyDown = (event) => {",
        "            if (event.key === 'Escape') {",
        "                event.preventDefault();",
        "                finish(false);",
        "            }",
        "        };",
        "        overlay.addEventListener('click', (event) => {",
        "            if (event.target === overlay) {",
        "                finish(false);",
        "            }",
        "        });",
        "        selectAllBtn.addEventListener('click', () => {",
        "            getVisibleOptions().forEach((item) => selected.add(item.id));",
        "            renderList();",
        "        });",
        "        clearAllBtn.addEventListener('click', () => {",
        "            getVisibleOptions().forEach((item) => selected.delete(item.id));",
        "            renderList();",
        "        });",
        "        searchInput.addEventListener('input', () => {",
        "            searchTerm = searchInput.value.trim().toLowerCase();",
        "            syncSelectionToVisible();",
        "            renderList();",
        "        });",
        "        cancelBtn.addEventListener('click', () => finish(false));",
        "        submitBtn.addEventListener('click', () => {",
        "            if (selected.size === 0) {",
        "                updateState();",
        "                return;",
        "            }",
        "            finish(true);",
        "        });",
        "        window.addEventListener('keydown', onKeyDown, true);",
        "        renderList();",
        "    } catch (error) {",
        "        console.error('[Batch Install] Plugin selection dialog failed', error);",
        "        resolve({",
        "            confirmed: false,",
        "            error: error instanceof Error ? error.message : String(error),",
        "            selected_ids: [],",
        "        });",
        "    }",
        "});",
    ]
    return "\n".join(lines)


async def _request_plugin_selection(
    event_call: Optional[Any],
    lang: str,
    candidates: List[PluginCandidate],
    hint: str,
) -> Tuple[Optional[List[PluginCandidate]], Optional[str]]:
    if not event_call:
        return candidates, None

    options = [
        {
            "id": candidate.selection_id,
            "title": candidate.title,
            "type": candidate.plugin_type,
            "repo": candidate.source_repo,
            "version": candidate.version,
            "file_path": candidate.file_path,
            "description": candidate.metadata.get("description", ""),
        }
        for candidate in candidates
    ]
    ui_text = {
        "title": _t(lang, "confirm_title"),
        "list_title": _t(lang, "status_list_title", count=len(candidates)),
        "repo_label": _selection_t(lang, "repo_label"),
        "hint": hint.strip(),
        "select_all": _selection_t(lang, "select_all"),
        "clear_all": _selection_t(lang, "clear_all"),
        "quick_select": _selection_t(lang, "quick_select"),
        "all_types": _selection_t(lang, "all_types"),
        "repo_filter": _selection_t(lang, "repo_filter"),
        "all_repos": _selection_t(lang, "all_repos"),
        "star_repo": _selection_t(lang, "star_repo"),
        "project_repo_url": PROJECT_REPO_URL,
        "search_label": _selection_t(lang, "search_label"),
        "search_placeholder": _selection_t(lang, "search_placeholder"),
        "no_results": _selection_t(lang, "no_results"),
        "selected_count": _selection_t(lang, "selected_count", count="{count}"),
        "install_selected": _selection_t(lang, "install_selected"),
        "cancel": _selection_t(lang, "cancel"),
        "version_label": _selection_t(lang, "version_label"),
        "file_label": _selection_t(lang, "file_label"),
        "description_label": _selection_t(lang, "description_label"),
    }
    js_code = _build_selection_dialog_js(options, ui_text)

    try:
        result = await asyncio.wait_for(
            event_call({"type": "execute", "data": {"code": js_code}}),
            timeout=CONFIRMATION_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning("Installation selection dialog timed out.")
        return None, _t(lang, "err_confirm_unavailable")
    except Exception as exc:
        logger.warning("Installation selection dialog failed: %s", exc)
        return None, _t(lang, "err_confirm_unavailable")

    if not isinstance(result, dict):
        logger.warning("Unexpected selection dialog result: %r", result)
        return None, _t(lang, "err_confirm_unavailable")

    if result.get("error"):
        logger.warning("Selection dialog returned error: %s", result.get("error"))
        return None, _t(lang, "err_confirm_unavailable")

    if not result.get("confirmed"):
        return [], None

    selected_ids = result.get("selected_ids")
    if not isinstance(selected_ids, list):
        logger.warning("Selection dialog returned invalid selected_ids: %r", selected_ids)
        return None, _t(lang, "err_confirm_unavailable")

    selected_id_set = {str(item).strip() for item in selected_ids if str(item).strip()}
    selected_candidates = [
        candidate for candidate in candidates if candidate.selection_id in selected_id_set
    ]
    return selected_candidates, None


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
    source_repo: str = "",
) -> Tuple[List[PluginCandidate], List[Tuple[str, str]]]:
    parsed = parse_github_url(url)
    if not parsed:
        return [], [("url", "invalid github url")]
    owner, repo, branch = parsed
    resolved_repo = source_repo or f"{owner}/{repo}"

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

            if is_default_repo and has_emoji(metadata.get("title", "")):
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
                    source_repo=resolved_repo,
                )
            )

    candidates.sort(key=lambda x: (x.plugin_type, x.file_path))
    return candidates, skipped


async def discover_plugins_from_repos(
    repos: List[str],
    skip_keywords: str = "test",
) -> Tuple[List[PluginCandidate], List[Tuple[str, str]]]:
    tasks = [
        discover_plugins(f"https://github.com/{repo}", skip_keywords, source_repo=repo)
        for repo in repos
    ]
    results = await asyncio.gather(*tasks)

    all_candidates: List[PluginCandidate] = []
    all_skipped: List[Tuple[str, str]] = []

    for repo, (candidates, skipped) in zip(repos, results):
        all_candidates.extend(candidates)
        all_skipped.extend([(f"{repo}:{path}", reason) for path, reason in skipped])

    return _sort_candidates_by_repo_order(all_candidates, repos), all_skipped


class ListParams(BaseModel):
    repo: str = Field(
        default=DEFAULT_REPO,
        description="One or more GitHub repositories (owner/repo), separated by commas, semicolons, or new lines. If the user mentions multiple repositories in one request, combine them here and call the tool once.",
    )
    plugin_types: List[str] = Field(
        default=["pipe", "action", "filter", "tool"],
        description="Plugin types to list (pipe, action, filter, tool)",
    )


class InstallParams(BaseModel):
    repo: str = Field(
        default=DEFAULT_REPO,
        description="One or more GitHub repositories (owner/repo), separated by commas, semicolons, or new lines. If the user mentions multiple repositories in one request, combine them here and call the tool once instead of making separate calls.",
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
        """List plugins from one or more repositories in a single call.

        If a user request mentions multiple repositories, combine them into the
        `repo` argument instead of calling this tool multiple times.
        """
        user_ctx = await _get_user_context(__user__, __event_call__, __request__)
        lang = user_ctx.get("user_language", "en-US")

        skip_keywords = DEFAULT_SKIP_KEYWORDS
        if valves and hasattr(valves, "SKIP_KEYWORDS") and valves.SKIP_KEYWORDS:
            skip_keywords = valves.SKIP_KEYWORDS

        repo_list = _parse_repo_inputs(repo)
        candidates, _ = await discover_plugins_from_repos(repo_list, skip_keywords)

        if not candidates:
            return _t(lang, "err_no_plugins")

        filtered = _filter_candidates(candidates, plugin_types, repo_list)
        if not filtered:
            return _t(lang, "err_no_match")

        lines = [f"## {_t(lang, 'status_list_title', count=len(filtered))}\n"]
        current_repo = ""
        for c in filtered:
            if c.source_repo != current_repo:
                lines.append(f"\n### {c.source_repo}")
                current_repo = c.source_repo
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
        """Install plugins from one or more repositories in a single call.

        If a user request mentions multiple repositories, combine them into the
        `repo` argument and call this tool once instead of making parallel
        calls for each repository.
        """
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

        repo_list = _parse_repo_inputs(repo)
        candidates, _ = await discover_plugins_from_repos(repo_list, skip_keywords)

        if not candidates:
            return await _finalize_message(
                event_emitter, _t(lang, "err_no_plugins"), notification_type="error"
            )

        filtered = _filter_candidates(candidates, plugin_types, repo_list, exclude_keywords)

        if not filtered:
            return await _finalize_message(
                event_emitter, _t(lang, "err_no_match"), notification_type="warning"
            )

        hint_msg = _build_confirmation_hint(lang, repo, exclude_keywords)
        selected_candidates, confirm_error = await _request_plugin_selection(
            __event_call__, lang, filtered, hint_msg
        )
        if confirm_error:
            return await _finalize_message(
                event_emitter, confirm_error, notification_type="warning"
            )
        if not selected_candidates:
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
                "repos": repo_list,
                "base_url": base_url,
                "note": "Backend uses default port 8080 (containerized environment)",
                "plugin_count": len(selected_candidates),
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
            for candidate in selected_candidates:
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

        summary = _t(
            lang,
            "status_done",
            success=success_count,
            total=len(selected_candidates),
        )
        output = "\n".join(results + [summary])
        notification_type = "success"
        if success_count == 0:
            notification_type = "error"
        elif success_count < len(selected_candidates):
            notification_type = "warning"

        await _emit_status(event_emitter, summary, done=True)
        await _emit_notification(event_emitter, summary, ntype=notification_type)

        return output
