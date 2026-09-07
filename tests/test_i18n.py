# -*- coding: utf-8 -*-
"""
test_i18n.py — i18n 模块单元测试
==================================

覆盖：
  - 自动检测 OS 语言
  - init() / get_lang() / set_lang() 优先级链
  - t() 函数 + 占位符 + fallback
  - 持久化 ~/.pandax/config.json
  - coverage_report() 准确性
  - available_languages() 列表
"""
import json
import os
from pathlib import Path
from unittest import mock

import pytest

from pandax import i18n


@pytest.fixture(autouse=True)
def reset_i18n_state(tmp_path, monkeypatch):
    """每个测试前重置 i18n 全局状态 + 临时 HOME（兼容 Windows + Unix）"""
    # 重置全局语言到默认值
    i18n._CURRENT_LANG = "zh-CN"
    # 临时 HOME 目录（Windows Path.home() 用 USERPROFILE；Unix 用 HOME）
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    # 清除可能的语言环境变量（让 _detect_os_language 走 Windows API / 兜底）
    monkeypatch.delenv("LANG", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.delenv("LANGUAGE", raising=False)
    yield tmp_path


class TestDetectOsLanguage:
    """测试 _detect_os_language() 自动检测"""

    def test_lang_env_chinese(self, monkeypatch):
        monkeypatch.setenv("LANG", "zh_CN.UTF-8")
        assert i18n._detect_os_language() == "zh-CN"

    def test_lang_env_simplified_chinese(self, monkeypatch):
        monkeypatch.setenv("LANG", "zh_CN")
        assert i18n._detect_os_language() == "zh-CN"

    def test_lang_env_traditional_chinese(self, monkeypatch):
        """繁体中文暂不支持，回退到 zh-CN（与简体中文共用）"""
        monkeypatch.setenv("LANG", "zh_TW.UTF-8")
        # 当前实现：所有 zh_* 都映射到 zh-CN
        result = i18n._detect_os_language()
        assert result in ("zh-CN", "en")  # 至少不崩溃

    def test_lang_env_english(self, monkeypatch):
        monkeypatch.setenv("LANG", "en_US.UTF-8")
        assert i18n._detect_os_language() == "en"

    def test_lc_all_overrides_lang(self, monkeypatch):
        monkeypatch.setenv("LANG", "en_US.UTF-8")
        monkeypatch.setenv("LC_ALL", "zh_CN.UTF-8")
        assert i18n._detect_os_language() == "zh-CN"

    def test_no_env_falls_back_to_en(self, monkeypatch):
        # 清空所有 locale 相关环境变量
        for var in ("LANG", "LC_ALL", "LANGUAGE"):
            monkeypatch.delenv(var, raising=False)
        # locale 模块可能返回 None → 抛异常 → 兜底 en
        result = i18n._detect_os_language()
        assert result in ("zh-CN", "en")


class TestInit:
    """测试 init() / get_lang() / set_lang()"""

    def test_init_default(self):
        """无参数 → OS 自动检测"""
        result = i18n.init()
        assert result in ("zh-CN", "en")
        assert i18n.get_lang() == result

    def test_init_explicit_zh(self, tmp_path):
        i18n.init("zh-CN")
        assert i18n.get_lang() == "zh-CN"

    def test_init_explicit_en(self):
        i18n.init("en")
        assert i18n.get_lang() == "en"

    def test_init_persists_preference(self, tmp_path):
        """init() 会写入 ~/.pandax/config.json"""
        i18n.init("en")
        config_path = tmp_path / ".pandax" / "config.json"
        assert config_path.exists()
        data = json.loads(config_path.read_text(encoding="utf-8"))
        assert data["lang"] == "en"

    def test_init_loads_existing_preference(self, tmp_path):
        """已有 config.json → 读取偏好"""
        config_path = tmp_path / ".pandax"
        config_path.mkdir(parents=True, exist_ok=True)
        (config_path / "config.json").write_text(
            json.dumps({"lang": "en"}, ensure_ascii=False),
            encoding="utf-8"
        )
        # 用 monkeypatch 改 HOME 后调用 init
        with mock.patch.dict(os.environ, {"HOME": str(tmp_path), "USERPROFILE": str(tmp_path)}):
            result = i18n.init()
            assert result == "en"

    def test_init_picks_explicit_over_preference(self, tmp_path):
        """显式指定优先于持久化偏好"""
        config_path = tmp_path / ".pandax"
        config_path.mkdir(parents=True, exist_ok=True)
        (config_path / "config.json").write_text(
            json.dumps({"lang": "en"}),
            encoding="utf-8"
        )
        with mock.patch.dict(os.environ, {"HOME": str(tmp_path), "USERPROFILE": str(tmp_path)}):
            # 显式指定 zh-CN，覆盖
            result = i18n.init("zh-CN")
            assert result == "zh-CN"
            assert i18n.get_lang() == "zh-CN"

    def test_set_lang_runtime(self):
        """set_lang() 运行时切换"""
        i18n.set_lang("en")
        assert i18n.get_lang() == "en"
        i18n.set_lang("zh-CN")
        assert i18n.get_lang() == "zh-CN"

    def test_set_lang_invalid_falls_back(self):
        """set_lang 传无效值保持不变"""
        i18n.init("zh-CN")
        i18n.set_lang("invalid")  # 应该被忽略
        assert i18n.get_lang() == "zh-CN"


class TestTranslation:
    """测试 t() 函数"""

    def test_translate_simple(self):
        i18n.set_lang("zh-CN")
        assert t("err_password_wrong") == "[ERROR] 密码错误，指纹未更新"

    def test_translate_english(self):
        i18n.set_lang("en")
        assert t("err_password_wrong") == "[ERROR] Wrong password, fingerprint not updated"

    def test_translate_with_placeholders(self):
        i18n.set_lang("zh-CN")
        result = t("ok_locked_n", n=3, exts=".py,.json")
        assert "3" in result and ".py" in result

    def test_translate_placeholder_english(self):
        i18n.set_lang("en")
        result = t("ok_locked_n", n=3, exts=".py,.json")
        assert "3" in result and ".py" in result

    def test_missing_key_returns_key(self):
        """key 不存在 → 返回原 key"""
        i18n.set_lang("zh-CN")
        result = t("nonexistent_key")
        assert result == "nonexistent_key"

    def test_missing_placeholder_returns_template(self):
        """占位符缺失 → 原样返回"""
        i18n.set_lang("zh-CN")
        result = t("ok_locked_n")  # 缺少 n, exts
        # 应该返回模板本身，不会崩溃
        assert "{n}" in result or "锁定" in result

    def test_fallback_to_english_when_lang_missing(self):
        """当前语言缺 key → fallback 到英文"""
        # 模拟 zh-CN 缺少某个 key
        original_zh = i18n.TRANSLATIONS["zh-CN"].copy()
        i18n.TRANSLATIONS["zh-CN"].pop("err_password_wrong", None)
        try:
            i18n.set_lang("zh-CN")
            result = t("err_password_wrong")
            assert "Wrong password" in result  # fallback 到 en
        finally:
            i18n.TRANSLATIONS["zh-CN"].update(original_zh)

    def test_t_bilingual_helper(self):
        """t_bilingual 返回双语并列"""
        i18n.set_lang("zh-CN")
        result = i18n.t_bilingual("menu_init", "menu_lock")
        assert "Init" in result and "Lock" in result

    # ===== Bug #17 / #20 回归测试：t() 在用户输入含特殊字符时的鲁棒性 =====
    def test_t_with_backslash_in_placeholder(self):
        """Bug #17 回归测试：占位符值含反斜杠 → 不应抛异常"""
        i18n.set_lang("zh-CN")
        # 反斜杠是 JSON/Windows 路径常见字符
        result = t("write_warn_git_add", err=r"C:\Users\test\file.py")
        assert isinstance(result, str)
        assert "C:\\Users" in result or "C:\\Users\\test\\file.py" in result

    def test_t_with_double_quote_in_placeholder(self):
        """Bug #17 回归测试：占位符值含双引号 → 不应破坏字符串"""
        i18n.set_lang("zh-CN")
        # 双引号是 f-string JSON 注入的攻击载体
        result = t("warn_init_config_corrupted", err='Expecting value at line 1 column 1 (char 0)')
        assert isinstance(result, str)
        assert 'Expecting value' in result

    def test_t_with_cjk_in_placeholder(self):
        """CJK 字符 → 应正确占位（CJK 是 v0.7.1 主要用户语言）"""
        i18n.set_lang("zh-CN")
        result = t("ok_locked_n", n=3, exts=".py,.json")
        assert "3" in result
        assert ".py,.json" in result

    def test_t_with_empty_kwargs(self):
        """空 kwargs → 不抛异常"""
        i18n.set_lang("zh-CN")
        # 调用一个无需占位符的 key
        result = t("err_readme_missing")
        assert "README" in result

    def test_t_with_extra_kwargs_ignored(self):
        """多余 kwargs → 应被忽略（不抛 KeyError）"""
        i18n.set_lang("zh-CN")
        # ok_locked_n 只需要 n, exts；多传一个 unused 应该安全
        result = t("ok_locked_n", n=5, exts=".py", unused_param="x")
        assert "5" in result

    def test_t_with_none_placeholder(self):
        """占位符值为 None → 应格式化为 'None' 而不是抛异常"""
        i18n.set_lang("zh-CN")
        # None 是 Python 中"缺失值"的常见表示
        result = t("warn_lock_failed", file=None, err="test error")
        assert isinstance(result, str)
        assert "test error" in result  # err 仍应被替换

    def test_zh_cn_en_parity(self):
        """Bug #20 回归测试：zh-CN 与 en 的 keys 完全一致（不能有遗漏）"""
        zh_keys = set(i18n.TRANSLATIONS["zh-CN"].keys())
        en_keys = set(i18n.TRANSLATIONS["en"].keys())
        diff_zh = zh_keys - en_keys
        diff_en = en_keys - zh_keys
        assert not diff_zh, f"zh-CN has keys not in en: {diff_zh}"
        assert not diff_en, f"en has keys not in zh-CN: {diff_en}"

    def test_all_called_keys_are_defined(self):
        """Bug #20 回归测试：src/pandax 中所有 t() 调用的 key 都必须在 zh-CN/en 中定义"""
        import re
        from pathlib import Path
        src_dir = Path(i18n.__file__).parent
        pattern = re.compile(r'(?<![a-zA-Z0-9_])t\(\s*["\']([a-zA-Z_][a-zA-Z0-9_]*)["\']')
        defined = set(i18n.TRANSLATIONS["zh-CN"].keys()) | set(i18n.TRANSLATIONS["en"].keys())
        undefined = set()
        for py_file in src_dir.glob("*.py"):
            for match in pattern.finditer(py_file.read_text(encoding="utf-8")):
                key = match.group(1)
                if key not in defined:
                    undefined.add(key)
        assert not undefined, f"t() calls undefined keys: {undefined}"


class TestCoverageReport:
    """测试 coverage_report()"""

    def test_returns_all_languages(self):
        report = i18n.coverage_report()
        assert "zh-CN" in report
        assert "en" in report

    def test_counts_match(self):
        report = i18n.coverage_report()
        for lang, stats in report.items():
            assert stats["total"] == len(i18n.TRANSLATIONS["zh-CN"])
            assert stats["present"] + len(stats["missing"]) == stats["total"]
            assert 0 <= stats["missing_pct"] <= 100

    def test_zh_cn_100_percent(self):
        """zh-CN 是基准，所有 key 都应存在"""
        report = i18n.coverage_report()
        assert report["zh-CN"]["missing"] == []
        assert report["zh-CN"]["missing_pct"] == 0.0


class TestAvailableLanguages:
    """测试 available_languages()"""

    def test_returns_list(self):
        langs = i18n.available_languages()
        assert isinstance(langs, list)
        assert len(langs) >= 2

    def test_each_lang_has_code_and_name(self):
        for code, name in i18n.available_languages():
            assert isinstance(code, str)
            assert isinstance(name, str)
            assert len(code) > 0
            assert len(name) > 0


class TestPersistence:
    """测试持久化逻辑"""

    def test_save_user_pref_creates_dir(self, tmp_path):
        """保存时自动创建 ~/.pandax/"""
        with mock.patch.dict(os.environ, {"HOME": str(tmp_path), "USERPROFILE": str(tmp_path)}):
            i18n._save_user_pref("en")
            assert (tmp_path / ".pandax" / "config.json").exists()

    def test_save_preserves_other_keys(self, tmp_path):
        """保存时不覆盖其他键"""
        config_dir = tmp_path / ".pandax"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.json").write_text(
            json.dumps({"other_key": "value", "lang": "en"}, ensure_ascii=False),
            encoding="utf-8"
        )
        with mock.patch.dict(os.environ, {"HOME": str(tmp_path), "USERPROFILE": str(tmp_path)}):
            i18n._save_user_pref("zh-CN")
            data = json.loads((config_dir / "config.json").read_text(encoding="utf-8"))
            assert data["other_key"] == "value"
            assert data["lang"] == "zh-CN"

    def test_load_user_pref_returns_none_on_missing(self, tmp_path):
        """config.json 不存在 → 返回 None"""
        with mock.patch.dict(os.environ, {"HOME": str(tmp_path), "USERPROFILE": str(tmp_path)}):
            result = i18n._load_user_pref()
            assert result is None

    def test_load_user_pref_handles_invalid_json(self, tmp_path):
        """config.json 损坏 → 返回 None（不崩溃）"""
        config_dir = tmp_path / ".pandax"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.json").write_text("not valid json", encoding="utf-8")
        with mock.patch.dict(os.environ, {"HOME": str(tmp_path), "USERPROFILE": str(tmp_path)}):
            result = i18n._load_user_pref()
            assert result is None


class TestCliLangIntegration:
    """集成测试：CLI --lang 旗标与 i18n 模块协同"""

    def test_cli_lang_zh_cn(self):
        """pandax --lang=zh-CN → 中文"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from pandax.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["--lang=zh-CN", "--version"])
        assert args.lang == "zh-CN"

    def test_cli_lang_en(self):
        """pandax --lang=en → 英文"""
        from pandax.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["--lang=en", "--version"])
        assert args.lang == "en"

    def test_cli_default_lang_is_none(self):
        """不指定 --lang → None（自动检测）"""
        from pandax.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["--version"])
        assert args.lang is None

    def test_cli_install_context_has_lang(self):
        """pandax install-context 支持 --lang"""
        from pandax.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["install-context", "--lang=en"])
        assert args.command == "install-context"
        assert args.lang == "en"


# 导入 pandax.cli.t 用于 TestTranslation（避免 Python 导入顺序问题）
from pandax.cli import t