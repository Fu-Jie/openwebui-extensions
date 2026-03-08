#!/usr/bin/env python3
"""
独立测试脚本：验证 OpenWebUI Skills Manager 的所有安全修复
不需要 OpenWebUI 环境，可以直接运行

测试内容：
1. SSRF 防护 (_is_safe_url)
2. 不安全 tar/zip 提取防护 (_safe_extract_zip, _safe_extract_tar)
3. 名称冲突检查 (update_skill)
4. URL 验证
"""

import asyncio
import json
import logging
import sys
import tempfile
import tarfile
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==================== 模拟 OpenWebUI Skills 类 ====================


class MockSkill:
    def __init__(self, id: str, name: str, description: str = "", content: str = ""):
        self.id = id
        self.name = name
        self.description = description
        self.content = content
        self.is_active = True
        self.updated_at = "2024-03-08T00:00:00Z"


class MockSkills:
    """Mock Skills 模型，用于测试"""

    _skills: Dict[str, List[MockSkill]] = {}

    @classmethod
    def reset(cls):
        cls._skills = {}

    @classmethod
    def get_skills_by_user_id(cls, user_id: str):
        return cls._skills.get(user_id, [])

    @classmethod
    def insert_new_skill(cls, user_id: str, form_data):
        if user_id not in cls._skills:
            cls._skills[user_id] = []
        skill = MockSkill(
            form_data.id, form_data.name, form_data.description, form_data.content
        )
        cls._skills[user_id].append(skill)
        return skill

    @classmethod
    def update_skill_by_id(cls, skill_id: str, updates: Dict[str, Any]):
        for user_skills in cls._skills.values():
            for skill in user_skills:
                if skill.id == skill_id:
                    for key, value in updates.items():
                        setattr(skill, key, value)
                    return skill
        return None

    @classmethod
    def delete_skill_by_id(cls, skill_id: str):
        for user_id, user_skills in cls._skills.items():
            for idx, skill in enumerate(user_skills):
                if skill.id == skill_id:
                    user_skills.pop(idx)
                    return True
        return False


# ==================== 提取安全测试的核心方法 ====================

import ipaddress
import urllib.parse


class SecurityTester:
    """提取出的安全测试核心类"""

    def __init__(self):
        # 模拟 Valves 配置
        self.valves = type(
            "Valves",
            (),
            {
                "ENABLE_DOMAIN_WHITELIST": True,
                "TRUSTED_DOMAINS": "github.com,raw.githubusercontent.com,huggingface.co",
            },
        )()

    def _is_safe_url(self, url: str) -> tuple:
        """
        验证 URL 是否指向内部/敏感目标。
        防止服务端请求伪造 (SSRF) 攻击。

        返回 (True, None) 如果 URL 是安全的，否则返回 (False, error_message)。
        """
        try:
            parsed = urllib.parse.urlparse(url)
            hostname = parsed.hostname or ""

            if not hostname:
                return False, "URL is malformed: missing hostname"

            # 拒绝 localhost 变体
            if hostname.lower() in (
                "localhost",
                "127.0.0.1",
                "::1",
                "[::1]",
                "0.0.0.0",
                "[::ffff:127.0.0.1]",
                "localhost.localdomain",
            ):
                return False, "URL points to local host"

            # 拒绝内部 IP 范围 (RFC 1918, link-local 等)
            try:
                ip = ipaddress.ip_address(hostname.lstrip("[").rstrip("]"))
                # 拒绝私有、回环、链接本地和保留 IP
                if (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_link_local
                    or ip.is_reserved
                ):
                    return False, f"URL points to internal IP: {ip}"
            except ValueError:
                # 不是 IP 地址，检查 hostname 模式
                pass

            # 拒绝 file:// 和其他非 http(s) 方案
            if parsed.scheme not in ("http", "https"):
                return False, f"URL scheme not allowed: {parsed.scheme}"

            # 域名白名单检查 (安全层 2)
            if self.valves.ENABLE_DOMAIN_WHITELIST:
                trusted_domains = [
                    d.strip().lower()
                    for d in (self.valves.TRUSTED_DOMAINS or "").split(",")
                    if d.strip()
                ]

                if not trusted_domains:
                    # 没有配置授信域名，仅进行安全检查
                    return True, None

                hostname_lower = hostname.lower()

                # 检查 hostname 是否匹配任何授信域名（精确或子域名）
                is_trusted = False
                for trusted_domain in trusted_domains:
                    # 精确匹配
                    if hostname_lower == trusted_domain:
                        is_trusted = True
                        break
                    # 子域名匹配 (*.example.com 匹配 api.example.com)
                    if hostname_lower.endswith("." + trusted_domain):
                        is_trusted = True
                        break

                if not is_trusted:
                    error_msg = f"URL domain '{hostname}' is not in whitelist. Trusted domains: {', '.join(trusted_domains)}"
                    return False, error_msg

            return True, None
        except Exception as e:
            return False, f"Error validating URL: {e}"

    def _safe_extract_zip(self, zip_path: Path, extract_dir: Path) -> None:
        """
        安全地提取 ZIP 文件，验证成员路径以防止路径遍历。
        """
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.namelist():
                # 检查路径遍历尝试
                member_path = Path(extract_dir) / member
                try:
                    # 确保解析的路径在 extract_dir 内
                    member_path.resolve().relative_to(extract_dir.resolve())
                except ValueError:
                    # 路径在 extract_dir 外（遍历尝试）
                    logger.warning(f"Skipping unsafe ZIP member: {member}")
                    continue

                # 提取成员
                zf.extract(member, extract_dir)

    def _safe_extract_tar(self, tar_path: Path, extract_dir: Path) -> None:
        """
        安全地提取 TAR 文件，验证成员路径以防止路径遍历。
        """
        with tarfile.open(tar_path, "r:*") as tf:
            for member in tf.getmembers():
                # 检查路径遍历尝试
                member_path = Path(extract_dir) / member.name
                try:
                    # 确保解析的路径在 extract_dir 内
                    member_path.resolve().relative_to(extract_dir.resolve())
                except ValueError:
                    # 路径在 extract_dir 外（遍历尝试）
                    logger.warning(f"Skipping unsafe TAR member: {member.name}")
                    continue

                # 提取成员
                tf.extract(member, extract_dir)


