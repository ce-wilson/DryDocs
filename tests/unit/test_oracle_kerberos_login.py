"""Unit tests for libs/oracle_kerberos/spider_login.py — no oracledb, no network."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from libs.oracle_kerberos import spider_login as sl


class TestParseConfig:
    def test_basic_keys_and_comments(self):
        text = (
            "# comment\n"
            "sid = D000000\n"
            "servicename = SOME_ALIAS_O_READWRITE\n"
            "; another comment\n"
            "\n"
            "dpi_debug_level = 0\n"
        )
        cfg = sl.parse_config(text)
        assert cfg == {
            "sid": "D000000",
            "servicename": "SOME_ALIAS_O_READWRITE",
            "dpi_debug_level": "0",
        }

    def test_values_may_be_quoted_and_keys_lowercased(self):
        cfg = sl.parse_config('HOSTNAME = "db.example.com"\n')
        assert cfg == {"hostname": "db.example.com"}

    def test_windows_paths_survive(self):
        cfg = sl.parse_config(r"tns_admin = C:\Users\D000000\TNSNAMES" + "\n")
        assert cfg["tns_admin"] == r"C:\Users\D000000\TNSNAMES"


class TestNormalizeKrb5ccname:
    def test_bare_path_gets_file_prefix(self):
        assert sl.normalize_krb5ccname(r"C:\Users\D0\krb5cc_D0") == r"FILE:C:\Users\D0\krb5cc_D0"

    def test_file_prefix_passthrough(self):
        assert sl.normalize_krb5ccname(r"FILE:C:\x\krb5cc") == r"FILE:C:\x\krb5cc"

    def test_mslsa_passthrough(self):
        assert sl.normalize_krb5ccname("MSLSA:") == "MSLSA:"
        assert sl.is_mslsa("MSLSA:")
        assert not sl.is_mslsa(r"FILE:C:\x")

    def test_blank_uses_env_krb5ccname(self, monkeypatch):
        monkeypatch.setenv("KRB5CCNAME", r"C:\env\krb5cc_env")
        assert sl.normalize_krb5ccname("", sid="D0") == r"FILE:C:\env\krb5cc_env"

    def test_blank_with_sid_derives_default(self, monkeypatch):
        monkeypatch.delenv("KRB5CCNAME", raising=False)
        result = sl.normalize_krb5ccname("", sid="D000000")
        assert result.startswith("FILE:")
        assert "krb5cc" in result
        assert "D000000" in result or "krb5cc_" in result  # POSIX default uses uid

    def test_cache_file_path(self):
        assert sl.cache_file_path(r"FILE:C:\x\cc") == Path(r"C:\x\cc")
        assert sl.cache_file_path("MSLSA:") is None


class TestBuildSqlnet:
    def test_file_mode_carries_mit_lines(self):
        text = sl.build_sqlnet_text(r"C:\u\krb5.conf", r"FILE:C:\u\krb5cc_D0")
        assert "SQLNET.AUTHENTICATION_SERVICES=(KERBEROS5)" in text
        assert r"SQLNET.KERBEROS5_CONF=C:\u\krb5.conf" in text
        assert "SQLNET.KERBEROS5_CONF_MIT=TRUE" in text
        assert r"SQLNET.KERBEROS5_CC_NAME=FILE:C:\u\krb5cc_D0" in text

    def test_mslsa_mode_has_no_mit_lines(self):
        # MIT lines + MSLSA: cache = the init-time "validating loaded library" hang
        text = sl.build_sqlnet_text(r"C:\u\krb5.conf", "MSLSA:")
        assert "SQLNET.KERBEROS5_CC_NAME=MSLSA:" in text
        assert "KERBEROS5_CONF" not in text.replace("KERBEROS5_CONF_MIT", "")
        assert "CONF_MIT" not in text
        assert "krb5.conf" not in text

    def test_both_modes_use_tnsnames_directory_path(self):
        for cc in (r"FILE:C:\u\cc", "MSLSA:"):
            assert "NAMES.DIRECTORY_PATH=(TNSNAMES,EZCONNECT)" in sl.build_sqlnet_text("x", cc)


class TestAliasAddressListCount:
    TNS = """
OTHER_ALIAS =
  (DESCRIPTION =
    (ADDRESS_LIST = (LOAD_BALANCE = on)(ADDRESS = (PROTOCOL = TCP)(HOST = a)(PORT = 1)))
  )

