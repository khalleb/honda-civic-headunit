# Fluxo EvilValet (Mermaid)

Diagrama renderizável no GitHub via Mermaid. Mostra o fluxo completo do deploy via EvilValet
na nossa safra `1.F187.16` BR.

```mermaid
flowchart TD
    Start([Carro ligado + pendrive USB-A frontal plugado]) --> Audio[Segurar botão AUDIO por 5s]
    Audio --> Dialog{Diálogo<br/>"Quer reiniciar?"<br/>aparece?}
    Dialog -->|Sim| Confirm[Confirmar reiniciar]
    Dialog -->|Não| TryAgain[Tentar de novo:<br/>desligar carro,<br/>aguardar 15 min,<br/>religar]
    TryAgain --> Audio

    Confirm --> ColdBoot[Cold boot da central]
    ColdBoot --> SysUpdate[SystemUpdate.apk detecta<br/>SwUpdate2.txt no pendrive]
    SysUpdate --> SysUI["Tela mostra<br/>'Software update'<br/>'Current: 1.F187.16'<br/>'New: IC1101'<br/>'Copying...'"]
    SysUI --> SysCopy[SystemUpdate copia pacote<br/>para /data interno]
    SysCopy --> Reboot1[Reboot automático]

    Reboot1 --> Daup[daupdater roda no boot<br/>via libsurfaceflinger]
    Daup --> ReadRom[Lê custom_rom.type do<br/>/system/vendor/build.prop<br/>= 0040]
    ReadRom --> FindMdt[Procura<br/>/mnt/usbdrive1/0040/SwUpdate.mdt]
    FindMdt --> Verify[Valida assinatura<br/>contra testkey AOSP em<br/>res/keys do recovery]
    Verify -->|Testkey confere ✓| Stage[Estaga /cache/recovery/command]
    Stage --> Reboot2[Reboot para recovery]

    Reboot2 --> Recovery[Recovery executa<br/>META-INF/.../update-binary]
    Recovery --> UpdaterScript[Updater-script edify]

    UpdaterScript --> ExtractBB[Extrai busybox<br/>para /tmp/busybox]
    ExtractBB --> Mount[Mount APP → /system via edify<br/>via block device by-name]
    Mount --> InstallAPK[Extrai AutoOk.apk<br/>para /system/app/<br/>uid=0 gid=0 mode=0644]
    InstallAPK --> InstallSu[Extrai su para<br/>/system/xbin/su<br/>uid=0 gid=0 mode=06755<br/>SETUID]
    InstallSu --> Umount[Unmount /system + sync]
    Umount --> Sleep[Sleep 30s<br/>para janela de retirada]

    Sleep --> Reboot3[Reboot normal]
    Reboot3 --> Dexopt[Android faz dexopt<br/>do AutoOk.apk]
    Dexopt --> BootCompl[BOOT_COMPLETED broadcast]
    BootCompl --> BR[BootReceiver dispara<br/>AutoOkService]
    BR --> Watcher["AutoOk: watcher iniciado,<br/>aguardando<br/>com.mitsubishielectric.ada.app.dalauncher/<br/>.OpeningDivideActivity"]

    Watcher --> AvisoShow[Mitsubishi Launcher mostra<br/>DisclaimerFragment<br/>na OpeningDivideActivity]
    AvisoShow --> LogCat[Logcat emite:<br/>ActivityManager: START ...<br/>cmp=....OpeningDivideActivity]
    LogCat --> Detect[Watcher detecta match<br/>no logcat via substring]
    Detect --> Wait2[Aguarda 2 segundos]
    Wait2 --> Tap["Shell.suTap(400, 350):<br/>su -c input tap 400 350"]
    Tap --> Done[Aviso some automaticamente]

    Done --> Rearm[rearmWatcher():<br/>sleep 10s + handled=false +<br/>reinicia LogcatWatcher]
    Rearm --> Watcher

    style Verify fill:#e94560,color:#fff
    style InstallAPK fill:#4ade80,color:#000
    style InstallSu fill:#4ade80,color:#000
    style Done fill:#4ade80,color:#000
```

## Diagrama de arquitetura do APK

```mermaid
flowchart LR
    Boot[Android<br/>cold boot] -->|BOOT_COMPLETED broadcast| BR[BootReceiver]
    BR -->|startService Intent| Svc[AutoOkService<br/>START_STICKY]
    Svc -->|cria| LW[LogcatWatcher<br/>Thread]
    LW -->|exec| Su["su -c logcat<br/>-v brief<br/>ActivityManager:I *:S"]
    Su -->|stream de linhas| LW
    LW -->|line.contains needle| Cb[AvisoCallback]
    Cb -->|onDetected| Svc
    Svc -->|Shell.suTap 400,350| Shell[Shell<br/>Runtime.exec su<br/>+ stdin: input tap]
    Shell -->|exit 0 = ok| Svc
    Svc -->|rearmWatcher sleep 10s + reset| LW

    style LW fill:#f27121,color:#fff
    style Shell fill:#e94560,color:#fff
    style Svc fill:#0f3460,color:#fff
```

## Diagrama de partições eMMC da safra `1.F187.16` BR

```mermaid
flowchart TB
    eMMC[eMMC 7.03 GiB<br/>chip VM010B<br/>device: mmcblk0]
    eMMC --> p1[mmcblk0p1<br/>CAC → /cache<br/>ext4 rw]
    eMMC --> p2[mmcblk0p2<br/>CAP → /system/vendor<br/>ext4 ro<br/>framework Mitsubishi]
    eMMC --> p3[mmcblk0p3<br/>APP → /system<br/>ext4 ro<br/>★ Android + apps nossos]
    eMMC --> p4[mmcblk0p4<br/>LOG → /log<br/>ext4 rw]
    eMMC --> p5[mmcblk0p5<br/>MITSU → ?<br/>ext4 rw<br/>★ exclusiva safra BR]
    eMMC --> p6[mmcblk0p6<br/>SDA → /mnt/data1<br/>ext4 rw]
    eMMC --> p7[mmcblk0p7<br/>SDA2 → /mnt/data2<br/>ext4 rw]
    eMMC --> p8[mmcblk0p8<br/>SDC → /mnt/media<br/>ext4 rw]
    eMMC --> p9[mmcblk0p9<br/>UDA → /data<br/>ext4 rw<br/>user data + dalvik cache]

    style p3 fill:#4ade80,color:#000
    style p5 fill:#f27121,color:#fff
```

A partição `APP` (= mmcblk0p3) é onde instalamos `AutoOk.apk` + `su`. É montada `ro` no boot
normal; o updater-script no recovery monta `rw` para gravar.

A partição `MITSU` (= mmcblk0p5) é exclusiva da safra BR — não existe na safra 2021 US
documentada no `ic1101`. Função exata ainda não determinada.
