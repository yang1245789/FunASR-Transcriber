# Deployment Guide

Deploy this project to a fresh Windows machine in three steps.

---

## 1. Install Python

- Download Python 3.10+ (recommended: 3.10 or 3.11)
  https://www.python.org/downloads/
- **Must check** `Add Python to PATH` during installation
- Verify in CMD:
  ```cmd
  python --version
  ```

## 2. Extract and Launch

- Extract the archive to any location (an ASCII-only path avoids a one-time
  model copy step; Chinese paths work but copy models to `%TEMP%` on first
  load)
- Double-click `启动器.bat`
- First run automates (requires internet, ~10--30 min):
  1. Detect Python
  2. Create virtual environment `venv/`
  3. Install ~85 Python packages from `requirements.txt`
  4. Download PyTorch 2.5.1+cu121 (~2.4 GB, CUDA support)
  5. Launch GUI

> If the process fails mid-way (e.g. network timeout), double-click
> `启动器.bat` again — it resumes from where it left off.

## 3. Download Models

After the GUI launches:

1. Go to "模型管理" tab
2. Check the models you need
3. Click "下载选中"
4. Models download from ModelScope (魔搭社区)

**Recommended first install**: SenseVoice-Small (~1 GB, default model,
fastest).

---

## FAQ

| Problem | Fix |
|---------|-----|
| Bat window flashes and closes | Run `启动器.bat` from CMD to see the error; usually Python not installed or PATH not set |
| Dependency download slow | The launcher auto-retries. You can also run `venv\Scripts\pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple` |
| PyTorch download slow | The launcher uses the official PyTorch CDN. For Chinese mainland, consider SJTU mirror: `venv\Scripts\pip install torch torchaudio --index-url https://mirrors.sjtug.sjtu.edu.cn/pytorch-wheels/cu121` |
| Model download fails | Go to "模型管理" and retry. Ensure network can reach modelscope.cn |
| venv is broken | Delete `venv/` and re-run `启动器.bat` — it auto-rebuilds |

---

## Verification

```cmd
cd App
venv\Scripts\python -c "import funasr; print('FunASR', funasr.__version__)"
venv\Scripts\python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```