MY_ALIAS_O_READWRITE =
  (DESCRIPTION =
    (ADDRESS_LIST = (LOAD_BALANCE = on)(ADDRESS = (PROTOCOL = TCP)(HOST = h1)(PORT = 6336)))
    (ADDRESS_LIST = (LOAD_BALANCE = on)(ADDRESS = (PROTOCOL = TCP)(HOST = h2)(PORT = 6336)))
    (CONNECT_DATA = (SERVICE_NAME = MY_ALIAS_O_READWRITE))
  )
"""

    def test_dual_address_list_counted(self):
        assert sl.alias_address_list_count(self.TNS, "MY_ALIAS_O_READWRITE") == 2

    def test_single_address_list_counted(self):
        assert sl.alias_address_list_count(self.TNS, "OTHER_ALIAS") == 1

    def test_missing_alias_returns_minus_one(self):
        assert sl.alias_address_list_count(self.TNS, "NOPE") == -1


class TestExplain:
    @pytest.mark.parametrize(
        ("fragment", "expect"),
        [
            ("ORA-12514: TNS:listener does not currently know", "alias"),
            ("ORA-01017: invalid username/password", "Thick mode"),
            ("ORA-12641: Authentication service failed", "krb5.conf"),
            ("DPY-4024: call timeout of 30000 ms exceeded", "NOT a connectivity"),
            ("ORA-12154: TNS:could not resolve", "tnsnames.ora"),
        ],
    )
    def test_known_codes_mapped(self, fragment, expect):
        result = sl.explain(RuntimeError(fragment))
        assert result is not None
        assert expect in result

    def test_unknown_returns_none(self):
        assert sl.explain(RuntimeError("ORA-00942: table or view does not exist")) is None


class TestConfigDiscovery:
    def test_explicit_path_wins(self, tmp_path):
        cfg_file = tmp_path / "custom.txt"
        cfg_file.write_text("sid = D0\nservicename = A\n", encoding="utf-8")
        cfg = sl.load_config(cfg_file)
        assert cfg["sid"] == "D0"
        assert cfg["_config_path"] == str(cfg_file)

    def test_overrides_beat_file(self, tmp_path):
        cfg_file = tmp_path / "custom.txt"
        cfg_file.write_text("sid = D0\n", encoding="utf-8")
        cfg = sl.load_config(cfg_file, sid="D999999")
        assert cfg["sid"] == "D999999"

    def test_missing_raises_with_search_list(self, tmp_path, monkeypatch):
        # a real gitignored config next to the module would otherwise be
        # discovered — repoint the module-dir fallback at the empty tmp_path
        # so this passes on machines that have one
        monkeypatch.delenv(sl.CONFIG_ENV_VAR, raising=False)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sl, "_MODULE_DIR", tmp_path)
        with pytest.raises(FileNotFoundError, match="Searched"):
            sl.load_config(None)

    def test_env_var_discovery(self, tmp_path, monkeypatch):
        cfg_file = tmp_path / "envconf.txt"
        cfg_file.write_text("sid = D0\n", encoding="utf-8")
        monkeypatch.setenv(sl.CONFIG_ENV_VAR, str(cfg_file))
        assert sl.load_config(None)["sid"] == "D0"


class TestBuildRuntimeTnsAdmin:
    def test_copies_tnsnames_and_writes_clean_sqlnet(self, tmp_path):
        src = tmp_path / "tns"
        src.mkdir()
        (src / "tnsnames.ora").write_text("MY_ALIAS = (DESCRIPTION=...)\n", encoding="utf-8")
        cfg = {"tns_admin": str(src), "krb5_config": r"C:\u\krb5.conf"}
        runtime = sl.build_runtime_tns_admin(cfg, r"FILE:C:\u\cc")
        assert (runtime / "tnsnames.ora").read_text(encoding="utf-8").startswith("MY_ALIAS")
        sqlnet = (runtime / "sqlnet.ora").read_text(encoding="utf-8")
        assert "KERBEROS5" in sqlnet

    def test_missing_tnsnames_raises(self, tmp_path):
        cfg = {"tns_admin": str(tmp_path), "krb5_config": "x"}
        with pytest.raises(FileNotFoundError, match="tnsnames.ora"):
            sl.build_runtime_tns_admin(cfg, "MSLSA:")
