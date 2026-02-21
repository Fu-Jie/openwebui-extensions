"""
title: Smart Mind Map
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
version: 1.0.0
openwebui_id: 3094c59a-b4dd-4e0c-9449-15e2dd547dc4
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxyZWN0IHg9IjE2IiB5PSIxNiIgd2lkdGg9IjYiIGhlaWdodD0iNiIgcng9IjEiLz48cmVjdCB4PSIyIiB5PSIxNiIgd2lkdGg9IjYiIGhlaWdodD0iNiIgcng9IjEiLz48cmVjdCB4PSI5IiB5PSIyIiB3aWR0aD0iNiIgaGVpZ2h0PSI2IiByeD0iMSIvPjxwYXRoIGQ9Ik01IDE2di0zYTEgMSAwIDAgMSAxLTFoMTJhMSAxIDAgMCAxIDEgMXYzIi8+PHBhdGggZD0iTTEyIDEyVjgiLz48L3N2Zz4=
description: Intelligently analyzes text content and generates interactive mind maps to help users structure and visualize knowledge.
"""

import logging
import os
import re
import time
import json
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable, Dict, Optional
from zoneinfo import ZoneInfo

from fastapi import Request
from pydantic import BaseModel, Field

from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users

try:
    from open_webui.env import VERSION as open_webui_version
except ImportError:
    open_webui_version = "0.0.0"


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

