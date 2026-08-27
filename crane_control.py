#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-

# <rtc-template block="description">
"""
 @file caran_control.py
 @brief ModuleDescription
 @date $Date$


"""
# </rtc-template>

import sys
import time
sys.path.append(".")

# Import RTM module
import RTC
import OpenRTM_aist

import crane_control_idl

# Import Service implementation class
# <rtc-template block="service_impl">
from crane_control_idl_example import CraneArmService_i

# </rtc-template>

# Import Service stub modules
# <rtc-template block="consumer_import">
# </rtc-template>


# This module's spesification
# <rtc-template block="module_spec">
crane_control_spec = ["implementation_id", "crane_control", 
         "type_name",         "crane_control", 
         "description",       "ModuleDescription", 
         "version",           "1.0.0", 
         "vendor",            "TMU", 
         "category",          "Actuator", 
         "activity_type",     "STATIC", 
         "max_instance",      "1", 
         "language",          "Python", 
         "lang_type",         "SCRIPT",
         "conf.default.ready_speed", "50",
         "conf.default.strike_speed", "100",
         "conf.default.return_speed", "50",

         "conf.__widget__.ready_speed", "text",
         "conf.__widget__.strike_speed", "text",
         "conf.__widget__.return_speed", "text",

         "conf.__type__.ready_speed", "int",
         "conf.__type__.strike_speed", "int",
         "conf.__type__.return_speed", "int",

         ""]
# </rtc-template>

# <rtc-template block="component_description">
##
# @class crane_control
# @brief ModuleDescription
# 
# 
# </rtc-template>
class crane_control(OpenRTM_aist.DataFlowComponentBase):
	
    ##
    # @brief constructor
    # @param manager Maneger Object
    # 
    def __init__(self, manager):
        OpenRTM_aist.DataFlowComponentBase.__init__(self, manager)


        """
        """
        self._craneserviceportPort = OpenRTM_aist.CorbaPort("craneserviceport")

        """
        """
        self._m_craneservice = CraneArmService_i()
		


        # initialize of configuration-data.
        # <rtc-template block="init_conf_param">
        """
        
         - Name:  ready_speed
         - DefaultValue: 50
        """
        self._ready_speed = [100]
        """
        
         - Name:  strike_speed
         - DefaultValue: 100
        """
        self._strike_speed = [170]
        """
        
         - Name:  return_speed
         - DefaultValue: 50
        """
        self._return_speed = [100]
		
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
        self.bindParameter("ready_speed", self._ready_speed, "50")
        self.bindParameter("strike_speed", self._strike_speed, "100")
        self.bindParameter("return_speed", self._return_speed, "50")
		
        # Set InPort buffers
		
        # Set OutPort buffers
		
        # Set service provider to Ports
        self._craneserviceportPort.registerProvider("craneservice", "CraneArmService", self._m_craneservice)
		
        # Set service consumers to Ports
		
        # Set CORBA Service Ports
        self.addPort(self._craneserviceportPort)
		
        return RTC.RTC_OK
	
    ###
    ## 
    ## The finalize action (on ALIVE->END transition)
    ## 
    ## @return RTC::ReturnCode_t
    #
    ## 
    #def onFinalize(self):
    #

    #    return RTC.RTC_OK
	
    ###
    ##
    ## The startup action when ExecutionContext startup
    ## 
    ## @param ec_id target ExecutionContext Id
    ##
    ## @return RTC::ReturnCode_t
    ##
    ##
    #def onStartup(self, ec_id):
    #
    #    return RTC.RTC_OK
	
    ###
    ##
    ## The shutdown action when ExecutionContext stop
    ##
    ## @param ec_id target ExecutionContext Id
    ##
    ## @return RTC::ReturnCode_t
    ##
    ##
    #def onShutdown(self, ec_id):
    #
    #    return RTC.RTC_OK
	
    ##
    #
    # The activated action (Active state entry action)
    #
    # @param ec_id target ExecutionContext Id
    # 
    # @return RTC::ReturnCode_t
    #
    #
    def onActivated(self, ec_id):
        self._m_craneservice.goHome()
        return RTC.RTC_OK
	
    ##
    #
    # The deactivated action (Active state exit action)
    #
    # @param ec_id target ExecutionContext Id
    #
    # @return RTC::ReturnCode_t
    #
    #
    def onDeactivated(self, ec_id):
    
        return RTC.RTC_OK
	
    ##
    #
    # The execution action that is invoked periodically
    #
    # @param ec_id target ExecutionContext Id
    #
    # @return RTC::ReturnCode_t
    #
    #
    def onExecute(self, ec_id):
    
        return RTC.RTC_OK
	
    ###
    ##
    ## The aborting action when main logic error occurred.
    ##
    ## @param ec_id target ExecutionContext Id
    ##
    ## @return RTC::ReturnCode_t
    ##
    ##
    #def onAborting(self, ec_id):
    #
    #    return RTC.RTC_OK
	
    ###
    ##
    ## The error action in ERROR state
    ##
    ## @param ec_id target ExecutionContext Id
    ##
    ## @return RTC::ReturnCode_t
    ##
    ##
    #def onError(self, ec_id):
    #
    #    return RTC.RTC_OK
	
    ###
    ##
    ## The reset action that is invoked resetting
    ##
    ## @param ec_id target ExecutionContext Id
    ##
    ## @return RTC::ReturnCode_t
    ##
    ##
    #def onReset(self, ec_id):
    #
    #    return RTC.RTC_OK
	
    ###
    ##
    ## The state update action that is invoked after onExecute() action
    ##
    ## @param ec_id target ExecutionContext Id
    ##
    ## @return RTC::ReturnCode_t
    ##

    ##
    #def onStateUpdate(self, ec_id):
    #
    #    return RTC.RTC_OK
	
    ###
    ##
    ## The action that is invoked when execution context's rate is changed
    ##
    ## @param ec_id target ExecutionContext Id
    ##
    ## @return RTC::ReturnCode_t
    ##
    ##
    #def onRateChanged(self, ec_id):
    #
    #    return RTC.RTC_OK
	



def crane_controlInit(manager):
    profile = OpenRTM_aist.Properties(defaults_str=crane_control_spec)
    manager.registerFactory(profile,
                            crane_control,
                            OpenRTM_aist.Delete)

def MyModuleInit(manager):
    crane_controlInit(manager)

    # create instance_name option for createComponent()
    instance_name = [i for i in sys.argv if "--instance_name=" in i]
    if instance_name:
        args = instance_name[0].replace("--", "?")
    else:
        args = ""
  
    # Create a component
    comp = manager.createComponent("crane_control" + args)

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

