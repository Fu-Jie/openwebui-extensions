"""
title: OpenWebUI Skills Manager Tool
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
version: 0.2.1
openwebui_id: b4bce8e4-08e7-4f90-bea7-dc31d463a0bb
requirements:
description: Standalone OpenWebUI tool for managing native Workspace Skills (list/show/install/create/update/delete) for any model.
"""

import asyncio
import json
import logging
import re
import tempfile
import tarfile
import uuid
import zipfile
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

try:
    from open_webui.models.skills import Skills, SkillForm, SkillMeta
except Exception:
    Skills = None
    SkillForm = None
    SkillMeta = None


BASE_TRANSLATIONS = {
    "status_listing": "Listing your skills...",
    "status_showing": "Reading skill details...",
    "status_installing": "Installing skill from URL...",
    "status_installing_batch": "Installing {total} skill(s)...",
    "status_discovering_skills": "Discovering skills in {url}...",
    "status_creating": "Creating skill...",
    "status_updating": "Updating skill...",
    "status_deleting": "Deleting skill...",
    "status_done": "Done.",
    "status_list_done": "Found {count} skills ({active_count} active).",
    "status_show_done": "Loaded skill: {name}.",
    "status_install_done": "Installed skill: {name}.",
    "status_install_overwrite_done": "Installed by updating existing skill: {name}.",
    "status_create_done": "Created skill: {name}.",
    "status_create_overwrite_done": "Updated existing skill: {name}.",
    "status_update_done": "Updated skill: {name}.",
    "status_delete_done": "Deleted skill: {name}.",
    "status_install_batch_done": "Batch install completed: {succeeded} succeeded, {failed} failed.",
    "err_unavailable": "OpenWebUI Skills model is unavailable in this runtime.",
    "err_user_required": "User context is required.",
    "err_name_required": "Skill name is required.",
    "err_not_found": "Skill not found.",
    "err_no_update_fields": "No update fields provided.",
    "err_url_required": "Skill URL is required.",
    "err_install_fetch": "Failed to fetch skill content from URL.",
    "err_install_parse": "Failed to parse skill package/content.",
    "err_invalid_url": "Invalid URL. Only http(s) URLs are supported.",
    "msg_created": "Skill created successfully.",
    "msg_updated": "Skill updated successfully.",
    "msg_deleted": "Skill deleted successfully.",
    "msg_installed": "Skill installed successfully.",
}

