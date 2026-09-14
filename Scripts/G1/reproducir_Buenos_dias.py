import sys
import time
import json
import numpy as np

from unitree_sdk2py.core.channel import ChannelPublisher, ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_, LowState_
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
from unitree_sdk2py.utils.crc import CRC


# Joints principales de ambos brazos
LEFT_ARM = [15, 16, 17, 18, 19]
RIGHT_ARM = [22, 23, 24, 25, 26]
ARM_JOINTS = LEFT_ARM + RIGHT_ARM

# En el ejemplo oficial se usa este joint fantasma para habilitar arm_sdk
K_NOT_USED_JOINT = 29

JSON_FILE = "Buenos_dias.json"

CONTROL_DT = 0.02
MOVE_DURATION = 1.0
KP = 25.0
KD = 1.0

latest_lowstate = None


def lowstate_handler(msg: LowState_):
    global latest_lowstate
    latest_lowstate = msg


def wait_lowstate():
    print("Esperando low_state...")
    while latest_lowstate is None:
        time.sleep(0.5)
        print("Sigo esperando low_state...")
    print("LowState recibido.")


def load_sequence(filename):
    with open(filename, "r") as f:
        poses_raw = json.load(f)

    sequence = []

    for pose in poses_raw:
        joints = {}

        left = pose["joints"]["left_arm"]
        right = pose["joints"]["right_arm"]

        for joint_id, data in left.items():
            joints[int(joint_id)] = float(data["q"])

        for joint_id, data in right.items():
            joints[int(joint_id)] = float(data["q"])

        sequence.append(joints)

    return sequence


def get_current_arm_pose():
    pose = {}

    for joint in ARM_JOINTS:
        pose[joint] = float(latest_lowstate.motor_state[joint].q)

    return pose


def interpolate_pose(start_pose, target_pose, ratio):
    pose = {}

    for joint in ARM_JOINTS:
        start_q = start_pose[joint]
        target_q = target_pose[joint]
        pose[joint] = (1.0 - ratio) * start_q + ratio * target_q

    return pose


def send_pose(publisher, low_cmd, crc, pose):
    # Habilita arm_sdk
    low_cmd.motor_cmd[K_NOT_USED_JOINT].q = 1.0

    for joint in ARM_JOINTS:
        low_cmd.motor_cmd[joint].tau = 0.0
        low_cmd.motor_cmd[joint].q = pose[joint]
        low_cmd.motor_cmd[joint].dq = 0.0
        low_cmd.motor_cmd[joint].kp = KP
        low_cmd.motor_cmd[joint].kd = KD

    low_cmd.crc = crc.Crc(low_cmd)
    publisher.Write(low_cmd)


def release_arm_sdk(publisher, low_cmd, crc):
    print("Liberando arm_sdk...")

    for i in range(50):
        ratio = i / 49.0
        low_cmd.motor_cmd[K_NOT_USED_JOINT].q = 1.0 - ratio
        low_cmd.crc = crc.Crc(low_cmd)
        publisher.Write(low_cmd)
        time.sleep(CONTROL_DT)


def move_smooth(publisher, low_cmd, crc, start_pose, target_pose, duration):
    steps = int(duration / CONTROL_DT)

    for step in range(steps):
        ratio = step / max(steps - 1, 1)
        ratio = np.clip(ratio, 0.0, 1.0)

        pose = interpolate_pose(start_pose, target_pose, ratio)
        send_pose(publisher, low_cmd, crc, pose)

        time.sleep(CONTROL_DT)


def main():
    if len(sys.argv) > 1:
        ChannelFactoryInitialize(0, sys.argv[1])
    else:
        ChannelFactoryInitialize(0)

    publisher = ChannelPublisher("rt/arm_sdk", LowCmd_)
    publisher.Init()

    subscriber = ChannelSubscriber("rt/lowstate", LowState_)
    subscriber.Init(lowstate_handler, 10)

    wait_lowstate()

    sequence = load_sequence(JSON_FILE)

    if len(sequence) == 0:
        print("No hay poses en el archivo JSON.")
        return

    print(f"Secuencia cargada: {len(sequence)} poses.")
    print("Asegurate de que no haya obstaculos alrededor del robot.")
    input("Presiona ENTER para iniciar la reproduccion...")

    low_cmd = unitree_hg_msg_dds__LowCmd_()
    crc = CRC()

    current_pose = get_current_arm_pose()

    print("Moviendo a la primera pose...")
    move_smooth(publisher, low_cmd, crc, current_pose, sequence[0], MOVE_DURATION)

    for i in range(1, len(sequence)):
        print(f"Moviendo pose {i} -> pose {i + 1}")
        move_smooth(publisher, low_cmd, crc, sequence[i - 1], sequence[i], MOVE_DURATION)

    print("Secuencia terminada.")
    release_arm_sdk(publisher, low_cmd, crc)


if __name__ == "__main__":
    main()