TRANSLATIONS = {
    "en-US": {
        "status_starting": "Smart Mind Map is starting, generating mind map for you...",
        "error_no_content": "Unable to retrieve valid user message content.",
        "error_text_too_short": "Text content is too short ({len} characters), unable to perform effective analysis. Please provide at least {min_len} characters of text.",
        "status_analyzing": "Smart Mind Map: Analyzing text structure in depth...",
        "status_drawing": "Smart Mind Map: Drawing completed!",
        "notification_success": "Mind map has been generated, {user_name}!",
        "error_processing": "Smart Mind Map processing failed: {error}",
        "error_user_facing": "Sorry, Smart Mind Map encountered an error during processing: {error}.\nPlease check the Open WebUI backend logs for more details.",
        "status_failed": "Smart Mind Map: Processing failed.",
        "notification_failed": "Smart Mind Map generation failed, {user_name}!",
        "status_rendering_image": "Smart Mind Map: Rendering image...",
        "status_image_generated": "Smart Mind Map: Image generated!",
        "notification_image_success": "Mind map image has been generated, {user_name}!",
        "ui_title": "🧠 Smart Mind Map",
        "ui_user": "User:",
        "ui_time": "Time:",
        "ui_download_png": "PNG",
        "ui_download_svg": "SVG",
        "ui_download_md": "Markdown",
        "ui_zoom_out": "-",
        "ui_zoom_reset": "Reset",
        "ui_zoom_in": "+",
        "ui_depth_select": "Expand Level",
        "ui_depth_all": "Expand All",
        "ui_depth_2": "Level 2",
        "ui_depth_3": "Level 3",
        "ui_fullscreen": "Fullscreen",
        "ui_theme": "Theme",
        "ui_footer": "<b>Powered by</b> <a href='https://markmap.js.org/' target='_blank' rel='noopener noreferrer'>Markmap</a>",
        "html_error_missing_content": "⚠️ Unable to load mind map: Missing valid content.",
        "html_error_load_failed": "⚠️ Resource loading failed, please try again later.",
        "js_done": "Done",
        "js_failed": "Failed",
        "js_generating": "Generating...",
        "js_filename": "mindmap.png",
        "js_upload_failed": "Upload failed: ",
        "md_image_alt": "🧠 Mind Map",
    },
    "zh-CN": {
        "status_starting": "思维导图已启动，正在为您生成思维导图...",
        "error_no_content": "无法获取有效的用户消息内容。",
        "error_text_too_short": "文本内容过短（{len}字符），无法进行有效分析。请提供至少{min_len}字符的文本。",
        "status_analyzing": "思维导图：深入分析文本结构...",
        "status_drawing": "思维导图：绘制完成！",
        "notification_success": "思维导图已生成，{user_name}！",
        "error_processing": "思维导图处理失败：{error}",
        "error_user_facing": "抱歉，思维导图在处理时遇到错误：{error}。\n请检查Open WebUI后端日志获取更多详情。",
        "status_failed": "思维导图：处理失败。",
        "notification_failed": "思维导图生成失败，{user_name}！",
        "status_rendering_image": "思维导图：正在渲染图片...",
        "status_image_generated": "思维导图：图片已生成！",
        "notification_image_success": "思维导图图片已生成，{user_name}！",
        "ui_title": "🧠 智能思维导图",
        "ui_user": "用户：",
        "ui_time": "时间：",
        "ui_download_png": "PNG",
        "ui_download_svg": "SVG",
        "ui_download_md": "Markdown",
        "ui_zoom_out": "缩小",
        "ui_zoom_reset": "重置",
        "ui_zoom_in": "放大",
        "ui_depth_select": "展开层级",
        "ui_depth_all": "全部展开",
        "ui_depth_2": "展开 2 级",
        "ui_depth_3": "展开 3 级",
        "ui_fullscreen": "全屏",
        "ui_theme": "主题",
        "ui_footer": "<b>Powered by</b> <a href='https://markmap.js.org/' target='_blank' rel='noopener noreferrer'>Markmap</a>",
        "html_error_missing_content": "⚠️ 无法加载思维导图：缺少有效内容。",
        "html_error_load_failed": "⚠️ 资源加载失败，请稍后重试。",
        "js_done": "完成",
        "js_failed": "失败",
        "js_generating": "生成中...",
        "js_filename": "思维导图.png",
        "js_upload_failed": "上传失败：",
        "md_image_alt": "🧠 思维导图",
    },
    "zh-HK": {
        "status_starting": "思維導圖已啟動，正在為您生成思維導圖...",
        "error_no_content": "無法獲取有效的用戶消息內容。",
        "error_text_too_short": "文本內容過短（{len}字元），無法進行有效分析。請提供至少{min_len}字元的文本。",
        "status_analyzing": "思維導圖：深入分析文本結構...",
        "status_drawing": "思維導圖：繪製完成！",
        "notification_success": "思維導圖已生成，{user_name}！",
        "error_processing": "思維導圖處理失敗：{error}",
        "error_user_facing": "抱歉，思維導圖在處理時遇到錯誤：{error}。\n請檢查Open WebUI後端日誌獲取更多詳情。",
        "status_failed": "思維導圖：處理失敗。",
        "notification_failed": "思維導圖生成失敗，{user_name}！",
        "status_rendering_image": "思維導圖：正在渲染圖片...",
        "status_image_generated": "思維導圖：圖片已生成！",
        "notification_image_success": "思維導圖圖片已生成，{user_name}！",
        "ui_title": "🧠 智能思維導圖",
        "ui_user": "用戶：",
        "ui_time": "時間：",
        "ui_download_png": "PNG",
        "ui_download_svg": "SVG",
        "ui_download_md": "Markdown",
        "ui_zoom_out": "縮小",
        "ui_zoom_reset": "重置",
        "ui_zoom_in": "放大",
        "ui_depth_select": "展開層級",
        "ui_depth_all": "全部展開",
        "ui_depth_2": "展開 2 級",
        "ui_depth_3": "展開 3 級",
        "ui_fullscreen": "全屏",
        "ui_theme": "主題",
        "ui_footer": "<b>Powered by</b> <a href='https://markmap.js.org/' target='_blank' rel='noopener noreferrer'>Markmap</a>",
        "html_error_missing_content": "⚠️ 無法加載思維導圖：缺少有效內容。",
        "html_error_load_failed": "⚠️ 資源加載失敗，請稍後重試。",
        "js_done": "完成",
        "js_failed": "失敗",
        "js_generating": "生成中...",
        "js_filename": "思維導圖.png",
        "js_upload_failed": "上傳失敗：",
        "md_image_alt": "🧠 思維導圖",
    },
    "zh-TW": {
        "status_starting": "思維導圖已啟動，正在為您生成思維導圖...",
        "error_no_content": "無法獲取有效的用戶消息內容。",
        "error_text_too_short": "文本內容過短（{len}字元），無法進行有效分析。請提供至少{min_len}字元的文本。",
        "status_analyzing": "思維導圖：深入分析文本結構...",
        "status_drawing": "思維導圖：繪製完成！",
        "notification_success": "思維導圖已生成，{user_name}！",
        "error_processing": "思維導圖處理失敗：{error}",
        "error_user_facing": "抱歉，思維導圖在處理時遇到錯誤：{error}。\n請檢查Open WebUI後端日誌獲取更多詳情。",
        "status_failed": "思維導圖：處理失敗。",
        "notification_failed": "思維導圖生成失敗，{user_name}！",
        "status_rendering_image": "思維導圖：正在渲染圖片...",
        "status_image_generated": "思維導圖：圖片已生成！",
        "notification_image_success": "思維導圖圖片已生成，{user_name}！",
        "ui_title": "🧠 智能思維導圖",
        "ui_user": "用戶：",
        "ui_time": "時間：",
        "ui_download_png": "PNG",
        "ui_download_svg": "SVG",
        "ui_download_md": "Markdown",
        "ui_zoom_out": "縮小",
        "ui_zoom_reset": "重置",
        "ui_zoom_in": "放大",
        "ui_depth_select": "展開層級",
        "ui_depth_all": "全部展開",
        "ui_depth_2": "展開 2 級",
        "ui_depth_3": "展開 3 級",
        "ui_fullscreen": "全屏",
        "ui_theme": "主題",
        "ui_footer": "<b>Powered by</b> <a href='https://markmap.js.org/' target='_blank' rel='noopener noreferrer'>Markmap</a>",
        "html_error_missing_content": "⚠️ 無法加載思維導圖：缺少有效內容。",
        "html_error_load_failed": "⚠️ 資源加載失敗，請稍後重試。",
        "js_done": "完成",
        "js_failed": "失敗",
        "js_generating": "生成中...",
        "js_filename": "思維導圖.png",
        "js_upload_failed": "上傳失敗：",
        "md_image_alt": "🧠 思維導圖",
    },
    "ko-KR": {
        "status_starting": "스마트 마인드맵이 시작되었습니다, 마인드맵을 생성 중입니다...",
        "error_no_content": "유효한 사용자 메시지 내용을 가져올 수 없습니다.",
        "error_text_too_short": "텍스트 내용이 너무 짧아({len}자), 효과적인 분석을 수행할 수 없습니다. 최소 {min_len}자 이상의 텍스트를 제공해 주세요.",
        "status_analyzing": "스마트 마인드맵: 텍스트 구조 심층 분석 중...",
        "status_drawing": "스마트 마인드맵: 그리기 완료!",
        "notification_success": "마인드맵이 생성되었습니다, {user_name}님!",
        "error_processing": "스마트 마인드맵 처리 실패: {error}",
        "error_user_facing": "죄송합니다, 스마트 마인드맵 처리 중 오류가 발생했습니다: {error}.\n자세한 내용은 Open WebUI 백엔드 로그를 확인해 주세요.",
        "status_failed": "스마트 마인드맵: 처리 실패.",
        "notification_failed": "스마트 마인드맵 생성 실패, {user_name}님!",
        "status_rendering_image": "스마트 마인드맵: 이미지 렌더링 중...",
        "status_image_generated": "스마트 마인드맵: 이미지 생성됨!",
        "notification_image_success": "마인드맵 이미지가 생성되었습니다, {user_name}님!",
        "ui_title": "🧠 스마트 마인드맵",
        "ui_user": "사용자:",
        "ui_time": "시간:",
        "ui_download_png": "PNG",
        "ui_download_svg": "SVG",
        "ui_download_md": "Markdown",
        "ui_zoom_out": "-",
        "ui_zoom_reset": "초기화",
        "ui_zoom_in": "+",
        "ui_depth_select": "레벨 확장",
        "ui_depth_all": "모두 확장",
        "ui_depth_2": "레벨 2",
        "ui_depth_3": "레벨 3",
        "ui_fullscreen": "전체 화면",
        "ui_theme": "테마",
        "ui_footer": "<b>Powered by</b> <a href='https://markmap.js.org/' target='_blank' rel='noopener noreferrer'>Markmap</a>",
        "html_error_missing_content": "⚠️ 마인드맵을 로드할 수 없습니다: 유효한 내용이 없습니다.",
        "html_error_load_failed": "⚠️ 리소스 로드 실패, 나중에 다시 시도해 주세요.",
        "js_done": "완료",
        "js_failed": "실패",
        "js_generating": "생성 중...",
        "js_filename": "mindmap.png",
        "js_upload_failed": "업로드 실패: ",
        "md_image_alt": "🧠 마인드맵",
    },
    "ja-JP": {
        "status_starting": "スマートマインドマップが起動しました。マインドマップを生成しています...",
        "error_no_content": "有効なユーザーメッセージの内容を取得できませんでした。",
        "error_text_too_short": "テキストの内容が短すぎるため（{len}文字）、効果的な分析を実行できません。少なくとも{min_len}文字のテキストを提供してください。",
        "status_analyzing": "スマートマインドマップ：テキスト構造を詳細に分析中...",
        "status_drawing": "スマートマインドマップ：描画完了！",
        "notification_success": "マインドマップが生成されました、{user_name}さん！",
        "error_processing": "スマートマインドマップ処理失敗：{error}",
        "error_user_facing": "申し訳ありません、スマートマインドマップの処理中にエラーが発生しました：{error}。\n詳細については、Open WebUIバックエンドログを確認してください。",
        "status_failed": "スマートマインドマップ：処理失敗。",
        "notification_failed": "スマートマインドマップ生成失敗、{user_name}さん！",
        "status_rendering_image": "スマートマインドマップ：画像レンダリング中...",
        "status_image_generated": "スマートマインドマップ：画像生成完了！",
        "notification_image_success": "マインドマップ画像が生成されました、{user_name}さん！",
        "ui_title": "🧠 スマートマインドマップ",
        "ui_user": "ユーザー：",
        "ui_time": "時間：",
        "ui_download_png": "PNG",
        "ui_download_svg": "SVG",
        "ui_download_md": "Markdown",
        "ui_zoom_out": "-",
        "ui_zoom_reset": "リセット",
        "ui_zoom_in": "+",
        "ui_depth_select": "レベル展開",
        "ui_depth_all": "すべて展開",
        "ui_depth_2": "レベル2",
        "ui_depth_3": "レベル3",
        "ui_fullscreen": "全画面",
        "ui_theme": "テーマ",
        "ui_footer": "<b>Powered by</b> <a href='https://markmap.js.org/' target='_blank' rel='noopener noreferrer'>Markmap</a>",
        "html_error_missing_content": "⚠️ マインドマップを読み込めません：有効なコンテンツがありません。",
        "html_error_load_failed": "⚠️ リソースの読み込みに失敗しました。後でもう一度お試しください。",
        "js_done": "完了",
        "js_failed": "失敗",
        "js_generating": "生成中...",
        "js_filename": "mindmap.png",
        "js_upload_failed": "アップロード失敗：",
        "md_image_alt": "🧠 マインドマップ",
    },
    "fr-FR": {
        "status_starting": "Smart Mind Map démarre, génération de la carte heuristique en cours...",
        "error_no_content": "Impossible de récupérer le contenu valide du message utilisateur.",
        "error_text_too_short": "Le contenu du texte est trop court ({len} caractères), impossible d'effectuer une analyse efficace. Veuillez fournir au moins {min_len} caractères de texte.",
        "status_analyzing": "Smart Mind Map : Analyse approfondie de la structure du texte...",
        "status_drawing": "Smart Mind Map : Dessin terminé !",
        "notification_success": "La carte heuristique a été générée, {user_name} !",
        "error_processing": "Échec du traitement de Smart Mind Map : {error}",
        "error_user_facing": "Désolé, Smart Mind Map a rencontré une erreur lors du traitement : {error}.\nVeuillez vérifier les journaux backend d'Open WebUI pour plus de détails.",
        "status_failed": "Smart Mind Map : Échec du traitement.",
        "notification_failed": "Échec de la génération de la carte heuristique, {user_name} !",
        "status_rendering_image": "Smart Mind Map : Rendu de l'image...",
        "status_image_generated": "Smart Mind Map : Image générée !",
        "notification_image_success": "L'image de la carte heuristique a été générée, {user_name} !",
        "ui_title": "🧠 Smart Mind Map",
        "ui_user": "Utilisateur :",
        "ui_time": "Heure :",
        "ui_download_png": "PNG",
        "ui_download_svg": "SVG",
        "ui_download_md": "Markdown",
        "ui_zoom_out": "-",
        "ui_zoom_reset": "Rénitialiser",
        "ui_zoom_in": "+",
        "ui_depth_select": "Niveau d'expansion",
        "ui_depth_all": "Tout développer",
        "ui_depth_2": "Niveau 2",
        "ui_depth_3": "Niveau 3",
        "ui_fullscreen": "Plein écran",
        "ui_theme": "Thème",
        "ui_footer": "<b>Powered by</b> <a href='https://markmap.js.org/' target='_blank' rel='noopener noreferrer'>Markmap</a>",
        "html_error_missing_content": "⚠️ Impossible de charger la carte heuristique : contenu valide manquant.",
        "html_error_load_failed": "⚠️ Échec du chargement des ressources, veuillez réessayer plus tard.",
        "js_done": "Terminé",
        "js_failed": "Échec",
        "js_generating": "Génération...",
        "js_filename": "carte_heuristique.png",
        "js_upload_failed": "Échec du téléchargement : ",
        "md_image_alt": "🧠 Carte Heuristique",
    },
    "de-DE": {
        "status_starting": "Smart Mind Map startet, Mindmap wird für Sie erstellt...",
        "error_no_content": "Gültiger Inhalt der Benutzernachricht konnte nicht abgerufen werden.",
        "error_text_too_short": "Der Textinhalt ist zu kurz ({len} Zeichen), eine effektive Analyse ist nicht möglich. Bitte geben Sie mindestens {min_len} Zeichen Text an.",
        "status_analyzing": "Smart Mind Map: Detaillierte Analyse der Textstruktur...",
        "status_drawing": "Smart Mind Map: Zeichnen abgeschlossen!",
        "notification_success": "Mindmap wurde erstellt, {user_name}!",
        "error_processing": "Smart Mind Map Verarbeitung fehlgeschlagen: {error}",
        "error_user_facing": "Entschuldigung, bei der Verarbeitung von Smart Mind Map ist ein Fehler aufgetreten: {error}.\nBitte überprüfen Sie die Open WebUI Backend-Protokolle für weitere Details.",
        "status_failed": "Smart Mind Map: Verarbeitung fehlgeschlagen.",
        "notification_failed": "Erstellung der Mindmap fehlgeschlagen, {user_name}!",
        "status_rendering_image": "Smart Mind Map: Bild wird gerendert...",
        "status_image_generated": "Smart Mind Map: Bild erstellt!",
        "notification_image_success": "Mindmap-Bild wurde erstellt, {user_name}!",
        "ui_title": "🧠 Smart Mind Map",
        "ui_user": "Benutzer:",
        "ui_time": "Zeit:",
        "ui_download_png": "PNG",
        "ui_download_svg": "SVG",
        "ui_download_md": "Markdown",
        "ui_zoom_out": "-",
        "ui_zoom_reset": "Zurücksetzen",
        "ui_zoom_in": "+",
        "ui_depth_select": "Ebene erweitern",
        "ui_depth_all": "Alles erweitern",
        "ui_depth_2": "Ebene 2",
        "ui_depth_3": "Ebene 3",
        "ui_fullscreen": "Vollbild",
        "ui_theme": "Thema",
        "ui_footer": "<b>Powered by</b> <a href='https://markmap.js.org/' target='_blank' rel='noopener noreferrer'>Markmap</a>",
        "html_error_missing_content": "⚠️ Mindmap kann nicht geladen werden: Gültiger Inhalt fehlt.",
        "html_error_load_failed": "⚠️ Ressourcenladen fehlgeschlagen, bitte versuchen Sie es später erneut.",
        "js_done": "Fertig",
        "js_failed": "Fehlgeschlagen",
        "js_generating": "Generiere...",
        "js_filename": "mindmap.png",
        "js_upload_failed": "Upload fehlgeschlagen: ",
        "md_image_alt": "🧠 Mindmap",
    },
    "es-ES": {
        "status_starting": "Smart Mind Map se está iniciando, generando mapa mental para usted...",
        "error_no_content": "No se puede recuperar el contenido válido del mensaje del usuario.",
        "error_text_too_short": "El contenido del texto es demasiado corto ({len} caracteres), no se puede realizar un análisis efectivo. Proporcione al menos {min_len} caracteres de texto.",
        "status_analyzing": "Smart Mind Map: Analizando la estructura del texto en profundidad...",
        "status_drawing": "Smart Mind Map: ¡Dibujo completado!",
        "notification_success": "¡El mapa mental ha sido generado, {user_name}!",
        "error_processing": "Falló el procesamiento de Smart Mind Map: {error}",
        "error_user_facing": "Lo sentimos, Smart Mind Map encontró un error durante el procesamiento: {error}.\nConsulte los registros del backend de Open WebUI para más detalles.",
        "status_failed": "Smart Mind Map: Procesamiento fallido.",
        "notification_failed": "¡La generación del mapa mental falló, {user_name}!",
        "status_rendering_image": "Smart Mind Map: Renderizando imagen...",
        "status_image_generated": "Smart Mind Map: ¡Imagen generada!",
        "notification_image_success": "¡La imagen del mapa mental ha sido generada, {user_name}!",
        "ui_title": "🧠 Smart Mind Map",
        "ui_user": "Usuario:",
        "ui_time": "Hora:",
        "ui_download_png": "PNG",
        "ui_download_svg": "SVG",
        "ui_download_md": "Markdown",
        "ui_zoom_out": "-",
        "ui_zoom_reset": "Restablecer",
        "ui_zoom_in": "+",
        "ui_depth_select": "Expandir Nivel",
        "ui_depth_all": "Expandir Todo",
        "ui_depth_2": "Nivel 2",
        "ui_depth_3": "Nivel 3",
        "ui_fullscreen": "Pantalla completa",
        "ui_theme": "Tema",
        "ui_footer": "<b>Powered by</b> <a href='https://markmap.js.org/' target='_blank' rel='noopener noreferrer'>Markmap</a>",
        "html_error_missing_content": "⚠️ No se puede cargar el mapa mental: Falta contenido válido.",
        "html_error_load_failed": "⚠️ Falló la carga de recursos, inténtelo de nuevo más tarde.",
        "js_done": "Hecho",
        "js_failed": "Fallido",
        "js_generating": "Generando...",
        "js_filename": "mapa_mental.png",
        "js_upload_failed": "Carga fallida: ",
        "md_image_alt": "🧠 Mapa Mental",
    },
    "it-IT": {
        "status_starting": "Smart Mind Map si sta avviando, generazione mappa mentale in corso...",
        "error_no_content": "Impossibile recuperare il contenuto valido del messaggio utente.",
        "error_text_too_short": "Il testo è troppo breve ({len} caratteri), impossibile eseguire un'analisi efficace. Fornire almeno {min_len} caratteri di testo.",
        "status_analyzing": "Smart Mind Map: Analisi approfondita della struttura del testo...",
        "status_drawing": "Smart Mind Map: Disegno completato!",
        "notification_success": "La mappa mentale è stata generata, {user_name}!",
        "error_processing": "Elaborazione Smart Mind Map fallita: {error}",
        "error_user_facing": "Spiacenti, Smart Mind Map ha riscontrato un errore durante l'elaborazione: {error}.\nControllare i log del backend di Open WebUI per ulteriori dettagli.",
        "status_failed": "Smart Mind Map: Elaborazione fallita.",
        "notification_failed": "Generazione mappa mentale fallita, {user_name}!",
        "status_rendering_image": "Smart Mind Map: Rendering immagine...",
        "status_image_generated": "Smart Mind Map: Immagine generata!",
        "notification_image_success": "L'immagine della mappa mentale è stata generata, {user_name}!",
        "ui_title": "🧠 Smart Mind Map",
        "ui_user": "Utente:",
        "ui_time": "Ora:",
        "ui_download_png": "PNG",
        "ui_download_svg": "SVG",
        "ui_download_md": "Markdown",
        "ui_zoom_out": "-",
        "ui_zoom_reset": "Reimposta",
        "ui_zoom_in": "+",
        "ui_depth_select": "Espandi Livello",
        "ui_depth_all": "Espandi Tutto",
        "ui_depth_2": "Livello 2",
        "ui_depth_3": "Livello 3",
        "ui_fullscreen": "Schermo intero",
        "ui_theme": "Tema",
        "ui_footer": "<b>Powered by</b> <a href='https://markmap.js.org/' target='_blank' rel='noopener noreferrer'>Markmap</a>",
        "html_error_missing_content": "⚠️ Impossibile caricare la mappa mentale: Contenuto valido mancante.",
        "html_error_load_failed": "⚠️ Caricamento risorse fallito, riprovare più tardi.",
        "js_done": "Fatto",
        "js_failed": "Fallito",
        "js_generating": "Generazione...",
        "js_filename": "mappa_mentale.png",
        "js_upload_failed": "Caricamento fallito: ",
        "md_image_alt": "🧠 Mappa Mentale",
    },
    "vi-VN": {
        "status_starting": "Smart Mind Map đang khởi động, đang tạo sơ đồ tư duy cho bạn...",
        "error_no_content": "Không thể lấy nội dung tin nhắn người dùng hợp lệ.",
        "error_text_too_short": "Nội dung văn bản quá ngắn ({len} ký tự), không thể thực hiện phân tích hiệu quả. Vui lòng cung cấp ít nhất {min_len} ký tự văn bản.",
        "status_analyzing": "Smart Mind Map: Phân tích sâu cấu trúc văn bản...",
        "status_drawing": "Smart Mind Map: Vẽ hoàn tất!",
        "notification_success": "Sơ đồ tư duy đã được tạo, {user_name}!",
        "error_processing": "Xử lý Smart Mind Map thất bại: {error}",
        "error_user_facing": "Xin lỗi, Smart Mind Map đã gặp lỗi trong quá trình xử lý: {error}.\nVui lòng kiểm tra nhật ký backend Open WebUI để biết thêm chi tiết.",
        "status_failed": "Smart Mind Map: Xử lý thất bại.",
        "notification_failed": "Tạo sơ đồ tư duy thất bại, {user_name}!",
        "status_rendering_image": "Smart Mind Map: Đang render hình ảnh...",
        "status_image_generated": "Smart Mind Map: Hình ảnh đã tạo!",
        "notification_image_success": "Hình ảnh sơ đồ tư duy đã được tạo, {user_name}!",
        "ui_title": "🧠 Smart Mind Map",
        "ui_user": "Người dùng:",
        "ui_time": "Thời gian:",
        "ui_download_png": "PNG",
        "ui_download_svg": "SVG",
        "ui_download_md": "Markdown",
        "ui_zoom_out": "-",
        "ui_zoom_reset": "Đặt lại",
        "ui_zoom_in": "+",
        "ui_depth_select": "Mở rộng Cấp độ",
        "ui_depth_all": "Mở rộng Tất cả",
        "ui_depth_2": "Cấp độ 2",
        "ui_depth_3": "Cấp độ 3",
        "ui_fullscreen": "Toàn màn hình",
        "ui_theme": "Chủ đề",
        "ui_footer": "<b>Powered by</b> <a href='https://markmap.js.org/' target='_blank' rel='noopener noreferrer'>Markmap</a>",
        "html_error_missing_content": "⚠️ Không thể tải sơ đồ tư duy: Thiếu nội dung hợp lệ.",
        "html_error_load_failed": "⚠️ Tải tài nguyên thất bại, vui lòng thử lại sau.",
        "js_done": "Xong",
        "js_failed": "Thất bại",
        "js_generating": "Đang tạo...",
        "js_filename": "sodo_tuduy.png",
        "js_upload_failed": "Tải lên thất bại: ",
        "md_image_alt": "🧠 Sơ đồ Tư duy",
    },
    "id-ID": {
        "status_starting": "Smart Mind Map sedang dimulai, membuat peta pikiran untuk Anda...",
        "error_no_content": "Tidak dapat mengambil konten pesan pengguna yang valid.",
        "error_text_too_short": "Konten teks terlalu pendek ({len} karakter), tidak dapat melakukan analisis efektif. Harap berikan setidaknya {min_len} karakter teks.",
        "status_analyzing": "Smart Mind Map: Menganalisis struktur teks secara mendalam...",
        "status_drawing": "Smart Mind Map: Menggambar selesai!",
        "notification_success": "Peta pikiran telah dibuat, {user_name}!",
        "error_processing": "Pemrosesan Smart Mind Map gagal: {error}",
        "error_user_facing": "Maaf, Smart Mind Map mengalami kesalahan saat memproses: {error}.\nSilakan periksa log backend Open WebUI untuk detail lebih lanjut.",
        "status_failed": "Smart Mind Map: Pemrosesan gagal.",
        "notification_failed": "Pembuatan peta pikiran gagal, {user_name}!",
        "status_rendering_image": "Smart Mind Map: Merender gambar...",
        "status_image_generated": "Smart Mind Map: Gambar dibuat!",
        "notification_image_success": "Gambar peta pikiran telah dibuat, {user_name}!",
        "ui_title": "🧠 Smart Mind Map",
        "ui_user": "Pengguna:",
        "ui_time": "Waktu:",
        "ui_download_png": "PNG",
        "ui_download_svg": "SVG",
        "ui_download_md": "Markdown",
        "ui_zoom_out": "-",
        "ui_zoom_reset": "Atur Ulang",
        "ui_zoom_in": "+",
        "ui_depth_select": "Perluas Level",
        "ui_depth_all": "Perluas Semua",
        "ui_depth_2": "Level 2",
        "ui_depth_3": "Level 3",
        "ui_fullscreen": "Layar Penuh",
        "ui_theme": "Tema",
        "ui_footer": "<b>Powered by</b> <a href='https://markmap.js.org/' target='_blank' rel='noopener noreferrer'>Markmap</a>",
        "html_error_missing_content": "⚠️ Tidak dapat memuat peta pikiran: Konten valid hilang.",
        "html_error_load_failed": "⚠️ Gagal memuat sumber daya, silakan coba lagi nanti.",
        "js_done": "Selesai",
        "js_failed": "Gagal",
        "js_generating": "Membuat...",
        "js_filename": "peta_pikiran.png",
        "js_upload_failed": "Unggah gagal: ",
        "md_image_alt": "🧠 Peta Pikiran",
    },
}

