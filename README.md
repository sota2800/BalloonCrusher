# 音声認識による風船割りロボットシステム
## システム概要
2台の移動ロボットによる風船割りタスクを題材としたシステム。風船を搭載した Raspberry Pi Mouse が指定経路を走行し、これを音声指示で操作する Kobuki が追跡してロボットアームで風船を割る。割れたことの判定は画像認識で行う.
## システム構成
移動ロボット:kobuki
アーム:crane+v2
カメラ:Realsense D435
移動ロボット:RaspberryPi Mouse

## コンポーネント構成
ASRRTC

ManagerRTC

pathfollower

drawing

BalloonDetector

balloonWeb

crane_controle

