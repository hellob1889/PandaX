    def test_all_called_keys_are_defined(self):
        """Bug #20 回归测试:src/pandaone 中所有 t() 调用的 key 都必须在 zh-CN/en 中定义"""
        import re
        from pathlib import Path
        src_dir = Path(i18n.__file__).parent
        pattern = re.compile(r'(?<![a-zA-Z0-9_])t\(\s*["\']([a-zA-Z_][a-zA-Z0-9_]*)["\']')
        # 收集 i18n.py 主 dict 的 key
        defined = set(i18n.TRANSLATIONS["zh-CN"].keys()) | set(i18n.TRANSLATIONS["en"].keys())
        # PR #28: 合并 i18n_extras (运行时注册,静态测试也需识别)
        try:
            from pandaone.i18n_extras import EXTRANSLATIONS
            defined |= set(EXTRANSLATIONS["zh-CN"].keys()) | set(EXTRANSLATIONS["en"].keys())
        except ImportError:
            pass
        undefined = set()
        for py_file in src_dir.glob("*.py"):
            for match in pattern.finditer(py_file.read_text(encoding="utf-8")):
                key = match.group(1)
                if key not in defined:
                    undefined.add(key)
        assert not undefined, f"t() calls undefined keys: {undefined}"  # PR #28 fix applied