TRANSLATIONS = {
    "en-US": BASE_TRANSLATIONS,
    "zh-CN": {
        "status_listing": "正在列出你的技能...",
        "status_showing": "正在读取技能详情...",
        "status_installing": "正在从 URL 安装技能...",
        "status_installing_batch": "正在安装 {total} 个技能...",
        "status_discovering_skills": "正在从 {url} 发现技能...",
        "status_creating": "正在创建技能...",
        "status_updating": "正在更新技能...",
        "status_deleting": "正在删除技能...",
        "status_done": "已完成。",
        "status_list_done": "已找到 {count} 个技能（启用 {active_count} 个）。",
        "status_show_done": "已加载技能：{name}。",
        "status_install_done": "技能安装完成：{name}。",
        "status_install_overwrite_done": "已通过覆盖更新完成安装：{name}。",
        "status_create_done": "技能创建完成：{name}。",
        "status_create_overwrite_done": "已更新同名技能：{name}。",
        "status_update_done": "技能更新完成：{name}。",
        "status_delete_done": "技能删除完成：{name}。",
        "status_install_batch_done": "批量安装完成：成功 {succeeded} 个，失败 {failed} 个。",
        "err_unavailable": "当前运行环境不可用 OpenWebUI Skills 模型。",
        "err_user_required": "需要用户上下文。",
        "err_name_required": "技能名称不能为空。",
        "err_not_found": "未找到技能。",
        "err_no_update_fields": "未提供可更新字段。",
        "err_url_required": "技能 URL 不能为空。",
        "err_install_fetch": "从 URL 获取技能内容失败。",
        "err_install_parse": "解析技能包或内容失败。",
        "err_invalid_url": "URL 无效，仅支持 http(s) 地址。",
        "msg_created": "技能创建成功。",
        "msg_updated": "技能更新成功。",
        "msg_deleted": "技能删除成功。",
        "msg_installed": "技能安装成功。",
    },
    "zh-TW": {
        "status_listing": "正在列出你的技能...",
        "status_showing": "正在讀取技能詳情...",
        "status_installing": "正在從 URL 安裝技能...",
        "status_installing_batch": "正在安裝 {total} 個技能...",
        "status_creating": "正在建立技能...",
        "status_updating": "正在更新技能...",
        "status_deleting": "正在刪除技能...",
        "status_done": "已完成。",
        "status_list_done": "已找到 {count} 個技能（啟用 {active_count} 個）。",
        "status_show_done": "已載入技能：{name}。",
        "status_install_done": "技能安裝完成：{name}。",
        "status_install_overwrite_done": "已透過覆蓋更新完成安裝：{name}。",
        "status_create_done": "技能建立完成：{name}。",
        "status_create_overwrite_done": "已更新同名技能：{name}。",
        "status_update_done": "技能更新完成：{name}。",
        "status_delete_done": "技能刪除完成：{name}。",
        "status_install_batch_done": "批次安裝完成：成功 {succeeded} 個，失敗 {failed} 個。",
        "err_unavailable": "目前執行環境不可用 OpenWebUI Skills 模型。",
        "err_user_required": "需要使用者上下文。",
        "err_name_required": "技能名稱不能為空。",
        "err_not_found": "未找到技能。",
        "err_no_update_fields": "未提供可更新欄位。",
        "err_url_required": "技能 URL 不能為空。",
        "err_install_fetch": "從 URL 取得技能內容失敗。",
        "err_install_parse": "解析技能包或內容失敗。",
        "err_invalid_url": "URL 無效，僅支援 http(s) 位址。",
        "msg_created": "技能建立成功。",
        "msg_updated": "技能更新成功。",
        "msg_deleted": "技能刪除成功。",
        "msg_installed": "技能安裝成功。",
    },
    "zh-HK": {
        "status_listing": "正在列出你的技能...",
        "status_showing": "正在讀取技能詳情...",
        "status_installing": "正在從 URL 安裝技能...",
        "status_installing_batch": "正在安裝 {total} 個技能...",
        "status_creating": "正在建立技能...",
        "status_updating": "正在更新技能...",
        "status_deleting": "正在刪除技能...",
        "status_done": "已完成。",
        "status_list_done": "已找到 {count} 個技能（啟用 {active_count} 個）。",
        "status_show_done": "已載入技能：{name}。",
        "status_install_done": "技能安裝完成：{name}。",
        "status_install_overwrite_done": "已透過覆蓋更新完成安裝：{name}。",
        "status_create_done": "技能建立完成：{name}。",
        "status_create_overwrite_done": "已更新同名技能：{name}。",
        "status_update_done": "技能更新完成：{name}。",
        "status_delete_done": "技能刪除完成：{name}。",
        "status_install_batch_done": "批次安裝完成：成功 {succeeded} 個，失敗 {failed} 個。",
        "err_unavailable": "目前執行環境不可用 OpenWebUI Skills 模型。",
        "err_user_required": "需要使用者上下文。",
        "err_name_required": "技能名稱不能為空。",
        "err_not_found": "未找到技能。",
        "err_no_update_fields": "未提供可更新欄位。",
        "err_url_required": "技能 URL 不能為空。",
        "err_install_fetch": "從 URL 取得技能內容失敗。",
        "err_install_parse": "解析技能包或內容失敗。",
        "err_invalid_url": "URL 無效，僅支援 http(s) 位址。",
        "msg_created": "技能建立成功。",
        "msg_updated": "技能更新成功。",
        "msg_deleted": "技能刪除成功。",
        "msg_installed": "技能安裝成功。",
    },
    "ja-JP": {
        "status_listing": "スキル一覧を取得しています...",
        "status_showing": "スキル詳細を読み込み中...",
        "status_installing": "URL からスキルをインストール中...",
        "status_installing_batch": "{total} 件のスキルをインストール中...",
        "status_discovering_skills": "{url} からスキルを検出中...",
        "status_creating": "スキルを作成中...",
        "status_updating": "スキルを更新中...",
        "status_deleting": "スキルを削除中...",
        "status_done": "完了しました。",
        "status_list_done": "{count} 件のスキルが見つかりました（有効: {active_count} 件）。",
        "status_show_done": "スキルを読み込みました: {name}。",
        "status_install_done": "スキルをインストールしました: {name}。",
        "status_install_overwrite_done": "既存スキルを更新してインストールしました: {name}。",
        "status_create_done": "スキルを作成しました: {name}。",
        "status_create_overwrite_done": "同名スキルを更新しました: {name}。",
        "status_update_done": "スキルを更新しました: {name}。",
        "status_delete_done": "スキルを削除しました: {name}。",
        "status_install_batch_done": "一括インストール完了: 成功 {succeeded} 件、失敗 {failed} 件。",
        "err_unavailable": "この実行環境では OpenWebUI Skills モデルを利用できません。",
        "err_user_required": "ユーザーコンテキストが必要です。",
        "err_name_required": "スキル名は必須です。",
        "err_not_found": "スキルが見つかりません。",
        "err_no_update_fields": "更新する項目が指定されていません。",
        "err_url_required": "スキル URL は必須です。",
        "err_install_fetch": "URL からスキル内容の取得に失敗しました。",
        "err_install_parse": "スキルパッケージ/内容の解析に失敗しました。",
        "err_invalid_url": "無効な URL です。http(s) のみサポートします。",
        "msg_created": "スキルを作成しました。",
        "msg_updated": "スキルを更新しました。",
        "msg_deleted": "スキルを削除しました。",
        "msg_installed": "スキルをインストールしました。",
    },
    "ko-KR": {
        "status_listing": "스킬 목록을 불러오는 중...",
        "status_showing": "스킬 상세 정보를 읽는 중...",
        "status_installing": "URL에서 스킬 설치 중...",
        "status_installing_batch": "스킬 {total}개를 설치하는 중...",
        "status_discovering_skills": "{url}에서 스킬 발견 중...",
        "status_creating": "스킬 생성 중...",
        "status_updating": "스킬 업데이트 중...",
        "status_deleting": "스킬 삭제 중...",
        "status_done": "완료되었습니다.",
        "status_list_done": "스킬 {count}개를 찾았습니다(활성 {active_count}개).",
        "status_show_done": "스킬을 불러왔습니다: {name}.",
        "status_install_done": "스킬 설치 완료: {name}.",
        "status_install_overwrite_done": "기존 스킬을 업데이트하여 설치 완료: {name}.",
        "status_create_done": "스킬 생성 완료: {name}.",
        "status_create_overwrite_done": "동일 이름 스킬 업데이트 완료: {name}.",
        "status_update_done": "스킬 업데이트 완료: {name}.",
        "status_delete_done": "스킬 삭제 완료: {name}.",
        "status_install_batch_done": "일괄 설치 완료: 성공 {succeeded}개, 실패 {failed}개.",
        "err_unavailable": "현재 런타임에서 OpenWebUI Skills 모델을 사용할 수 없습니다.",
        "err_user_required": "사용자 컨텍스트가 필요합니다.",
        "err_name_required": "스킬 이름은 필수입니다.",
        "err_not_found": "스킬을 찾을 수 없습니다.",
        "err_no_update_fields": "업데이트할 필드가 제공되지 않았습니다.",
        "err_url_required": "스킬 URL이 필요합니다.",
        "err_install_fetch": "URL에서 스킬 내용을 가져오지 못했습니다.",
        "err_install_parse": "스킬 패키지/내용 파싱에 실패했습니다.",
        "err_invalid_url": "잘못된 URL입니다. http(s)만 지원됩니다.",
        "msg_created": "스킬이 생성되었습니다.",
        "msg_updated": "스킬이 업데이트되었습니다.",
        "msg_deleted": "스킬이 삭제되었습니다.",
        "msg_installed": "스킬이 설치되었습니다.",
    },
    "fr-FR": {
        "status_listing": "Liste des skills en cours...",
        "status_showing": "Lecture des détails du skill...",
        "status_installing": "Installation du skill depuis l'URL...",
        "status_installing_batch": "Installation de {total} skill(s)...",
        "status_discovering_skills": "Découverte de skills dans {url}...",
        "status_creating": "Création du skill...",
        "status_updating": "Mise à jour du skill...",
        "status_deleting": "Suppression du skill...",
        "status_done": "Terminé.",
        "status_list_done": "{count} skills trouvés ({active_count} actifs).",
        "status_show_done": "Skill chargé : {name}.",
        "status_install_done": "Skill installé : {name}.",
        "status_install_overwrite_done": "Skill installé en mettant à jour l'existant : {name}.",
        "status_create_done": "Skill créé : {name}.",
        "status_create_overwrite_done": "Skill existant mis à jour : {name}.",
        "status_update_done": "Skill mis à jour : {name}.",
        "status_delete_done": "Skill supprimé : {name}.",
        "status_install_batch_done": "Installation en lot terminée : {succeeded} réussies, {failed} échouées.",
        "err_unavailable": "Le modèle OpenWebUI Skills n'est pas disponible dans cet environnement.",
        "err_user_required": "Le contexte utilisateur est requis.",
        "err_name_required": "Le nom du skill est requis.",
        "err_not_found": "Skill introuvable.",
        "err_no_update_fields": "Aucun champ à mettre à jour n'a été fourni.",
        "err_url_required": "L'URL du skill est requise.",
        "err_install_fetch": "Échec de récupération du contenu du skill depuis l'URL.",
        "err_install_parse": "Échec de l'analyse du package/contenu du skill.",
        "err_invalid_url": "URL invalide. Seules les URL http(s) sont prises en charge.",
        "msg_created": "Skill créé avec succès.",
        "msg_updated": "Skill mis à jour avec succès.",
        "msg_deleted": "Skill supprimé avec succès.",
        "msg_installed": "Skill installé avec succès.",
    },
    "de-DE": {
        "status_listing": "Deine Skills werden aufgelistet...",
        "status_showing": "Skill-Details werden gelesen...",
        "status_installing": "Skill wird von URL installiert...",
        "status_installing_batch": "{total} Skill(s) werden installiert...",
        "status_discovering_skills": "Suche nach Skills in {url}...",
        "status_creating": "Skill wird erstellt...",
        "status_updating": "Skill wird aktualisiert...",
        "status_deleting": "Skill wird gelöscht...",
        "status_done": "Fertig.",
        "status_list_done": "{count} Skills gefunden ({active_count} aktiv).",
        "status_show_done": "Skill geladen: {name}.",
        "status_install_done": "Skill installiert: {name}.",
        "status_install_overwrite_done": "Skill durch Aktualisierung installiert: {name}.",
        "status_create_done": "Skill erstellt: {name}.",
        "status_create_overwrite_done": "Bestehender Skill aktualisiert: {name}.",
        "status_update_done": "Skill aktualisiert: {name}.",
        "status_delete_done": "Skill gelöscht: {name}.",
        "status_install_batch_done": "Batch-Installation abgeschlossen: {succeeded} erfolgreich, {failed} fehlgeschlagen.",
        "err_unavailable": "Das OpenWebUI-Skills-Modell ist in dieser Laufzeit nicht verfügbar.",
        "err_user_required": "Benutzerkontext ist erforderlich.",
        "err_name_required": "Skill-Name ist erforderlich.",
        "err_not_found": "Skill nicht gefunden.",
        "err_no_update_fields": "Keine zu aktualisierenden Felder angegeben.",
        "err_url_required": "Skill-URL ist erforderlich.",
        "err_install_fetch": "Skill-Inhalt konnte nicht von URL geladen werden.",
        "err_install_parse": "Skill-Paket/Inhalt konnte nicht geparst werden.",
        "err_invalid_url": "Ungültige URL. Nur http(s)-URLs werden unterstützt.",
        "msg_created": "Skill erfolgreich erstellt.",
        "msg_updated": "Skill erfolgreich aktualisiert.",
        "msg_deleted": "Skill erfolgreich gelöscht.",
        "msg_installed": "Skill erfolgreich installiert.",
    },
    "es-ES": {
        "status_listing": "Listando tus skills...",
        "status_showing": "Leyendo detalles del skill...",
        "status_installing": "Instalando skill desde URL...",
        "status_installing_batch": "Instalando {total} skill(s)...",
        "status_discovering_skills": "Descubriendo skills en {url}...",
        "status_creating": "Creando skill...",
        "status_updating": "Actualizando skill...",
        "status_deleting": "Eliminando skill...",
        "status_done": "Hecho.",
        "status_list_done": "Se encontraron {count} skills ({active_count} activos).",
        "status_show_done": "Skill cargado: {name}.",
        "status_install_done": "Skill instalado: {name}.",
        "status_install_overwrite_done": "Skill instalado actualizando el existente: {name}.",
        "status_create_done": "Skill creado: {name}.",
        "status_create_overwrite_done": "Skill existente actualizado: {name}.",
        "status_update_done": "Skill actualizado: {name}.",
        "status_delete_done": "Skill eliminado: {name}.",
        "status_install_batch_done": "Instalación por lotes completada: {succeeded} correctas, {failed} fallidas.",
        "err_unavailable": "El modelo OpenWebUI Skills no está disponible en este entorno.",
        "err_user_required": "Se requiere contexto de usuario.",
        "err_name_required": "Se requiere el nombre del skill.",
        "err_not_found": "Skill no encontrado.",
        "err_no_update_fields": "No se proporcionaron campos para actualizar.",
        "err_url_required": "Se requiere la URL del skill.",
        "err_install_fetch": "No se pudo obtener el contenido del skill desde la URL.",
        "err_install_parse": "No se pudo analizar el paquete/contenido del skill.",
        "err_invalid_url": "URL inválida. Solo se admiten URLs http(s).",
        "msg_created": "Skill creado correctamente.",
        "msg_updated": "Skill actualizado correctamente.",
        "msg_deleted": "Skill eliminado correctamente.",
        "msg_installed": "Skill instalado correctamente.",
    },
    "it-IT": {
        "status_listing": "Elenco delle skill in corso...",
        "status_showing": "Lettura dei dettagli della skill...",
        "status_installing": "Installazione della skill da URL...",
        "status_installing_batch": "Installazione di {total} skill in corso...",
        "status_discovering_skills": "Scoperta di skills in {url}...",
        "status_creating": "Creazione della skill...",
        "status_updating": "Aggiornamento della skill...",
        "status_deleting": "Eliminazione della skill...",
        "status_done": "Fatto.",
        "status_list_done": "Trovate {count} skill ({active_count} attive).",
        "status_show_done": "Skill caricata: {name}.",
        "status_install_done": "Skill installata: {name}.",
        "status_install_overwrite_done": "Skill installata aggiornando l'esistente: {name}.",
        "status_create_done": "Skill creata: {name}.",
        "status_create_overwrite_done": "Skill esistente aggiornata: {name}.",
        "status_update_done": "Skill aggiornata: {name}.",
        "status_delete_done": "Skill eliminata: {name}.",
        "status_install_batch_done": "Installazione batch completata: {succeeded} riuscite, {failed} non riuscite.",
        "err_unavailable": "Il modello OpenWebUI Skills non è disponibile in questo runtime.",
        "err_user_required": "È richiesto il contesto utente.",
        "err_name_required": "Il nome della skill è obbligatorio.",
        "err_not_found": "Skill non trovata.",
        "err_no_update_fields": "Nessun campo da aggiornare fornito.",
        "err_url_required": "L'URL della skill è obbligatoria.",
        "err_install_fetch": "Impossibile recuperare il contenuto della skill dall'URL.",
        "err_install_parse": "Impossibile analizzare il pacchetto/contenuto della skill.",
        "err_invalid_url": "URL non valido. Sono supportati solo URL http(s).",
        "msg_created": "Skill creata con successo.",
        "msg_updated": "Skill aggiornata con successo.",
        "msg_deleted": "Skill eliminata con successo.",
        "msg_installed": "Skill installata con successo.",
    },
    "vi-VN": {
        "status_listing": "Đang liệt kê kỹ năng của bạn...",
        "status_showing": "Đang đọc chi tiết kỹ năng...",
        "status_installing": "Đang cài đặt kỹ năng từ URL...",
        "status_installing_batch": "Đang cài đặt {total} kỹ năng...",
        "status_discovering_skills": "Đang phát hiện kỹ năng trong {url}...",
        "status_creating": "Đang tạo kỹ năng...",
        "status_updating": "Đang cập nhật kỹ năng...",
        "status_deleting": "Đang xóa kỹ năng...",
        "status_done": "Hoàn tất.",
        "status_list_done": "Đã tìm thấy {count} kỹ năng ({active_count} đang bật).",
        "status_show_done": "Đã tải kỹ năng: {name}.",
        "status_install_done": "Cài đặt kỹ năng hoàn tất: {name}.",
        "status_install_overwrite_done": "Đã cài đặt bằng cách cập nhật kỹ năng hiện có: {name}.",
        "status_create_done": "Tạo kỹ năng hoàn tất: {name}.",
        "status_create_overwrite_done": "Đã cập nhật kỹ năng cùng tên: {name}.",
        "status_update_done": "Cập nhật kỹ năng hoàn tất: {name}.",
        "status_delete_done": "Xóa kỹ năng hoàn tất: {name}.",
        "status_install_batch_done": "Cài đặt hàng loạt hoàn tất: thành công {succeeded}, thất bại {failed}.",
        "err_unavailable": "Mô hình OpenWebUI Skills không khả dụng trong môi trường hiện tại.",
        "err_user_required": "Cần có ngữ cảnh người dùng.",
        "err_name_required": "Tên kỹ năng là bắt buộc.",
        "err_not_found": "Không tìm thấy kỹ năng.",
        "err_no_update_fields": "Không có trường nào để cập nhật.",
        "err_url_required": "URL kỹ năng là bắt buộc.",
        "err_install_fetch": "Không thể tải nội dung kỹ năng từ URL.",
        "err_install_parse": "Không thể phân tích gói/nội dung kỹ năng.",
        "err_invalid_url": "URL không hợp lệ. Chỉ hỗ trợ URL http(s).",
        "msg_created": "Tạo kỹ năng thành công.",
        "msg_updated": "Cập nhật kỹ năng thành công.",
        "msg_deleted": "Xóa kỹ năng thành công.",
        "msg_installed": "Cài đặt kỹ năng thành công.",
    },
    "id-ID": {
        "status_listing": "Sedang menampilkan daftar skill Anda...",
        "status_showing": "Sedang membaca detail skill...",
        "status_installing": "Sedang memasang skill dari URL...",
        "status_installing_batch": "Sedang memasang {total} skill...",
        "status_discovering_skills": "Sedang mencari skill di {url}...",
        "status_creating": "Sedang membuat skill...",
        "status_updating": "Sedang memperbarui skill...",
        "status_deleting": "Sedang menghapus skill...",
        "status_done": "Selesai.",
        "status_list_done": "Ditemukan {count} skill ({active_count} aktif).",
        "status_show_done": "Skill dimuat: {name}.",
        "status_install_done": "Skill berhasil dipasang: {name}.",
        "status_install_overwrite_done": "Skill dipasang dengan memperbarui skill yang ada: {name}.",
        "status_create_done": "Skill berhasil dibuat: {name}.",
        "status_create_overwrite_done": "Skill dengan nama sama berhasil diperbarui: {name}.",
        "status_update_done": "Skill berhasil diperbarui: {name}.",
        "status_delete_done": "Skill berhasil dihapus: {name}.",
        "status_install_batch_done": "Pemasangan batch selesai: {succeeded} berhasil, {failed} gagal.",
        "err_unavailable": "Model OpenWebUI Skills tidak tersedia di runtime ini.",
        "err_user_required": "Konteks pengguna diperlukan.",
        "err_name_required": "Nama skill wajib diisi.",
        "err_not_found": "Skill tidak ditemukan.",
        "err_no_update_fields": "Tidak ada field pembaruan yang diberikan.",
        "err_url_required": "URL skill wajib diisi.",
        "err_install_fetch": "Gagal mengambil konten skill dari URL.",
        "err_install_parse": "Gagal mem-parsing paket/konten skill.",
        "err_invalid_url": "URL tidak valid. Hanya URL http(s) yang didukung.",
        "msg_created": "Skill berhasil dibuat.",
        "msg_updated": "Skill berhasil diperbarui.",
        "msg_deleted": "Skill berhasil dihapus.",
        "msg_installed": "Skill berhasil dipasang.",
    },
}

