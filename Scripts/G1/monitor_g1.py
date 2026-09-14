import sys
import time

from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_

latest = None

def handler(msg):
    global latest
    latest = msg

if len(sys.argv) <2 :
    print("Uso: python3 monitor_g1.py enp55s0")
    sys.exit(1)

ChannelFactoryInitialize(0, sys.argv[1])

sub = ChannelSubscriber("rt/lowstate", LowState_)
sub.Init(handler, 10)

print("Monitoreando G1. Ctrl+C para salir")

while True:
    if latest:
        print("\033c", end="") # limpia pantalla
        print("=== G1 LOWSTATE ===")
        print("IMU quaternion:", latest.imu_state.quaternion)
        print("IMU gyroscope: ", latest.imu_state.gyroscope)
        print("IMU accel,    ", latest.imu_state.accelerometer)

        print("\n___ Motores ___")
        for i, motor in enumerate(latest.motor_state):
            print(f"{i:02d} | q={motor.q: .3f} | dq={motor.dq: .3f} | tau={motor.tau_est: .3f}")

    time.sleep(0.2)
