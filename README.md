# ReBot B601 RS Motor Parameter Restore

一键备份 / 恢复 ReBot B601 RS（RobStride 电机）机械臂参数。

One-click backup / restore tool for ReBot B601 RS (RobStride motor) arm parameters.

---

## 文件说明 / File Description

| 文件 | 说明 |
|------|------|
| `dump_motor_params.py` | 从正常机械臂导出所有参数到 JSON |
| `restore_motor_params.py` | 从 JSON 一键恢复参数到目标机械臂 |
| `reference_arm.json` | 正常机械臂参数基准（示例） |

| File | Description |
|------|-------------|
| `dump_motor_params.py` | Dump all parameters from a reference arm to JSON |
| `restore_motor_params.py` | Restore parameters from JSON to target arm |
| `reference_arm.json` | Reference arm parameter baseline (example) |

---

## 环境要求 / Requirements

- Python 3.12+
- `motorbridge` SDK (`pip install motorbridge`)
- Windows + PCAN-USB 驱动（或 Linux SocketCAN）
- 机械臂已上电，CAN 总线连接正常

---

## 使用流程 / Workflow

### 1. 导出正常机械臂参数 / Dump Reference Arm

```bash
python dump_motor_params.py --output my_reference_arm.json
```

会自动扫描 `0x7000 ~ 0x7030` 范围内所有可读寄存器，并将每颗电机的参数保存为 JSON。

Scans all readable registers in `0x7000 ~ 0x7030` and saves per-motor parameters to JSON.

### 2. 恢复到目标机械臂 / Restore to Target Arm

接上目标机械臂，关闭 `motorbridge-gateway`（脚本会独占 PCAN），然后运行：

Connect the target arm, **close `motorbridge-gateway`** (script needs exclusive PCAN access), then run:

```bash
# 基本恢复（写入 + 保存到 EEPROM）
python restore_motor_params.py --input my_reference_arm.json

# 恢复并回读验证
python restore_motor_params.py --input my_reference_arm.json --verify

# 只恢复到指定电机（例如 4-7）
python restore_motor_params.py --input my_reference_arm.json --motor-ids 4,5,6,7

# 只写入但不保存（测试用）
python restore_motor_params.py --input my_reference_arm.json --no-store
```

---

## 自动跳过的参数 / Auto-Skipped Parameters

以下参数不会被复制（与实时状态相关）：

| 参数 ID | 原因 |
|---------|------|
| `0x7016` | 当前位置（随姿态变化） |
| `0x7019` | 当前位置 |
| `0x701B` | 偏移/位置相关 |
| `0x701C` | 温度（实时变化） |

These parameters are skipped because they are real-time state dependent:

| Param ID | Reason |
|----------|--------|
| `0x7016` | Current position (changes with pose) |
| `0x7019` | Current position |
| `0x701B` | Offset / position related |
| `0x701C` | Temperature (real-time varying) |

---

## 注意事项 / Notes

- **运行前请关闭 `motorbridge-gateway`**：脚本会独占 PCAN 设备
- 恢复完成后可重新启动 gateway：`motorbridge-gateway --bind 127.0.0.1:9002`
- 建议每次只连接 **1 颗机械臂**到 CAN 总线，避免 ID 冲突

- **Close `motorbridge-gateway` before running**: scripts need exclusive PCAN access
- Restart gateway after restore: `motorbridge-gateway --bind 127.0.0.1:9002`
- Connect **only one arm** to the CAN bus at a time to avoid ID conflicts

---

## 适用场景 / Use Cases

- 批量组装机械臂时统一参数
- 替换电机后恢复正确参数
- 调试时对比正常/异常机械臂参数差异
- 固件刷写后重新配置

- Unify parameters during batch assembly
- Restore correct params after motor replacement
- Compare params between normal and faulty arms
- Re-configure after firmware update

---

## License

MIT
