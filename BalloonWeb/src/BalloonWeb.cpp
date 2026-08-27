// -*- C++ -*-
// <rtc-template block="description">
/*!
 * @file  BalloonWeb.cpp
 * @brief ModuleDescription
 *
 */
// </rtc-template>

#include "BalloonWeb.h"
#include <opencv2/opencv.hpp>
#include <fstream>
#include <iostream>
#include <string>

// Module specification
// <rtc-template block="module_spec">
#if RTM_MAJOR_VERSION >= 2
static const char* const balloonweb_spec[] =
#else
static const char* balloonweb_spec[] =
#endif
  {
    "implementation_id", "BalloonWeb",
    "type_name",         "BalloonWeb",
    "description",       "ModuleDescription",
    "version",           "1.0.0",
    "vendor",            "VenderName",
    "category",          "Category",
    "activity_type",     "PERIODIC",
    "kind",              "DataFlowComponent",
    "max_instance",      "1",
    "language",          "C++",
    "lang_type",         "compile",
    ""
  };
// </rtc-template>

/*!
 * @brief constructor
 * @param manager Maneger Object
 */
BalloonWeb::BalloonWeb(RTC::Manager* manager)
    // <rtc-template block="initializer">
  : RTC::DataFlowComponentBase(manager),
    m_imageIn("image", m_image),
    m_brokenIn("broken", m_broken),
    m_resetOut("reset", m_reset)
    // </rtc-template>
{
}

/*!
 * @brief destructor
 */
BalloonWeb::~BalloonWeb()
{
}



RTC::ReturnCode_t BalloonWeb::onInitialize()
{
  // Registration: InPort/OutPort/Service
  // <rtc-template block="registration">
  // Set InPort buffers
  addInPort("image", m_imageIn);
  addInPort("broken", m_brokenIn);
  
  // Set OutPort buffer
  addOutPort("reset", m_resetOut);

  
  // Set service provider to Ports
  
  // Set service consumers to Ports
  
  // Set CORBA Service Ports
  
  // </rtc-template>

  // <rtc-template block="bind_config">
  // </rtc-template>

  
  return RTC::RTC_OK;
}

/*
RTC::ReturnCode_t BalloonWeb::onFinalize()
{
  return RTC::RTC_OK;
}
*/


//RTC::ReturnCode_t BalloonWeb::onStartup(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}


//RTC::ReturnCode_t BalloonWeb::onShutdown(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}


//RTC::ReturnCode_t BalloonWeb::onActivated(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}


//RTC::ReturnCode_t BalloonWeb::onDeactivated(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}


RTC::ReturnCode_t BalloonWeb::onExecute(RTC::UniqueId ec_id)
{
    if (m_imageIn.isNew()) {
        m_imageIn.read();
        cv::Mat rgb( m_image.height, m_image.width, CV_8UC3, m_image.pixels.get_buffer() );
        cv::Mat bgr;
        cv::cvtColor( rgb, bgr, cv::COLOR_RGB2BGR );

        cv::imwrite( "C:/Users/shoei/workspace/BalloonWebSite/latest.jpg", bgr );
    }

    if (m_brokenIn.isNew()) {
        m_brokenIn.read();
        std::ofstream ofs( "C:/Users/shoei/workspace/BalloonWebSite/status.txt" );

        if (ofs.is_open()) {
            ofs << m_broken.data;
            ofs.close();
        }
        std::cout << "[WEB] broken color = " << m_broken.data << std::endl;
    }

    // ============================================
    // RESET要求
    // ============================================
    {
        std::ifstream ifs(
            "C:/Users/shoei/workspace/BalloonWebSite/reset.flag"
        );

        if (ifs.is_open())
        {
            std::string value;
            ifs >> value;
            ifs.close();

            if (value == "true")
            {
                m_reset.data = true;
                setTimestamp(m_reset);
                m_resetOut.write();

                std::cout << "[WEB] RESET -> true" << std::endl;

                std::ofstream clear(
                    "C:/Users/shoei/workspace/BalloonWebSite/reset.flag"
                );

                clear << "false";
                clear.close();

                std::ofstream status(
                    "C:/Users/shoei/workspace/BalloonWebSite/status.txt"
                );

                status << "NONE";
                status.close();
            }
        }
        return RTC::RTC_OK;
    }
}


//RTC::ReturnCode_t BalloonWeb::onAborting(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}


//RTC::ReturnCode_t BalloonWeb::onError(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}


//RTC::ReturnCode_t BalloonWeb::onReset(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}


//RTC::ReturnCode_t BalloonWeb::onStateUpdate(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}


//RTC::ReturnCode_t BalloonWeb::onRateChanged(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}

extern "C"
{
    void BalloonWebInit(RTC::Manager* manager)
    {
            coil::Properties profile(balloonweb_spec);

            manager->registerFactory(
                profile,
                RTC::Create<BalloonWeb>,
                RTC::Delete<BalloonWeb>
            );
    }
}
