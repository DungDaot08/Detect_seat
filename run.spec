# run.spec
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=[],
    datas=[('app', 'app')],
    hiddenimports=[
        'fastapi',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'fastapi_utils',
        'fastapi_utils.tasks',
        'fastapi.middleware.httpsredirect',
        'uvicorn',
        'uvicorn.logging',
        'starlette.routing',
        'starlette.middleware',
        'starlette.middleware.trustedhost',
        'starlette.middleware.wsgi',
        'pydantic',
        'jinja2',
        'anyio',
        'idna'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='run',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # để hiện lỗi khi chạy
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='run',
)
