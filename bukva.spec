# -*- mode: python -*-
from kivy_deps import sdl2, glew, gstreamer
block_cipher = None


a = Analysis(['main.py'],
             pathex=['C:\\Projects\\kivyframework\\bukva_kivy'],
             binaries=[],
             datas=[('bukva.kv', '.'), ('Rubik.ttf', '.'), ('click.wav', '.'), ('popup.wav', '.'), ('move.wav', '.'), ('combi.py', '.'), ('dictionary.db', '.'), ('data/*.png', 'data'), ('data/*.atlas', 'data')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz, Tree('C:\\Projects\\kivyframework\\bukva_kivy'),
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins + gstreamer.dep_bins)],
          name='bukva',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False, icon='C:\\Projects\\kivyframework\\bukva_kivy\\bukva.ico' )
