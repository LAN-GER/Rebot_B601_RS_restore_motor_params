#!/usr/bin/env python3
"""
Dump all RobStride motor parameters from a reference arm to a JSON file.

Usage:
    python dump_motor_params.py --output reference_arm.json
    python dump_motor_params.py --output my_arm.json --motor-ids 1,2,3,4,5,6,7
"""

import argparse
import json
import sys

import motorbridge


def probe_and_read(motor, param_id: int, timeout_ms: int = 200) -> tuple[bool, float, str]:
    types_to_try = ["f32", "u32", "u16", "u8", "i8"]
    for t in types_to_try:
        try:
            if t == "f32":
                val = motor.robstride_get_param_f32(param_id, timeout_ms)
            elif t == "u32":
                val = motor.robstride_get_param_u32(param_id, timeout_ms)
            elif t == "u16":
                val = motor.robstride_get_param_u16(param_id, timeout_ms)
            elif t == "u8":
                val = motor.robstride_get_param_u8(param_id, timeout_ms)
            elif t == "i8":
                val = motor.robstride_get_param_i8(param_id, timeout_ms)
            else:
                continue
            return True, val, t
        except Exception:
            continue
    return False, None, ""


def main():
    parser = argparse.ArgumentParser(description="Dump motor parameters to JSON")
    parser.add_argument("--output", default="reference_arm.json", help="Output JSON file")
    parser.add_argument("--channel", default="can0", help="CAN channel")
    parser.add_argument("--model", default="rs-00", help="Motor model hint")
    parser.add_argument("--motor-ids", default="1,2,3,4,5,6,7", help="Comma-separated motor IDs")
    parser.add_argument("--feedback-id", default="0xFD", help="Feedback/host ID")
    parser.add_argument("--start", default="0x7000", help="Start param ID (hex)")
    parser.add_argument("--end", default="0x7030", help="End param ID (hex)")
    args = parser.parse_args()

    motor_ids = [int(x.strip(), 0) for x in args.motor_ids.split(",")]
    feedback_id = int(args.feedback_id, 0)
    start = int(args.start, 0)
    end = int(args.end, 0)

    print(f"Discovering readable registers on motor {motor_ids[0]}...")
    readable_params = []
    ctrl = motorbridge.Controller(args.channel)
    try:
        motor = ctrl.add_robstride_motor(motor_ids[0], feedback_id, args.model)
        try:
            for param_id in range(start, end + 1):
                ok, _, t = probe_and_read(motor, param_id, timeout_ms=200)
                if ok:
                    readable_params.append((param_id, t))
        finally:
            motor.close()
    finally:
        ctrl.close()

    print(f"Found {len(readable_params)} readable registers.\n")

    data = {}
    for mid in motor_ids:
        data[f"motor_{mid}"] = {}
        ctrl = motorbridge.Controller(args.channel)
        try:
            motor = ctrl.add_robstride_motor(mid, feedback_id, args.model)
            try:
                for param_id, t in readable_params:
                    ok, val, _ = probe_and_read(motor, param_id, timeout_ms=200)
                    if ok:
                        data[f"motor_{mid}"][f"0x{param_id:04X}"] = {
                            "value": val,
                            "type": t,
                        }
            finally:
                motor.close()
        finally:
            ctrl.close()
        print(f"  Motor {mid}: {len(data[f'motor_{mid}'])} params read")

    with open(args.output, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nSaved to: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
