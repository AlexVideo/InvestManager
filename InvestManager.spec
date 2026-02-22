# -*- mode: python ; coding: utf-8 -*-
import os
_spec_dir = os.path.dirname(os.path.abspath(SPEC))
_icon = os.path.join(_spec_dir, 'assets', 'Invest.ico')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[(_icon, 'assets')] if os.path.isfile(_icon) else [],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'docx', 'PIL', 'lxml', 'numpy', 'matplotlib', 'scipy',
        # Неиспользуемые подмодули PyQt6 — сильно уменьшают объём
        'PyQt6.QtWebEngineCore', 'PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngine',
        'PyQt6.QtQuick', 'PyQt6.QtQuickWidgets', 'PyQt6.QtQml', 'PyQt6.QtQuick3D',
        'PyQt6.Qt3DCore', 'PyQt6.Qt3DRender', 'PyQt6.Qt3DInput', 'PyQt6.Qt3DLogic', 'PyQt6.Qt3DExtras', 'PyQt6.Qt3DAnimation',
        'PyQt6.QtMultimedia', 'PyQt6.QtMultimediaWidgets',
        'PyQt6.QtBluetooth', 'PyQt6.QtDesigner', 'PyQt6.QtHelp', 'PyQt6.QtSql', 'PyQt6.QtTest',
        'PyQt6.QtXml', 'PyQt6.QtSensors', 'PyQt6.QtSerialPort', 'PyQt6.QtWebSockets',
        'PyQt6.QtPdf', 'PyQt6.QtPdfWidgets', 'PyQt6.QtCharts', 'PyQt6.QtDataVisualization',
        'PyQt6.QtNetworkAuth', 'PyQt6.QtNfc', 'PyQt6.QtPositioning', 'PyQt6.QtLocation',
        'PyQt6.QtRemoteObjects', 'PyQt6.QtScxml', 'PyQt6.QtStateMachine', 'PyQt6.QtTextToSpeech',
        'PyQt6.QtWebChannel', 'PyQt6.QtHttpServer', 'PyQt6.QtOpenGL', 'PyQt6.QtOpenGLWidgets',
    ],
    noarchive=False,
    optimize=1,  # убирает assert и __doc__ — чуть меньше размер
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='InvestManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,   # убрать символы из бинарников (меньше размер)
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[_icon],  # иконка .exe в Проводнике
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name='InvestManager',
)
