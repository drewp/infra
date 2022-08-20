from pyinfra import host
from pyinfra.operations import files

if host.name in [
    #'dash',
    'slash',
    'bang',
    ]:
    # maybe bring sync.py in here too

    # chsh zsh

    files.link(path='/home/drewp/.aptitude/config', target='../own/config/aptitude-config', force=True)
    files.link(path='/home/drewp/.config/blender',  target='../own/config/blender', force=True)
    files.link(path='/home/drewp/.emacs.d',         target='own/config/emacs-d', force=True)
    files.link(path='/home/drewp/.fonts',           target='own/config/fonts', force=True)
    files.link(path='/home/drewp/.fvwm2rc',         target='own/config/fvwm2rc', force=True)
    files.link(path='/home/drewp/.hgrc',            target='own/config/hgrc', force=True)
    files.link(path='/home/drewp/.kitty',           target='own/config/kitty', force=True)
    files.link(path='/home/drewp/.zshrc',           target='own/config/zshrc', force=True)
    files.link(path='/home/drewp/bin',              target='own/config/bin/', force=True)
    files.link(path='/home/drewp/blenderkit_data',  target='own/gfx-lib/blenderkit_data/', force=True)

#drwx------  3 drewp drewp  4096 Jul 31 15:07 .config/syncthing