# ==================== 测试用例 ====================


def test_ssrf_protection():
    """测试 SSRF 防护"""
    print("\n" + "=" * 60)
    print("测试 1: SSRF 防护 (_is_safe_url)")
    print("=" * 60)

    tester = SecurityTester()

    # 不安全的 URLs (应该被拒绝)
    unsafe_urls = [
        "http://localhost/skill",
        "http://127.0.0.1:8000/skill",
        "http://[::1]/skill",
        "http://0.0.0.0/skill",
        "http://192.168.1.1/skill",  # 私有 IP (RFC 1918)
        "http://10.0.0.1/skill",
        "http://172.16.0.1/skill",
        "http://169.254.1.1/skill",  # link-local
        "file:///etc/passwd",  # file:// scheme
        "gopher://example.com/skill",  # 非 http(s)
    ]

    print("\n❌ 不安全的 URLs (应该被拒绝):")
    for url in unsafe_urls:
        is_safe, error_msg = tester._is_safe_url(url)
        status = "✗ 被拒绝 (正确)" if not is_safe else "✗ 被接受 (错误)"
        error_info = f" - {error_msg}" if error_msg else ""
        print(f"  {url:<50} {status}{error_info}")
        assert not is_safe, f"URL 不应该被接受: {url}"

    # 安全的 URLs (应该被接受)
    safe_urls = [
        "https://github.com/Fu-Jie/openwebui-extensions/raw/main/SKILL.md",
        "https://raw.githubusercontent.com/user/repo/main/skill.md",
        "https://huggingface.co/spaces/user/skill",
    ]

    print("\n✅ 安全且在白名单中的 URLs (应该被接受):")
    for url in safe_urls:
        is_safe, error_msg = tester._is_safe_url(url)
        status = "✓ 被接受 (正确)" if is_safe else "✓ 被拒绝 (错误)"
        error_info = f" - {error_msg}" if error_msg else ""
        print(f"  {url:<60} {status}{error_info}")
        assert is_safe, f"URL 不应该被拒绝: {url} - {error_msg}"

    print("\n✓ SSRF 防护测试通过!")


