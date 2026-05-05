# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['agent_ilm/cli/__init__.py'],
    pathex=[],
    binaries=[],
    datas=[('agent_ilm', 'agent_ilm')],
    hiddenimports=['fire', 'agent_ilm'],
    hookspath=[],
    hooksconfig={},
    runtime_hooksparams=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

exe = Executable(
    a.binaries,
    name='agent-ilm',
    console=True,
    raw_custom_deps=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='agent-ilm',
)