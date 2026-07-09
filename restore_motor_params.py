#!/usr/bin/env python3
"""
Restore motor parameters from a reference JSON dump to a target arm.
Usage: python restore_motor_params.py --input reference_arm.json

Skips position/temperature-related registers that should not be copied:
  0x7016 (current position), 0x7019 (current position),
  0x701B (offset/position), 0x701C (temperature)
  
# 基本恢复（写入 + 保存到 EEPROM）
python restore_motor_params.py --input reference_arm.json

# 恢复并回读验证
python restore_motor_params.py --input reference_arm.json --verify

# 只恢复到指定电机（例如 4-7）
python restore_motor_params.py --input reference_arm.json --motor-ids 4,5,6,7

# 只写入但不保存（测试用）
python restore_motor_params.py --input reference_arm.json --no-store
"""

import argparse
import json
import sys

import motorbridge


# Registers that should NOT be copied (position/temperature/offset related)
SKIP_PARAMS = {
    0x7016,  # current position
    0x7019,  # current position (duplicate)
    0x701B,  # offset/position related
    0x701C,  # temperature (real-time, varies)
}


def write_param(motor, param_id: int, value: float, param_type: str) -> None:
    if param_type == "f32":
        motor.robstride_write_param_f32(param_id, float(value))
    elif param_type == "u32":
        motor.robstride_write_param_u32(param_id, int(value))
    elif param_type == "u16":
        motor.robstride_write_param_u16(param_id, int(value))
    elif param_type == "u8":
        motor.robstride_write_param_u8(param_id, int(value))
    elif param_type == "i8":
        motor.robstride_write_param_i8(param_id, int(value))
    else:
        raise ValueError(f"Unknown param type: {param_type}")


def read_param(motor, param_id: int, param_type: str, timeout_ms: int = 200) -> float:
    if param_type == "f32":
        return motor.robstride_get_param_f32(param_id, timeout_ms)
    elif param_type == "u32":
        return motor.robstride_get_param_u32(param_id, timeout_ms)
    elif param_type == "u16":
        return motor.robstride_get_param_u16(param_id, timeout_ms)
    elif param_type == "u8":
        return motor.robstride_get_param_u8(param_id, timeout_ms)
    elif param_type == "i8":
        return motor.robstride_get_param_i8(param_id, timeout_ms)
    else:
        raise ValueError(f"Unknown param type: {param_type}")


def main():
    parser = argparse.ArgumentParser(description="Restore motor parameters from JSON dump")
    parser.add_argument("--input", default="reference_arm.json", help="Input JSON file")
    parser.add_argument("--channel", default="can0")
    parser.add_argument("--model", default="rs-00")
    parser.add_argument("--feedback-id", default="0xFD")
    parser.add_argument("--motor-ids", default="1,2,3,4,5,6,7", help="Target motor IDs to restore")
    parser.add_argument("--timeout-ms", type=int, default=200)
    parser.add_argument("--no-store", action="store_true", help="Do not call store_parameters after write")
    parser.add_argument("--verify", action="store_true", help="Read back and verify after write")
    args = parser.parse_args()

    with open(args.input, "r") as f:
        data = json.load(f)

    target_ids = [int(x.strip(), 0) for x in args.motor_ids.split(",")]
    feedback_id = int(args.feedback_id, 0)

    print(f"Restoring from: {args.input}")
    print(f"Target motors: {target_ids}")
    print(f"Store to EEPROM: {not args.no_store}")
    print()

    for mid in target_ids:
        key = f"motor_{mid}"
        if key not in data:
            print(f"[WARN] Motor {mid} not found in reference data, skipping")
            continue

        params = data[key]
        print(f"Motor {mid}: restoring {len(params)} params...")

        ctrl = motorbridge.Controller(args.channel)
        try:
            motor = ctrl.add_robstride_motor(mid, feedback_id, args.model)
            try:
                written = 0
                for param_hex, info in params.items():
                    param_id = int(param_hex, 0)
                    if param_id in SKIP_PARAMS:
                        continue

                    ref_value = info["value"]
                    param_type = info["type"]

                    try:
                        write_param(motor, param_id, ref_value, param_type)
                        written += 1
                    except Exception as e:
                        print(f"  [ERR] 0x{param_id:04X} write failed: {e}")

                # Store parameters
                if not args.no_store:
                    try:
                        motor.store_parameters()
                        print(f"  Stored {written} params to EEPROM")
                    except Exception as e:
                        print(f"  [WARN] store_parameters failed: {e}")
                else:
                    print(f"  Written {written} params (NOT stored)")

                # Verify
                if args.verify:
                    print(f"  Verifying...")
                    mismatches = 0
                    for param_hex, info in params.items():
                        param_id = int(param_hex, 0)
                        if param_id in SKIP_PARAMS:
                            continue

                        ref_value = info["value"]
                        param_type = info["type"]
                        try:
                            actual = read_param(motor, param_id, param_type, args.timeout_ms)
                            if param_type == "f32":
                                ok = abs(actual - ref_value) < 0.01
                            else:
                                ok = actual == ref_value
                            if not ok:
                                mismatches += 1
                                print(f"  [MISMATCH] 0x{param_id:04X}: expected={ref_value}, actual={actual}")
                        except Exception as e:
                            mismatches += 1
                            print(f"  [ERR] 0x{param_id:04X} verify read failed: {e}")
                    if mismatches == 0:
                        print(f"  All params verified OK")
                    else:
                        print(f"  {mismatches} mismatches found")

            finally:
                motor.close()
        finally:
            ctrl.close()

    print("\nRestore complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
