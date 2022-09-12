
## Install
Requires GTK3 and [ACE](http://sweaglesw.org/linguistics/ace/).

ACE needs to be in the path, and the ERG needs to exist as `erg.dat` next to bot.py.
```
pip install -r requirements.txt
gcc --shared `pkg-config --cflags gtk+-3.0` wc.c -o lib.so `pkg-config --libs gtk+-3.0`
```
## Run
First put token in token.txt, then run
```
python bot.py
```