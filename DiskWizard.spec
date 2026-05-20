# DiskWizard.spec
block_cipher = None


a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("assets/fonts/*.ttf", "assets/fonts"),
    ],
    hiddenimports=["customtkinter", "wmi", "psutil", "win32api", "win32con"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="DiskWizard",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    uac_admin=True,
    icon="assets/icon.ico",
)