SYSTEM_PROMPT_MINDMAP_ASSISTANT = """
You are a professional mind map generation assistant, capable of efficiently analyzing long-form text provided by users and structuring its core themes, key concepts, branches, and sub-branches into standard Markdown list syntax for rendering by Markmap.js.

Please strictly follow these guidelines:
-   **Language**: All output must be in the exact same language as the input text (the text you are analyzing).
-   **Format Consistency**: Even if this system prompt is in English, if the user input is in Chinese, the mind map content must be in Chinese. If input is Japanese, output Japanese.
-   **Format**: Your output must strictly be in Markdown list format, wrapped with ```markdown and ```.
    -   Use `#` to define the central theme (root node).
    -   Use `-` with two-space indentation to represent branches and sub-branches.
-   **Root Node (Central Theme) — Strict Length Limits**:
    -   The `#` root node must be an ultra-compact title, like a newspaper headline. It should be a keyword or short phrase, NEVER a full sentence.
    -   **CJK scripts (Chinese, Japanese, Korean)**: Maximum **10 characters** (e.g., `# 老人缓解呼吸困难方法` ✓ / `# 老人在家时感到呼吸困难的缓解方法` ✗)
    -   **Latin-script languages (English, Spanish, French, Italian, Portuguese)**: Maximum **5 words or 35 characters** (e.g., `# Methods to Relieve Dyspnea` ✓ / `# How Elderly People Can Relieve Breathing Difficulty at Home` ✗)
    -   **German, Dutch or languages with long compound words**: Maximum **4 words or 30 characters**
    -   **Arabic, Hebrew and other RTL scripts**: Maximum **5 words or 25 characters**
    -   **All other languages**: Maximum **5 words or 30 characters**
    -   If the identified theme would exceed the limit, distill it further into the single most essential keyword or 2-3 word phrase.
-   **Branch Node Content**:
    -   Identify main concepts as first-level list items.
    -   Identify supporting details or sub-concepts as nested list items.
    -   Node content should be concise and clear, avoiding verbosity.
-   **Output Markdown syntax only**: Do not include any additional greetings, explanations, or guiding text.
-   **If text is too short or cannot generate a valid mind map**: Output a simple Markdown list indicating inability to generate, for example:
    ```markdown
    # Unable to Generate Mind Map
    - Reason: Insufficient or unclear text content
    ```
-   **Awareness of Target Audience Layout**: You will be provided `Target Rendering Mode`.
    -   If `Target Rendering Mode` is `direct`: The client has massive horizontal space but limited scrolling vertically. Extract more first-level concepts to make the mind map spread wide like a sprawling fan, rather than deep single columns.
    -   If `Target Rendering Mode` is `legacy`: The client uses a narrow, portrait sidebar. Extract fewer top-level nodes, and break points into deeper, tighter sub-branches so the map grows vertically downwards.
"""

USER_PROMPT_GENERATE_MINDMAP = """
Please analyze the following long-form text and structure its core themes, key concepts, branches, and sub-branches into standard Markdown list syntax for Markmap.js rendering.

---
**User Context Information:**
User Name: {user_name}
Current Date & Time: {current_date_time_str}
Current Weekday: {current_weekday}
Current Timezone: {current_timezone_str}
User Language: {user_language}
Target Rendering Mode: Auto-adapting (Dynamic width based on viewport)
---

**Long-form Text Content:**
{long_text_content}
"""

HTML_WRAPPER_TEMPLATE = """
<!-- OPENWEBUI_PLUGIN_OUTPUT -->
<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            margin: 0; 
            padding: 2px; 
            background-color: transparent; 
        }
        #main-container { 
            display: flex; 
            flex-direction: column; 
            gap: 20px; 
            align-items: stretch; 
            width: 100%;
        }
        .plugin-item { 
            width: 100%; 
            border-radius: 12px; 
            overflow: visible; 
            transition: all 0.3s ease;
        }
        .plugin-item:hover {
            transform: translateY(-2px);
        }
        /* STYLES_INSERTION_POINT */
    </style>
</head>
<body>
    <div id="main-container">
        <!-- CONTENT_INSERTION_POINT -->
    </div>
    <!-- SCRIPTS_INSERTION_POINT -->
</body>
</html>
"""

CSS_TEMPLATE_MINDMAP = """
        :root {
            --primary-color: #1e88e5;
            --secondary-color: #43a047;
            --background-color: #f4f6f8;
            --card-bg-color: #ffffff;
            --text-color: #000000;
            --link-color: #546e7a;
            --node-stroke-color: #90a4ae;
            --muted-text-color: #546e7a;
            --border-color: #e0e0e0;
            --header-gradient: linear-gradient(135deg, var(--secondary-color), var(--primary-color));
            --shadow: 0 10px 20px rgba(0, 0, 0, 0.06);
            --border-radius: 12px;
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        .theme-dark {
            --primary-color: #64b5f6;
            --secondary-color: #81c784;
            --background-color: #111827;
            --card-bg-color: #1f2937;
            --text-color: #ffffff;
            --link-color: #cbd5e1;
            --node-stroke-color: #94a3b8;
            --muted-text-color: #9ca3af;
            --border-color: #374151;
            --header-gradient: linear-gradient(135deg, #0ea5e9, #22c55e);
            --shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
        }
        html, body {
            margin: 0;
            padding: 0;
            width: 100vw;
            height: 100vh;
            background: var(--card-bg-color);
            overflow: hidden;
        }
        .mindmap-container-wrapper {
            font-family: var(--font-family);
            line-height: 1.6;
            color: var(--text-color);
            margin: 0;
            padding: 0;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            display: flex;
            flex-direction: column;
            background: var(--card-bg-color);
            width: 100vw;
            height: 100vh;
            box-sizing: border-box;
            overflow: hidden;
            border: none;
            border-radius: 0;
            box-shadow: none;
        }
        .header {
            background: var(--card-bg-color);
            color: var(--text-color);
            padding: 12px 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            flex-shrink: 0;
            border-bottom: 1px solid var(--border-color);
            z-index: 10;
        }
        .header-top {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .header h1 {
            margin: 0;
            font-size: 1.2em;
            font-weight: 600;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .header-credits {
            font-size: 0.8em;
            color: var(--muted-text-color);
            opacity: 0.8;
            white-space: nowrap;
        }
        .header-credits a {
            color: var(--primary-color);
            text-decoration: none;
            border-bottom: 1px dotted var(--link-color);
        }
        
        .content-area {
            padding: 0;
            flex: 1 1 0;
            background: transparent;
            position: relative;
            overflow: hidden;
            width: 100%;
            min-height: 0;
            /* Height will be computed dynamically by JS below */
        }
        .markmap-container {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: var(--card-bg-color);
        }
        .markmap-container svg {
            width: 100%;
            height: 100%;
            display: block;
        }
        .markmap-container svg text {
            fill: var(--text-color) !important;
            font-family: var(--font-family);
        }
        .markmap-container svg foreignObject,
        .markmap-container svg .markmap-foreign,
        .markmap-container svg .markmap-foreign div {
            color: var(--text-color) !important;
            font-family: var(--font-family);
        }
        .markmap-container svg .markmap-link {
            stroke: var(--link-color) !important;
            stroke-opacity: 0.6;
        }
        .theme-dark .markmap-node circle {
            fill: var(--card-bg-color) !important;
        }
        .markmap-container svg .markmap-node circle,
        .markmap-container svg .markmap-node rect {
            stroke: var(--node-stroke-color) !important;
        }
        .control-rows {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            margin-left: auto; /* Push controls to the right */
        }
        .btn-group {
            display: inline-flex;
            gap: 4px;
            align-items: center;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 2px;
            background: var(--background-color);
        }
        .control-btn {
            background-color: transparent;
            color: var(--text-color);
            border: none;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            height: 28px;
            box-sizing: border-box;
            opacity: 0.8;
        }
        .control-btn:hover {
            background-color: var(--card-bg-color);
            opacity: 1;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .control-btn:active {
            transform: translateY(1px);
        }
        .control-btn.primary { 
            background-color: var(--primary-color);
            color: white;
            opacity: 1;
        }
        .control-btn.primary:hover {
            box-shadow: 0 2px 5px rgba(30,136,229,0.3);
        }
        
        select.control-btn {
            appearance: none;
            padding-right: 28px;
            background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23FFFFFF%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E");
            background-repeat: no-repeat;
            background-position: right 8px center;
            background-size: 10px;
        }
        .control-btn option {
            background-color: var(--card-bg-color);
            color: var(--text-color);
        }
        .error-message {
            color: #c62828;
            background-color: #ffcdd2;
            border: 1px solid #ef9a9a;
            padding: 14px;
            border-radius: 8px;
            font-weight: 500;
            font-size: 1em;
            margin: 10px;
        }

        /* Mobile Responsive Adjustments */
        @media screen and (max-width: 768px) {
            .mindmap-container-wrapper {
                min-height: 400px;
                height: 80vh;
            }
            .header {
                flex-direction: column;
                gap: 10px;
            }
            .btn-group {
                padding: 2px;
            }
            .control-btn {
                padding: 4px 6px;
                font-size: 0.75em;
                height: 28px;
            }
            select.control-btn {
                padding-right: 20px;
                background-position: right 4px center;
            }
        }
"""

