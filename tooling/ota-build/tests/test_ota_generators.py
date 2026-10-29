import importlib.util
import re
import unittest
from pathlib import Path

OTA_DIR = Path(__file__).resolve().parent.parent

GERADORES = [
    "build.py",
    "build-rollback.py",
    "build-dump-raw.py",
    "build-deep-scan.py",
    "build-diagnostic.py",
    "build-enable-adb.py",
]

LOOP_BREAK_MV = "SwUpdate2.txt /mnt/usbdrive1/SwUpdate2.txt.done"
LOOP_BREAK_RM = "rm -f /cache/.copy_complete"


def _load(filename):
    path = OTA_DIR / filename
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _updater_script_de(filename):
    mod = _load(filename)
    if filename == "build.py":
        mod.CURRENT_ROM_TYPE = "0040"
        return mod.our_create_updater_script([], {}, mod.upstream.PARTITIONS)
    if filename in ("build-diagnostic.py", "build-enable-adb.py"):
        return mod._updater_script("0040")
    return mod._updater_script("0040", {}, mod.upstream.PARTITIONS)


class TodoGeradorQuebraOLoop(unittest.TestCase):
    def test_todo_gerador_renomeia_swupdate2_e_remove_copy_complete(self):
        for filename in GERADORES:
            with self.subTest(gerador=filename):
                script = _updater_script_de(filename)
                self.assertIn(LOOP_BREAK_MV, script)
                self.assertIn(LOOP_BREAK_RM, script)

    def test_loop_break_vem_antes_do_sleep_final(self):
        for filename in GERADORES:
            with self.subTest(gerador=filename):
                script = _updater_script_de(filename)
                pos_sleep = script.find('run_program("/tmp/sleep"')
                self.assertNotEqual(pos_sleep, -1)
                self.assertLess(script.find(LOOP_BREAK_MV), pos_sleep)
                self.assertLess(script.find(LOOP_BREAK_RM), pos_sleep)


class NenhumGeradorPrendeORecoveryEmLoop(unittest.TestCase):
    def test_nenhum_gerador_tem_assert_nem_abort_no_updater_script(self):
        for filename in GERADORES:
            with self.subTest(gerador=filename):
                script = _updater_script_de(filename)
                self.assertNotIn("assert(", script)
                self.assertNotIn("abort(", script)

    def test_set_perm_so_em_tmp_porque_aborta_quando_o_arquivo_falta(self):
        for filename in GERADORES:
            with self.subTest(gerador=filename):
                alvos = re.findall(r'set_perm\(.*"([^"]+)"\);', _updater_script_de(filename))
                self.assertTrue(alvos)
                self.assertTrue(all(alvo.startswith("/tmp/") for alvo in alvos), alvos)


class OperacoesEspecificas(unittest.TestCase):
    def test_build_instala_autook_e_su(self):
        script = _updater_script_de("build.py")
        self.assertIn("AutoOk.apk", script)
        self.assertIn("/system/xbin/su", script)

    def test_rollback_remove_autook_e_su(self):
        script = _updater_script_de("build-rollback.py")
        self.assertIn("rm -f /system/app/AutoOk.apk /system/xbin/su", script)

    def test_build_da_perm_em_system_pelo_busybox_e_confirma_setuid_do_su(self):
        script = _updater_script_de("build.py")
        self.assertIn("chown 0:0 /system/app/AutoOk.apk", script)
        self.assertIn("chmod 0644 /system/app/AutoOk.apk", script)
        self.assertIn("chown 0:0 /system/xbin/su", script)
        self.assertIn("chmod 6755 /system/xbin/su", script)
        # su sem setuid = AutoOk sem root: o gate tem que conferir o bit.
        self.assertIn("test -u /system/xbin/su", script)
        self.assertIn("AUTOOK-INSTALLED.OK", script)
        self.assertIn("AUTOOK-INSTALLED.FAIL", script)

    def test_rollback_confirma_remocao_so_com_system_montado(self):
        script = _updater_script_de("build-rollback.py")
        # sem o teste do build.prop, /system não montado daria "removido" falso
        self.assertIn("test -e /system/build.prop", script)
        self.assertIn("AUTOOK-REMOVED.OK", script)
        self.assertIn("AUTOOK-REMOVED.FAIL", script)


if __name__ == "__main__":
    unittest.main()
