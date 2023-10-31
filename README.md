# Characterizing Distributed Mobile Augmented Reality Applications at the Edge

## 🛠️ Repository Structure
```
/
├── 🔗scAtteR 
├── 🔗scAtteR++ 
├── 🔗Active-Internal-Queue (Sidecar Queue Component)
├── /graphing
│		├── data
│ 		├── graphs.ipynb
│		├── processing.ipynb
│		└── README.md
├── /deployment
│		├── fig2
│		├── fig3
│		├── fig6
│		├── fig7
│		├── automation
│		└── README.md
└── README.md 			 

```

## 🖼️ Container Images

- scAtter `ghcr.io/cao-jacky/ar_server:20230125_1348`
- scAtteR++ `ghcr.io/giobart/arpipeline:latest`
- Active-Internal-Queue sidecar base 
	- cuda12 compatible `ghcr.io/giobart/active-internal-queue/active-sidecar-queue:v1.0.10-cuda12` 
	- ubuntu22 `ghcr.io/giobart/active-internal-queue/active-sidecar-queue:v1.0.10-ubuntu22` 

## 🔗 Paper Reference 

```
@inproceedings{characterizing-mar-2023,
  title     = {Characterizing Distributed Mobile Augmented Reality Applications at the Edge},
  author    = {Bartolomeo, Giovanni and Cao, Jacky and Su, Xiang and Mohan, Nitinder},
  year      = 2023,
  booktitle = {Companion of the 19th International Conference on emerging Networking EXperiments and Technologies (CoNEXT Companion '23), December 5--8, 2023, Paris, France},
  doi       = {10.1145/3624354.3630584}
}
```
