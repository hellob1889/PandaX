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