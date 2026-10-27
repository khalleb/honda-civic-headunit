import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
LIB = SCRIPTS_DIR / "lib-pendrive.sh"
WRAPPERS = sorted(SCRIPTS_DIR.glob("prepare-pendrive-*.sh"))


def _bash(comandos, entrada=""):
    return subprocess.run(
        ["bash", "-c", f'set -euo pipefail; source "{LIB}"; {comandos}'],
        input=entrada,
        capture_output=True,
        text=True,
    )


def _criar_build(raiz, timestamp, mdt=b"mdt"):
    build = raiz / timestamp
    (build / "0040").mkdir(parents=True)
    (build / "SwUpdate2.txt").write_text("Ver:IC1101\n")
    (build / "0040" / "SwUpdate.mdt").write_bytes(mdt)
    return build


class _ComPastaTemporaria(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


class EscolhaDoBuild(_ComPastaTemporaria):
    def test_usa_o_build_mais_novo_do_diretorio(self):
        _criar_build(self.raiz, "20261023T213911Z")
        novo = _criar_build(self.raiz, "20261026T214450Z")
        r = _bash(f'resolve_build_dir "{self.raiz}" build.py')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), str(novo))

    def test_usa_o_build_exato_quando_recebe_um_timestamp(self):
        velho = _criar_build(self.raiz, "20261023T213911Z")
        _criar_build(self.raiz, "20261026T214450Z")
        r = _bash(f'resolve_build_dir "{velho}" build.py')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), str(velho))

    def test_recusa_diretorio_inexistente_dizendo_qual_build_rodar(self):
        r = _bash(f'resolve_build_dir "{self.raiz}/nao-existe" "python3 build-x.py"')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("nenhum build encontrado", r.stderr)
        self.assertIn("python3 build-x.py", r.stderr)

    def test_recusa_build_mais_novo_incompleto_em_vez_de_cair_no_anterior(self):
        _criar_build(self.raiz, "20261023T213911Z")
        incompleto = self.raiz / "20261026T214450Z"
        incompleto.mkdir()
        (incompleto / "SwUpdate2.txt").write_text("Ver:IC1101\n")
        r = _bash(f'resolve_build_dir "{self.raiz}" build.py')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(f"{incompleto} não tem SwUpdate2.txt e 0040/SwUpdate.mdt", r.stderr)

    def test_recusa_build_exato_sem_swupdate2(self):
        build = _criar_build(self.raiz, "20261026T214450Z")
        (build / "SwUpdate2.txt").unlink()
        r = _bash(f'resolve_build_dir "{build}" build.py')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("não tem SwUpdate2.txt", r.stderr)


class LimpezaECopia(_ComPastaTemporaria):
    def test_limpa_restos_da_rodada_anterior_e_preserva_lost_found(self):
        pendrive = self.raiz / "pendrive"
        (pendrive / "lost+found").mkdir(parents=True)
        (pendrive / "0040").mkdir()
        (pendrive / "0040" / "SwUpdate.mdt").write_bytes(b"pacote velho")
        (pendrive / "ROLLBACK-RESTORED.OK").write_text("OK\n")
        (pendrive / "SwUpdate2.txt.done").write_text("Ver:IC1101\n")
        r = _bash(f'wipe_pendrive "{pendrive}"')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([p.name for p in pendrive.iterdir()], ["lost+found"])

    def test_copia_o_gatilho_e_o_pacote_do_rom_type(self):
        build = _criar_build(self.raiz, "20261026T214450Z", mdt=b"pacote novo")
        pendrive = self.raiz / "pendrive"
        pendrive.mkdir()
        r = _bash(f'copy_package "{build}" "{pendrive}"')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((pendrive / "SwUpdate2.txt").read_text(), "Ver:IC1101\n")
        self.assertEqual((pendrive / "0040" / "SwUpdate.mdt").read_bytes(), b"pacote novo")


class Desmontagem(_ComPastaTemporaria):
    def test_cleanup_apaga_a_pasta_temporaria_e_pode_rodar_de_novo_pelo_trap(self):
        pasta = self.raiz / "montagem"
        pasta.mkdir()
        r = _bash(f'TEMP_MP="{pasta}"; MP="{pasta}"; cleanup; cleanup')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(pasta.exists())

    def test_umount_que_falha_avisa_para_ejetar_antes_de_puxar(self):
        r = _bash(f'MP="{self.raiz}"; umount() {{ return 32; }}; unmount_pendrive')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Ejetar pelo desktop antes de puxar o pendrive", r.stderr)


class ConferenciaDaCopia(_ComPastaTemporaria):
    def setUp(self):
        super().setUp()
        self.build = _criar_build(self.raiz, "20261026T214450Z", mdt=b"pacote novo")
        self.pendrive = self.raiz / "pendrive"
        self.pendrive.mkdir()
        _bash(f'copy_package "{self.build}" "{self.pendrive}"')

    def _conferir(self):
        return _bash(f'verify_copy "{self.build}" "{self.pendrive}"')

    def test_copia_identica_passa_com_uma_linha_ok_por_arquivo(self):
        r = self._conferir()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual([linha.split()[:2] for linha in r.stdout.splitlines()],
                         [["OK", "SwUpdate2.txt"], ["OK", "0040/SwUpdate.mdt"]])

    def test_um_byte_diferente_no_pendrive_reprova(self):
        (self.pendrive / "0040" / "SwUpdate.mdt").write_bytes(b"pacote nove")
        r = self._conferir()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ERRO 0040/SwUpdate.mdt", r.stdout)

    def test_arquivo_que_falta_no_pendrive_reprova(self):
        (self.pendrive / "SwUpdate2.txt").unlink()
        r = self._conferir()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("pendrive=ausente", r.stdout)


