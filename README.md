
## Install
Requires GTK3.
```
pip install -r requirements.txt
gcc --shared `pkg-config --cflags gtk+-3.0` wc.c -o lib.so `pkg-config --libs gtk+-3.0`
```
## Run
First put token in token.txt, then run
```
python bot.py
```