import importlib.util
import unittest
from pathlib import Path

OTA_DIR = Path(__file__).resolve().parent.parent


def _load(filename):
    path = OTA_DIR / filename
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fase10 = _load("build-dalauncher-fase10.py")
restore = _load("build-dalauncher-restore.py")

FASE10_SCRIPT = fase10._updater_script("0040", None)
RESTORE_SCRIPT = restore._updater_script("0040", None)


class InvariantesComunsDoUpdaterScript(unittest.TestCase):
    def test_tem_device_guard_vcm30t30_nos_dois_pacotes(self):
        for script in (FASE10_SCRIPT, RESTORE_SCRIPT):
            self.assertIn('getprop("ro.product.device") == "vcm30t30"', script)

    def test_monta_app_e_vendor_na_ordem_certa(self):
        for script in (FASE10_SCRIPT, RESTORE_SCRIPT):
            pos_app = script.find('by-name/APP", "/system"')
            pos_cap = script.find('by-name/CAP", "/system/vendor"')
            self.assertNotEqual(pos_app, -1)
            self.assertNotEqual(pos_cap, -1)
            self.assertLess(pos_app, pos_cap)

    def test_desmonta_vendor_antes_de_system(self):
        for script in (FASE10_SCRIPT, RESTORE_SCRIPT):
            self.assertLess(script.find('unmount("/system/vendor")'), script.find('unmount("/system")'))

    def test_quebra_o_loop_antes_do_sleep_final(self):
        for script in (FASE10_SCRIPT, RESTORE_SCRIPT):
            pos_mv = script.find("SwUpdate2.txt /mnt/usbdrive1/SwUpdate2.txt.done")
            pos_rm = script.find("rm -f /cache/.copy_complete")
            pos_sleep = script.find('run_program("/tmp/sleep"')
            self.assertNotEqual(pos_mv, -1)
            self.assertNotEqual(pos_rm, -1)
            self.assertLess(pos_mv, pos_sleep)
            self.assertLess(pos_rm, pos_sleep)


class Fase10DeployInvariantes(unittest.TestCase):
    def test_substitui_o_apk_do_dalauncher(self):
        self.assertIn('package_extract_file("system/vendor/app/DaLauncher.apk", "/system/vendor/app/DaLauncher.apk")', FASE10_SCRIPT)

    def test_remove_o_odex_antigo(self):
        self.assertIn("rm -f /system/vendor/app/DaLauncher.odex", FASE10_SCRIPT)

    def test_remocao_do_odex_e_verificada_com_gate_de_status(self):
        self.assertIn("test ! -e /system/vendor/app/DaLauncher.odex", FASE10_SCRIPT)
        self.assertIn("FASE10-ODEX-REMOVED.OK", FASE10_SCRIPT)
        self.assertIn("FASE10-ODEX-REMOVED.FAIL", FASE10_SCRIPT)

    def test_nao_deixa_a_falha_do_rm_passar_silenciosa(self):
        self.assertNotIn("echo rm-odex-exit=$?", FASE10_SCRIPT)


class RollbackRestoreInvariantes(unittest.TestCase):
    def test_restaura_apk_e_odex_originais(self):
        self.assertIn('package_extract_file("system/vendor/app/DaLauncher.apk"', RESTORE_SCRIPT)
        self.assertIn('package_extract_file("system/vendor/app/DaLauncher.odex"', RESTORE_SCRIPT)

    def test_verifica_md5_dos_originais_e_grava_gate(self):
        self.assertIn(restore.EXPECTED_APK_MD5, RESTORE_SCRIPT)
        self.assertIn(restore.EXPECTED_ODEX_MD5, RESTORE_SCRIPT)
        self.assertIn("ROLLBACK-RESTORED.OK", RESTORE_SCRIPT)
        self.assertIn("ROLLBACK-RESTORED.FAIL", RESTORE_SCRIPT)


if __name__ == "__main__":
    unittest.main()