FALLBACK_MAP = {
    "zh": "zh-CN",
    "zh-TW": "zh-TW",
    "zh-HK": "zh-HK",
    "en": "en-US",
    "ja": "ja-JP",
    "ko": "ko-KR",
    "fr": "fr-FR",
    "de": "de-DE",
    "es": "es-ES",
    "it": "it-IT",
    "vi": "vi-VN",
    "id": "id-ID",
}


class Tools:
    """OpenWebUI native tools for simple skill lifecycle management."""

    class Valves(BaseModel):
        """Configurable plugin valves."""

        SHOW_STATUS: bool = Field(
            default=True,
            description="Whether to show operation status updates.",
        )
        ALLOW_OVERWRITE_ON_CREATE: bool = Field(
            default=False,
            description="Allow create_skill/install_skill to overwrite same-name skill by default.",
        )
        INSTALL_FETCH_TIMEOUT: float = Field(
            default=12.0,
            description="Timeout in seconds for URL fetch when installing a skill.",
        )

    def __init__(self):
        """Initialize plugin valves."""
        self.valves = self.Valves()

    def _resolve_language(self, user_language: str) -> str:
        """Normalize user language code to a supported translation key."""
        value = str(user_language or "").strip()
        if not value:
            return "en-US"

        normalized = value.replace("_", "-")

        if normalized in TRANSLATIONS:
            return normalized

        lower_to_lang = {k.lower(): k for k in TRANSLATIONS.keys()}
        if normalized.lower() in lower_to_lang:
            return lower_to_lang[normalized.lower()]

        if normalized in FALLBACK_MAP:
            return FALLBACK_MAP[normalized]

        lower_fallback = {k.lower(): v for k, v in FALLBACK_MAP.items()}
        if normalized.lower() in lower_fallback:
            return lower_fallback[normalized.lower()]

        base = normalized.split("-")[0].lower()
        return lower_fallback.get(base, "en-US")

    def _t(self, lang: str, key: str, **kwargs) -> str:
        """Return translated text for key with safe formatting."""
        lang_key = self._resolve_language(lang)
        text = TRANSLATIONS.get(lang_key, TRANSLATIONS["en-US"]).get(
            key, TRANSLATIONS["en-US"].get(key, key)
        )
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        return text

    async def _get_user_context(
        self,
        __user__: Optional[dict],
        __event_call__: Optional[Any] = None,
        __request__: Optional[Any] = None,
    ) -> Dict[str, str]:
        """Extract robust user context with frontend language fallback."""
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
            except Exception as e:
                logger.warning(f"Failed to retrieve frontend language: {e}")

        return {
            "user_id": str(user_data.get("id", "")).strip(),
            "user_name": user_data.get("name", "User"),
            "user_language": user_language,
        }

    async def _emit_status(
        self,
        emitter: Optional[Any],
        description: str,
        done: bool = False,
    ):
        """Emit status event to OpenWebUI status bar when enabled."""
        if self.valves.SHOW_STATUS and emitter:
            await emitter(
                {
                    "type": "status",
                    "data": {"description": description, "done": done},
                }
            )

    def _require_skills_model(self):
        """Ensure OpenWebUI Skills model APIs are available."""
        if Skills is None or SkillForm is None or SkillMeta is None:
            raise RuntimeError("skills_model_unavailable")

    def _user_skills(self, user_id: str, access: str = "read") -> List[Any]:
        """Load user-scoped skills using OpenWebUI Skills model."""
        return Skills.get_skills_by_user_id(user_id, access) or []

    def _find_skill(
        self,
        user_id: str,
        skill_id: str = "",
        name: str = "",
    ) -> Optional[Any]:
        """Find a skill by id or case-insensitive name within user scope."""
        skills = self._user_skills(user_id, "read")
        target_id = (skill_id or "").strip()
        target_name = (name or "").strip().lower()

        for skill in skills:
            sid = str(getattr(skill, "id", "") or "")
            sname = str(getattr(skill, "name", "") or "")
            if target_id and sid == target_id:
                return skill
            if target_name and sname.lower() == target_name:
                return skill
        return None

    def _extract_folder_name_from_url(self, url: str) -> str:
        """Extract folder name from GitHub URL path.
        Examples:
          - https://github.com/.../tree/main/skills/xlsx -> xlsx
          - https://github.com/.../blob/main/skills/README.md -> skills
          - https://raw.githubusercontent.com/.../main/skills/README.md -> skills
        """
        try:
            # Remove query string and fragments
            path = url.split("?")[0].split("#")[0]
            # Get last path component
            parts = path.rstrip("/").split("/")
            if parts:
                last = parts[-1]
                # Skip if it's a file extension
                if "." not in last or last.startswith("."):
                    return last
                # Return parent directory if it's a filename
                if len(parts) > 1:
                    return parts[-2]
        except Exception:
            pass
        return ""

    async def _discover_skills_from_github_directory(
        self, url: str, lang: str
    ) -> List[str]:
        """
        Discover all skill subdirectories from a GitHub tree URL.
        Uses GitHub API to list directory contents.

        Example: https://github.com/anthropics/skills/tree/main/skills
        Returns: List of individual skill tree URLs for each subdirectory
        """
        skill_urls = []
        match = re.match(
            r"https://github\.com/([^/]+)/([^/]+)/tree/([^/]+)(/.*)?\Z", url
        )
        if not match:
            return skill_urls

        owner = match.group(1)
        repo = match.group(2)
        branch = match.group(3)
        path = match.group(4) or ""

        try:
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents{path}?ref={branch}"
            response_bytes = await self._fetch_bytes(api_url)
            contents = json.loads(response_bytes.decode("utf-8"))

            if isinstance(contents, list):
                for item in contents:
                    if item.get("type") == "dir":
                        subdir_name = item.get("name", "")
                        if subdir_name and not subdir_name.startswith("."):
                            subdir_url = f"https://github.com/{owner}/{repo}/tree/{branch}{path}/{subdir_name}"
                            skill_urls.append(subdir_url)

            skill_urls.sort()
        except Exception as e:
            logger.warning(
                f"Failed to discover skills from GitHub directory {url}: {e}"
            )

        return skill_urls

    def _resolve_github_tree_urls(self, url: str) -> List[str]:
        """For GitHub tree URLs, resolve to direct file URLs to try.

        Example: https://github.com/anthropics/skills/tree/main/skills/xlsx
        Returns: [
            https://raw.githubusercontent.com/anthropics/skills/main/skills/xlsx/SKILL.md,
            https://raw.githubusercontent.com/anthropics/skills/main/skills/xlsx/README.md,
        ]
        """
        urls = []
        match = re.match(
            r"https://github\.com/([^/]+)/([^/]+)/tree/([^/]+)(/.*)?\Z", url
        )
        if match:
            owner = match.group(1)
            repo = match.group(2)
            branch = match.group(3)
            path = match.group(4) or ""
            base = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}{path}"
            # Try SKILL.md first, then README.md
            urls.append(f"{base}/SKILL.md")
            urls.append(f"{base}/README.md")
        return urls

    def _normalize_url(self, url: str) -> str:
        """Normalize supported URLs (GitHub blob -> raw, tree -> try direct files first)."""
        value = (url or "").strip()
        if not value.startswith("http://") and not value.startswith("https://"):
            raise ValueError("invalid_url")

        # Handle GitHub blob URLs -> convert to raw
        if "github.com" in value and "/blob/" in value:
            value = value.replace("github.com", "raw.githubusercontent.com")
            value = value.replace("/blob/", "/")

        # Note: GitHub tree URLs are handled separately in install_skill
        # via _resolve_github_tree_urls()

        return value

    async def _fetch_bytes(self, url: str) -> bytes:
        """Fetch bytes from URL with timeout guard."""

        def _sync_fetch(target: str) -> bytes:
            with urllib.request.urlopen(
                target, timeout=self.valves.INSTALL_FETCH_TIMEOUT
            ) as resp:
                return resp.read()

        return await asyncio.wait_for(
            asyncio.to_thread(_sync_fetch, url),
            timeout=self.valves.INSTALL_FETCH_TIMEOUT + 1.0,
        )

    def _parse_skill_md_meta(
        self, content: str, fallback_name: str
    ) -> Tuple[str, str, str]:
        """Parse markdown skill content into (name, description, body)."""
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if fm_match:
            fm_text = fm_match.group(1)
            body = content[fm_match.end() :].strip()
            name = fallback_name
            description = ""
            for line in fm_text.split("\n"):
                m_name = re.match(r"^name:\s*(.+)$", line)
                if m_name:
                    name = m_name.group(1).strip().strip("\"'")
                m_desc = re.match(r"^description:\s*(.+)$", line)
                if m_desc:
                    description = m_desc.group(1).strip().strip("\"'")
            return name, description, body

        h1_match = re.search(r"^#\s+(.+)$", content.strip(), re.MULTILINE)
        name = h1_match.group(1).strip() if h1_match else fallback_name
        return name, "", content.strip()

    def _extract_skill_from_archive(self, payload: bytes) -> Tuple[str, str, str]:
        """Extract first SKILL.md (or README.md) from zip/tar archives."""
        with tempfile.TemporaryDirectory(prefix="owui-skill-") as tmp:
            root = Path(tmp)
            archive_path = root / "pkg"
            archive_path.write_bytes(payload)

            extract_dir = root / "extract"
            extract_dir.mkdir(parents=True, exist_ok=True)

            extracted = False
            try:
                with zipfile.ZipFile(archive_path, "r") as zf:
                    zf.extractall(extract_dir)
                    extracted = True
            except Exception:
                pass

            if not extracted:
                try:
                    with tarfile.open(archive_path, "r:*") as tf:
                        tf.extractall(extract_dir)
                        extracted = True
                except Exception:
                    pass

            if not extracted:
                raise ValueError("install_parse")

            candidates = list(extract_dir.rglob("SKILL.md"))
            if not candidates:
                candidates = list(extract_dir.rglob("README.md"))
            if not candidates:
                raise ValueError("install_parse")

            chosen = candidates[0]
            text = chosen.read_text(encoding="utf-8", errors="ignore")
            fallback_name = chosen.parent.name or "installed-skill"
            return self._parse_skill_md_meta(text, fallback_name)

    async def list_skills(
        self,
        include_content: bool = False,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Any] = None,
        __event_call__: Optional[Any] = None,
        __request__: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """List current user's OpenWebUI skills."""
        user_ctx = await self._get_user_context(__user__, __event_call__, __request__)
        lang = user_ctx["user_language"]
        user_id = user_ctx["user_id"]

        try:
            self._require_skills_model()
            if not user_id:
                raise ValueError(self._t(lang, "err_user_required"))

            await self._emit_status(__event_emitter__, self._t(lang, "status_listing"))

            skills = self._user_skills(user_id, "read")
            rows = []
            for skill in skills:
                row = {
                    "id": str(getattr(skill, "id", "") or ""),
                    "name": getattr(skill, "name", ""),
                    "description": getattr(skill, "description", ""),
                    "is_active": bool(getattr(skill, "is_active", True)),
                    "updated_at": str(getattr(skill, "updated_at", "") or ""),
                }
                if include_content:
                    row["content"] = getattr(skill, "content", "")
                rows.append(row)

            rows.sort(key=lambda x: (x.get("name") or "").lower())
            active_count = sum(1 for row in rows if row.get("is_active"))

            await self._emit_status(
                __event_emitter__,
                self._t(
                    lang,
                    "status_list_done",
                    count=len(rows),
                    active_count=active_count,
                ),
                done=True,
            )
            return {"count": len(rows), "skills": rows}
        except Exception as e:
            msg = (
                self._t(lang, "err_unavailable")
                if str(e) == "skills_model_unavailable"
                else str(e)
            )
            await self._emit_status(__event_emitter__, msg, done=True)
            return {"error": msg}

    async def show_skill(
        self,
        skill_id: str = "",
        name: str = "",
        include_content: bool = True,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Any] = None,
        __event_call__: Optional[Any] = None,
        __request__: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Show one skill by id or name."""
        user_ctx = await self._get_user_context(__user__, __event_call__, __request__)
        lang = user_ctx["user_language"]
        user_id = user_ctx["user_id"]

        try:
            self._require_skills_model()
            if not user_id:
                raise ValueError(self._t(lang, "err_user_required"))

            await self._emit_status(__event_emitter__, self._t(lang, "status_showing"))

            skill = self._find_skill(user_id=user_id, skill_id=skill_id, name=name)
            if not skill:
                raise ValueError(self._t(lang, "err_not_found"))

            result = {
                "id": str(getattr(skill, "id", "") or ""),
                "name": getattr(skill, "name", ""),
                "description": getattr(skill, "description", ""),
                "is_active": bool(getattr(skill, "is_active", True)),
                "updated_at": str(getattr(skill, "updated_at", "") or ""),
            }
            if include_content:
                result["content"] = getattr(skill, "content", "")

            skill_name = result.get("name") or result.get("id") or "unknown"
            await self._emit_status(
                __event_emitter__,
                self._t(lang, "status_show_done", name=skill_name),
                done=True,
            )
            return result
        except Exception as e:
            msg = (
                self._t(lang, "err_unavailable")
                if str(e) == "skills_model_unavailable"
                else str(e)
            )
            await self._emit_status(__event_emitter__, msg, done=True)
            return {"error": msg}

    async def _install_single_skill(
        self,
        url: str,
        name: str,
        user_id: str,
        lang: str,
        overwrite: bool,
        __event_emitter__: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Internal method to install a single skill from URL."""
        try:
            if not (url or "").strip():
                raise ValueError(self._t(lang, "err_url_required"))

            # Extract potential folder name from URL before normalization
            url_folder = self._extract_folder_name_from_url(url).strip()

            parsed_name = ""
            parsed_desc = ""
            parsed_body = ""
            payload = None

            # Special handling for GitHub tree URLs
            if "github.com" in url and "/tree/" in url:
                fallback_file_urls = self._resolve_github_tree_urls(url)
                # Try to fetch SKILL.md or README.md directly from the tree path
                for file_url in fallback_file_urls:
                    try:
                        payload = await self._fetch_bytes(file_url)
                        if payload:
                            break
                    except Exception:
                        continue

                if payload:
                    # Successfully fetched direct file
                    text = payload.decode("utf-8", errors="ignore")
                    fallback = url_folder or "installed-skill"
                    parsed_name, parsed_desc, parsed_body = self._parse_skill_md_meta(
                        text, fallback
                    )
                else:
                    # Fallback: download entire branch as zip and extract
                    # This is a last resort if direct file access fails
                    raise ValueError(f"Could not find SKILL.md or README.md in {url}")
            else:
                # Handle other URL types (blob, direct markdown, archives)
                normalized = self._normalize_url(url)
                payload = await self._fetch_bytes(normalized)

                if normalized.lower().endswith((".zip", ".tar", ".tar.gz", ".tgz")):
                    parsed_name, parsed_desc, parsed_body = (
                        self._extract_skill_from_archive(payload)
                    )
                else:
                    text = payload.decode("utf-8", errors="ignore")
                    # Use extracted folder name as fallback
                    fallback = url_folder or "installed-skill"
                    parsed_name, parsed_desc, parsed_body = self._parse_skill_md_meta(
                        text, fallback
                    )

            final_name = (
                name or parsed_name or url_folder or "installed-skill"
            ).strip()
            final_desc = (parsed_desc or final_name).strip()
            final_content = (parsed_body or final_desc).strip()
            if not final_name:
                raise ValueError(self._t(lang, "err_name_required"))

            existing = self._find_skill(user_id=user_id, name=final_name)
            # install_skill always overwrites by default (overwrite=True);
            # ALLOW_OVERWRITE_ON_CREATE valve also controls this.
            allow_overwrite = overwrite or self.valves.ALLOW_OVERWRITE_ON_CREATE
            if existing:
                sid = str(getattr(existing, "id", "") or "")
                if not allow_overwrite:
                    # Should not normally reach here since install defaults overwrite=True
                    return {
                        "error": f"Skill already exists: {final_name}",
                        "hint": "Pass overwrite=true to replace the existing skill.",
                    }
                updated = Skills.update_skill_by_id(
                    sid,
                    {
                        "name": final_name,
                        "description": final_desc,
                        "content": final_content,
                        "is_active": True,
                    },
                )
                await self._emit_status(
                    __event_emitter__,
                    self._t(lang, "status_install_overwrite_done", name=final_name),
                    done=True,
                )
                return {
                    "success": True,
                    "action": "updated",
                    "id": str(getattr(updated, "id", "") or sid),
                    "name": final_name,
                    "source_url": url,
                }

            new_skill = Skills.insert_new_skill(
                user_id=user_id,
                form_data=SkillForm(
                    id=str(uuid.uuid4()),
                    name=final_name,
                    description=final_desc,
                    content=final_content,
                    meta=SkillMeta(),
                    is_active=True,
                ),
            )

            await self._emit_status(
                __event_emitter__,
                self._t(lang, "status_install_done", name=final_name),
                done=True,
            )
            return {
                "success": True,
                "action": "installed",
                "id": str(getattr(new_skill, "id", "") or ""),
                "name": final_name,
                "source_url": url,
            }
        except Exception as e:
            key = None
            if str(e) in {"invalid_url", "install_parse"}:
                key = (
                    "err_invalid_url"
                    if str(e) == "invalid_url"
                    else "err_install_parse"
                )
            msg = (
                self._t(lang, key)
                if key
                else (
                    self._t(lang, "err_unavailable")
                    if str(e) == "skills_model_unavailable"
                    else str(e)
                )
            )
            logger.error(
                f"_install_single_skill failed for {url}: {msg}", exc_info=True
            )
            return {"error": msg, "url": url}

    async def install_skill(
        self,
        url: str,
        name: str = "",
        overwrite: bool = True,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Any] = None,
        __event_call__: Optional[Any] = None,
        __request__: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Install one or more skills from URL(s), with support for GitHub directory auto-discovery.

        Args:
            url: A single URL string OR a JSON array of URL strings for batch install.
                 Examples:
                   Single: "https://github.com/owner/repo/tree/main/skills/xlsx"
                   Directory: "https://github.com/owner/repo/tree/main/skills"
                   Batch:  ["https://github.com/owner/repo/tree/main/skills/xlsx",
                            "https://github.com/owner/repo/tree/main/skills/csv"]
            name: Optional custom name for the skill (single install only).
            overwrite: If True (default), overwrites any existing skill with the same name.

        Auto-Discovery Feature:
        If a GitHub tree URL points to a directory that contains multiple skill subdirectories,
        this tool will automatically discover all subdirectories and batch install them.
        Example: "https://github.com/anthropics/skills/tree/main/skills" will auto-discover
        all skill folders under /skills and install them all at once.

        Supported URL formats:
        - GitHub tree URL: https://github.com/owner/repo/tree/branch/path/to/skill
        - GitHub skill directory (auto-discovery): https://github.com/owner/repo/tree/branch/path
        - GitHub blob URL: https://github.com/owner/repo/blob/branch/path/SKILL.md
        - Raw markdown URL: https://raw.githubusercontent.com/.../SKILL.md
        - Archive URL: https://example.com/skill.zip (must contain SKILL.md or README.md)
        """
        user_ctx = await self._get_user_context(__user__, __event_call__, __request__)
        lang = user_ctx["user_language"]
        user_id = user_ctx["user_id"]

        try:
            self._require_skills_model()
            if not user_id:
                raise ValueError(self._t(lang, "err_user_required"))

            # Stage 1: Check for directory auto-discovery (single string GitHub URL)
            if isinstance(url, str) and "github.com" in url and "/tree/" in url:
                await self._emit_status(
                    __event_emitter__,
                    self._t(lang, "status_discovering_skills", url=(url or "")[-50:]),
                )
                discover_fn = getattr(
                    self, "_discover_skills_from_github_directory", None
                )
                discovered = []
                if callable(discover_fn):
                    discovered = await discover_fn(url, lang)
                else:
                    logger.warning(
                        "_discover_skills_from_github_directory is unavailable on current Tools instance."
                    )
                if discovered:
                    # Auto-discovered subdirectories, treat as batch
                    url = discovered

            # Stage 2: Check if url is a list/tuple (batch mode)
            if isinstance(url, (list, tuple)):
                urls = url
                if not urls:
                    raise ValueError(self._t(lang, "err_url_required"))

                await self._emit_status(
                    __event_emitter__,
                    self._t(lang, "status_installing_batch", total=len(urls)),
                )

                results = []
                for idx, single_url in enumerate(urls, 1):
                    result = await self._install_single_skill(
                        url=str(single_url).strip(),
                        name="",  # Batch mode doesn't support per-item names
                        user_id=user_id,
                        lang=lang,
                        overwrite=overwrite,
                        __event_emitter__=__event_emitter__,
                    )
                    results.append(result)

                # Summary
                success_count = sum(1 for r in results if r.get("success"))
                error_count = len(results) - success_count

                await self._emit_status(
                    __event_emitter__,
                    self._t(
                        lang,
                        "status_install_batch_done",
                        succeeded=success_count,
                        failed=error_count,
                    ),
                    done=True,
                )

                return {
                    "batch": True,
                    "total": len(results),
                    "succeeded": success_count,
                    "failed": error_count,
                    "results": results,
                }
            else:
                # Single mode
                if not (url or "").strip():
                    raise ValueError(self._t(lang, "err_url_required"))

                await self._emit_status(
                    __event_emitter__, self._t(lang, "status_installing")
                )

                result = await self._install_single_skill(
                    url=str(url).strip(),
                    name=name,
                    user_id=user_id,
                    lang=lang,
                    overwrite=overwrite,
                    __event_emitter__=__event_emitter__,
                )
                return result

        except Exception as e:
            key = None
            if str(e) in {"invalid_url", "install_parse"}:
                key = (
                    "err_invalid_url"
                    if str(e) == "invalid_url"
                    else "err_install_parse"
                )
            msg = (
                self._t(lang, key)
                if key
                else (
                    self._t(lang, "err_unavailable")
                    if str(e) == "skills_model_unavailable"
                    else str(e)
                )
            )
            await self._emit_status(__event_emitter__, msg, done=True)
            logger.error(f"install_skill failed: {msg}", exc_info=True)
            return {"error": msg}

    async def create_skill(
        self,
        name: str,
        description: str = "",
        content: str = "",
        overwrite: bool = False,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Any] = None,
        __event_call__: Optional[Any] = None,
        __request__: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Create a new skill, or update same-name skill when overwrite is enabled."""
        user_ctx = await self._get_user_context(__user__, __event_call__, __request__)
        lang = user_ctx["user_language"]
        user_id = user_ctx["user_id"]

        try:
            self._require_skills_model()
            if not user_id:
                raise ValueError(self._t(lang, "err_user_required"))

            skill_name = (name or "").strip()
            if not skill_name:
                raise ValueError(self._t(lang, "err_name_required"))

            await self._emit_status(__event_emitter__, self._t(lang, "status_creating"))

            existing = self._find_skill(user_id=user_id, name=skill_name)
            allow_overwrite = overwrite or self.valves.ALLOW_OVERWRITE_ON_CREATE

            final_description = (description or skill_name).strip()
            final_content = (content or final_description).strip()

            if existing:
                if not allow_overwrite:
                    return {
                        "error": f"Skill already exists: {skill_name}",
                        "hint": "Use overwrite=true to update existing skill.",
                    }

                sid = str(getattr(existing, "id", "") or "")
                updated = Skills.update_skill_by_id(
                    sid,
                    {
                        "name": skill_name,
                        "description": final_description,
                        "content": final_content,
                        "is_active": True,
                    },
                )
                await self._emit_status(
                    __event_emitter__,
                    self._t(lang, "status_create_overwrite_done", name=skill_name),
                    done=True,
                )
                return {
                    "success": True,
                    "action": "updated",
                    "id": str(getattr(updated, "id", "") or sid),
                    "name": skill_name,
                }

            new_skill = Skills.insert_new_skill(
                user_id=user_id,
                form_data=SkillForm(
                    id=str(uuid.uuid4()),
                    name=skill_name,
                    description=final_description,
                    content=final_content,
                    meta=SkillMeta(),
                    is_active=True,
                ),
            )

            await self._emit_status(
                __event_emitter__,
                self._t(lang, "status_create_done", name=skill_name),
                done=True,
            )
            return {
                "success": True,
                "action": "created",
                "id": str(getattr(new_skill, "id", "") or ""),
                "name": skill_name,
            }
        except Exception as e:
            msg = (
                self._t(lang, "err_unavailable")
                if str(e) == "skills_model_unavailable"
                else str(e)
            )
            await self._emit_status(__event_emitter__, msg, done=True)
            logger.error(f"create_skill failed: {msg}", exc_info=True)
            return {"error": msg}

    async def update_skill(
        self,
        skill_id: str = "",
        name: str = "",
        new_name: str = "",
        description: str = "",
        content: str = "",
        is_active: Optional[bool] = None,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Any] = None,
        __event_call__: Optional[Any] = None,
        __request__: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Update one skill's fields by id or name."""
        user_ctx = await self._get_user_context(__user__, __event_call__, __request__)
        lang = user_ctx["user_language"]
        user_id = user_ctx["user_id"]

        try:
            self._require_skills_model()
            if not user_id:
                raise ValueError(self._t(lang, "err_user_required"))

            await self._emit_status(__event_emitter__, self._t(lang, "status_updating"))

            skill = self._find_skill(user_id=user_id, skill_id=skill_id, name=name)
            if not skill:
                raise ValueError(self._t(lang, "err_not_found"))

            updates: Dict[str, Any] = {}
            if new_name.strip():
                updates["name"] = new_name.strip()
            if description.strip():
                updates["description"] = description.strip()
            if content.strip():
                updates["content"] = content.strip()
            if is_active is not None:
                updates["is_active"] = bool(is_active)

            if not updates:
                raise ValueError(self._t(lang, "err_no_update_fields"))

            sid = str(getattr(skill, "id", "") or "")
            updated = Skills.update_skill_by_id(sid, updates)
            updated_name = str(
                getattr(updated, "name", "")
                or updates.get("name")
                or getattr(skill, "name", "")
                or sid
            )

            await self._emit_status(
                __event_emitter__,
                self._t(lang, "status_update_done", name=updated_name),
                done=True,
            )
            return {
                "success": True,
                "id": str(getattr(updated, "id", "") or sid),
                "name": str(
                    getattr(updated, "name", "")
                    or updates.get("name")
                    or getattr(skill, "name", "")
                ),
                "updated_fields": list(updates.keys()),
            }
        except Exception as e:
            msg = (
                self._t(lang, "err_unavailable")
                if str(e) == "skills_model_unavailable"
                else str(e)
            )
            await self._emit_status(__event_emitter__, msg, done=True)
            return {"error": msg}

    async def delete_skill(
        self,
        skill_id: str = "",
        name: str = "",
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Any] = None,
        __event_call__: Optional[Any] = None,
        __request__: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Delete one skill by id or name."""
        user_ctx = await self._get_user_context(__user__, __event_call__, __request__)
        lang = user_ctx["user_language"]
        user_id = user_ctx["user_id"]

        try:
            self._require_skills_model()
            if not user_id:
                raise ValueError(self._t(lang, "err_user_required"))

            await self._emit_status(__event_emitter__, self._t(lang, "status_deleting"))

            skill = self._find_skill(user_id=user_id, skill_id=skill_id, name=name)
            if not skill:
                raise ValueError(self._t(lang, "err_not_found"))

            sid = str(getattr(skill, "id", "") or "")
            sname = str(getattr(skill, "name", "") or "")
            Skills.delete_skill_by_id(sid)
            deleted_name = sname or sid or "unknown"

            await self._emit_status(
                __event_emitter__,
                self._t(lang, "status_delete_done", name=deleted_name),
                done=True,
            )
            return {
                "success": True,
                "id": sid,
                "name": sname,
            }
        except Exception as e:
            msg = (
                self._t(lang, "err_unavailable")
                if str(e) == "skills_model_unavailable"
                else str(e)
            )
            await self._emit_status(__event_emitter__, msg, done=True)
            return {"error": msg}