class GuardaDoDevice(unittest.TestCase):
    def test_sem_device_mostra_o_uso_com_o_diretorio_opcional(self):
        r = _bash('check_device ""')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("[diretorio-de-build]", r.stderr)

    def test_recusa_o_que_nao_e_block_device(self):
        with tempfile.NamedTemporaryFile() as arquivo:
            r = _bash(f'check_device "{arquivo.name}"')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("não é um block device", r.stderr)


# O que precisa de root ou de pendrive de verdade vira stub. O pendrive é uma
# pasta, montada "pelo desktop": mount_pendrive só aponta MP para ela.
STUBS_SEM_ROOT = """
check_device() { :; }
require_root() { :; }
check_pendrive_format() { PART="${1}1"; }
mount_pendrive() { MP="$PENDRIVE"; }
mountpoint() { [ "$2" = "$PENDRIVE" ]; }
lsblk() { echo "Cruzer-Fit-teste"; }
drop_page_cache() { :; }
umount() { echo "$1" >> "$DESMONTAGENS"; }
"""


class SequenciaCompleta(_ComPastaTemporaria):
    def setUp(self):
        super().setUp()
        self.padrao = self.raiz / "output"
        self.pendrive = self.raiz / "pendrive"
        (self.pendrive / "0040").mkdir(parents=True)
        (self.pendrive / "0040" / "SwUpdate.mdt").write_bytes(b"pacote da rodada anterior")
        (self.pendrive / "SwUpdate2.txt.done").write_text("Ver:IC1101\n")
        self.desmontagens = self.raiz / "desmontagens"

    def _preparar(self, *dir_de_build, entrada="yes\n", stub_extra=""):
        argumentos = " ".join(f'"{d}"' for d in dir_de_build)
        return _bash(
            f'PENDRIVE="{self.pendrive}"; DESMONTAGENS="{self.desmontagens}"\n'
            f"{STUBS_SEM_ROOT}{stub_extra}\n"
            f'prepare_pendrive INSTALL "{self.padrao}" "python3 build.py" 0 /dev/sdz {argumentos}',
            entrada=entrada,
        )

    def _conteudo(self):
        return sorted(str(p.relative_to(self.pendrive)) for p in self.pendrive.rglob("*"))

    def test_grava_o_build_do_diretorio_passado_e_nao_o_mais_novo_do_padrao(self):
        _criar_build(self.padrao, "20261026T220000Z", mdt=b"autook")
        fase10 = _criar_build(self.raiz / "output-dalauncher-fase10", "20261026T214450Z", mdt=b"fase10")
        r = self._preparar(self.raiz / "output-dalauncher-fase10")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"Usando build: {fase10}", r.stdout)
        self.assertEqual(self._conteudo(), ["0040", "0040/SwUpdate.mdt", "SwUpdate2.txt"])
        self.assertEqual((self.pendrive / "0040" / "SwUpdate.mdt").read_bytes(), b"fase10")

    def test_sem_diretorio_grava_o_mais_novo_do_padrao(self):
        _criar_build(self.padrao, "20261020T181124Z", mdt=b"autook velho")
        _criar_build(self.padrao, "20261026T220000Z", mdt=b"autook novo")
        r = self._preparar()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.pendrive / "0040" / "SwUpdate.mdt").read_bytes(), b"autook novo")

    def test_diretorio_sem_build_para_antes_de_tocar_no_pendrive(self):
        _criar_build(self.padrao, "20261026T220000Z")
        antes = self._conteudo()
        r = self._preparar(self.raiz / "nao-existe")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("nenhum build encontrado", r.stderr)
        self.assertEqual(self._conteudo(), antes)

    def test_mostra_o_pendrive_e_sem_yes_nao_apaga_nada(self):
        _criar_build(self.padrao, "20261026T220000Z")
        antes = self._conteudo()
        for entrada in ("no\n", ""):
            with self.subTest(entrada=entrada):
                r = self._preparar(entrada=entrada)
                self.assertIn("Cruzer-Fit-teste", r.stdout)
                self.assertIn("Abortado. Nada foi apagado.", r.stdout)
                self.assertEqual(self._conteudo(), antes)

    def test_sem_ponto_de_montagem_nao_limpa(self):
        _criar_build(self.padrao, "20261026T220000Z")
        antes = self._conteudo()
        r = self._preparar(stub_extra="mountpoint() { return 1; }")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("não vou limpar", r.stderr)
        self.assertEqual(self._conteudo(), antes)

    def test_copia_que_nao_bate_com_o_build_termina_com_erro(self):
        _criar_build(self.padrao, "20261026T220000Z", mdt=b"pacote novo")
        r = self._preparar(stub_extra='drop_page_cache() { echo x >> "$MP/0040/SwUpdate.mdt"; }')
        self.assertEqual(r.returncode, 1)
        self.assertIn("ERRO 0040/SwUpdate.mdt", r.stdout)
        self.assertIn("Não levar este pendrive ao carro", r.stderr)
        self.assertNotIn("PRONTO", r.stdout)

    def test_desmonta_no_fim_mesmo_quando_a_montagem_era_do_desktop(self):
        _criar_build(self.padrao, "20261026T220000Z")
        r = self._preparar()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.desmontagens.read_text().split(), [str(self.pendrive)])
        self.assertIn("PRONTO", r.stdout)


class ScriptsDePendrive(unittest.TestCase):
    def test_todo_prepare_pendrive_carrega_a_lib_e_para_sem_device(self):
        self.assertGreaterEqual(len(WRAPPERS), 5)
        for script in WRAPPERS:
            with self.subTest(script=script.name):
                r = subprocess.run(["bash", str(script)], capture_output=True, text=True)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("[diretorio-de-build]", r.stderr)


if __name__ == "__main__":
    unittest.main()