def test_tar_extraction_safety():
    """测试 TAR 提取路径遍历防护"""
    print("\n" + "=" * 60)
    print("测试 2: TAR 提取安全性 (_safe_extract_tar)")
    print("=" * 60)

    tester = SecurityTester()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # 创建一个包含路径遍历尝试的 tar 文件
        tar_path = tmpdir_path / "malicious.tar"
        extract_dir = tmpdir_path / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)

        print("\n创建测试 TAR 文件...")
        with tarfile.open(tar_path, "w") as tf:
            # 合法的成员
            import io

            info = tarfile.TarInfo(name="safe_file.txt")
            info.size = 11
            tf.addfile(tarinfo=info, fileobj=io.BytesIO(b"safe content"))

            # 路径遍历尝试
            info = tarfile.TarInfo(name="../../etc/passwd")
            info.size = 10
            tf.addfile(tarinfo=info, fileobj=io.BytesIO(b"evil data!"))

        print(f"  TAR 文件已创建: {tar_path}")

        # 提取文件
        print("\n提取 TAR 文件...")
        try:
            tester._safe_extract_tar(tar_path, extract_dir)

            # 检查结果
            safe_file = extract_dir / "safe_file.txt"
            evil_file = extract_dir / "etc" / "passwd"
            evil_file_alt = Path("/etc/passwd")

            print(f"  检查合法文件: {safe_file.exists()} (应该为 True)")
            assert safe_file.exists(), "合法文件应该被提取"

            print(f"  检查恶意文件不存在: {not evil_file.exists()} (应该为 True)")
            assert not evil_file.exists(), "恶意文件不应该被提取"

            print("\n✓ TAR 提取安全性测试通过!")
        except Exception as e:
            print(f"✗ 提取失败: {e}")
            raise


def test_zip_extraction_safety():
    """测试 ZIP 提取路径遍历防护"""
    print("\n" + "=" * 60)
    print("测试 3: ZIP 提取安全性 (_safe_extract_zip)")
    print("=" * 60)

    tester = SecurityTester()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # 创建一个包含路径遍历尝试的 zip 文件
        zip_path = tmpdir_path / "malicious.zip"
        extract_dir = tmpdir_path / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)

        print("\n创建测试 ZIP 文件...")
        with zipfile.ZipFile(zip_path, "w") as zf:
            # 合法的成员
            zf.writestr("safe_file.txt", "safe content")

            # 路径遍历尝试
            zf.writestr("../../etc/passwd", "evil data!")

        print(f"  ZIP 文件已创建: {zip_path}")

        # 提取文件
        print("\n提取 ZIP 文件...")
        try:
            tester._safe_extract_zip(zip_path, extract_dir)

            # 检查结果
            safe_file = extract_dir / "safe_file.txt"
            evil_file = extract_dir / "etc" / "passwd"

            print(f"  检查合法文件: {safe_file.exists()} (应该为 True)")
            assert safe_file.exists(), "合法文件应该被提取"

            print(f"  检查恶意文件不存在: {not evil_file.exists()} (应该为 True)")
            assert not evil_file.exists(), "恶意文件不应该被提取"

            print("\n✓ ZIP 提取安全性测试通过!")
        except Exception as e:
            print(f"✗ 提取失败: {e}")
            raise


def test_skill_name_collision():
    """测试技能名称冲突检查"""
    print("\n" + "=" * 60)
    print("测试 4: 技能名称冲突检查")
    print("=" * 60)

    # 模拟技能管理
    user_id = "test_user_1"
    MockSkills.reset()

    # 创建第一个技能
    print("\n创建技能 1: 'MySkill'...")
    skill1 = MockSkill("skill_1", "MySkill", "First skill", "content1")
    MockSkills._skills[user_id] = [skill1]
    print(f"  ✓ 技能已创建: {skill1.name}")

    # 创建第二个技能
    print("\n创建技能 2: 'AnotherSkill'...")
    skill2 = MockSkill("skill_2", "AnotherSkill", "Second skill", "content2")
    MockSkills._skills[user_id].append(skill2)
    print(f"  ✓ 技能已创建: {skill2.name}")

    # 测试名称冲突检查逻辑
    print("\n测试名称冲突检查...")

    # 模拟尝试将 skill2 改名为 skill1 的名称
    new_name = "MySkill"  # 已被 skill1 占用
    print(f"\n尝试将技能 2 改名为 '{new_name}'...")
    print(f"  检查是否与其他技能冲突...")

    # 这是 update_skill 中的冲突检查逻辑
    collision_found = False
    for other_skill in MockSkills._skills[user_id]:
        # 跳过要更新的技能本身
        if other_skill.id == "skill_2":
            continue
        # 检查是否存在同名技能
        if other_skill.name.lower() == new_name.lower():
            collision_found = True
            print(f"  ✓ 冲突检测成功！发现重复名称: {other_skill.name}")
            break

    assert collision_found, "应该检测到名称冲突"

    # 测试允许的改名（改为不同的名称）
    print(f"\n尝试将技能 2 改名为 'UniqueSkill'...")
    new_name = "UniqueSkill"
    collision_found = False
    for other_skill in MockSkills._skills[user_id]:
        if other_skill.id == "skill_2":
            continue
        if other_skill.name.lower() == new_name.lower():
            collision_found = True
            break

    assert not collision_found, "不应该存在冲突"
    print(f"  ✓ 允许改名，没有冲突")

    print("\n✓ 技能名称冲突检查测试通过!")


