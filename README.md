# shotControl
Control application for SHOT-304GS

## Required python modules
+ PyQt5
+ PySerial

## Serial Port
This application does not supported the USB driver provided by SIGMA Ltd.
Instead of that, serial connection is only suppored by this application.
Various USB - RS-232C converter devices are applicable for most of modern PC
to connect USB port to the RS-232C port on SHOT-304GS.

## Usage
type following from terminal 
```sh
$ python shotControl.py
```
`$` represents the shell prompt depending on your environment.

An optional argument `-v` or `--verbose` is acceptable.
The script writes out various information to the terminal (standard output).

Further information of optional arguments will be shown by `-h` or `--help` option.

# miniterm での通信

```
python -m serial.tools.miniterm -e --eol CRLF /dev/cu.usbserial-AI05GTL2
```
