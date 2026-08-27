#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-

import sys
import time
import math
import cv2
import numpy as np

sys.path.append(".")

# Import RTM module
import RTC
import OpenRTM_aist

# Module specification
drowing_spec = [
    "implementation_id", "Drowing", 
    "type_name",         "Drowing", 
    "description",       "Path Drawer UI Component", 
    "version",           "1.0.0", 
    "vendor",            "TMU", 
    "category",          "User Interface", 
    "activity_type",     "STATIC", 
    "max_instance",      "1", 
    "language",          "Python", 
    "lang_type",         "SCRIPT",
    "conf.default.scale", "0.002",
    "conf.default.min_point_distance", "15.0",
    "conf.default.approx_epsilon", "8.0",

    "conf.__widget__.scale", "text",
    "conf.__widget__.min_point_distance", "text",
    "conf.__widget__.approx_epsilon", "text",

    "conf.__type__.scale", "double",
    "conf.__type__.min_point_distance", "double",
    "conf.__type__.approx_epsilon", "double",
    ""
]

class Drowing(OpenRTM_aist.DataFlowComponentBase):
    def __init__(self, manager):
        super().__init__(manager)

        self._d_drowing_path = OpenRTM_aist.instantiateDataType(RTC.TimedDoubleSeq)
        self._drowing_pathOut = OpenRTM_aist.OutPort("drowing_path", self._d_drowing_path)

        # Configuration parameters
        self._scale = [0.002]                # 1px = 0.002m (2mm)
        self._min_point_distance = [15.0]    # 送信点の間隔(px)
        self._approx_epsilon = [8.0]         # 折れ線・角検出の許容誤差(px)

        # UI State Variables
        self.canvas_size = 600
        self.canvas = np.ones((self.canvas_size, self.canvas_size, 3), dtype=np.uint8) * 255
        self.points = []
        self.drawing = False
        self.path_ready = False
        self.window_name = "Path Drawer UI"

    def _optimize_path(self, points):
        """
        折れ線近似（Douglas-Peucker法）を用いて、
        Z字・コの字・直線の手ブレを除去し、等間隔なサンプリング点列に再構成する
        """
        if len(points) < 3:
            return points

        pts_array = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
        epsilon = float(self._approx_epsilon[0])
        min_dist = float(self._min_point_distance[0])

        # 1. 軌跡の角（キーポイント）を抽出
        approx_curve = cv2.approxPolyDP(pts_array, epsilon, closed=False)
        key_points = [tuple(pt[0]) for pt in approx_curve]

        # 2. 抽出された各線分（キーポイント間）を min_point_distance で補間
        resampled_points = []
        for i in range(len(key_points) - 1):
            p1 = np.array(key_points[i], dtype=np.float64)
            p2 = np.array(key_points[i+1], dtype=np.float64)
            seg_vec = p2 - p1
            seg_len = np.linalg.norm(seg_vec)

            if seg_len < 1e-6:
                continue

            num_steps = max(1, int(round(seg_len / min_dist)))
            for s in range(num_steps):
                t = s / float(num_steps)
                pt = p1 + t * seg_vec
                resampled_points.append((int(round(pt[0])), int(round(pt[1]))))

        # 最後の終点を追加
        resampled_points.append(key_points[-1])
        return resampled_points

    def _redraw_canvas(self):
        """補正後の綺麗な点列でキャンバスを再描画"""
        self.canvas[:] = 255
        if not self.points:
            return

        for i in range(len(self.points) - 1):
            cv2.line(self.canvas, self.points[i], self.points[i+1], (0, 0, 255), 2)

        # 始点（緑）と終点（赤）
        cv2.circle(self.canvas, self.points[0], 5, (0, 200, 0), -1)
        if len(self.points) > 1:
            cv2.circle(self.canvas, self.points[-1], 5, (0, 0, 200), -1)

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.points = [(x, y)]
            self.canvas[:] = 255
            cv2.circle(self.canvas, (x, y), 5, (0, 200, 0), -1)
            print(f"\n[UI] 描画開始: START地点 (px: {x}, {y})", flush=True)

        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            last_x, last_y = self.points[-1]
            dist = math.hypot(x - last_x, y - last_y)

            # 描画中は細かくサンプリングして形状を捉える (3pxごと)
            if dist >= 3.0:
                self.points.append((x, y))
                cv2.line(self.canvas, (last_x, last_y), (x, y), (200, 200, 200), 1)

        elif event == cv2.EVENT_LBUTTONUP:
            if self.drawing:
                self.drawing = False
                if self.points[-1] != (x, y):
                    self.points.append((x, y))

                # 折れ線・直線・曲線の最適化
                self.points = self._optimize_path(self.points)
                self._redraw_canvas()

                print(f"[UI] 描画終了: GOAL地点 (px: {self.points[-1][0]}, {self.points[-1][1]}) / 補正後: 合計 {len(self.points)} 点", flush=True)
                self.path_ready = True

    def onInitialize(self):
        self.bindParameter("scale", self._scale, "0.002")
        self.bindParameter("min_point_distance", self._min_point_distance, "15.0")
        self.bindParameter("approx_epsilon", self._approx_epsilon, "8.0")
        self.addOutPort("drowing_path", self._drowing_pathOut)
        return RTC.RTC_OK

    def onActivated(self, ec_id):
        print("\n" + "=" * 50, flush=True)
        print("[UI] Activated: 描画ウィンドウを開きました", flush=True)
        print("  - 直線 / 折れ線(Zやコの字) / 曲線 を自由に描画できます", flush=True)
        print("  - 'C' キーでクリアできます", flush=True)
        print("=" * 50 + "\n", flush=True)

        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        self.canvas[:] = 255
        self.points.clear()
        self.path_ready = False
        return RTC.RTC_OK

    def onDeactivated(self, ec_id):
        print("[UI] Deactivated: 描画ウィンドウを閉じます", flush=True)
        cv2.destroyAllWindows()
        return RTC.RTC_OK

    def onExecute(self, ec_id):
        display_img = self.canvas.copy()
        cv2.putText(display_img, "Drag: Draw | C: Clear", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 100, 100), 1, cv2.LINE_AA)

        cv2.imshow(self.window_name, display_img)
        key = cv2.waitKey(10) & 0xFF

        if key == ord('c') or key == ord('C'):
            self.canvas[:] = 255
            self.points.clear()
            self.path_ready = False
            print("\n[UI] キャンバスをリセットしました", flush=True)

        if self.path_ready and len(self.points) >= 2:
            scale_val = float(self._scale[0])
            flat_path = []

            print("\n" + "=" * 60, flush=True)
            print(f"[UI] ★ 送信座標一覧 (全 {len(self.points)} 点 / scale: {scale_val} m/px)", flush=True)
            print("-" * 60, flush=True)

            for i, pt in enumerate(self.points):
                x_m = float(pt[0]) * scale_val
                y_m = float(pt[1]) * scale_val
                flat_path.extend([x_m, y_m])

                label = "START" if i == 0 else ("GOAL " if i == len(self.points)-1 else f"Pt {i:02d}")
                print(f"  {label} : 画面({pt[0]:3d}px, {pt[1]:3d}px) -> 実座標 X: {x_m:6.3f} m, Y: {y_m:6.3f} m", flush=True)

            print("=" * 60, flush=True)

            self._d_drowing_path.data = flat_path
            OpenRTM_aist.setTimestamp(self._d_drowing_path)
            self._drowing_pathOut.write()

            self.path_ready = False

        return RTC.RTC_OK


def DrowingInit(manager):
    profile = OpenRTM_aist.Properties(defaults_str=drowing_spec)
    manager.registerFactory(profile, Drowing, OpenRTM_aist.Delete)

def MyModuleInit(manager):
    DrowingInit(manager)
    instance_name = [i for i in sys.argv if "--instance_name=" in i]
    args = instance_name[0].replace("--", "?") if instance_name else ""
    manager.createComponent("Drowing" + args)

def main():
    mgr = OpenRTM_aist.Manager.init(sys.argv)
    mgr.setModuleInitProc(MyModuleInit)
    mgr.activateManager()
    mgr.runManager()

if __name__ == "__main__":
    main()