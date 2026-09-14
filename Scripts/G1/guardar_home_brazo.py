import time
import json
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_

latest = None
JOINTS = [15, 16, 17, 18, 19]

def cb(msg):
    global latest
    latest = msg

ChannelFactoryInitialize(0, "enp55s0")

sub = ChannelSubscriber("rt/lf/lowstate", LowState_)
sub.Init(cb, 10)

print("Esperando datos...")
while latest is None:
    time.sleep(0.1)

home = {str(i): latest.motor_state[i].q for i in JOINTS}

print("HOME brazo:")
print(home)

with open("home_brazo.json", "w") as f:
    json.dump(home, f, indent = 4)

print("Guardando en home_brazo.json")
