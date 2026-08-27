#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-


import sys
import math
sys.path.append(".")

import RTC
import OpenRTM_aist


pathfollowrtc_spec = ["implementation_id", "PathFollowRTC",
                      "type_name",         "PathFollowRTC",
                      "description",       "Pure pursuit path following",
                      "version",           "1.0.0",
                      "vendor",            "VenderName",
                      "category",          "Navigation",
                      "activity_type",     "PERIODIC",
                      "max_instance",      "1",
                      "language",          "Python",
                      "lang_type",         "SCRIPT",

                      # --- 速度（ロボット側の上限を超えないこと）---
                      "conf.default.speed", "0.08",
                      "conf.default.min_va", "0.03",
                      "conf.default.max_va", "0.45",

                      # --- Pure Pursuit ---
                      "conf.default.look_ahead", "0.15",
                      "conf.default.goal_tolerance", "0.05",

                      # --- その場旋回 ---
                      "conf.default.turn_threshold", "1.0",
                      "conf.default.turn_va", "0.4",

                      # --- 経路の前処理 ---
                      "conf.default.scale", "0.002",

                      # --- 動作 ---
                      "conf.default.loop", "0",

                      ""]


class PathFollowRTC(OpenRTM_aist.DataFlowComponentBase):

    def __init__(self, manager):
        OpenRTM_aist.DataFlowComponentBase.__init__(self, manager)

        self._d_path = OpenRTM_aist.instantiateDataType(RTC.TimedDoubleSeq)
        """
        """
        self._pathIn = OpenRTM_aist.InPort("path", self._d_path)

        self._d_end = OpenRTM_aist.instantiateDataType(RTC.TimedBoolean)
        """
        """
        self._endIn = OpenRTM_aist.InPort("end", self._d_end)

        self._d_pose = OpenRTM_aist.instantiateDataType(RTC.TimedPose2D)
        """
        """
        self._poseIn = OpenRTM_aist.InPort("pose", self._d_pose)

        self._d_out = OpenRTM_aist.instantiateDataType(RTC.TimedVelocity2D)
        """
        """
        self._outOut = OpenRTM_aist.OutPort("out", self._d_out)

        # コンフィギュレーション
        self._speed = [0.08]
        self._min_va = [0.03]
        self._max_va = [0.45]
        self._look_ahead = [0.15] #１ループで進む距離
        self._goal_tolerance = [0.05] #最後のindexからゴールまでの距離の許容範囲
        self._turn_threshold = [1.0] #これ以上ならその場で回転する
        self._turn_va = [0.4]
        self._scale = [0.002]
        self._loop = [0]

        # 内部状態
        self._path = []          # 前処理後の経由点
        self._idx = 0           #どの経由点か

        self._x = 0.0           #受け取った自己位置
        self._y = 0.0
        self._th = 0.0

        self._has_pose = False   # pose を一度でも受信したかTrueで走行スタート
        self._done = True       #走行終了
        self._pending_raw = None  # pose 未受信時に届いた経路の保留


    def onInitialize(self):

        # Bind variables and configuration variable
		
        # Set InPort buffers
        self.addInPort("path", self._pathIn)
        self.addInPort("end", self._endIn)
        self.addInPort("pose", self._poseIn)
        self.addOutPort("out", self._outOut)

        self.bindParameter("speed", self._speed, "0.08")
        self.bindParameter("min_va", self._min_va, "0.03")
        self.bindParameter("max_va", self._max_va, "0.45")
        self.bindParameter("look_ahead", self._look_ahead, "0.15")
        self.bindParameter("goal_tolerance", self._goal_tolerance, "0.05")

        self.bindParameter("turn_threshold", self._turn_threshold, "1.0")
        self.bindParameter("turn_va", self._turn_va, "0.4")

        self.bindParameter("scale", self._scale, "0.002")
        self.bindParameter("loop", self._loop, "0")


        return RTC.RTC_OK

    def onActivated(self, ec_id):
        self._path = [] #初期化
        self._idx = 0
        self._has_pose = False
        self._done = True
        self._pending_raw = None
        self._x = 0.0
        self._y = 0.0
        self._th = 0.0

        print("PathFollow: 開始（pose の受信を待っています）")
        return RTC.RTC_OK

    def onDeactivated(self, ec_id):
        self._write_velocity(0.0, 0.0)  #途中でも止まれるように
        print("PathFollow: 停止")
        return RTC.RTC_OK

    def onExecute(self, ec_id):


        if self._endIn.isNew():

            if self._endIn.read().data:
                print("割れた")
                self._reset()
                self._write_velocity(0.0, 0.0)
                return RTC.RTC_OK
        # 自己位置
        if self._poseIn.isNew():
            p = self._poseIn.read().data
            self._x = p.position.x
            self._y = p.position.y
            self._th = p.heading    #rad
            if not self._has_pose: #初回だけ自己位置を出す
                self._has_pose = True
                print("PathFollow: pose を受信 (%.3f, %.3f, %.1f deg)"
                      % (self._x, self._y, math.degrees(self._th)))

        # 経路の受信 
        if self._pathIn.isNew():
            raw = list(self._pathIn.read().data)
            if len(raw) < 4:
                # 短すぎる場合は止める
                self._path = []
                self._done = True
                self._pending_raw = None
                print("PathFollow: 経路をクリア（停止）")
            else:
                pts = [(float(raw[i]), float(raw[i + 1]))
                       for i in range(0, len(raw) - 1, 2)] #rawデータがから座標系に変換 奇数の場合範囲外に出ないために-1
                self._pending_raw = ("pixel", pts)# ピクセル

        # pose が来てから経路を現在位置基準で展開する
        if self._pending_raw is not None and self._has_pose:
            kind, pts = self._pending_raw #kindにピクセル ptsに座標
            self._pending_raw = None #なくす
            self._set_path(pts, metric=(kind == "metric"))

        # 停止走行　自己位置不明　か　終わっているか　指定経路が不明か 
        if not self._has_pose or self._done or not self._path:
            self._write_velocity(0.0, 0.0)
            return RTC.RTC_OK


        vx, va = self._pure_pursuit()
        print(vx,va)
        self._write_velocity(vx, va)
        return RTC.RTC_OK

    def _reset(self):
        self._path = []
        self._idx = 0
        self._done = True
        self._pending_raw = None

    def _pure_pursuit(self):
        Ld = max(0.01, self._look_ahead[0]) #ゼロ割防止

        # 現在位置から Ld 以上離れた点まで進める
        while self._idx < len(self._path) - 1:
            px, py = self._path[self._idx]
            if math.hypot(px - self._x, py - self._y) >= Ld:
                break
            self._idx += 1

        tx, ty = self._path[self._idx] #目標点

        #ここでどこまで進んだか

        # 終端に到達したか
        if self._idx >= len(self._path) - 1:
            if math.hypot(tx - self._x, ty - self._y) < self._goal_tolerance[0]:#十分に近いか
                if self._loop[0]:
                    self._idx = 0
                    print("PathFollow: 一周完了、ループ")
                else:
                    self._done = True
                    print("PathFollow: 到達")
                return 0.0, 0.0

        # 目標点をロボット座標系へ

        #ロボット動かす

        dx = tx - self._x #今いる場所から目標点までの差分
        dy = ty - self._y

        c, s = math.cos(self._th), math.sin(self._th) 

        local_x = dx * c + dy * s #ロボットから見た座標系
        local_y = -dx * s + dy * c

        alpha = math.atan2(local_y, local_x)

        # 角度差が大きいときはその場旋回
        if abs(alpha) > self._turn_threshold[0]:
            va = self._turn_va[0] if alpha > 0 else -self._turn_va[0]
            return 0.0, va

        vx = self._speed[0]
        va = 2.0 * vx * math.sin(alpha) / Ld

        # 角速度を上限で飽和させ、旋回半径を保つため vx も同率で下げる
        if abs(va) > self._max_va[0]:
            ratio = self._max_va[0] / abs(va)
            va = math.copysign(self._max_va[0], va)
            vx = max(self._min_va[0], vx * ratio)

        return vx, va

    # 経路の前処理
    def _set_path(self, pts, metric):
        #  ピクセル → メートル。画面は y 軸が下向きなので反転する
        if not metric:
            sc = self._scale[0]
            pts = [(x * sc, -y * sc) for x, y in pts]

        #  始点が現在位置に来るよう平行移動する
        ox, oy = pts[0]
        pts = [(x - ox + self._x, y - oy + self._y) for x, y in pts]



        if len(pts) < 2:
            print("PathFollow: 前処理後の点数が不足")
            return

        self._path = pts
        self._idx = 0
        self._done = False
   


    def _write_velocity(self, vx, va):
        self._d_out.data.vx = float(vx)
        self._d_out.data.vy = 0.0
        self._d_out.data.va = float(va)
        OpenRTM_aist.setTimestamp(self._d_out)
        self._outOut.write()


def PathFollowRTCInit(manager):
    profile = OpenRTM_aist.Properties(defaults_str=pathfollowrtc_spec)
    manager.registerFactory(profile, PathFollowRTC, OpenRTM_aist.Delete)


def MyModuleInit(manager):
    PathFollowRTCInit(manager)

    instance_name = [i for i in sys.argv if "--instance_name=" in i]
    args = instance_name[0].replace("--", "?") if instance_name else ""
    manager.createComponent("PathFollowRTC" + args)


def main():
    # remove --instance_name= option
    argv = [i for i in sys.argv if not "--instance_name=" in i]
    # Initialize manager
    mgr = OpenRTM_aist.Manager.init(sys.argv)
    mgr.setModuleInitProc(MyModuleInit)
    mgr.activateManager()
    mgr.runManager()


if __name__ == "__main__":
    main()