import sys
import time
import json
from datetime import datetime

from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_

# Joints principales de ambos brazos
LEFT_ARM = [15, 16, 17, 18, 19]
RIGHT_ARM = [22, 23, 24, 25, 26]

JOINT_NAMES = {
    15: "LeftShoulderPitch",
    16: "LeftShoulderRoll",
    17: "LeftShoulderYaw",
    18: "LeftElbow",
    19: "LeftWristRoll",

    22: "RightShoulderPitch",
    23: "RightShoulderRoll",
    24: "RightShoulderYaw",
    25: "RightElbow",
    26: "RightWristRoll",
}

latest_lowstate = None


def lowstate_handler(msg: LowState_):
    global latest_lowstate
    latest_lowstate = msg


def get_joint_data(joint_id):
    return {
        "name": JOINT_NAMES.get(joint_id, f"Joint_{joint_id}"),
        "q": float(latest_lowstate.motor_state[joint_id].q)
    }


def get_both_arm_pose():
    if latest_lowstate is None:
        return None

    pose = {
        "left_arm": {},
        "right_arm": {}
    }

    for joint in LEFT_ARM:
        pose["left_arm"][str(joint)] = get_joint_data(joint)

    for joint in RIGHT_ARM:
        pose["right_arm"][str(joint)] = get_joint_data(joint)

    return pose


def print_pose(pose):
    print("\nPose capturada:")

    print("\nBrazo izquierdo:")
    for joint_id, data in pose["left_arm"].items():
        print(f"Joint {joint_id:>2} | {data['name']:<20} | q = {data['q']:.4f} rad")

    print("\nBrazo derecho:")
    for joint_id, data in pose["right_arm"].items():
        print(f"Joint {joint_id:>2} | {data['name']:<20} | q = {data['q']:.4f} rad")


def main():
    if len(sys.argv) > 1:
        ChannelFactoryInitialize(0, sys.argv[1])
    else:
        ChannelFactoryInitialize(0)

    subscriber = ChannelSubscriber("rt/lowstate", LowState_)
    subscriber.Init(lowstate_handler, 10)

    print("Esperando low_state...")

    while latest_lowstate is None:
        time.sleep(0.5)

    print("LowState recibido.")
    print("Mueve ambos brazos manualmente a una pose.")
    print("Presiona ENTER para guardar una pose.")
    print("Escribe q y ENTER para terminar.\n")

    poses = []
    count = 1

    while True:
        user_input = input(f"Pose {count} > ")

        if user_input.lower().strip() == "q":
            break

        pose = get_both_arm_pose()

        if pose is None:
            print("No hay low_state todavía.")
            continue

        pose_data = {
            "pose_id": count,
            "timestamp": datetime.now().isoformat(),
            "joints": pose
        }

        poses.append(pose_data)
        print_pose(pose)

        count += 1

    filename = "secuencia_ambos_brazos.json"

    with open(filename, "w") as f:
        json.dump(poses, f, indent=4)

    print(f"\nSecuencia guardada en: {filename}")
    print(f"Total de poses guardadas: {len(poses)}")


if __name__ == "__main__":
    main()
