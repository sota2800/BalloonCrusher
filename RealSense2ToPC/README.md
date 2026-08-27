# Point Cloud Grabber RTC by Using Intel RealSense SDK 2

大阪電気通信大学  
升谷 保博  
2021年3月25日（色の順をBGRからRGBへ変更）

## はじめに

- Intel RealSenseから深度と色の情報を読み取り，RTC:PCLのPointCloud型（`PointCloudTypes::PointCoud`）を
出力するRTコンポーネントです．RealSense SDK 2を使っており，D400シリーズで動作します．R200には対応していません．
- 以下の環境で開発，動作確認しています．
  - Windows 10 64bit版
  - Visual Studio 2019 x64
  - OpenRTM-aist 1.2.2 64bit版
  - [Intel® RealSense™ SDK 2.0](https://github.com/IntelRealSense/librealsense/)
- CMakeでRealSense SDKを見つけるモジュール[`cmake/Modules/FindRealSense2.cmake`](cmake/Modules/FindRealSense2.cmake)は，
[INRIA Rennes Bretagne Atlantique](https://github.com/lagadic)の[vispに付属のもの](https://github.com/lagadic/visp/blob/master/cmake/FindRealSense2.cmake)を真似して作りました．
- [`pointcloud.idl`](idl/pointcloud.idl) は，Geoffrey Biggs (gbiggs)氏の
[RT-Components for the Point Cloud Library](https://github.com/gbiggs/rtcpcl/)
に[含まれているもの](https://github.com/gbiggs/rtcpcl/blob/master/pc_type/pointcloud.idl)
をそのまま使っています．
- 出力する点群を表す座標系は，y軸は上向きが正，z軸は後ろ向きが正です（それぞれRealSenseの座標系と逆向き，x軸はどちらも右向きが正）．
Choeonoidの深度センサのモデルに合わせるためにこのようにしています．

## インストール

- [OpenRTM-aist](http://www.openrtm.org/openrtm/)をインストール．
- [Eigen]()をインストール．PCL AllInOneパッケージに付属のものでも構わない．
- [GitHubのlibrealsenseのRelease](https://github.com/IntelRealSense/librealsense/releases)の中の
Windows用インストーラ`Intel.RealSense.SDK.exe` をダウンロードし実行．
- 環境変数
  - Pathの値の並びに以下を追加．
    - `C:\Program Files (x86)\Intel RealSense SDK 2.0\bin\x64` （または`C:\Program Files (x86)\Intel RealSense SDK 2.0\bin\x86`）
- [RealSense2ToPC](https://github.com/MasutaniLab/RealSense2ToPC)
をクローンかダウンロードする．
- CMake
  - ビルドディレクトリはトップ直下の`build`
  - ConfigureはVisual Studioのバージョンとプラットフォームに合わせる．
  - 必要に応じて変数EIGEN_DIRの値を設定する．
- `build\RealSense2ToPC.sln`をVisual Studioで開く．
- パフォーマンスを出すために，Releaseでビルドがお勧め．

## 使い方

- RealSenseは，USB 3.0のポートに接続することが望ましい．新しいRealsenseSDKでは2.0でも動作する．
- 出力されるデータ量が多いので，CORBAのデフォルトの設定ではエラーになります．
rtc.confに`corba.args: -ORBgiopMaxMsgSize`の設定が必要です．
トップディレクトリのrtc.confでは`corba.args: -ORBgiopMaxMsgSize 20971520`
にしています（デフォルト値の10倍）．
- コンポーネントを起動するバッチファイル[`RealSense2ToPC.bat`](RealSense2ToPC.bat)を用意しています．
  - ビルドディレクトリがトップ直下の`build`であることを仮定しています．
  - 環境変数`RTM_VC_CONFIG`を`Debug`か`Release`に設定してください．
- 動作確認のための接続相手として，
[PointCloudViewer](https://github.com/MasutaniLab/PointCloudViewer)
を使ってください．そのためのバッチファイル[`TestRealSense2ToPC.bat`](TestRealSense2ToPC.bat)を用意しています．

### コンフィギュレーション
- transX 座標変換の並進x成分 [m]
- transY 座標変換の並進y成分 [m]
- transZ 座標変換の並進z成分 [m]
- rotX 座標変換の回転x成分 [deg]
- rotY: 座標変換の回転y成分 [deg]
- rotZ: 座標変換の回転z成分 [deg]
- colorResolution 色の画素数（「横画素数x縦画素数」形式の文字列）
- depthResolution 深度の画素数（「横画素数x縦画素数」形式の文字列）

## 既知の問題・TODO

- type "xyzrgb"しか出力できません．
- キャリブレーション．

## 覚書（2020/2/16）
- PCLなしバージョン
- プログラムの中で1秒間隔でfpsを計算
- 座標変換なし
- CF-SZ5, D435
- 単体で実行
  - 424x240 → 30 fps
  - 640x360 → 30 fps
  - 640x480 → 30 fps
  - 848x480 → 30 fps
  - 1280x720 → 19 fps
- PointCloudViewerと組み合わせて実行
  - 424x240 → 30 fps，viewer 25 fps ?変動が激しく判断しづらい
  - 640x360 → 30 fps，viewer 18 fps ?変動が激しく判断しづらい
  - 640x480 → 26 fps，viewer 10 fps
  - 848x480 → 23 fps，viewer 10 fps
  - 1280x720 → 9 fps，viewer 5 fps