CONTENT_TEMPLATE_MINDMAP = """
        <div class="mindmap-container-wrapper">
            <div class="header">
                <div class="header-top">
                    <h1>{t_ui_title}</h1>
                    <div class="header-credits">
                        <span>{t_ui_footer}</span>
                    </div>
                    <div class="control-rows">
                        <div class="btn-group">
                            <button id="download-png-btn-{unique_id}" class="control-btn primary" title="{t_ui_download_png}">PNG</button>
                            <button id="download-svg-btn-{unique_id}" class="control-btn" title="{t_ui_download_svg}">SVG</button>
                            <button id="download-md-btn-{unique_id}" class="control-btn" title="{t_ui_download_md}">MD</button>
                        </div>
                        <div class="btn-group">
                            <button id="zoom-out-btn-{unique_id}" class="control-btn" title="{t_ui_zoom_out}">－</button>
                            <button id="zoom-reset-btn-{unique_id}" class="control-btn" title="{t_ui_zoom_reset}">↺</button>
                            <button id="zoom-in-btn-{unique_id}" class="control-btn" title="{t_ui_zoom_in}">＋</button>
                        </div>
                        <div class="btn-group">
                            <select id="depth-select-{unique_id}" class="control-btn" title="{t_ui_depth_select}">
                                <option value="0" selected>{t_ui_depth_all}</option>
                                <option value="2">{t_ui_depth_2}</option>
                                <option value="3">{t_ui_depth_3}</option>
                            </select>
                            <button id="fullscreen-btn-{unique_id}" class="control-btn" title="{t_ui_fullscreen}">⛶</button>
                            <button id="theme-toggle-btn-{unique_id}" class="control-btn" title="{t_ui_theme}">◑</button>
                        </div>
                    </div>
                </div>
            </div>
            <div class="content-area">
                <div class="markmap-container" id="markmap-container-{unique_id}"></div>
            </div>
        </div>
        
        <script type="text/template" id="markdown-source-{unique_id}">{markdown_syntax}</script>
"""

SCRIPT_TEMPLATE_MINDMAP = """
    <script>
      (function() {
        const uniqueId = {unique_id_json};
        const i18n = {i18n_json};

        const loadScriptOnce = (src, checkFn) => {
            if (checkFn()) return Promise.resolve();
            return new Promise((resolve, reject) => {
                const existing = document.querySelector(`script[data-src="${src}"]`);
                if (existing) {
                    existing.addEventListener('load', () => resolve());
                    existing.addEventListener('error', () => reject(new Error('Loading failed: ' + src)));
                    return;
                }
                const script = document.createElement('script');
                script.src = src;
                script.async = true;
                script.dataset.src = src;
                script.onload = () => resolve();
                script.onerror = () => reject(new Error('Loading failed: ' + src));
                document.head.appendChild(script);
            });
        };

        const ensureMarkmapReady = () =>
            loadScriptOnce('https://cdn.jsdelivr.net/npm/d3@7', () => window.d3)
                .then(() => loadScriptOnce('https://cdn.jsdelivr.net/npm/markmap-lib@0.17', () => window.markmap && window.markmap.Transformer))
                .then(() => loadScriptOnce('https://cdn.jsdelivr.net/npm/markmap-view@0.17', () => window.markmap && window.markmap.Markmap));

        const parseColorLuma = (colorStr) => {
            if (!colorStr) return null;
            // hex #rrggbb or rrggbb
            let m = colorStr.match(/^#?([0-9a-f]{6})$/i);
            if (m) {
                const hex = m[1];
                const r = parseInt(hex.slice(0, 2), 16);
                const g = parseInt(hex.slice(2, 4), 16);
                const b = parseInt(hex.slice(4, 6), 16);
                return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
            }
            // rgb(r, g, b) or rgba(r, g, b, a)
            m = colorStr.match(/rgba?\\s*\\(\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)/i);
            if (m) {
                const r = parseInt(m[1], 10);
                const g = parseInt(m[2], 10);
                const b = parseInt(m[3], 10);
                return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
            }
            return null;
        };

        const getThemeFromMeta = (doc, scope = 'self') => {
            const metas = Array.from((doc || document).querySelectorAll('meta[name="theme-color"]'));
            if (!metas.length) return null;
            const color = metas[metas.length - 1].content.trim();
            const luma = parseColorLuma(color);
            if (luma === null) return null;
            return luma < 0.5 ? 'dark' : 'light';
        };

        const getParentDocumentSafe = () => {
            try {
                if (!window.parent || window.parent === window) return null;
                const pDoc = window.parent.document;
                void pDoc.title;
                return pDoc;
            } catch (err) {
                return null;
            }
        };

        const getThemeFromParentClass = () => {
            try {
                if (!window.parent || window.parent === window) return null;
                const pDoc = window.parent.document;
                const html = pDoc.documentElement;
                const body = pDoc.body;
                const htmlClass = html ? html.className : '';
                const bodyClass = body ? body.className : '';
                const htmlDataTheme = html ? html.getAttribute('data-theme') : '';
                if (htmlDataTheme === 'dark' || bodyClass.includes('dark') || htmlClass.includes('dark')) return 'dark';
                if (htmlDataTheme === 'light' || bodyClass.includes('light') || htmlClass.includes('light')) return 'light';
                return null;
            } catch (err) {
                return null;
            }
        };

        const setTheme = (wrapperEl, explicitTheme) => {
            const parentDoc = getParentDocumentSafe();
            const metaThemeParent = parentDoc ? getThemeFromMeta(parentDoc, 'parent') : null;
            const parentClassTheme = getThemeFromParentClass();
            const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
            
            const chosen = explicitTheme || metaThemeParent || parentClassTheme || (prefersDark ? 'dark' : 'light');
            wrapperEl.classList.toggle('theme-dark', chosen === 'dark');
            return chosen;
        };

        const renderMindmap = () => {
            const containerEl = document.getElementById('markmap-container-' + uniqueId);
            if (!containerEl || containerEl.dataset.markmapRendered) return;

            const sourceEl = document.getElementById('markdown-source-' + uniqueId);
            if (!sourceEl) return;

            const markdownContent = sourceEl.textContent.trim();
            if (!markdownContent) {
                containerEl.innerHTML = '<div class="error-message">' + i18n.html_error_missing_content + '</div>';
                return;
            }

            ensureMarkmapReady().then(() => {
                const svgEl = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                svgEl.style.width = '100%';
                svgEl.style.height = '100%';
                containerEl.innerHTML = '';
                containerEl.appendChild(svgEl);

                const { Transformer, Markmap } = window.markmap;
                const transformer = new Transformer();
                const { root } = transformer.transform(markdownContent);

                const containerWidth = containerEl.clientWidth || window.innerWidth;
                const containerHeight = containerEl.clientHeight || window.innerHeight;
                const isPortrait = containerHeight >= containerWidth * 0.8;

                const style = (id) => `
                    ${id} text, ${id} foreignObject { font-size: 16px; }
                    ${id} foreignObject { line-height: 1.6; }
                    ${id} foreignObject div { padding: 2px 0; }
                    ${id} foreignObject h1 { font-size: 24px; font-weight: 700; margin: 0 0 6px 0; border-bottom: 2px solid currentColor; padding-bottom: 4px; display: inline-block; }
                    ${id} foreignObject h2 { font-size: 18px; font-weight: 600; margin: 0 0 4px 0; }
                    ${id} foreignObject strong { font-weight: 700; }
                    ${id} foreignObject p { margin: 2px 0; }
                `;
                
                let responsiveMaxWidth;
                let dynamicSpacingVertical = 5;
                let dynamicSpacingHorizontal = 80;

                if (isPortrait) {
                    // Old Version / Mobile: Force early text wrap to explode height and tighten width
                    responsiveMaxWidth = Math.max(140, Math.floor(containerWidth * 0.35)); 
                    dynamicSpacingVertical = 20; // Explicitly spread out branches vertically
                    dynamicSpacingHorizontal = 60;
                } else {
                    // New Version (Direct Chat): Generous width to utilize massive horizontal space
                    responsiveMaxWidth = Math.max(220, Math.floor(containerWidth * 0.35)); 
                    dynamicSpacingVertical = 12;
                    dynamicSpacingHorizontal = 60; // Tighter horizontal gaps so the chart doesn't get too wide to scale up
                }

                const options = {
                    autoFit: true,
                    style: style,
                    initialExpandLevel: 3,
                    zoom: true,
                    pan: true,
                    fitRatio: 0.95, // Maximize scale to make text bigger
                    maxWidth: responsiveMaxWidth,
                    spacingVertical: dynamicSpacingVertical,
                    spacingHorizontal: dynamicSpacingHorizontal,
                    colorFreezeLevel: 2
                };

                const markmapInstance = Markmap.create(svgEl, options, root);
                
                // Extra tick: force fit to make sure bounding box centers
                setTimeout(() => {
                    markmapInstance.fit();
                }, 100);

                // Dynamically refit if the user drags to resize the sidebar/iframe
                const resizeObserver = new ResizeObserver(entries => {
                    for (let entry of entries) {
                        if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
                            requestAnimationFrame(() => markmapInstance.fit());
                        }
                    }
                });
                resizeObserver.observe(containerEl);

                window.markmapInstance = markmapInstance; // Expose for external triggers
                containerEl.dataset.markmapRendered = 'true';

                setupControls({
                    containerEl,
                    svgEl,
                    markmapInstance,
                    root,
                    isPortrait
                });

            }).catch((error) => {
                console.error('Markmap loading error:', error);
                containerEl.innerHTML = '<div class="error-message">' + i18n.html_error_load_failed + '</div>';
            });
        };

        // Dynamically fix layout: measure header height and set content-area height precisely
        const adjustLayout = () => {
            const wrapper = document.querySelector('.mindmap-container-wrapper');
            const header = document.querySelector('.header');
            const contentArea = document.querySelector('.content-area');
            if (!wrapper || !header || !contentArea) return;
            const headerH = header.getBoundingClientRect().height;
            const totalH = wrapper.getBoundingClientRect().height;
            const contentH = Math.max(totalH - headerH, 200);
            contentArea.style.height = contentH + 'px';
        };

        // Run once after DOM is ready, then on any resize
        adjustLayout();
        window.addEventListener('resize', () => {
            adjustLayout();
            if (window.markmapInstance) {
                requestAnimationFrame(() => window.markmapInstance.fit());
            }
        });

        const setupControls = ({ containerEl, svgEl, markmapInstance, root, isPortrait }) => {
            const downloadSvgBtn = document.getElementById('download-svg-btn-' + uniqueId);
            const downloadPngBtn = document.getElementById('download-png-btn-' + uniqueId);
            const downloadMdBtn = document.getElementById('download-md-btn-' + uniqueId);
            const zoomInBtn = document.getElementById('zoom-in-btn-' + uniqueId);
            const zoomOutBtn = document.getElementById('zoom-out-btn-' + uniqueId);
            const zoomResetBtn = document.getElementById('zoom-reset-btn-' + uniqueId);
            const depthSelect = document.getElementById('depth-select-' + uniqueId);
            const fullscreenBtn = document.getElementById('fullscreen-btn-' + uniqueId);
            const themeToggleBtn = document.getElementById('theme-toggle-btn-' + uniqueId);

            if (depthSelect) {
                depthSelect.value = "3";
            }

            const wrapper = containerEl.closest('.mindmap-container-wrapper');
            let currentTheme = setTheme(wrapper);

            const showFeedback = (button, textOk = i18n.js_done, textFail = i18n.js_failed) => {
                if (!button) return;
                const buttonText = button.querySelector('.btn-text') || button;
                const originalText = buttonText.textContent;
                button.disabled = true;
                buttonText.textContent = textOk;
                button.classList.add('copied');
                setTimeout(() => {
                    buttonText.textContent = originalText;
                    button.disabled = false;
                    button.classList.remove('copied');
                }, 1800);
            };

            const copyToClipboard = (content, button) => {
                if (navigator.clipboard && window.isSecureContext) {
                    navigator.clipboard.writeText(content).then(() => showFeedback(button), () => showFeedback(button, i18n.js_failed, i18n.js_failed));
                } else {
                    const textArea = document.createElement('textarea');
                    textArea.value = content;
                    textArea.style.position = 'fixed';
                    textArea.style.opacity = '0';
                    document.body.appendChild(textArea);
                    textArea.focus();
                    textArea.select();
                    try {
                        document.execCommand('copy');
                        showFeedback(button);
                    } catch (err) {
                        showFeedback(button, i18n.js_failed, i18n.js_failed);
                    }
                    document.body.removeChild(textArea);
                }
            };

            const handleDownloadSVG = () => {
                const svg = containerEl.querySelector('svg');
                if (!svg) return;
                // Inline styles before export
                const clonedSvg = svg.cloneNode(true);
                const style = document.createElement('style');
                style.textContent = `
                    text { font-family: sans-serif; fill: ${currentTheme === 'dark' ? '#ffffff' : '#000000'}; }
                    foreignObject, .markmap-foreign, .markmap-foreign div { color: ${currentTheme === 'dark' ? '#ffffff' : '#000000'}; font-family: sans-serif; font-size: 14px; }
                    h1 { font-size: 22px; font-weight: 700; margin: 0; }
                    h2 { font-size: 18px; font-weight: 600; margin: 0; }
                    strong { font-weight: 700; }
                    .markmap-link { stroke: ${currentTheme === 'dark' ? '#cbd5e1' : '#546e7a'}; }
                    .markmap-node circle, .markmap-node rect { stroke: ${currentTheme === 'dark' ? '#94a3b8' : '#94a3b8'}; }
                `;
                clonedSvg.prepend(style);
                const svgData = new XMLSerializer().serializeToString(clonedSvg);
                copyToClipboard(svgData, downloadSvgBtn);
            };

            const handleDownloadMD = () => {
                const markdownContent = document.getElementById('markdown-source-' + uniqueId)?.textContent || '';
                if (!markdownContent) return;
                copyToClipboard(markdownContent, downloadMdBtn);
            };

            const handleDownloadPNG = () => {
                const btn = downloadPngBtn;
                const btnTextEl = btn.querySelector('.btn-text') || btn;
                const originalText = btnTextEl.textContent;
                btnTextEl.textContent = i18n.js_generating;
                btn.disabled = true;

                const svg = containerEl.querySelector('svg');
                if (!svg) {
                    btnTextEl.textContent = originalText;
                    btn.disabled = false;
                    showFeedback(btn, i18n.js_failed, i18n.js_failed);
                    return;
                }

                try {
                    // Clone SVG and inline styles
                    const clonedSvg = svg.cloneNode(true);
                    clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
                    clonedSvg.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink');
                    
                    const rect = svg.getBoundingClientRect();
                    const width = rect.width || 800;
                    const height = rect.height || 600;
                    clonedSvg.setAttribute('width', width);
                    clonedSvg.setAttribute('height', height);

                    // Remove foreignObject (HTML content) and replace with text
                    const foreignObjects = clonedSvg.querySelectorAll('foreignObject');
                    foreignObjects.forEach(fo => {
                        const text = fo.textContent || '';
                        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                        const textEl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                        textEl.setAttribute('x', fo.getAttribute('x') || '0');
                        textEl.setAttribute('y', (parseFloat(fo.getAttribute('y') || '0') + 14).toString());
                        textEl.setAttribute('fill', currentTheme === 'dark' ? '#ffffff' : '#000000');
                        textEl.setAttribute('font-family', 'sans-serif');
                        textEl.setAttribute('font-size', '14');
                        textEl.textContent = text.trim();
                        g.appendChild(textEl);
                        fo.parentNode.replaceChild(g, fo);
                    });

                    // Inline styles
                    const style = document.createElementNS('http://www.w3.org/2000/svg', 'style');
                    style.textContent = `
                        text { font-family: sans-serif; font-size: 14px; fill: ${currentTheme === 'dark' ? '#ffffff' : '#000000'}; }
                        .markmap-link { fill: none; stroke: ${currentTheme === 'dark' ? '#cbd5e1' : '#546e7a'}; stroke-width: 2; }
                        .markmap-node circle { stroke: ${currentTheme === 'dark' ? '#94a3b8' : '#94a3b8'}; stroke-width: 2; }
                    `;
                    clonedSvg.insertBefore(style, clonedSvg.firstChild);

                    // Add background rect
                    const bgRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                    bgRect.setAttribute('width', '100%');
                    bgRect.setAttribute('height', '100%');
                    bgRect.setAttribute('fill', currentTheme === 'dark' ? '#1f2937' : '#ffffff');
                    clonedSvg.insertBefore(bgRect, clonedSvg.firstChild);

                    const svgData = new XMLSerializer().serializeToString(clonedSvg);
                    const svgBase64 = btoa(unescape(encodeURIComponent(svgData)));
                    const dataUrl = 'data:image/svg+xml;base64,' + svgBase64;

                    const img = new Image();
                    img.onload = () => {
                        const canvas = document.createElement('canvas');
                        const scale = 9;
                        canvas.width = width * scale;
                        canvas.height = height * scale;
                        const ctx = canvas.getContext('2d');
                        ctx.scale(scale, scale);
                        ctx.fillStyle = currentTheme === 'dark' ? '#1f2937' : '#ffffff';
                        ctx.fillRect(0, 0, width, height);
                        ctx.drawImage(img, 0, 0, width, height);

                        canvas.toBlob((blob) => {
                            if (!blob) {
                                btnTextEl.textContent = originalText;
                                btn.disabled = false;
                                showFeedback(btn, i18n.js_failed, i18n.js_failed);
                                return;
                            }
                            
                            // Use non-bubbling MouseEvent to avoid router interception
                            const a = document.createElement('a');
                            a.download = i18n.js_filename;
                            a.href = URL.createObjectURL(blob);
                            a.style.display = 'none';
                            document.body.appendChild(a);
                            
                            const evt = new MouseEvent('click', {
                                view: window,
                                bubbles: false,
                                cancelable: false
                            });
                            a.dispatchEvent(evt);
                            
                            setTimeout(() => {
                                document.body.removeChild(a);
                                URL.revokeObjectURL(a.href);
                            }, 100);

                            btnTextEl.textContent = originalText;
                            btn.disabled = false;
                            showFeedback(btn);
                        }, 'image/png');
                    };
                    
                    img.onerror = (e) => {
                        console.error('PNG image load error:', e);
                        btnTextEl.textContent = originalText;
                        btn.disabled = false;
                        showFeedback(btn, i18n.js_failed, i18n.js_failed);
                    };
                    
                    img.src = dataUrl;
                } catch (err) {
                    console.error('PNG export error:', err);
                    btnTextEl.textContent = originalText;
                    btn.disabled = false;
                    showFeedback(btn, i18n.js_failed, i18n.js_failed);
                }
            };

            const handleZoom = (direction) => {
                if (direction === 'reset') {
                    markmapInstance.fit();
                    return;
                }
                // Simple zoom simulation if d3 zoom instance is not accessible
                // Markmap uses d3-zoom, so we can try to select the svg and transition
                const svg = d3.select(svgEl);
                // We can't easily access the internal zoom behavior object created by markmap
                // So we rely on fit() for reset, and maybe just let user scroll/pinch for zoom
                // Or we can try to rescale if supported
                if (markmapInstance.rescale) {
                    const scale = direction === 'in' ? 1.25 : 0.8;
                    markmapInstance.rescale(scale);
                } else {
                    // Fallback: just fit, as manual transform manipulation conflicts with d3
                    // Or we could try to find the zoom behavior attached to the node
                    // const zoom = d3.zoomTransform(svgEl);
                    // But we need the zoom behavior function to call scaleBy
                }
            };

            const setExpandLevel = (levelStr) => {
                const level = parseInt(levelStr, 10);
                const expandLevel = level === 0 ? Infinity : level;

                // Recursively set fold state on cloned tree nodes
                const applyFold = (node, currentDepth) => {
                    if (!node) return;
                    if (!node.payload) node.payload = {};
                    if (expandLevel === Infinity) {
                        // Expand ALL: clear all fold flags
                        node.payload.fold = 0;
                    } else {
                        // Fold any node deeper than the target level
                        node.payload.fold = currentDepth >= expandLevel ? 1 : 0;
                    }
                    if (node.children) {
                        node.children.forEach(child => applyFold(child, currentDepth + 1));
                    }
                };

                const cleanRoot = JSON.parse(JSON.stringify(root));
                applyFold(cleanRoot, 0);

                markmapInstance.setOptions({ initialExpandLevel: expandLevel });
                markmapInstance.setData(cleanRoot);
                setTimeout(() => markmapInstance.fit(), 50);
            };

            const handleDepthChange = (e) => {
                setExpandLevel(e.target.value);
            };

            const handleFullscreen = () => {
                const el = wrapper || containerEl;
                if (!document.fullscreenElement) {
                    el.requestFullscreen().then(() => {
                        if (depthSelect) depthSelect.value = "0";
                        setExpandLevel("0");
                    }).catch(err => {
                        console.error('Fullscreen failed:', err);
                        // Fallback to container if wrapper fails
                        containerEl.requestFullscreen().then(() => {
                            if (depthSelect) depthSelect.value = "0";
                            setExpandLevel("0");
                        });
                    });
                } else {
                    document.exitFullscreen();
                }
            };
            
            document.addEventListener('fullscreenchange', () => {
                const isFs = !!document.fullscreenElement;
                if (isFs && (document.fullscreenElement === containerEl || document.fullscreenElement === wrapper)) {
                    setTimeout(() => markmapInstance.fit(), 300);
                } else if (!isFs) {
                    // Revert to default depth when exiting fullscreen
                    const defaultLevel = "3";
                    if (depthSelect) depthSelect.value = defaultLevel;
                    setExpandLevel(defaultLevel);
                }
            });

            const handleThemeToggle = () => {
                currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
                setTheme(wrapper, currentTheme);
            };

            downloadSvgBtn?.addEventListener('click', (e) => { e.stopPropagation(); handleDownloadSVG(); });
            downloadMdBtn?.addEventListener('click', (e) => { e.stopPropagation(); handleDownloadMD(); });
            downloadPngBtn?.addEventListener('click', (e) => { e.stopPropagation(); handleDownloadPNG(); });
            zoomInBtn?.addEventListener('click', (e) => { e.stopPropagation(); handleZoom('in'); });
            zoomOutBtn?.addEventListener('click', (e) => { e.stopPropagation(); handleZoom('out'); });
            zoomResetBtn?.addEventListener('click', (e) => { e.stopPropagation(); handleZoom('reset'); });
            depthSelect?.addEventListener('change', (e) => { e.stopPropagation(); handleDepthChange(e); });
            fullscreenBtn?.addEventListener('click', (e) => { e.stopPropagation(); handleFullscreen(); });
            themeToggleBtn?.addEventListener('click', (e) => { e.stopPropagation(); handleThemeToggle(); });
        };

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', renderMindmap);
        } else {
            renderMindmap();
        }
      })();
    </script>
"""


