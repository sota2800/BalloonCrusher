#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-

# <rtc-template block="description">
"""
 @file ASRRTC.py
 @brief ModuleDescription
 @date $Date$


"""
# </rtc-template>

import sys
import time
sys.path.append(".")
import os

# Import RTM module
import RTC
import OpenRTM_aist
import threading
import azure.cognitiveservices.speech as speechsdk

SPEECH_KEY = os.environ.get("SPEECH_KEY") #環境変数にkey と　regionを保存しておく
SPEECH_REGION = os.environ.get("SPEECH_REGION")

if not SPEECH_KEY or not SPEECH_REGION:
    raise RuntimeError("SPEECH_KEY / SPEECH_REGION が設定されていません")


# Import Service implementation class
# <rtc-template block="service_impl">

# </rtc-template>

# Import Service stub modules
# <rtc-template block="consumer_import">
# </rtc-template>


# This module's spesification
# <rtc-template block="module_spec">
asrrtc_spec = ["implementation_id", "ASRRTC", 
         "type_name",         "ASRRTC", 
         "description",       "ModuleDescription", 
         "version",           "1.0.0", 
         "vendor",            "VenderName", 
         "category",          "Category", 
         "activity_type",     "STATIC", 
         "max_instance",      "1", 
         "language",          "Python", 
         "lang_type",         "SCRIPT",
         ""]
# </rtc-template>

# <rtc-template block="component_description">
##
# @class ASRRTC
# @brief ModuleDescription
# 
# 
# </rtc-template>
class ASRRTC(OpenRTM_aist.DataFlowComponentBase):
	
    ##
    # @brief constructor
    # @param manager Maneger Object
    # 
    def __init__(self, manager):
        OpenRTM_aist.DataFlowComponentBase.__init__(self, manager)

        self._d_spoke = OpenRTM_aist.instantiateDataType(RTC.TimedString)
        """
        """
        self._spokeOut = OpenRTM_aist.OutPort("spoke", self._d_spoke)

        self._heard = None
        self._lock = threading.Lock()
        self._recognizer = None
		


        # initialize of configuration-data.
        # <rtc-template block="init_conf_param">
		
        # </rtc-template>


		 
    ##
    #
    # The initialize action (on CREATED->ALIVE transition)
    # 
    # @return RTC::ReturnCode_t
    # 
    #
    def onInitialize(self):
        # Bind variables and configuration variable
		
        # Set InPort buffers
		
        # Set OutPort buffers
        self.addOutPort("spoke",self._spokeOut)
		
        # Set service provider to Ports
		
        # Set service consumers to Ports
		
        # Set CORBA Service Ports
		
        return RTC.RTC_OK
	

    def onActivated(self, ec_id):
        cfg = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
        cfg.speech_recognition_language = "ja-JP"
        self._recognizer = speechsdk.SpeechRecognizer(speech_config=cfg)
        self._recognizer.recognized.connect(self._on_recognized) #関数を登録する。音声認識出来たらこの関数を呼ぶ
        #マイクから音を読む → Azureのサーバへ送る → 返事を待つ→ 文字が返ってきた → 登録された関数を呼ぶ
        self._recognizer.start_continuous_recognition() #   新しいスレッドを作って、マイクを開いてAzureへ送り続けろ」と指示する
        self._heard = None
        print("ASR: 開始")
    
        return RTC.RTC_OK
    
    def _on_recognized(self, evt):          # 別スレッドから呼ばれる
        text = evt.result.text
        if text:
            print("ASR:", text)
            with self._lock:
                self._heard = text
	
    def onDeactivated(self, ec_id):

        if self._recognizer:
            self._recognizer.stop_continuous_recognition()
            self._recognizer = None
        print("ASR: 停止")

        return RTC.RTC_OK

    def onExecute(self, ec_id):
        #音声認識とポートは別スレッドで動いている。音声認識が終わったタイミングだとself._heardにNoneが入ってしまう。
        with self._lock: #self._heardを変更禁止にして、解除
            text, self._heard = self._heard, None
        data = None 
        if text:
            if "止" in text or "ストップ" in text:
                    data="kobuki,0,0"
                    self._d_spoke.data = data
                    self._spokeOut.write()
            if ("向いて" in text or "旋回" in text) and not "割って" in text:
                if "右"in text:
                    data="kobuki,0,-0.3"
                    self._d_spoke.data = data
                    self._spokeOut.write()
                elif "左"in text:
                    data="kobuki,0,0.3"
                    self._d_spoke.data = data
                    self._spokeOut.write()
            elif "進" in text or "進んで" in text:
                data="kobuki,-0.1,0"
                self._d_spoke.data = data
                self._spokeOut.write()
            elif "戻れ" in text or "後退"in text or "交代" in text:
                data="kobuki,0.1,0"
                self._d_spoke.data = data
                self._spokeOut.write()

            elif "割って" in text  or "われ" in text  or "割れ" in text or "アーム" in text:
                if "右" in text:
                    data="hand,57"
                    self._d_spoke.data = data
                    self._spokeOut.write()  
                elif "左" in text:
                    data="hand,238"
                    self._d_spoke.data = data
                    self._spokeOut.write()
                else:
                    data="hand,150"
                    self._d_spoke.data = data
                    self._spokeOut.write()

            print(data) 

        return RTC.RTC_OK




def ASRRTCInit(manager):
    profile = OpenRTM_aist.Properties(defaults_str=asrrtc_spec)
    manager.registerFactory(profile,
                            ASRRTC,
                            OpenRTM_aist.Delete)

def MyModuleInit(manager):
    ASRRTCInit(manager)

    # create instance_name option for createComponent()
    instance_name = [i for i in sys.argv if "--instance_name=" in i]
    if instance_name:
        args = instance_name[0].replace("--", "?")
    else:
        args = ""
  
    # Create a component
    comp = manager.createComponent("ASRRTC" + args)

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

