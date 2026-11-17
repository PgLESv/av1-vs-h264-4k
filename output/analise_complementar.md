# Análises complementares

Gerado por `analise_complementar.py` a partir de `resultados_completos.json` e dos arquivos de VMAF por quadro.

## 1. Mediana do BD-Rate (%) por métrica

| Métrica | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) |
|---|---|---|---|---|
| VMAF | -75.3 (8) | -43.8 (6) | -69.9 (8) | -24.9 (8) |
| VMAF NEG | -74.5 (8) | -47.2 (6) | -71.3 (8) | -23.9 (8) |
| PSNR | -77.0 (6) | -54.9 (6) | -77.6 (6) | -38.3 (8) |
| XPSNR | -63.0 (3) | +13.0 (4) | -49.8 (2) | -4.8 (8) |
| SSIM | -70.8 (6) | -9.4 (2) | -74.0 (7) | -24.5 (8) |
| MS-SSIM | -74.4 (7) | -46.8 (6) | -75.4 (7) | -25.9 (8) |
| SSIMULACRA2 | -66.3 (7) | -34.5 (6) | -65.6 (7) | -24.3 (8) |
| Butteraugli (2-norma) | -76.7 (8) | -46.7 (6) | -77.9 (8) | -33.9 (8) |
| Butteraugli (3-norma) | -73.5 (8) | -47.2 (6) | -75.0 (8) | -32.4 (7) |
| CVVDP | -76.8 (7) | -32.2 (6) | -75.9 (7) | -21.8 (8) |

Entre parênteses: sequências com sobreposição mínima de 50% na própria métrica. Butteraugli com sinal invertido (medida de distorção).

### BD-Rate por sequência e métrica