class Action:
    class Valves(BaseModel):
        SHOW_STATUS: bool = Field(
            default=True,
            description="Whether to show action status updates in the chat interface.",
        )
        MODEL_ID: str = Field(
            default="",
            description="Built-in LLM model ID for text analysis. If empty, uses the current conversation's model.",
        )
        MIN_TEXT_LENGTH: int = Field(
            default=100,
            description="Minimum text length (character count) required for mind map analysis.",
        )
        CLEAR_PREVIOUS_HTML: bool = Field(
            default=False,
            description="Whether to force clear previous plugin results (if True, overwrites instead of merging).",
        )
        MESSAGE_COUNT: int = Field(
            default=1,
            description="Number of recent messages to use for generation. Set to 1 for just the last message, or higher for more context.",
        )
        OUTPUT_MODE: str = Field(
            default="html",
            description="Output mode: 'html' for interactive HTML (default), or 'image' to embed as Markdown image.",
        )
        SHOW_DEBUG_LOG: bool = Field(
            default=False,
            description="Whether to print debug logs in the browser console.",
        )
        ENABLE_DIRECT_EMBED_MODE: bool = Field(
            default=False,
            description="Enable Direct Embed Mode (v0.8.0+ layout) instead of Legacy Mode. Defaults to False (Legacy Mode).",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.weekday_map = {
            "Monday": "Monday",
            "Tuesday": "Tuesday",
            "Wednesday": "Wednesday",
            "Thursday": "Thursday",
            "Friday": "Friday",
            "Saturday": "Saturday",
            "Sunday": "Sunday",
        }
        # Fallback mapping for variants not in TRANSLATIONS keys
        self.fallback_map = {
            "es-AR": "es-ES",
            "es-MX": "es-ES",
            "fr-CA": "fr-FR",
            "en-CA": "en-US",
            "en-GB": "en-US",
            "en-AU": "en-US",
            "de-AT": "de-DE",
        }

    def _resolve_language(self, lang: str) -> str:
        """Resolve the best matching language code from the TRANSLATIONS dict."""
        target_lang = lang

        # 1. Direct match
        if target_lang in TRANSLATIONS:
            return target_lang

        # 2. Variant fallback (explicit mapping)
        if target_lang in self.fallback_map:
            target_lang = self.fallback_map[target_lang]
            if target_lang in TRANSLATIONS:
                return target_lang

        # 3. Base language fallback (e.g. fr-BE -> fr-FR)
        # Check if the base language (part before -) exists in translations
        if "-" in lang:
            base_lang = lang.split("-")[0]
            # Try to find a supported language starting with base_lang
            # Prioritize standard variants (e.g., fr -> fr-FR)
            for supported_lang in TRANSLATIONS:
                if supported_lang.startswith(base_lang + "-"):
                    return supported_lang

        # 4. Final Fallback to en-US
        return "en-US"

    def _get_translation(self, lang: str, key: str, **kwargs) -> str:
        """Get translated string for the given language and key."""
        target_lang = self._resolve_language(lang)

        # Retrieve dictionary
        lang_dict = TRANSLATIONS.get(target_lang, TRANSLATIONS["en-US"])

        # Get string
        text = lang_dict.get(key, TRANSLATIONS["en-US"].get(key, key))

        # Format if arguments provided
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception as e:
                logger.warning(f"Translation formatting failed for {key}: {e}")

        return text

    async def _get_user_context(
        self,
        __user__: Optional[Dict[str, Any]],
        __event_call__: Optional[Callable[[Any], Awaitable[None]]] = None,
    ) -> Dict[str, str]:
        """Extract basic user context with safe fallbacks."""
        if isinstance(__user__, (list, tuple)):
            user_data = __user__[0] if __user__ else {}
        elif isinstance(__user__, dict):
            user_data = __user__
        else:
            user_data = {}

        user_id = user_data.get("id", "unknown_user")
        user_name = user_data.get("name", "User")
        # Default from profile
        user_language = user_data.get("language", "en-US")

        # Priority: Document Lang > LocalStorage (Frontend) > Browser > Profile (Default)
        if __event_call__:
            try:
                js_code = """
                    return (
                        document.documentElement.lang ||
                        localStorage.getItem('locale') || 
                        localStorage.getItem('language') || 
                        navigator.language || 
                        'en-US'
                    );
                """
                frontend_lang = await __event_call__(
                    {"type": "execute", "data": {"code": js_code}}
                )
                if frontend_lang and isinstance(frontend_lang, str):
                    user_language = frontend_lang
            except Exception as e:
                logger.warning(f"Failed to retrieve frontend language: {e}")

        return {
            "user_id": user_id,
            "user_name": user_name,
            "user_language": user_language,
        }

    def _get_chat_context(
        self, body: dict, __metadata__: Optional[dict] = None
    ) -> Dict[str, str]:
        """
        Unified extraction of chat context information (chat_id, message_id).
        Prioritizes extraction from body, then metadata.
        """
        chat_id = ""
        message_id = ""

        # 1. Try to get from body
        if isinstance(body, dict):
            chat_id = body.get("chat_id", "")
            message_id = body.get("id", "")  # message_id is usually 'id' in body

            # Check body.metadata as fallback
            if not chat_id or not message_id:
                body_metadata = body.get("metadata", {})
                if isinstance(body_metadata, dict):
                    if not chat_id:
                        chat_id = body_metadata.get("chat_id", "")
                    if not message_id:
                        message_id = body_metadata.get("message_id", "")

        # 2. Try to get from __metadata__ (as supplement)
        if __metadata__ and isinstance(__metadata__, dict):
            if not chat_id:
                chat_id = __metadata__.get("chat_id", "")
            if not message_id:
                message_id = __metadata__.get("message_id", "")

        return {
            "chat_id": str(chat_id).strip(),
            "message_id": str(message_id).strip(),
        }

    def _extract_markdown_syntax(self, llm_output: str) -> str:
        match = re.search(r"```markdown\s*(.*?)\s*```", llm_output, re.DOTALL)
        if match:
            extracted_content = match.group(1).strip()
        else:
            logger.warning(
                "LLM output did not strictly follow the expected Markdown format, treating the entire output as summary."
            )
            extracted_content = llm_output.strip()
        return extracted_content.replace("</script>", "<\\/script>")

    async def _emit_status(self, emitter, description: str, done: bool = False):
        """Emits a status update event."""
        if self.valves.SHOW_STATUS and emitter:
            await emitter(
                {"type": "status", "data": {"description": description, "done": done}}
            )

    async def _emit_notification(self, emitter, content: str, ntype: str = "info"):
        """Emits a notification event (info/success/warning/error)."""
        if emitter:
            await emitter(
                {"type": "notification", "data": {"type": ntype, "content": content}}
            )

    async def _emit_debug_log(self, emitter, title: str, data: dict):
        """Print structured debug logs in the browser console"""
        if not self.valves.SHOW_DEBUG_LOG or not emitter:
            return

        try:
            js_code = f"""
                (async function() {{
                    console.group("🛠️ {title}");
                    console.log({json.dumps(data, ensure_ascii=False)});
                    console.groupEnd();
                }})();
            """

            await emitter({"type": "execute", "data": {"code": js_code}})
        except Exception as e:
            print(f"Error emitting debug log: {e}")

    def _remove_existing_html(self, content: str) -> str:
        """Removes existing plugin-generated HTML code blocks from the content."""
        pattern = r"```html\s*<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?```"
        return re.sub(pattern, "", content).strip()

    def _extract_text_content(self, content) -> str:
        """Extract text from message content, supporting multimodal message formats"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Multimodal message: [{"type": "text", "text": "..."}, {"type": "image_url", ...}]
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif isinstance(item, str):
                    text_parts.append(item)
            return "\n".join(text_parts)
        return str(content) if content else ""

    def _merge_html(
        self,
        existing_html_code: str,
        new_content: str,
        new_styles: str = "",
        new_scripts: str = "",
        user_language: str = "en-US",
    ) -> str:
        """
        Merges new content into an existing HTML container, or creates a new one.
        """
        # Security: Escape user_language to prevent XSS
        safe_language = user_language.replace('"', "&quot;")

        if (
            "<!-- OPENWEBUI_PLUGIN_OUTPUT -->" in existing_html_code
            and "<!-- CONTENT_INSERTION_POINT -->" in existing_html_code
        ):
            base_html = existing_html_code
            base_html = re.sub(r"^```html\s*", "", base_html)
            base_html = re.sub(r"\s*```$", "", base_html)
        else:
            base_html = HTML_WRAPPER_TEMPLATE.replace("{lang}", safe_language)

        wrapped_content = f'<div class="plugin-item">\n{new_content}\n</div>'

        if new_styles:
            base_html = base_html.replace(
                "/* STYLES_INSERTION_POINT */",
                f"{new_styles}\n/* STYLES_INSERTION_POINT */",
            )

        base_html = base_html.replace(
            "<!-- CONTENT_INSERTION_POINT -->",
            f"{wrapped_content}\n<!-- CONTENT_INSERTION_POINT -->",
        )

        if new_scripts:
            base_html = base_html.replace(
                "<!-- SCRIPTS_INSERTION_POINT -->",
                f"{new_scripts}\n<!-- SCRIPTS_INSERTION_POINT -->",
            )

        return base_html.strip()

    def _generate_image_js_code(
        self,
        unique_id: str,
        chat_id: str,
        message_id: str,
        markdown_syntax: str,
        lang: str,
    ) -> str:
        """Generate JavaScript code for frontend SVG rendering and image embedding"""

        # Escape the syntax for JS embedding
        syntax_escaped = (
            markdown_syntax.replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("${", "\\${")
            .replace("</script>", "<\\/script>")
        )

        # Prepare i18n for this specific context
        i18n_data = {}
        target_lang = lang
        if target_lang not in TRANSLATIONS and target_lang in self.fallback_map:
            target_lang = self.fallback_map[target_lang]
        if target_lang not in TRANSLATIONS:
            target_lang = "en-US"

        full_trans = TRANSLATIONS.get(target_lang, TRANSLATIONS["en-US"])
        # We only need specific keys for the JS image generation part
        keys = ["js_upload_failed", "md_image_alt"]
        for k in keys:
            i18n_data[k] = full_trans.get(k, TRANSLATIONS["en-US"].get(k, k))

        i18n_json = json.dumps(i18n_data, ensure_ascii=False)

        return f"""
(async function() {{
    const uniqueId = "{unique_id}";
    const chatId = "{chat_id}";
    const messageId = "{message_id}";
    const i18n = {i18n_json};
    const defaultWidth = 1200;
    
    // Theme detection - check parent document for OpenWebUI theme
    const detectTheme = () => {{
        try {{
            // 1. Check parent document's html/body class or data-theme
            const html = document.documentElement;
            const body = document.body;
            const htmlClass = html ? html.className : '';
            const bodyClass = body ? body.className : '';
            const htmlDataTheme = html ? html.getAttribute('data-theme') : '';
            
            if (htmlDataTheme === 'dark' || bodyClass.includes('dark') || htmlClass.includes('dark')) {{
                return 'dark';
            }}
            if (htmlDataTheme === 'light' || bodyClass.includes('light') || htmlClass.includes('light')) {{
                return 'light';
            }}
            
            // 2. Check meta theme-color
            const metas = document.querySelectorAll('meta[name="theme-color"]');
            if (metas.length > 0) {{
                const color = metas[metas.length - 1].content.trim();
                const m = color.match(/^#?([0-9a-f]{{6}})$/i);
                if (m) {{
                    const hex = m[1];
                    const r = parseInt(hex.slice(0, 2), 16);
                    const g = parseInt(hex.slice(2, 4), 16);
                    const b = parseInt(hex.slice(4, 6), 16);
                    const luma = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
                    return luma < 0.5 ? 'dark' : 'light';
                }}
            }}
            
            // 3. Check system preference
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {{
                return 'dark';
            }}
            
            return 'light';
        }} catch (e) {{
            return 'light';
        }}
    }};
    
    const currentTheme = detectTheme();
    console.log("[MindMap Image] Detected theme:", currentTheme);
    
    // Theme-based colors
    const colors = currentTheme === 'dark' ? {{
        background: '#1f2937',
        text: '#e5e7eb',
        link: '#94a3b8',
        nodeStroke: '#94a3b8'
    }} : {{
        background: '#ffffff',
        text: '#1f2937',
        link: '#546e7a',
        nodeStroke: '#94a3b8'
    }};
    
    // Auto-detect chat container width for responsive sizing
    let svgWidth = defaultWidth;
    // Initial height placeholder, will be adjusted by fit()
    let svgHeight = 600; 
    
    const chatContainer = document.getElementById('chat-container');
    if (chatContainer) {{
        const containerWidth = chatContainer.clientWidth;
        if (containerWidth > 100) {{
            // Use container width with some padding (90% of container)
            svgWidth = Math.floor(containerWidth * 0.9);
        }}
    }}
    
    try {{
        // Load D3 if not loaded
        if (typeof d3 === 'undefined') {{
            await new Promise((resolve, reject) => {{
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/d3@7';
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            }});
        }}
        
        // Load markmap-lib if not loaded
        if (!window.markmap || !window.markmap.Transformer) {{
            await new Promise((resolve, reject) => {{
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/markmap-lib@0.17';
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            }});
        }}
        
        // Load markmap-view if not loaded
        if (!window.markmap || !window.markmap.Markmap) {{
            await new Promise((resolve, reject) => {{
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/markmap-view@0.17';
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            }});
        }}
        
        const {{ Transformer, Markmap }} = window.markmap;
        
        // Get markdown syntax
        let syntaxContent = `{syntax_escaped}`;
        
        // Create offscreen container
        const container = document.createElement('div');
        container.id = 'mindmap-offscreen-' + uniqueId;
        // Start with a reasonably large height to allow layout, but we'll crop it later
        container.style.cssText = 'position:absolute;left:-9999px;top:-9999px;width:' + svgWidth + 'px;height:2000px;overflow:hidden;';
        document.body.appendChild(container);
        
        // Create SVG element
        const svgEl = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svgEl.setAttribute('width', svgWidth);
        svgEl.setAttribute('height', '2000'); // Initial large height
        svgEl.style.width = svgWidth + 'px';
        svgEl.style.height = '2000px';
        svgEl.style.backgroundColor = colors.background;
        container.appendChild(svgEl);
        
        // Transform markdown to tree
        const transformer = new Transformer();
        const {{ root }} = transformer.transform(syntaxContent);
        
        // Create markmap instance
        const options = {{
            autoFit: false, // We will manually fit and measure
            initialExpandLevel: Infinity,
            zoom: false,
            pan: false,
            maxWidth: 280
        }};
        
        const markmapInstance = Markmap.create(svgEl, options, root);
        
        // Wait for render to complete
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Fit to content to get bounds
        markmapInstance.fit();
        
        // Calculate actual content height based on the graph state
        // Markmap D3 logic: minY, maxY are stored in state or we can measure the group
        let minY = Infinity;
        let maxY = -Infinity;
        
        // Inspect D3 nodes to find bounding box
        const nodes = svgEl.querySelectorAll('g.markmap-node');
        if (nodes.length > 0) {{
             // This is a rough estimation. Better to use D3's getBBox if possible
             // But we are in an isolated context.
             // Let's try to get the main group transform which markmap sets for zoom/pan
             const g = svgEl.querySelector('g'); 
             if (g) {{
                 const bbox = g.getBBox();
                 // Markmap applies a transform to 'g' to center it.
                 // We want to adjust the SVG height to match this bbox height + padding
                 // And re-center.
                 
                 // Add some padding
                 const padding = 20;
                 const contentHeight = bbox.height + (padding * 2);
                 const contentWidth = bbox.width + (padding * 2);
                 
                 // Update SVG height to fit content exactly
                 svgHeight = Math.ceil(contentHeight);
                 
                 // Ensure minimum height
                 if (svgHeight < 300) svgHeight = 300;
                 
                 svgEl.setAttribute('height', svgHeight);
                 svgEl.style.height = svgHeight + 'px';
                 
                 // Re-fit with new dimensions
                 markmapInstance.fit();
                 await new Promise(resolve => setTimeout(resolve, 500));
             }}
        }}

        // Clone and prepare SVG for export
        const clonedSvg = svgEl.cloneNode(true);
        clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        clonedSvg.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink');
        
        // Explicitly set the final width/height on the cloned SVG
        clonedSvg.setAttribute('width', svgWidth);
        clonedSvg.setAttribute('height', svgHeight);
        
        // Add background rect with theme color
        const bgRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        bgRect.setAttribute('width', '100%');
        bgRect.setAttribute('height', '100%');
        bgRect.setAttribute('fill', colors.background);
        clonedSvg.insertBefore(bgRect, clonedSvg.firstChild);
        
        // Add inline styles with theme colors
        const style = document.createElementNS('http://www.w3.org/2000/svg', 'style');
        style.textContent = `
            text {{ font-family: sans-serif; font-size: 14px; fill: ${{colors.text}}; }}
            foreignObject, .markmap-foreign, .markmap-foreign div {{ color: ${{colors.text}}; font-family: sans-serif; font-size: 14px; }}
            h1 {{ font-size: 22px; font-weight: 700; margin: 0; }}
            h2 {{ font-size: 18px; font-weight: 600; margin: 0; }}
            strong {{ font-weight: 700; }}
            .markmap-link {{ stroke: ${{colors.link}}; fill: none; }}
            .markmap-node circle, .markmap-node rect {{ stroke: ${{colors.nodeStroke}}; }}
        `;
        clonedSvg.insertBefore(style, bgRect.nextSibling);
        
        // Convert foreignObject to text for better compatibility
        const foreignObjects = clonedSvg.querySelectorAll('foreignObject');
        foreignObjects.forEach(fo => {{
            const text = fo.textContent || '';
            const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            const textEl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            textEl.setAttribute('x', fo.getAttribute('x') || '0');
            textEl.setAttribute('y', (parseFloat(fo.getAttribute('y') || '0') + 14).toString());
            textEl.setAttribute('fill', colors.text);
            textEl.setAttribute('font-family', 'sans-serif');
            textEl.setAttribute('font-size', '14');
            textEl.textContent = text.trim();
            g.appendChild(textEl);
            fo.parentNode.replaceChild(g, fo);
        }});
        
        // Serialize SVG to string
        const svgData = new XMLSerializer().serializeToString(clonedSvg);
        
        // Cleanup container
        document.body.removeChild(container);
        
        // Convert SVG string to Blob
        const blob = new Blob([svgData], {{ type: 'image/svg+xml' }});
        const file = new File([blob], `mindmap-${{uniqueId}}.svg`, {{ type: 'image/svg+xml' }});
        
        // Upload file to OpenWebUI API
        const token = localStorage.getItem("token");
        const formData = new FormData();
        formData.append('file', file);
        
        const uploadResponse = await fetch('/api/v1/files/', {{
            method: 'POST',
            headers: {{
                'Authorization': `Bearer ${{token}}`
            }},
            body: formData
        }});
        
        if (!uploadResponse.ok) {{
            throw new Error(i18n.js_upload_failed + uploadResponse.statusText);
        }}
        
        const fileData = await uploadResponse.json();
        const fileId = fileData.id;
        const imageUrl = `/api/v1/files/${{fileId}}/content`;
        
        const markdownImage = `![${{i18n.md_image_alt}}](${{imageUrl}})`;
        
        // Update message via API
        if (chatId && messageId) {{
            
            // Helper function with retry logic
            const fetchWithRetry = async (url, options, retries = 3) => {{
                for (let i = 0; i < retries; i++) {{
                    try {{
                        const response = await fetch(url, options);
                        if (response.ok) return response;
                        if (i < retries - 1) {{
                            await new Promise(r => setTimeout(r, 1000 * (i + 1)));
                        }}
                    }} catch (e) {{
                        if (i === retries - 1) throw e;
                        await new Promise(r => setTimeout(r, 1000 * (i + 1)));
                    }}
                }}
                return null;
            }};
            
            // Get current chat data
            const getResponse = await fetch(`/api/v1/chats/${{chatId}}`, {{
                method: "GET",
                headers: {{ "Authorization": `Bearer ${{token}}` }}
            }});
            
            if (!getResponse.ok) {{
                throw new Error("Failed to get chat data: " + getResponse.status);
            }}
            
            const chatData = await getResponse.json();
            let updatedMessages = [];
            let newContent = "";
            
            if (chatData.chat && chatData.chat.messages) {{
                updatedMessages = chatData.chat.messages.map(m => {{
                    if (m.id === messageId) {{
                        const originalContent = m.content || "";
                        const mindmapPattern = /\\n*!\\[[^[\\]]*\\]\\((?:data:image\\/[^)]+|(?:\\/api\\/v1\\/files\\/[^)]+))\\)/g;
                        let cleanedContent = originalContent.replace(mindmapPattern, "");
                        cleanedContent = cleanedContent.replace(/\\n{{3,}}/g, "\\n\\n").trim();
                        newContent = cleanedContent + "\\n\\n" + markdownImage;
                        
                        // Critical: Update content in both messages array AND history object
                        // The history object is the source of truth for the database
                        if (chatData.chat.history && chatData.chat.history.messages) {{
                            if (chatData.chat.history.messages[messageId]) {{
                                chatData.chat.history.messages[messageId].content = newContent;
                            }}
                        }}
                        
                        return {{ ...m, content: newContent }};
                    }}
                    return m;
                }});
            }}
            
            if (!newContent) {{
                return;
            }}
            
            // Try to update frontend display via event API (optional)
            try {{
                await fetch(`/api/v1/chats/${{chatId}}/messages/${{messageId}}/event`, {{
                    method: "POST",
                    headers: {{
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${{token}}`
                    }},
                    body: JSON.stringify({{
                        type: "chat:message",
                        data: {{ content: newContent }}
                    }})
                }});
            }} catch (eventErr) {{
            }}
            
            // Persist to database
            const updatePayload = {{
                chat: {{
                    ...chatData.chat,
                    messages: updatedMessages
                }}
            }};
            
            await fetchWithRetry(`/api/v1/chats/${{chatId}}`, {{
                method: "POST",
                headers: {{
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${{token}}`
                }},
                body: JSON.stringify(updatePayload)
            }});
        }}
        
    }} catch (error) {{
        console.error("[MindMap Image] Error:", error);
    }}
}})();
"""

    CSS_TEMPLATE_MINDMAP_DIRECT = """
        :root {
            --primary-color: #1e88e5;
            --secondary-color: #43a047;
            --background-color: #f4f6f8;
            --card-bg-color: #ffffff;
            --text-color: #000000;
            --link-color: #546e7a;
            --node-stroke-color: #90a4ae;
            --muted-text-color: #546e7a;
            --border-color: #e0e0e0;
            --header-gradient: linear-gradient(135deg, var(--secondary-color), var(--primary-color));
            --shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            --border-radius: 0;
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        .theme-dark {
            --primary-color: #3b82f6;      /* High contrast blue */
            --secondary-color: #22c55e;    /* High contrast green */
            --background-color: #0d1117;   /* Deep background */
            --card-bg-color: #161b22;      /* Header background */
            --text-color: #ffffff;         /* Pure white text for max contrast */
            --link-color: #58a6ff;
            --node-stroke-color: #8b949e;  /* Brighter node lines */
            --muted-text-color: #7d8590;
            --border-color: #30363d;
            --header-gradient: linear-gradient(135deg, #1e88e5, #43a047);
            --shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
            /* Legacy Control Styles */
            --legacy-header-gradient: linear-gradient(135deg, var(--secondary-color), var(--primary-color));
        }
        html, body { 
            margin: 0;
            padding: 0;
        }
        body { 
            font-family: var(--font-family);
            background-color: transparent; 
            display: flex;
            flex-direction: column;
        }
        .mindmap-container-wrapper {
            font-family: var(--font-family);
            line-height: 1.5;
            color: var(--text-color);
            margin: 0;
            padding: 0;
            width: 100%;
            height: clamp(600px, 85vh, 1400px); /* Canvas area even larger */
            display: flex;
            flex-direction: column;
            background: var(--background-color);
            position: relative;
            overflow: hidden;
            box-sizing: border-box;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        .header {
            background: var(--card-bg-color);
            color: var(--text-color);
            padding: 12px 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            flex-shrink: 0;
            border-bottom: 1px solid var(--border-color);
            z-index: 10;
        }
        .header-top {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .header h1 {
            margin: 0;
            font-size: 1.2em;
            font-weight: 600;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .header-credits {
            font-size: 0.8em;
            color: var(--muted-text-color);
            opacity: 0.8;
            white-space: nowrap;
        }
        .header-credits a {
            color: var(--primary-color);
            text-decoration: none;
            border-bottom: 1px dotted var(--link-color);
        }
        .content-area {
            flex-grow: 1;
            position: relative;
            overflow: hidden;
            background: transparent;
            min-height: 0;
            width: 100%;
            height: 100%;
        }
        .markmap-container {
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
        }
        .markmap-container svg {
            width: 100%;
            height: 100%;
            display: block;
        }
        .markmap-container svg text {
            fill: var(--text-color) !important;
            font-family: var(--font-family);
        }
        /* Force override all text containers within markmap */
        .markmap-container foreignObject,
        .markmap-container .markmap-foreign_object,
        .markmap-container .markmap-node-label,
        .markmap-container div {
            color: var(--text-color) !important;
            fill: var(--text-color) !important;
        }
        /* Optimize branch line colors for dark mode */
        .theme-dark .markmap-link {
            stroke-opacity: 0.6;
        }
        .theme-dark .markmap-node circle {
            fill: var(--card-bg-color) !important;
        }
        /* Controls */
        .control-rows {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            margin-left: auto; /* Push controls to the right */
        }
        .btn-group {
            display: inline-flex;
            gap: 4px;
            align-items: center;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 2px;
            background: var(--background-color);
        }
        .control-btn {
            background-color: transparent;
            color: var(--text-color);
            border: none;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            height: 28px;
            box-sizing: border-box;
            opacity: 0.8;
        }
        .control-btn:hover {
            background-color: var(--card-bg-color);
            opacity: 1;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .control-btn:active {
            transform: translateY(1px);
        }
        .control-btn.primary { 
            background-color: var(--primary-color);
            color: white;
            opacity: 1;
        }
        .control-btn.primary:hover {
            box-shadow: 0 2px 5px rgba(30,136,229,0.3);
        }
        
        select.control-btn {
            appearance: none;
            padding-right: 28px;
            background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23FFFFFF%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E");
            background-repeat: no-repeat;
            background-position: right 8px center;
            background-size: 10px;
        }
        .control-btn option {
            background-color: var(--card-bg-color);
            color: var(--text-color);
        }
        .error-message {
            color: #d32f2f;
            background-color: #ffebee;
            padding: 20px;
            text-align: center;
            border-bottom: 1px solid #ffcdd2;
        }

        /* Mobile Responsive Adjustments */
        @media screen and (max-width: 768px) {
            .mindmap-container-wrapper {
                min-height: 480px;
                height: 75vh;
            }
            .header {
                flex-direction: column;
                gap: 10px;
            }
            .btn-group {
                padding: 2px;
            }
            .control-btn {
                padding: 4px 6px;
                font-size: 0.75em;
                height: 28px;
            }
            select.control-btn {
                padding-right: 20px;
                background-position: right 4px center;
            }
        }
"""

    CONTENT_TEMPLATE_MINDMAP_DIRECT = """
        <div class="mindmap-container-wrapper">
            <div class="header">
                <div class="header-top">
                    <h1>{t_ui_title}</h1>
                    <div class="header-credits">
                        <span>{t_ui_footer}</span>
                    </div>
                    <div class="control-rows">
                        <div class="btn-group">
                            <button id="download-png-btn-{unique_id}" class="control-btn primary" title="{t_ui_download_png}">PNG</button>
                            <button id="download-svg-btn-{unique_id}" class="control-btn" title="{t_ui_download_svg}">SVG</button>
                            <button id="download-md-btn-{unique_id}" class="control-btn" title="{t_ui_download_md}">MD</button>
                        </div>
                        <div class="btn-group">
                            <button id="zoom-out-btn-{unique_id}" class="control-btn" title="{t_ui_zoom_out}">－</button>
                            <button id="zoom-reset-btn-{unique_id}" class="control-btn" title="{t_ui_zoom_reset}">↺</button>
                            <button id="zoom-in-btn-{unique_id}" class="control-btn" title="{t_ui_zoom_in}">＋</button>
                        </div>
                        <div class="btn-group">
                            <select id="depth-select-{unique_id}" class="control-btn" title="{t_ui_depth_select}">
                                <option value="0" selected>{t_ui_depth_all}</option>
                                <option value="2">{t_ui_depth_2}</option>
                                <option value="3">{t_ui_depth_3}</option>
                            </select>
                            <button id="fullscreen-btn-{unique_id}" class="control-btn" title="{t_ui_fullscreen}">⛶</button>
                            <button id="theme-toggle-btn-{unique_id}" class="control-btn" title="{t_ui_theme}">◑</button>
                        </div>
                    </div>
                </div>
            </div>
            <div class="content-area">
                <div class="markmap-container" id="markmap-container-{unique_id}"></div>
            </div>
        </div>
        
        <script type="text/template" id="markdown-source-{unique_id}">{markdown_syntax}</script>
"""

    async def action(
        self,
        body: dict,
        __user__: Optional[Dict[str, Any]] = None,
        __event_emitter__: Optional[Any] = None,
        __event_call__: Optional[Callable[[Any], Awaitable[None]]] = None,
        __metadata__: Optional[dict] = None,
        __request__: Optional[Request] = None,
    ) -> Optional[dict]:
        logger.info("Action: Smart Mind Map (v1.0.0) started")
        user_ctx = await self._get_user_context(__user__, __event_call__)
        user_language = user_ctx["user_language"]
        user_name = user_ctx["user_name"]
        user_id = user_ctx["user_id"]
        long_text_content = ""  # Initialize for exception handler safety

        try:
            tz_env = os.environ.get("TZ")
            tzinfo = ZoneInfo(tz_env) if tz_env else None
            now_dt = datetime.now(tzinfo or timezone.utc)

            # Format current date time string for LLM parsing
            current_date_time_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

            current_weekday_en = now_dt.strftime("%A")
            current_weekday_zh = self.weekday_map.get(current_weekday_en, "Unknown")

            current_year = now_dt.strftime("%Y")
            current_timezone_str = tz_env or "UTC"
        except Exception as e:
            logger.warning(f"Failed to get timezone info: {e}, using default values.")
            now = datetime.now()
            current_date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            current_weekday_zh = "Unknown"
            current_year = now.strftime("%Y")
            current_timezone_str = "Unknown"

        await self._emit_notification(
            __event_emitter__,
            self._get_translation(user_language, "status_starting"),
            "info",
        )

        messages = body.get("messages")
        if not messages or not isinstance(messages, list):
            error_message = self._get_translation(user_language, "error_no_content")
            await self._emit_notification(__event_emitter__, error_message, "error")
            body["messages"].append(
                {"role": "assistant", "content": f"❌ {error_message}"}
            )
            return body

        # Get last N messages based on MESSAGE_COUNT
        message_count = min(self.valves.MESSAGE_COUNT, len(messages))
        recent_messages = messages[-message_count:]

        # Aggregate content from selected messages with labels
        aggregated_parts = []
        for i, msg in enumerate(recent_messages, 1):
            text_content = self._extract_text_content(msg.get("content"))
            if text_content:
                aggregated_parts.append(f"{text_content}")

        if not aggregated_parts:
            error_message = self._get_translation(user_language, "error_no_content")
            await self._emit_notification(__event_emitter__, error_message, "error")
            body["messages"].append(
                {"role": "assistant", "content": f"❌ {error_message}"}
            )
            return body

        original_content = "\n\n---\n\n".join(aggregated_parts)

        parts = re.split(r"```html.*?```", original_content, flags=re.DOTALL)
        long_text_content = ""
        if parts:
            for part in reversed(parts):
                if part.strip():
                    long_text_content = part.strip()
                    break

        if not long_text_content:
            long_text_content = original_content.strip()

        if len(long_text_content) < self.valves.MIN_TEXT_LENGTH:
            short_text_message = self._get_translation(
                user_language,
                "error_text_too_short",
                len=len(long_text_content),
                min_len=self.valves.MIN_TEXT_LENGTH,
            )
            await self._emit_notification(
                __event_emitter__, short_text_message, "warning"
            )
            body["messages"].append(
                {"role": "assistant", "content": f"⚠️ {short_text_message}"}
            )
            return body

        await self._emit_notification(
            __event_emitter__,
            self._get_translation(user_language, "status_analyzing"),
            "info",
        )

        await self._emit_status(
            __event_emitter__,
            self._get_translation(user_language, "status_analyzing"),
            False,
        )

        try:
            unique_id = f"id_{int(time.time() * 1000)}"

            # Prepare LLM request
            formatted_user_prompt = USER_PROMPT_GENERATE_MINDMAP.format(
                user_name=user_name,
                current_date_time_str=current_date_time_str,
                current_weekday=current_weekday_zh,
                current_timezone_str=current_timezone_str,
                user_language=user_language,
                long_text_content=long_text_content,
            )

            # Determine model to use
            target_model = self.valves.MODEL_ID
            if not target_model:
                target_model = body.get("model")

            llm_payload = {
                "model": target_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT_MINDMAP_ASSISTANT},
                    {"role": "user", "content": formatted_user_prompt},
                ],
                "temperature": 0.5,
                "stream": False,
            }
            user_obj = Users.get_user_by_id(user_id)
            if not user_obj:
                raise ValueError(f"Unable to get user object, user ID: {user_id}")

            llm_response = await generate_chat_completion(
                __request__, llm_payload, user_obj
            )

            if (
                not llm_response
                or "choices" not in llm_response
                or not llm_response["choices"]
            ):
                raise ValueError("LLM response format is incorrect or empty.")

            assistant_response_content = llm_response["choices"][0]["message"][
                "content"
            ]
            logger.info(f"LLM Response length: {len(assistant_response_content)}")
            if self.valves.SHOW_DEBUG_LOG:
                logger.info(
                    f"LLM Response content: {assistant_response_content[:500]}..."
                )
            markdown_syntax = self._extract_markdown_syntax(assistant_response_content)

            # Prepare content components
            # Resolve translations for UI
            ui_trans = {}
            # Iterate over base language keys to ensure no missing placeholders
            for k in TRANSLATIONS["en-US"]:
                if k.startswith("ui_"):
                    val = self._get_translation(user_language, k)
                    if k == "ui_footer":
                        ui_trans[f"t_{k}"] = val.format(year=current_year)
                    else:
                        ui_trans[f"t_{k}"] = val

            # Security: Use simple string replacement instead of format() to prevent
            # crashes if markdown_syntax contains braces { or }.
            # Also escape user_name for basic HTML safety.
            content_html = CONTENT_TEMPLATE_MINDMAP
            for k, v in ui_trans.items():
                content_html = content_html.replace(f"{{{k}}}", v)

            content_html = content_html.replace("{unique_id}", unique_id).replace(
                "{markdown_syntax}", markdown_syntax
            )

            # Prepare JS i18n
            target_lang = self._resolve_language(user_language)
            full_trans = TRANSLATIONS.get(target_lang, TRANSLATIONS["en-US"])
            js_trans = {}
            for k in full_trans:
                if k.startswith("js_") or k.startswith("html_"):
                    js_trans[k] = full_trans[k]

            i18n_json = json.dumps(js_trans, ensure_ascii=False)
            unique_id_json = json.dumps(unique_id)

            # Note: We don't need chat/message ID in HTML mode JS, but we do need uniqueId and i18n
            # The SCRIPT_TEMPLATE_MINDMAP now uses {unique_id_json} for the ID
            script_html = (
                SCRIPT_TEMPLATE_MINDMAP.replace(
                    "{unique_id}",
                    unique_id,  # Fallback for other non-JSON placeholders if any
                )
                .replace("{unique_id_json}", unique_id_json)
                .replace("{i18n_json}", i18n_json)
            )

            # Extract existing HTML if any
            existing_html_block = ""
            match = re.search(
                r"```html\s*(<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?)```",
                long_text_content,
            )
            if match:
                existing_html_block = match.group(1)

            if self.valves.CLEAR_PREVIOUS_HTML:
                long_text_content = self._remove_existing_html(long_text_content)
                final_html = self._merge_html(
                    "", content_html, CSS_TEMPLATE_MINDMAP, script_html, user_language
                )
            else:
                # If we found existing HTML, we remove the old block from text and merge into it
                if existing_html_block:
                    long_text_content = self._remove_existing_html(long_text_content)
                    final_html = self._merge_html(
                        existing_html_block,
                        content_html,
                        CSS_TEMPLATE_MINDMAP,
                        script_html,
                        user_language,
                    )
                else:
                    final_html = self._merge_html(
                        "",
                        content_html,
                        CSS_TEMPLATE_MINDMAP,
                        script_html,
                        user_language,
                    )

            # Check output mode
            if self.valves.OUTPUT_MODE == "image":
                # Image mode: use JavaScript to render and embed as Markdown image
                chat_ctx = self._get_chat_context(body, __metadata__)
                chat_id = chat_ctx["chat_id"]
                message_id = chat_ctx["message_id"]

                await self._emit_status(
                    __event_emitter__,
                    self._get_translation(user_language, "status_rendering_image"),
                    False,
                )

                if __event_call__:
                    js_code = self._generate_image_js_code(
                        unique_id=unique_id,
                        chat_id=chat_id,
                        message_id=message_id,
                        markdown_syntax=markdown_syntax,
                        lang=user_language,
                    )

                    await __event_call__(
                        {
                            "type": "execute",
                            "data": {"code": js_code},
                        }
                    )

                await self._emit_status(
                    __event_emitter__,
                    self._get_translation(user_language, "status_image_generated"),
                    True,
                )
                await self._emit_notification(
                    __event_emitter__,
                    self._get_translation(
                        user_language, "notification_image_success", user_name=user_name
                    ),
                    "success",
                )
                logger.info("Action: Smart Mind Map (v1.0.0) completed in image mode")
                return body

            # HTML mode
            is_direct_mode = self._is_direct_html_supported(body)

            if is_direct_mode:
                # DIRECT EMBED MODE
                # Use new templates
                content_html_direct = self.CONTENT_TEMPLATE_MINDMAP_DIRECT
                for k, v in ui_trans.items():
                    content_html_direct = content_html_direct.replace(f"{{{k}}}", v)

                content_html_direct = (
                    content_html_direct.replace("{unique_id}", unique_id)
                    .replace(
                        "{user_name}",
                        user_name.replace("<", "&lt;").replace(">", "&gt;"),
                    )
                    .replace("{current_date_time_str}", current_date_time_str)
                    .replace("{markdown_syntax}", markdown_syntax)
                )

                # Script injection remains similar but tailored if needed
                script_html_direct = (
                    SCRIPT_TEMPLATE_MINDMAP.replace("{unique_id}", unique_id)
                    .replace("{unique_id_json}", unique_id_json)
                    .replace("{i18n_json}", i18n_json)
                )

                # We do NOT wrap in <html> body for Direct Mode if using standard return
                # But we still need styles.
                # We can prepend styles to the div or return a full html doc?
                # The requirements say: `return (html_content, ...)`
                # Usually standard Action returns full HTML or fragments.
                # If "inline", fragments are better, but styles need to be scoped or global.
                # Our CSS templates use specific classes, should be safe.
                # But to ensure it renders correctly, we usually wrap in a div.

                final_html_direct = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                    {self.CSS_TEMPLATE_MINDMAP_DIRECT}
                    </style>
                </head>
                <body>
                    {content_html_direct}
                    {script_html_direct}
                    <script>
                        // Extra fit insurance for Direct Mode
                        const triggerFit = () => {{
                            const svg = document.querySelector('svg');
                            if (svg && window.markmapInstance) {{
                                window.markmapInstance.fit();
                            }}
                        }};
                        window.addEventListener('load', () => {{
                            triggerFit();
                            setTimeout(triggerFit, 300);
                            setTimeout(triggerFit, 800);
                        }});
                        // Also trigger on resize
                        window.addEventListener('resize', triggerFit);
                    </script>
                </body>
                </html>
                """

                await self._emit_status(
                    __event_emitter__,
                    self._get_translation(user_language, "status_drawing"),
                    True,
                )
                await self._emit_notification(
                    __event_emitter__,
                    self._get_translation(
                        user_language, "notification_success", user_name=user_name
                    ),
                    "success",
                )
                logger.info("Action: Smart Mind Map (v1.0.0) completed in Direct Mode")

                return (
                    final_html_direct,
                    {"Content-Disposition": "inline", "Content-Type": "text/html"},
                )

            else:
                # LEGACY MODE
                # embed as HTML block into the message content
                html_embed_tag = f"```html\n{final_html}\n```"
                body["messages"][-1][
                    "content"
                ] = f"{long_text_content}\n\n{html_embed_tag}"

                await self._emit_status(
                    __event_emitter__,
                    self._get_translation(user_language, "status_drawing"),
                    True,
                )
                await self._emit_notification(
                    __event_emitter__,
                    self._get_translation(
                        user_language, "notification_success", user_name=user_name
                    ),
                    "success",
                )
                logger.info(
                    "Action: Smart Mind Map (v1.0.0) completed in Legacy HTML mode"
                )

        except Exception as e:
            error_message = f"Smart Mind Map processing failed: {str(e)}"
            logger.error(f"Smart Mind Map error: {error_message}", exc_info=True)
            user_facing_error = self._get_translation(
                user_language, "error_user_facing", error=str(e)
            )

            body["messages"][-1][
                "content"
            ] = f"{long_text_content}\n\n❌ **Error:** {user_facing_error}"

            await self._emit_status(
                __event_emitter__,
                self._get_translation(user_language, "status_failed"),
                True,
            )
            await self._emit_notification(
                __event_emitter__,
                self._get_translation(
                    user_language, "notification_failed", user_name=user_name
                ),
                "error",
            )
        return body

    def _is_direct_html_supported(self, body: dict) -> bool:
        """
        Check if the current Open WebUI version supports direct HTML return + inline display.
        Target version >= 0.8.0.
        """
        if not self.valves.ENABLE_DIRECT_EMBED_MODE:
            return False

        try:
            # First check server-side version
            version = open_webui_version
            if not version or version == "0.0.0":
                # If server version unknown, fallback to body version
                version = body.get("version")

            if not version:
                # If still no version, default to True (assume modern)
                return True

            # If version is present, check 0.8.0+
            # Simple lexicographical check usually works for semver if format is consistent x.y.z
            # But "0.9.0" > "0.8.0" is true. "0.10.0" > "0.8.0" (lexicographically "0.1" < "0.8") fails.
            # So we need safer parsing.
            parts = version.split(".")
            if len(parts) >= 2:
                major = int(parts[0])
                minor = int(parts[1])
                if major > 0 or (major == 0 and minor >= 8):
                    return True
            return False
        except Exception:
            # On error, default to True to assume modern features
            return True

    # ... (Rest of Action class methods) ...
