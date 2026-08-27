#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-

import time
import math
from dynamixel_sdk import *
import _GlobalIDL__POA

# --- ハードウェア設定 (Protocol 1.0 / AXシリーズ) ---
DXL_IDS           = [1, 2, 3, 4, 5]  # J1(旋回), J2(肩), J3(肘), J4(手首), J5(グリッパー)
PROTOCOL_VERSION  = 1.0              # Protocol 1.0
BAUDRATE          = 115200           # 通信速度
DEVICENAME        = 'COM8'           # COMポート名

# Protocol 1.0 コントロールテーブル
ADDR_TORQUE_ENABLE = 24              # トルクON/OFF (1 Byte)
ADDR_GOAL_POSITION  = 30              # 目標位置 (2 Byte)
LEN_GOAL_POSITION   = 2              # 2 Byte
ADDR_MOVING_SPEED   = 32              # 動作速度 (2 Byte)

class CraneArmService_i(_GlobalIDL__POA.CraneArmService):
    def __init__(self):
        self.rtc = None

        # Dynamixel SDK の初期化
        self.portHandler = PortHandler(DEVICENAME)
        self.packetHandler = PacketHandler(PROTOCOL_VERSION)

        # ポートオープン
        if not self.portHandler.openPort():
            print(f"[Error] COMポート ({DEVICENAME}) を開けませんでした。")
            return
        print(f"[CraneArm] COMポート ({DEVICENAME}) をオープンしました。")

        # ボーレート設定
        if not self.portHandler.setBaudRate(BAUDRATE):
            print(f"[Error] ボーレート ({BAUDRATE}) の設定に失敗しました。")
            return

        # Protocol 1.0 用 GroupSyncWrite (2 Byte) の初期化
        self.groupSyncWrite = GroupSyncWrite(
            self.portHandler, self.packetHandler, ADDR_GOAL_POSITION, LEN_GOAL_POSITION
        )

        # 全モータのトルクON
        for dxl_id in DXL_IDS:
            comm_result, dxl_error = self.packetHandler.write1ByteTxRx(
                self.portHandler, dxl_id, ADDR_TORQUE_ENABLE, 1
            )
            if comm_result != COMM_SUCCESS:
                print(f"[Error] ID {dxl_id} トルクON失敗: {self.packetHandler.getTxRxResult(comm_result)}")
            else:
                print(f"[CraneArm] ID {dxl_id} トルクON完了")

    # 切断・トルクOFF
    def close_hardware(self):
        if self.portHandler:
            for dxl_id in DXL_IDS:
                self.packetHandler.write1ByteTxRx(self.portHandler, dxl_id, ADDR_TORQUE_ENABLE, 0)
            self.portHandler.closePort()
            print("[CraneArm] 通信切断 (トルクOFF)")

    # 角度（0〜300度）-> Position値 (0〜1023)
    def deg_to_pos(self, deg):
        pos = int(deg * 1023.0 / 300.0)
        return max(0, min(1023, pos))

    # 各関節の動作速度を設定 (Moving Speed: 1〜1023)
    def set_speed(self, speed_val):
        val = max(1, min(1023, int(speed_val)))
        for dxl_id in DXL_IDS:
            self.packetHandler.write2ByteTxRx(self.portHandler, dxl_id, ADDR_MOVING_SPEED, val)

    # 5軸一括角度指令（度[deg]指定）
    def set_joint_angles(self, j1, j2, j3, j4, j5):
        angles = [j1, j2, j3, j4, j5]
        self.groupSyncWrite.clearParam()

        for dxl_id, deg in zip(DXL_IDS, angles):
            pos = self.deg_to_pos(deg)
            param = [
                DXL_LOBYTE(pos),
                DXL_HIBYTE(pos)
            ]
            self.groupSyncWrite.addParam(dxl_id, param)

        self.groupSyncWrite.txPacket()

    # 待機姿勢復帰（J1=150°, J2=150°, J3=62°, J4=112°, J5=196°）
    def goHome(self):
        print("[CraneArm] goHome 実行中...")
        return_spd = self.rtc._return_speed[0] if (self.rtc and hasattr(self.rtc, '_return_speed')) else 50
        self.set_speed(return_spd)
        self.set_joint_angles(150, 150, 62, 112, 196)
        time.sleep(5.0)
        return True

    # 叩き割り動作
    def strike(self, j1_angle):
        # サービスから渡されたラジアンを正面150°基準の度に変換
        j1_deg = float(j1_angle)
        j1_deg = max(0.0, min(300.0, j1_deg))
        print(f"[CraneArm] Strike実行: 目標J1角度 {j1_deg:.1f}°")

        ready_spd = self.rtc._ready_speed[0] if (self.rtc and hasattr(self.rtc, '_ready_speed')) else 50
        strike_spd = self.rtc._strike_speed[0] if (self.rtc and hasattr(self.rtc, '_strike_speed')) else 100

        # 1. 旋回（待機姿勢のままJ1を目標方向へ向ける）
        self.set_speed(ready_spd)
        self.set_joint_angles(j1_deg, 150, 62, 112, 196)
        time.sleep(5.0)

        # 2. 振りかぶり構え (J2: 105°, J3: 150°)
        self.set_joint_angles(j1_deg, 105, 150, 112, 196)
        time.sleep(5.0)

        # 3. 叩き割り (J2: 231°, J3: 150°)
        self.set_speed(strike_spd)
        self.set_joint_angles(j1_deg, 231, 139, 124, 196)
        time.sleep(5.0)

        # 4. 待機姿勢へ復帰
        self.goHome()
        return True

    # 喜び・バンザイモーション
    def celebrate(self):
        self.set_speed(170)  # キビキビ動かすため速度高め

        # 1. アームを真上にピシッと伸ばす（バンザイポーズ）
        self.set_joint_angles(150, 150, 150, 150, 196)
        time.sleep(0.6)

        # 2. 左右フリフリ ＆ グリッパーのパカパカ（2往復）
        for _ in range(3):
            # 左へ傾けつつ手を開く (J1:135°, J5:230°)
            self.set_joint_angles(130, 150, 150, 150, 150)
            time.sleep(0.5)
            # 右へ傾けつつ手を閉じる (J1:165°, J5:150°)
            self.set_joint_angles(170, 150, 150, 150, 196)
            time.sleep(0.5)

        # 3. 中央でキメポーズ
        self.set_joint_angles(150, 150, 150, 150, 150)
        time.sleep(0.5)

        # 4. ホーム姿勢へ復帰
        self.goHome()
        return True