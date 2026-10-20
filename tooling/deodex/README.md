# deodex-apk.sh

Converte um APK **odex-only** (como todos os `/system/app/` e `/system/vendor/app/` do dump 0040) em um APK com `classes.dex` injetado, pronto para análise estática via JADX, apktool, REA ou qualquer ferramenta Android padrão.

## Por que isso é necessário

A ROM da central Mitsubishi (Andromeda / Tegra 3 / Android 4.2.2) **pré-dexa** todos os APKs em build time. O que fica em disco é:

- `App.apk` — manifest + resources + nada de bytecode
- `App.odex` — bytecode Dalvik otimizado, dependente do framework (BOOTCLASSPATH)

JADX abre `App.apk` e reporta `class_count: 1`, porque não há `classes.dex` dentro. Para analisar, é preciso desodexar.

## O que o script faz

1. Localiza `<APK>.odex` ao lado do APK de entrada.
2. Monta um bootclasspath temporário juntando `/system/framework/*.odex` + `/system/vendor/framework/*.odex` do dump (configurável via `BOOTCLASSPATH_SRC_DIRS`).
3. `baksmali deodex` → árvore `.smali`.
4. `smali assemble` → `classes.dex`.
5. Copia o APK original e injeta `classes.dex` com `zip -j`.
6. Workspace temporário em `/tmp` é apagado no final (`trap`).

A saída fica em `tooling/apks-decoded/<NomeAPK>-deodexed.apk`.

## Uso

```bash
./tooling/deodex/deodex-apk.sh tooling/apks-dumped/dump-0040/vendor-app/DaLauncher.apk
```

Variáveis opcionais:

| Variável | Default | O que controla |
|---|---|---|
| `API_LEVEL` | `17` | Nível de API alvo (Android 4.2.2 = 17) |
| `OUT_DIR` | `tooling/apks-decoded` | Onde a APK de saída é escrita |
| `BOOTCLASSPATH_SRC_DIRS` | `dump-0040/{system-framework,vendor-framework}` | Diretórios com `.odex` do BOOTCLASSPATH, separados por `:` |
| `BAKSMALI_JAR` | `tooling/references/ic1101/apk-rebuilder/input/baksmali-2.5.2.jar` | Jar do baksmali |
| `SMALI_JAR` | mesmo path, `smali-2.5.2.jar` | Jar do smali |

## Pré-requisitos

- JDK 17+ no PATH
- `zip` no PATH
- Baksmali/smali 2.5.2 em `tooling/references/ic1101/apk-rebuilder/input/` (vem do `MIGRATION/setup.sh`, que clona o `librick/ic1101`)
- Dump dos frameworks em `tooling/apks-dumped/dump-0040/{system-framework,vendor-framework}` (vem do deep-scan — ver §20.4 do MAPA)

## Validado em

- `DaLauncher.apk` (2026-10-19): 579 arquivos smali, `classes.dex` de 1.2 MB, REA reconheceu 216 classes incluindo `OpeningDivideActivity`.

## Limitação

O script usa `-a 17` fixo. Para APKs com target SDK diferente, exportar `API_LEVEL` antes. Nenhuma APK do dump-0040 observado até agora foge do API 17.