| Sequência | Métrica | Comparação | BD-Rate (%) | Sobreposição (%) | Válida |
|---|---|---|---|---|---|
| Amostra 1 (CityAlley) | VMAF | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -91.07 | 57.5 | sim |
| Amostra 2 (FlowerFocus) | VMAF | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -89.36 | 64.1 | sim |
| Amostra 3 (FlowerKids) | VMAF | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -65.92 | 96.2 | sim |
| Amostra 4 (FlowerPan) | VMAF | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -85.13 | 73.5 | sim |
| Amostra 5 (RaceNight) | VMAF | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -64.01 | 98.3 | sim |
| Amostra 6 (RiverBank) | VMAF | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -52.63 | 92.4 | sim |
| Amostra 7 (Twilight) | VMAF | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -84.76 | 90.5 | sim |
| Amostra 8 (CrowdRun) | VMAF | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -39.53 | 99.2 | sim |
| Amostra 1 (CityAlley) | VMAF NEG | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -89.44 | 60.7 | sim |
| Amostra 2 (FlowerFocus) | VMAF NEG | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -89.83 | 64.6 | sim |
| Amostra 3 (FlowerKids) | VMAF NEG | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -65.20 | 93.4 | sim |
| Amostra 4 (FlowerPan) | VMAF NEG | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -84.74 | 69.8 | sim |
| Amostra 5 (RaceNight) | VMAF NEG | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -65.17 | 93.8 | sim |
| Amostra 6 (RiverBank) | VMAF NEG | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -53.60 | 92.1 | sim |
| Amostra 7 (Twilight) | VMAF NEG | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -83.77 | 87.8 | sim |
| Amostra 8 (CrowdRun) | VMAF NEG | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -40.03 | 97.5 | sim |
| Amostra 1 (CityAlley) | PSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -90.66 | 58.5 | sim |
| Amostra 2 (FlowerFocus) | PSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -92.52 | 39.2 | não |
| Amostra 3 (FlowerKids) | PSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -66.04 | 78.6 | sim |
| Amostra 4 (FlowerPan) | PSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -88.37 | 52.1 | sim |
| Amostra 5 (RaceNight) | PSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -67.05 | 45.3 | não |
| Amostra 6 (RiverBank) | PSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -63.27 | 79.8 | sim |
| Amostra 7 (Twilight) | PSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -88.04 | 61.6 | sim |
| Amostra 8 (CrowdRun) | PSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -40.10 | 65.3 | sim |
| Amostra 1 (CityAlley) | XPSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -84.25 | 29.8 | não |
| Amostra 2 (FlowerFocus) | XPSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -86.21 | 16.3 | não |
| Amostra 3 (FlowerKids) | XPSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -57.49 | 53.9 | sim |
| Amostra 4 (FlowerPan) | XPSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -80.50 | 50.3 | sim |
| Amostra 5 (RaceNight) | XPSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -62.48 | 13.5 | não |
| Amostra 6 (RiverBank) | XPSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -62.99 | 71.3 | sim |
| Amostra 7 (Twilight) | XPSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -82.52 | 29.7 | não |
| Amostra 8 (CrowdRun) | XPSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -5.46 | 40.4 | não |
| Amostra 1 (CityAlley) | SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -88.39 | 49.2 | não |
| Amostra 2 (FlowerFocus) | SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -92.21 | 67.6 | sim |
| Amostra 3 (FlowerKids) | SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -66.37 | 93.2 | sim |
| Amostra 4 (FlowerPan) | SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -85.63 | 48.3 | não |
| Amostra 5 (RaceNight) | SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -75.27 | 89.5 | sim |
| Amostra 6 (RiverBank) | SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -62.22 | 96.5 | sim |
| Amostra 7 (Twilight) | SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -85.86 | 68.5 | sim |
| Amostra 8 (CrowdRun) | SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -48.48 | 92.2 | sim |
| Amostra 1 (CityAlley) | MS-SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -89.62 | 55.6 | sim |
| Amostra 2 (FlowerFocus) | MS-SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -93.72 | 36.3 | não |
| Amostra 3 (FlowerKids) | MS-SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -67.61 | 88.6 | sim |
| Amostra 4 (FlowerPan) | MS-SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -86.07 | 53.3 | sim |
| Amostra 5 (RaceNight) | MS-SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -74.45 | 66.1 | sim |
| Amostra 6 (RiverBank) | MS-SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -65.51 | 93.4 | sim |
| Amostra 7 (Twilight) | MS-SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -87.38 | 65.8 | sim |
| Amostra 8 (CrowdRun) | MS-SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -44.24 | 82.3 | sim |
| Amostra 1 (CityAlley) | SSIMULACRA2 | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -87.23 | 64.5 | sim |
| Amostra 2 (FlowerFocus) | SSIMULACRA2 | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -92.37 | 48.1 | não |
| Amostra 3 (FlowerKids) | SSIMULACRA2 | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -57.47 | 82.2 | sim |
| Amostra 4 (FlowerPan) | SSIMULACRA2 | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -83.11 | 56.2 | sim |
| Amostra 5 (RaceNight) | SSIMULACRA2 | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -66.32 | 66.7 | sim |
| Amostra 6 (RiverBank) | SSIMULACRA2 | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -49.86 | 86.0 | sim |
| Amostra 7 (Twilight) | SSIMULACRA2 | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -78.55 | 82.0 | sim |
| Amostra 8 (CrowdRun) | SSIMULACRA2 | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -28.06 | 73.6 | sim |
| Amostra 1 (CityAlley) | Butteraugli (2-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -89.24 | 55.4 | sim |
| Amostra 2 (FlowerFocus) | Butteraugli (2-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -92.15 | 55.7 | sim |
| Amostra 3 (FlowerKids) | Butteraugli (2-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -65.68 | 85.6 | sim |
| Amostra 4 (FlowerPan) | Butteraugli (2-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -85.81 | 54.4 | sim |
| Amostra 5 (RaceNight) | Butteraugli (2-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -67.67 | 67.9 | sim |
| Amostra 6 (RiverBank) | Butteraugli (2-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -62.61 | 89.0 | sim |
| Amostra 7 (Twilight) | Butteraugli (2-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -86.11 | 67.6 | sim |
| Amostra 8 (CrowdRun) | Butteraugli (2-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -36.05 | 82.2 | sim |
| Amostra 1 (CityAlley) | Butteraugli (3-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -88.77 | 58.5 | sim |
| Amostra 2 (FlowerFocus) | Butteraugli (3-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -91.82 | 60.8 | sim |
| Amostra 3 (FlowerKids) | Butteraugli (3-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -61.68 | 86.7 | sim |
| Amostra 4 (FlowerPan) | Butteraugli (3-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -85.01 | 57.4 | sim |
| Amostra 5 (RaceNight) | Butteraugli (3-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -63.63 | 71.7 | sim |
| Amostra 6 (RiverBank) | Butteraugli (3-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -55.15 | 89.5 | sim |
| Amostra 7 (Twilight) | Butteraugli (3-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -83.27 | 81.2 | sim |
| Amostra 8 (CrowdRun) | Butteraugli (3-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -33.10 | 83.5 | sim |
| Amostra 1 (CityAlley) | CVVDP | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -86.97 | 65.0 | sim |
| Amostra 2 (FlowerFocus) | CVVDP | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -94.56 | 42.0 | não |
| Amostra 3 (FlowerKids) | CVVDP | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -62.55 | 89.6 | sim |
| Amostra 4 (FlowerPan) | CVVDP | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -85.85 | 62.1 | sim |
| Amostra 5 (RaceNight) | CVVDP | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -76.82 | 82.6 | sim |
| Amostra 6 (RiverBank) | CVVDP | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -53.18 | 92.3 | sim |
| Amostra 7 (Twilight) | CVVDP | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -83.70 | 80.0 | sim |
| Amostra 8 (CrowdRun) | CVVDP | AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | -39.31 | 83.8 | sim |
| Amostra 1 (CityAlley) | VMAF | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -64.05 | 55.9 | sim |
| Amostra 2 (FlowerFocus) | VMAF | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -39.35 | 42.9 | não |
| Amostra 3 (FlowerKids) | VMAF | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -39.08 | 59.3 | sim |
| Amostra 4 (FlowerPan) | VMAF | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -48.58 | 65.0 | sim |
| Amostra 5 (RaceNight) | VMAF | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -46.12 | 43.8 | não |
| Amostra 6 (RiverBank) | VMAF | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -15.02 | 69.2 | sim |
| Amostra 7 (Twilight) | VMAF | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -56.54 | 52.2 | sim |
| Amostra 8 (CrowdRun) | VMAF | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -22.12 | 98.3 | sim |
| Amostra 1 (CityAlley) | VMAF NEG | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -66.75 | 56.7 | sim |
| Amostra 2 (FlowerFocus) | VMAF NEG | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -47.29 | 42.8 | não |
| Amostra 3 (FlowerKids) | VMAF NEG | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -41.50 | 59.7 | sim |
| Amostra 4 (FlowerPan) | VMAF NEG | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -52.83 | 63.1 | sim |
| Amostra 5 (RaceNight) | VMAF NEG | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -50.28 | 47.8 | não |
| Amostra 6 (RiverBank) | VMAF NEG | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -18.54 | 68.6 | sim |
| Amostra 7 (Twilight) | VMAF NEG | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -59.60 | 55.1 | sim |
| Amostra 8 (CrowdRun) | VMAF NEG | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -24.13 | 95.9 | sim |
| Amostra 1 (CityAlley) | PSNR | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -65.37 | 69.1 | sim |
| Amostra 2 (FlowerFocus) | PSNR | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -52.93 | 36.0 | não |
| Amostra 3 (FlowerKids) | PSNR | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -48.75 | 72.8 | sim |
| Amostra 4 (FlowerPan) | PSNR | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -61.15 | 67.0 | sim |
| Amostra 5 (RaceNight) | PSNR | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -50.19 | 39.3 | não |
| Amostra 6 (RiverBank) | PSNR | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -35.09 | 76.1 | sim |
| Amostra 7 (Twilight) | PSNR | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -64.33 | 56.7 | sim |
| Amostra 8 (CrowdRun) | PSNR | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -31.29 | 74.6 | sim |
| Amostra 1 (CityAlley) | XPSNR | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | +30.97 | 47.6 | não |
| Amostra 2 (FlowerFocus) | XPSNR | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | +82.46 | 44.0 | não |
| Amostra 3 (FlowerKids) | XPSNR | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -2.02 | 60.0 | sim |
| Amostra 4 (FlowerPan) | XPSNR | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -27.66 | 65.2 | sim |
| Amostra 5 (RaceNight) | XPSNR | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | +106.52 | 41.8 | não |
| Amostra 6 (RiverBank) | XPSNR | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | +28.06 | 73.1 | sim |
| Amostra 7 (Twilight) | XPSNR | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | +37.93 | 39.2 | não |
| Amostra 8 (CrowdRun) | XPSNR | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | +29.87 | 60.9 | sim |
| Amostra 1 (CityAlley) | SSIM | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -58.92 | 41.7 | não |
| Amostra 2 (FlowerFocus) | SSIM | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -52.81 | 25.5 | não |
| Amostra 3 (FlowerKids) | SSIM | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -34.51 | 43.0 | não |
| Amostra 4 (FlowerPan) | SSIM | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -55.59 | 44.1 | não |
| Amostra 5 (RaceNight) | SSIM | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -44.75 | 24.8 | não |
| Amostra 6 (RiverBank) | SSIM | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | +1.36 | 61.0 | sim |
| Amostra 7 (Twilight) | SSIM | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -50.72 | 40.1 | não |
| Amostra 8 (CrowdRun) | SSIM | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -20.25 | 91.7 | sim |
| Amostra 1 (CityAlley) | MS-SSIM | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -61.80 | 55.6 | sim |
| Amostra 2 (FlowerFocus) | MS-SSIM | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -49.58 | 33.9 | não |
| Amostra 3 (FlowerKids) | MS-SSIM | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -39.74 | 52.7 | sim |
| Amostra 4 (FlowerPan) | MS-SSIM | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -56.12 | 55.2 | sim |
| Amostra 5 (RaceNight) | MS-SSIM | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -48.09 | 32.9 | não |
| Amostra 6 (RiverBank) | MS-SSIM | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | +7.80 | 72.4 | sim |
| Amostra 7 (Twilight) | MS-SSIM | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -53.85 | 52.7 | sim |
| Amostra 8 (CrowdRun) | MS-SSIM | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -18.57 | 86.4 | sim |
| Amostra 1 (CityAlley) | SSIMULACRA2 | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -51.89 | 59.9 | sim |
| Amostra 2 (FlowerFocus) | SSIMULACRA2 | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -33.04 | 33.4 | não |
| Amostra 3 (FlowerKids) | SSIMULACRA2 | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -27.75 | 60.8 | sim |
| Amostra 4 (FlowerPan) | SSIMULACRA2 | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -42.74 | 56.1 | sim |
| Amostra 5 (RaceNight) | SSIMULACRA2 | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -36.15 | 38.2 | não |
| Amostra 6 (RiverBank) | SSIMULACRA2 | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | +8.54 | 77.9 | sim |
| Amostra 7 (Twilight) | SSIMULACRA2 | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -41.23 | 60.5 | sim |
| Amostra 8 (CrowdRun) | SSIMULACRA2 | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -5.34 | 79.7 | sim |
| Amostra 1 (CityAlley) | Butteraugli (2-norma) | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -60.95 | 56.8 | sim |
| Amostra 2 (FlowerFocus) | Butteraugli (2-norma) | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -47.36 | 31.3 | não |
| Amostra 3 (FlowerKids) | Butteraugli (2-norma) | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -41.20 | 56.1 | sim |
| Amostra 4 (FlowerPan) | Butteraugli (2-norma) | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -57.23 | 54.8 | sim |
| Amostra 5 (RaceNight) | Butteraugli (2-norma) | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -46.46 | 36.1 | não |
| Amostra 6 (RiverBank) | Butteraugli (2-norma) | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -13.97 | 63.8 | sim |
| Amostra 7 (Twilight) | Butteraugli (2-norma) | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -52.14 | 51.1 | sim |
| Amostra 8 (CrowdRun) | Butteraugli (2-norma) | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -24.26 | 84.4 | sim |
| Amostra 1 (CityAlley) | Butteraugli (3-norma) | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -60.96 | 57.0 | sim |
| Amostra 2 (FlowerFocus) | Butteraugli (3-norma) | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -48.86 | 31.2 | não |
| Amostra 3 (FlowerKids) | Butteraugli (3-norma) | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -41.24 | 54.3 | sim |
| Amostra 4 (FlowerPan) | Butteraugli (3-norma) | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -56.22 | 55.2 | sim |
| Amostra 5 (RaceNight) | Butteraugli (3-norma) | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -47.57 | 35.9 | não |
| Amostra 6 (RiverBank) | Butteraugli (3-norma) | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -13.83 | 62.7 | sim |
| Amostra 7 (Twilight) | Butteraugli (3-norma) | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -53.06 | 51.8 | sim |
| Amostra 8 (CrowdRun) | Butteraugli (3-norma) | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -24.30 | 84.8 | sim |
| Amostra 1 (CityAlley) | CVVDP | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -51.26 | 61.9 | sim |
| Amostra 2 (FlowerFocus) | CVVDP | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -60.12 | 30.8 | não |
| Amostra 3 (FlowerKids) | CVVDP | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -34.10 | 59.1 | sim |
| Amostra 4 (FlowerPan) | CVVDP | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -53.33 | 63.0 | sim |
| Amostra 5 (RaceNight) | CVVDP | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -63.55 | 34.3 | não |
| Amostra 6 (RiverBank) | CVVDP | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | +17.89 | 81.3 | sim |
| Amostra 7 (Twilight) | CVVDP | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -30.24 | 72.7 | sim |
| Amostra 8 (CrowdRun) | CVVDP | AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | -17.27 | 88.3 | sim |
| Amostra 1 (CityAlley) | VMAF | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -88.09 | 75.7 | sim |
| Amostra 2 (FlowerFocus) | VMAF | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -87.64 | 63.7 | sim |
| Amostra 3 (FlowerKids) | VMAF | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -61.53 | 95.9 | sim |
| Amostra 4 (FlowerPan) | VMAF | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -78.20 | 85.8 | sim |
| Amostra 5 (RaceNight) | VMAF | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -58.73 | 98.3 | sim |
| Amostra 6 (RiverBank) | VMAF | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -43.96 | 90.9 | sim |
| Amostra 7 (Twilight) | VMAF | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -81.48 | 96.3 | sim |
| Amostra 8 (CrowdRun) | VMAF | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -31.60 | 99.2 | sim |
| Amostra 1 (CityAlley) | VMAF NEG | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -87.55 | 73.4 | sim |
| Amostra 2 (FlowerFocus) | VMAF NEG | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -88.70 | 65.0 | sim |
| Amostra 3 (FlowerKids) | VMAF NEG | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -62.70 | 93.6 | sim |
| Amostra 4 (FlowerPan) | VMAF NEG | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -79.88 | 77.4 | sim |
| Amostra 5 (RaceNight) | VMAF NEG | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -62.59 | 94.0 | sim |
| Amostra 6 (RiverBank) | VMAF NEG | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -48.54 | 91.7 | sim |
| Amostra 7 (Twilight) | VMAF NEG | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -81.88 | 91.8 | sim |
| Amostra 8 (CrowdRun) | VMAF NEG | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -35.75 | 97.6 | sim |
| Amostra 1 (CityAlley) | PSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -91.34 | 61.9 | sim |
| Amostra 2 (FlowerFocus) | PSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -93.05 | 38.5 | não |
| Amostra 3 (FlowerKids) | PSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -67.14 | 79.9 | sim |
| Amostra 4 (FlowerPan) | PSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -87.97 | 54.8 | sim |
| Amostra 5 (RaceNight) | PSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -68.31 | 46.7 | não |
| Amostra 6 (RiverBank) | PSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -61.63 | 81.0 | sim |
| Amostra 7 (Twilight) | PSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -88.72 | 62.3 | sim |
| Amostra 8 (CrowdRun) | PSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -41.15 | 66.8 | sim |
| Amostra 1 (CityAlley) | XPSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -78.06 | 31.2 | não |
| Amostra 2 (FlowerFocus) | XPSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -80.62 | 13.9 | não |
| Amostra 3 (FlowerKids) | XPSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -51.44 | 52.0 | sim |
| Amostra 4 (FlowerPan) | XPSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -66.48 | 46.5 | não |
| Amostra 5 (RaceNight) | XPSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -54.47 | 13.2 | não |
| Amostra 6 (RiverBank) | XPSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -48.10 | 66.7 | sim |
| Amostra 7 (Twilight) | XPSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -78.48 | 29.8 | não |
| Amostra 8 (CrowdRun) | XPSNR | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | +16.15 | 38.9 | não |
| Amostra 1 (CityAlley) | SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -88.97 | 52.2 | sim |
| Amostra 2 (FlowerFocus) | SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -92.09 | 63.4 | sim |
| Amostra 3 (FlowerKids) | SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -66.69 | 93.7 | sim |
| Amostra 4 (FlowerPan) | SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -84.19 | 49.8 | não |
| Amostra 5 (RaceNight) | SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -73.97 | 89.8 | sim |
| Amostra 6 (RiverBank) | SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -61.41 | 96.7 | sim |
| Amostra 7 (Twilight) | SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -86.15 | 74.3 | sim |
| Amostra 8 (CrowdRun) | SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -49.04 | 93.0 | sim |
| Amostra 1 (CityAlley) | MS-SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -91.66 | 58.0 | sim |
| Amostra 2 (FlowerFocus) | MS-SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -94.58 | 34.3 | não |
| Amostra 3 (FlowerKids) | MS-SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -68.90 | 89.4 | sim |
| Amostra 4 (FlowerPan) | MS-SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -86.17 | 53.5 | sim |
| Amostra 5 (RaceNight) | MS-SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -75.39 | 67.1 | sim |
| Amostra 6 (RiverBank) | MS-SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -62.18 | 93.4 | sim |
| Amostra 7 (Twilight) | MS-SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -89.02 | 68.8 | sim |
| Amostra 8 (CrowdRun) | MS-SSIM | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -43.33 | 83.0 | sim |
| Amostra 1 (CityAlley) | SSIMULACRA2 | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -88.17 | 67.2 | sim |
| Amostra 2 (FlowerFocus) | SSIMULACRA2 | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -92.71 | 46.9 | não |
| Amostra 3 (FlowerKids) | SSIMULACRA2 | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -57.78 | 82.6 | sim |
| Amostra 4 (FlowerPan) | SSIMULACRA2 | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -81.61 | 59.1 | sim |
| Amostra 5 (RaceNight) | SSIMULACRA2 | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -65.59 | 66.8 | sim |
| Amostra 6 (RiverBank) | SSIMULACRA2 | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -47.95 | 86.1 | sim |
| Amostra 7 (Twilight) | SSIMULACRA2 | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -78.32 | 80.4 | sim |
| Amostra 8 (CrowdRun) | SSIMULACRA2 | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -27.66 | 74.4 | sim |
| Amostra 1 (CityAlley) | Butteraugli (2-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -90.84 | 57.5 | sim |
| Amostra 2 (FlowerFocus) | Butteraugli (2-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -92.60 | 55.4 | sim |
| Amostra 3 (FlowerKids) | Butteraugli (2-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -68.08 | 87.0 | sim |
| Amostra 4 (FlowerPan) | Butteraugli (2-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -86.36 | 54.6 | sim |
| Amostra 5 (RaceNight) | Butteraugli (2-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -69.46 | 69.8 | sim |
| Amostra 6 (RiverBank) | Butteraugli (2-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -63.41 | 89.8 | sim |
| Amostra 7 (Twilight) | Butteraugli (2-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -87.50 | 68.3 | sim |
| Amostra 8 (CrowdRun) | Butteraugli (2-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -38.72 | 83.8 | sim |
| Amostra 1 (CityAlley) | Butteraugli (3-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -90.47 | 60.7 | sim |
| Amostra 2 (FlowerFocus) | Butteraugli (3-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -92.25 | 62.1 | sim |
| Amostra 3 (FlowerKids) | Butteraugli (3-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -64.03 | 88.2 | sim |
| Amostra 4 (FlowerPan) | Butteraugli (3-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -85.54 | 56.9 | sim |
| Amostra 5 (RaceNight) | Butteraugli (3-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -65.27 | 73.7 | sim |
| Amostra 6 (RiverBank) | Butteraugli (3-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -57.09 | 90.4 | sim |
| Amostra 7 (Twilight) | Butteraugli (3-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -84.70 | 81.1 | sim |
| Amostra 8 (CrowdRun) | Butteraugli (3-norma) | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -35.35 | 85.0 | sim |
| Amostra 1 (CityAlley) | CVVDP | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -87.49 | 68.3 | sim |
| Amostra 2 (FlowerFocus) | CVVDP | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -94.98 | 40.5 | não |
| Amostra 3 (FlowerKids) | CVVDP | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -61.81 | 90.0 | sim |
| Amostra 4 (FlowerPan) | CVVDP | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -84.52 | 63.4 | sim |
| Amostra 5 (RaceNight) | CVVDP | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -75.92 | 82.6 | sim |
| Amostra 6 (RiverBank) | CVVDP | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -48.47 | 92.0 | sim |
| Amostra 7 (Twilight) | CVVDP | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -83.37 | 85.0 | sim |
| Amostra 8 (CrowdRun) | CVVDP | AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | -36.00 | 84.0 | sim |
| Amostra 1 (CityAlley) | VMAF | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -39.19 | 90.9 | sim |
| Amostra 2 (FlowerFocus) | VMAF | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -18.38 | 76.9 | sim |
| Amostra 3 (FlowerKids) | VMAF | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -25.93 | 98.9 | sim |
| Amostra 4 (FlowerPan) | VMAF | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -23.82 | 92.3 | sim |
| Amostra 5 (RaceNight) | VMAF | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -27.90 | 87.1 | sim |
| Amostra 6 (RiverBank) | VMAF | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -17.24 | 98.3 | sim |
| Amostra 7 (Twilight) | VMAF | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -25.93 | 93.9 | sim |
| Amostra 8 (CrowdRun) | VMAF | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -18.21 | 99.4 | sim |
| Amostra 1 (CityAlley) | VMAF NEG | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -36.47 | 93.6 | sim |
| Amostra 2 (FlowerFocus) | VMAF NEG | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -22.44 | 77.0 | sim |
| Amostra 3 (FlowerKids) | VMAF NEG | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -25.32 | 98.0 | sim |
| Amostra 4 (FlowerPan) | VMAF NEG | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -24.92 | 92.3 | sim |
| Amostra 5 (RaceNight) | VMAF NEG | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -26.02 | 86.8 | sim |
| Amostra 6 (RiverBank) | VMAF NEG | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -16.36 | 98.8 | sim |
| Amostra 7 (Twilight) | VMAF NEG | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -22.80 | 94.0 | sim |
| Amostra 8 (CrowdRun) | VMAF NEG | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -18.27 | 98.7 | sim |
| Amostra 1 (CityAlley) | PSNR | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -46.18 | 94.2 | sim |
| Amostra 2 (FlowerFocus) | PSNR | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -42.36 | 72.5 | sim |
| Amostra 3 (FlowerKids) | PSNR | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -34.94 | 97.3 | sim |
| Amostra 4 (FlowerPan) | PSNR | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -45.88 | 94.9 | sim |
| Amostra 5 (RaceNight) | PSNR | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -33.56 | 89.6 | sim |
| Amostra 6 (RiverBank) | PSNR | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -27.43 | 95.5 | sim |
| Amostra 7 (Twilight) | PSNR | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -41.74 | 93.8 | sim |
| Amostra 8 (CrowdRun) | PSNR | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -19.41 | 100.0 | sim |
| Amostra 1 (CityAlley) | XPSNR | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | +6.03 | 69.8 | sim |
| Amostra 2 (FlowerFocus) | XPSNR | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | +3.45 | 75.9 | sim |
| Amostra 3 (FlowerKids) | XPSNR | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -21.63 | 82.6 | sim |
| Amostra 4 (FlowerPan) | XPSNR | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -31.33 | 93.2 | sim |
| Amostra 5 (RaceNight) | XPSNR | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | +6.67 | 90.7 | sim |
| Amostra 6 (RiverBank) | XPSNR | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -19.38 | 90.6 | sim |
| Amostra 7 (Twilight) | XPSNR | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -1.48 | 69.6 | sim |
| Amostra 8 (CrowdRun) | XPSNR | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -8.18 | 96.7 | sim |
| Amostra 1 (CityAlley) | SSIM | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -28.78 | 85.8 | sim |
| Amostra 2 (FlowerFocus) | SSIM | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -21.48 | 62.1 | sim |
| Amostra 3 (FlowerKids) | SSIM | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -25.88 | 88.2 | sim |
| Amostra 4 (FlowerPan) | SSIM | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -29.05 | 91.7 | sim |
| Amostra 5 (RaceNight) | SSIM | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -28.71 | 60.5 | sim |
| Amostra 6 (RiverBank) | SSIM | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -9.43 | 98.1 | sim |
| Amostra 7 (Twilight) | SSIM | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -19.05 | 92.6 | sim |
| Amostra 8 (CrowdRun) | SSIM | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -23.22 | 97.6 | sim |
| Amostra 1 (CityAlley) | MS-SSIM | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -32.86 | 89.7 | sim |
| Amostra 2 (FlowerFocus) | MS-SSIM | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -18.01 | 69.5 | sim |
| Amostra 3 (FlowerKids) | MS-SSIM | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -26.83 | 97.1 | sim |
| Amostra 4 (FlowerPan) | MS-SSIM | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -32.90 | 94.1 | sim |
| Amostra 5 (RaceNight) | MS-SSIM | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -29.38 | 78.2 | sim |
| Amostra 6 (RiverBank) | MS-SSIM | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -14.84 | 98.6 | sim |
| Amostra 7 (Twilight) | MS-SSIM | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -25.05 | 93.7 | sim |
| Amostra 8 (CrowdRun) | MS-SSIM | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -21.17 | 98.6 | sim |
| Amostra 1 (CityAlley) | SSIMULACRA2 | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -28.10 | 90.5 | sim |
| Amostra 2 (FlowerFocus) | SSIMULACRA2 | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -26.28 | 61.6 | sim |
| Amostra 3 (FlowerKids) | SSIMULACRA2 | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -24.74 | 93.0 | sim |
| Amostra 4 (FlowerPan) | SSIMULACRA2 | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -29.63 | 91.8 | sim |
| Amostra 5 (RaceNight) | SSIMULACRA2 | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -23.78 | 76.3 | sim |
| Amostra 6 (RiverBank) | SSIMULACRA2 | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -10.33 | 96.8 | sim |
| Amostra 7 (Twilight) | SSIMULACRA2 | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -19.14 | 91.4 | sim |
| Amostra 8 (CrowdRun) | SSIMULACRA2 | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -15.33 | 97.3 | sim |
| Amostra 1 (CityAlley) | Butteraugli (2-norma) | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -38.42 | 87.1 | sim |
| Amostra 2 (FlowerFocus) | Butteraugli (2-norma) | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -45.01 | 50.5 | sim |
| Amostra 3 (FlowerKids) | Butteraugli (2-norma) | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -35.69 | 86.1 | sim |
| Amostra 4 (FlowerPan) | Butteraugli (2-norma) | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -48.21 | 83.0 | sim |
| Amostra 5 (RaceNight) | Butteraugli (2-norma) | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -28.38 | 78.0 | sim |
| Amostra 6 (RiverBank) | Butteraugli (2-norma) | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -23.20 | 91.4 | sim |
| Amostra 7 (Twilight) | Butteraugli (2-norma) | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -32.19 | 85.2 | sim |
| Amostra 8 (CrowdRun) | Butteraugli (2-norma) | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -20.44 | 99.8 | sim |
| Amostra 1 (CityAlley) | Butteraugli (3-norma) | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -37.08 | 89.1 | sim |
| Amostra 2 (FlowerFocus) | Butteraugli (3-norma) | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -45.64 | 47.4 | não |
| Amostra 3 (FlowerKids) | Butteraugli (3-norma) | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -33.41 | 88.7 | sim |
| Amostra 4 (FlowerPan) | Butteraugli (3-norma) | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -46.68 | 84.2 | sim |
| Amostra 5 (RaceNight) | Butteraugli (3-norma) | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -28.47 | 79.4 | sim |
| Amostra 6 (RiverBank) | Butteraugli (3-norma) | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -20.20 | 95.3 | sim |
| Amostra 7 (Twilight) | Butteraugli (3-norma) | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -32.36 | 88.2 | sim |
| Amostra 8 (CrowdRun) | Butteraugli (3-norma) | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -19.09 | 99.6 | sim |
| Amostra 1 (CityAlley) | CVVDP | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -23.24 | 94.8 | sim |
| Amostra 2 (FlowerFocus) | CVVDP | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -31.44 | 63.5 | sim |
| Amostra 3 (FlowerKids) | CVVDP | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -19.35 | 96.8 | sim |
| Amostra 4 (FlowerPan) | CVVDP | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -35.87 | 95.4 | sim |
| Amostra 5 (RaceNight) | CVVDP | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -32.24 | 78.2 | sim |
| Amostra 6 (RiverBank) | CVVDP | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -11.19 | 98.1 | sim |
| Amostra 7 (Twilight) | CVVDP | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -15.07 | 95.0 | sim |
| Amostra 8 (CrowdRun) | CVVDP | AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | -20.42 | 97.8 | sim |

## 2. Correlação de Spearman entre SI e BD-Rate VMAF

| Comparação | n | rho | p (bilateral) |
|---|---|---|---|
| AV1 SVT-AV1 P6 (CPU) x H.264 x264 medium (CPU) | 8 | 0.79 | 0.0208 |
| AV1 NVENC p7 (GPU) x H.264 x264 medium (CPU) | 6 | 0.83 | 0.0416 |
| AV1 SVT-AV1 P6 (CPU) x H.264 x264 veryslow (CPU) | 8 | 0.81 | 0.0149 |
| AV1 NVENC p7 (GPU) x H.264 NVENC p7 (GPU) | 8 | 0.29 | 0.4927 |

Análise exploratória. rho positivo: quanto maior o SI, menor a economia.

## 3. Iso-qualidade em VMAF 93 (7 sequências)

| Codificador | Taxa média (Mb/s) | Mediana da variação por sequência | Desvio padrão do VMAF | Percentil 1% | Percentil 5% |
|---|---|---|---|---|---|
| H.264 x264 medium (CPU) | 16.67 | referência | 1.49 | 89.74 | 91.20 |
| H.264 x264 veryslow (CPU) | 14.20 | -13.7% | 1.57 | 89.65 | 91.01 |
| H.264 NVENC p7 (GPU) | 15.50 | -20.9% | 1.76 | 89.07 | 90.71 |
| AV1 SVT-AV1 P6 (CPU) | 8.50 | -61.5% | 1.81 | 88.55 | 90.28 |
| AV1 NVENC p7 (GPU) | 11.93 | -48.1% | 1.60 | 88.81 | 90.80 |

Desvio padrão e percentis do VMAF por quadro interpolados (PCHIP) no alvo e promediados entre as sequências. Sequências: Amostra 1 (CityAlley), Amostra 3 (FlowerKids), Amostra 4 (FlowerPan), Amostra 5 (RaceNight), Amostra 6 (RiverBank), Amostra 7 (Twilight), Amostra 8 (CrowdRun).

## 3. Iso-qualidade em VMAF 95 (7 sequências)

| Codificador | Taxa média (Mb/s) | Mediana da variação por sequência | Desvio padrão do VMAF | Percentil 1% | Percentil 5% |
|---|---|---|---|---|---|
| H.264 x264 medium (CPU) | 24.83 | referência | 1.42 | 91.70 | 93.35 |
| H.264 x264 veryslow (CPU) | 20.55 | -17.6% | 1.49 | 91.67 | 93.24 |
| H.264 NVENC p7 (GPU) | 22.36 | -15.5% | 1.52 | 91.36 | 93.11 |
| AV1 SVT-AV1 P6 (CPU) | 11.80 | -58.3% | 1.54 | 90.90 | 92.79 |
| AV1 NVENC p7 (GPU) | 18.61 | -36.6% | 1.53 | 91.08 | 92.98 |

Desvio padrão e percentis do VMAF por quadro interpolados (PCHIP) no alvo e promediados entre as sequências. Sequências: Amostra 1 (CityAlley), Amostra 3 (FlowerKids), Amostra 4 (FlowerPan), Amostra 5 (RaceNight), Amostra 6 (RiverBank), Amostra 7 (Twilight), Amostra 8 (CrowdRun).

## 4. Coeficiente de variação do tempo de codificação (3 repetições)

| Codificador | CV médio (%) | CV máximo (%) |
|---|---|---|
| H.264 x264 medium (CPU) | 0.32 | 3.09 |
| H.264 x264 veryslow (CPU) | 0.24 | 1.09 |
| H.264 NVENC p7 (GPU) | 0.13 | 0.48 |
| AV1 SVT-AV1 P6 (CPU) | 0.31 | 1.07 |
| AV1 NVENC p7 (GPU) | 0.12 | 0.29 |

## 5. Sensibilidade ao volume de horas assistidas (VMAF 93)

| Horas assistidas/mês | Codificador | Custo mensal (R$) | Economia mensal (R$) | Ponto de equilíbrio (meses) |
|---|---|---|---|---|
| 1.000 | H.264 x264 veryslow (CPU) | 5058.48 | 881.47 | 11.143 |
| 1.000 | H.264 NVENC p7 (GPU) | 5522.77 | 417.18 | 9.094 |
| 1.000 | AV1 SVT-AV1 P6 (CPU) | 3029.32 | 2910.62 | 0.423 |
| 1.000 | AV1 NVENC p7 (GPU) | 4251.25 | 1688.70 | 1.496 |
| 10.000 | H.264 x264 veryslow (CPU) | 39872.73 | 6948.03 | 1.414 |
| 10.000 | H.264 NVENC p7 (GPU) | 43532.41 | 3288.35 | 1.154 |
| 10.000 | AV1 SVT-AV1 P6 (CPU) | 23878.19 | 22942.57 | 0.054 |
| 10.000 | AV1 NVENC p7 (GPU) | 33509.85 | 13310.91 | 0.190 |
| 100.000 | H.264 x264 veryslow (CPU) | 388015.25 | 67613.63 | 0.145 |
| 100.000 | H.264 NVENC p7 (GPU) | 423628.86 | 32000.02 | 0.119 |
| 100.000 | AV1 SVT-AV1 P6 (CPU) | 232366.85 | 223262.03 | 0.006 |
| 100.000 | AV1 NVENC p7 (GPU) | 326095.85 | 129533.03 | 0.020 |
| 1.000.000 | H.264 x264 veryslow (CPU) | 3869440.43 | 674269.68 | 0.015 |
| 1.000.000 | H.264 NVENC p7 (GPU) | 4224593.30 | 319116.81 | 0.012 |
| 1.000.000 | AV1 SVT-AV1 P6 (CPU) | 2317253.50 | 2226456.61 | 0.001 |
| 1.000.000 | AV1 NVENC p7 (GPU) | 3251955.85 | 1291754.26 | 0.002 |
| 10.000.000 | H.264 x264 veryslow (CPU) | 38683692.19 | 6740830.20 | 0.001 |
| 10.000.000 | H.264 NVENC p7 (GPU) | 42234237.73 | 3190284.66 | 0.001 |
| 10.000.000 | AV1 SVT-AV1 P6 (CPU) | 23166119.99 | 22258402.40 | 0.000 |
| 10.000.000 | AV1 NVENC p7 (GPU) | 32510555.81 | 12913966.57 | 0.000 |

## 6. Distribuição híbrida (VMAF 93. 5.000 h assistidas/mês)

### a) Cópia adicional mantida ao lado do acervo H.264

| Cópia adicional | Armazenamento da cópia (R$/mês) | Economia de tráfego por hora assistida (R$) | Fração mínima de horas em dispositivos compatíveis |
|---|---|---|---|
| AV1 SVT-AV1 P6 (CPU) | 712.78 | 2.226 | 6.4% |
| AV1 NVENC p7 (GPU) | 1000.29 | 1.291 | 15.5% |

Fração mínima = armazenamento da cópia / (horas assistidas por mês x economia por hora). Não inclui o custo único de codificação da cópia.

### b) Transcodificação sob demanda para H.264

| Item | Valor |
|---|---|
| Armazenamento da cópia H.264 x264 medium (CPU) (R$/mês) | 1397.63 |
| Custo de transcodificação por hora assistida, H.264 NVENC p7 (GPU) em nuvem (R$) | 6.219 |
| Limite de horas assistidas/mês em dispositivos sem AV1 | 225 |

Abaixo do limite, transcodificar sob demanda custa menos que manter a cópia H.264. Usa-se o H.264 NVENC p7 (GPU) porque o x264 medium não codifica 4K a 50 quadros/s em tempo real. Considera apenas o custo da instância em nuvem.
