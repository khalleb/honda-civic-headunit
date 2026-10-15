# Fase 1 — Reconhecimento no carro

Primeira coleta prática na central do Civic 2017 EXL BR, feita em 2026-10-15.

- **Relato completo:** [`achados-2026-10-15.md`](achados-2026-10-15.md)
- **Fotos:** [`fotos/`](fotos/)

## Legenda das fotos

As 21 fotos neste diretório são o scroll da tela **Version** (Self-Diagnosis Mode → Detail Information & Setting → Version), que lista TODOS os pacotes Android instalados na central. Essa foi a captura mais valiosa da sessão. Fotos anteriores (telas de Settings, painel, menu de serviço) foram feitas via WhatsApp e perdidas antes de serem copiadas para o repo; o conteúdo relevante delas está transcrito no relato (`achados-2026-10-15.md`).

| Arquivo | Conteúdo |
|---|---|
| `01-version-aosp-01.jpeg` até `10-version-aosp-10.jpeg` | Pacotes padrão AOSP (`com.android.*`, versão `4.2.2-55`) e wallpapers (Balões, Feixe fásico, Black Hole) |
| `11-version-mitsubishi-apps-01.jpeg` até `16-version-mitsubishi-apps-06.jpeg` | Apps proprietários Mitsubishi — `com.mitsubishielectric.ada.app.*` (Launcher/dalauncher, DaSettings, DealerDiag, DeveloperDiag, Instalador Aplicativo, PreShipmentDiag, etc.) |
| `17-version-mitsubishi-services-01.jpeg` até `19-version-mitsubishi-services-03.jpeg` | Services — `com.mitsubishielectric.ada.appservice.*` (ScreenshotApService, WhiteListApService, DiagApService, etc.) |
| `20-version-mitsubishi-low-level.jpeg` | Framework/util — CpuComService, MediaCoreService, VRSD, VehicleDbManager, vehiclerw |
| `21-version-bootloader.jpeg` | Fim do scroll: DBOOT `1.10_20160407183722`, Software loader `1.F187.16`, System µCom `H62F0N 71.55.13` |

## Como as fotos foram obtidas

1. Carro em ON, áudio off.
2. Combo físico `DAY/NIGHT + AUDIO + MENU` por ~2s abre o menu de serviço (TSB Honda 17-049).
3. `Detail Information & Setting → Version` → scroll pela lista.
4. Fotos pelo celular, uma a cada ~6 pacotes.

Fotos originais foram pelo WhatsApp. Nenhum VIN, serial de dispositivo ou dado pessoal aparece nas fotos (reflexo ocasional de mão/dedo do operador, nada mais).