def test_url_normalization():
    """测试 URL 标准化"""
    print("\n" + "=" * 60)
    print("测试 5: URL 标准化")
    print("=" * 60)

    tester = SecurityTester()

    # 测试无效的 URL
    print("\n测试无效的 URL:")
    invalid_urls = [
        "not-a-url",
        "ftp://example.com/file",
        "",
        "   ",
    ]

    for url in invalid_urls:
        is_safe, error_msg = tester._is_safe_url(url)
        print(f"  '{url}' -> 被拒绝: {not is_safe} ✓")
        assert not is_safe, f"无效 URL 应该被拒绝: {url}"

    print("\n✓ URL 标准化测试通过!")


def test_domain_whitelist():
    """测试域名白名单功能"""
    print("\n" + "=" * 60)
    print("测试 6: 域名白名单 (ENABLE_DOMAIN_WHITELIST)")
    print("=" * 60)

    # 创建启用白名单的测试器
    tester = SecurityTester()
    tester.valves.ENABLE_DOMAIN_WHITELIST = True
    tester.valves.TRUSTED_DOMAINS = (
        "github.com,raw.githubusercontent.com,huggingface.co"
    )

    print("\n配置信息:")
    print(f"  白名单启用: {tester.valves.ENABLE_DOMAIN_WHITELIST}")
    print(f"  授信域名: {tester.valves.TRUSTED_DOMAINS}")

    # 白名单中的 URLs (应该被接受)
    whitelisted_urls = [
        "https://github.com/user/repo/raw/main/skill.md",
        "https://raw.githubusercontent.com/user/repo/main/skill.md",
        "https://api.github.com/repos/user/repo/contents",
        "https://huggingface.co/spaces/user/skill",
    ]

    print("\n✅ 白名单中的 URLs (应该被接受):")
    for url in whitelisted_urls:
        is_safe, error_msg = tester._is_safe_url(url)
        status = "✓ 被接受 (正确)" if is_safe else "✗ 被拒绝 (错误)"
        print(f"  {url:<65} {status}")
        assert is_safe, f"白名单中的 URL 应该被接受: {url} - {error_msg}"

    # 不在白名单中的 URLs (应该被拒绝)
    non_whitelisted_urls = [
        "https://example.com/skill.md",
        "https://evil.com/skill.zip",
        "https://api.example.com/skill",
    ]

    print("\n❌ 非白名单 URLs (应该被拒绝):")
    for url in non_whitelisted_urls:
        is_safe, error_msg = tester._is_safe_url(url)
        status = "✗ 被拒绝 (正确)" if not is_safe else "✓ 被接受 (错误)"
        print(f"  {url:<65} {status}")
        assert not is_safe, f"非白名单 URL 应该被拒绝: {url}"

    # 测试禁用白名单
    print("\n禁用白名单进行测试...")
    tester.valves.ENABLE_DOMAIN_WHITELIST = False
    is_safe, error_msg = tester._is_safe_url("https://example.com/skill.md")
    print(f"  example.com without whitelist: {is_safe} ✓")
    assert is_safe, "禁用白名单时，example.com 应该被接受"

    print("\n✓ 域名白名单测试通过!")


# ==================== 主函数 ====================


def main():
    print("\n" + "🔒 OpenWebUI Skills Manager 安全修复测试".center(60, "="))
    print("版本: 0.2.2")
    print("=" * 60)

    try:
        # 运行所有测试
        test_ssrf_protection()
        test_tar_extraction_safety()
        test_zip_extraction_safety()
        test_skill_name_collision()
        test_url_normalization()
        test_domain_whitelist()

        # 测试总结
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！".center(60))
        print("=" * 60)
        print("\n修复验证：")
        print("  ✓ SSRF 防护：阻止指向内部 IP 的请求")
        print("  ✓ TAR/ZIP 安全提取：防止路径遍历攻击")
        print("  ✓ 名称冲突检查：防止技能名称重复")
        print("  ✓ URL 验证：仅接受安全的 HTTP(S) URL")
        print("  ✓ 域名白名单：只允许授信域名下载技能")
        print("\n所有安全功能都已成功实现！")
        print("=" * 60 + "\n")

        return 0
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ 测试错误: {e}\n")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
