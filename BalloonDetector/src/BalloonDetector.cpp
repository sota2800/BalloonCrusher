// -*- C++ -*-
// <rtc-template block="description">
/*!
 * @file  BalloonDetector.cpp
 * @brief ModuleDescription
 *
 */
// </rtc-template>

#include <opencv2/opencv.hpp>
#include "BalloonDetector.h"
#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <opencv2/opencv.hpp>
#include <fstream>

// Module specification
// <rtc-template block="module_spec">
#if RTM_MAJOR_VERSION >= 2
static const char* const balloondetector_spec[] =
#else
static const char* balloondetector_spec[] =
#endif
  {
    "implementation_id", "BalloonDetector",
    "type_name",         "BalloonDetector",
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
BalloonDetector::BalloonDetector(RTC::Manager* manager)
    // <rtc-template block="initializer">
  : RTC::DataFlowComponentBase(manager),
    m_rgbIn("rgb", m_rgb),
    m_depthIn("depth", m_depth),
    m_resetIn("reset", m_reset),
    m_brokenOut("broken", m_broken),
    m_webImageOut("image", m_webImage),
    m_stopOut("stop",m_stop)
    // </rtc-template>
{
}

/*!
 * @brief destructor
 */
BalloonDetector::~BalloonDetector()
{
}



RTC::ReturnCode_t BalloonDetector::onInitialize()
{
  // Registration: InPort/OutPort/Service
  // <rtc-template block="registration">
  // Set InPort buffers
  addInPort("rgb", m_rgbIn);
  addInPort("depth", m_depthIn);
  addInPort("reset", m_resetIn);
  // Set OutPort buffer
  addOutPort("broken", m_brokenOut);
  addOutPort("image", m_webImageOut);
  addOutPort("stop", m_stopOut);
  // Set service provider to Ports
  
  // Set service consumers to Ports
  
  // Set CORBA Service Ports
  
  // </rtc-template>

  // <rtc-template block="bind_config">
  // </rtc-template>

  m_broken.data = CORBA::string_dup("NONE");
  return RTC::RTC_OK;
}

/*
RTC::ReturnCode_t BalloonDetector::onFinalize()
{
  return RTC::RTC_OK;
}
*/


//RTC::ReturnCode_t BalloonDetector::onStartup(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}


//RTC::ReturnCode_t BalloonDetector::onShutdown(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}


//RTC::ReturnCode_t BalloonDetector::onActivated(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}


//RTC::ReturnCode_t BalloonDetector::onDeactivated(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}


  RTC::ReturnCode_t BalloonDetector::onExecute(RTC::UniqueId ec_id)
{
  // =========================================================
  // Depth receive
  // =========================================================
  if (m_depthIn.isNew()) {
    m_depthIn.read();
    cv::Mat depth( m_depth.height, m_depth.width, CV_16UC1, m_depth.pixels.get_buffer() );

    // Save independently from InPort buffer
    m_latestDepth = depth.clone();

    // Depth image for display
    cv::Mat depth8;
    cv::convertScaleAbs( depth, depth8, 0.03 );
    cv::imshow( "Depth", depth8 );
  }


  // =========================================================
  // RGB receive
  // =========================================================
  if (m_rgbIn.isNew()) {
    m_rgbIn.read();
    cv::Mat rgb( m_rgb.height, m_rgb.width, CV_8UC3, m_rgb.pixels.get_buffer() );

    // RealSense RGB -> OpenCV BGR
    cv::Mat bgr;
    cv::cvtColor( rgb, bgr, cv::COLOR_RGB2BGR );

    // BGR -> HSV
    cv::Mat hsv;
    cv::cvtColor( bgr, hsv, cv::COLOR_BGR2HSV );

    // =========================================================
    // Color masks
    // =========================================================
    cv::Mat red1;
    cv::Mat red2;
    cv::Mat redMask;
    cv::Mat orangeMask;
    cv::Mat yellowMask;
    cv::Mat yellowGreenMask;
    cv::Mat greenMask;
    cv::Mat cyanMask;
    cv::Mat purpleMask;
    cv::Mat pinkMask;

    // ---------------------------------------------------------
    // RED
    //
    // Orange is close to red, therefore limit RED
    // to 0-4 and 175-179.
    // ---------------------------------------------------------
    cv::inRange( hsv, cv::Scalar(0, 100, 70), cv::Scalar(7, 255, 255), red1 );
    cv::inRange( hsv, cv::Scalar(175, 100, 70), cv::Scalar(179, 255, 255), red2 );
    cv::bitwise_or( red1, red2, redMask );

    // ---------------------------------------------------------
    // ORANGE
    // ---------------------------------------------------------
    cv::inRange( hsv, cv::Scalar(2, 100, 70), cv::Scalar(20, 255, 255), orangeMask );

    // ---------------------------------------------------------
    // YELLOW
    // ---------------------------------------------------------
    cv::inRange( hsv, cv::Scalar(17, 60, 70), cv::Scalar(36, 255, 255), yellowMask );

    // ---------------------------------------------------------
    // YELLOW-GREEN
    // ---------------------------------------------------------
    cv::inRange( hsv, cv::Scalar(37, 60, 60), cv::Scalar(58, 255, 255), yellowGreenMask );

    // ---------------------------------------------------------
    // GREEN
    // ---------------------------------------------------------
    cv::inRange( hsv, cv::Scalar(50, 70, 50), cv::Scalar(95, 255, 255), greenMask );

    // ---------------------------------------------------------
    // CYAN / LIGHT BLUE
    // ---------------------------------------------------------
    cv::inRange( hsv, cv::Scalar(85, 60, 80), cv::Scalar(105, 255, 255), cyanMask );

    // ---------------------------------------------------------
    // PURPLE
    // ---------------------------------------------------------
    cv::inRange( hsv, cv::Scalar(125, 70, 50), cv::Scalar(159, 255, 255), purpleMask );

    // ---------------------------------------------------------
    // PINK
    // ---------------------------------------------------------
    cv::inRange( hsv, cv::Scalar(160, 60, 100), cv::Scalar(174, 255, 255), pinkMask );

    // =========================================================
    // Morphological noise removal
    // =========================================================
    cv::Mat kernel = cv::getStructuringElement( cv::MORPH_ELLIPSE, cv::Size(5, 5) );

    std::vector<cv::Mat*> masks = {
      &redMask,
      &orangeMask,
      &yellowMask,
      &yellowGreenMask,
      &greenMask,
      &cyanMask,
      &purpleMask,
      &pinkMask
    };

    for (cv::Mat* mask : masks) {
        cv::morphologyEx(*mask, *mask, cv::MORPH_OPEN, kernel);
        cv::morphologyEx(*mask, *mask, cv::MORPH_CLOSE, kernel);
    }
    // =========================================================
    // Balloon processing function
    // =========================================================
    auto processBalloon = [&](cv::Mat& mask, int index, const std::string& label, const cv::Scalar& drawColor)
    {
      std::vector< std::vector<cv::Point> > contours;
      cv::findContours( mask.clone(), contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE );
      double maxArea = 0.0;
      int maxIndex = -1;

      // -------------------------------------------------------
      // Find largest region
      // -------------------------------------------------------

      for ( int i = 0; i < static_cast<int>(contours.size()); i++ )
      {
        double area = cv::contourArea( contours[i] );
        if (area > maxArea) { 
            maxArea = area; maxIndex = i;
        }
      }


      // =======================================================
      // Balloon detected
      // =======================================================
      if ( maxIndex >= 0 && maxArea > 500.0 )
      {
        cv::Rect box = cv::boundingRect( contours[maxIndex] );

        // -----------------------------------------------------
        // Check whether balloon is near screen edge
        // -----------------------------------------------------
        const int margin = 30;
        bool nearEdge = box.x < margin || box.y < margin || box.br().x > bgr.cols - margin || box.br().y > bgr.rows - margin;

        // -----------------------------------------------------
        // First detection
        // -----------------------------------------------------

        if (!m_seen[index]) {

            m_seen[index] = true;
          m_areaEma[index] = maxArea;
          m_dropCount[index] = 0;

          std::cout << "Detected : " << label << std::endl;
        }


        // =====================================================
        // Burst detection
        // =====================================================

        if (!m_isBroken[index]) {
          // Balloon area suddenly became
          // smaller than 30% of normal area
          if ( !nearEdge && maxArea < m_areaEma[index] * 0.20 )
          {
            m_dropCount[index]++;
          }

          else {
            m_dropCount[index] = 0;

            // Update normal area slowly
            if (!nearEdge) {
              m_areaEma[index] = 0.9 * m_areaEma[index] + 0.1 * maxArea;
            }
          }
          // 5 consecutive frames
          if (m_dropCount[index] >= 5)
          {
            m_isBroken[index] = true;
            std::cout << "******** " << label << " BALLOON BROKEN! " << "********" << std::endl;
            m_broken.data = CORBA::string_dup("BROKEN");
            setTimestamp(m_broken);
            std::cout << "[OUTPUT] send ->" << m_broken.data << std::endl;
            m_brokenOut.write();
            m_stop.data = true;
            setTimestamp(m_stop);
            m_stopOut.write();
          }
        }
        // Save last detected position
        m_lastBox[index] = box;
        // =====================================================
        // Draw balloon box on camera image
        // =====================================================
        cv::rectangle( bgr, box, drawColor, 2 );
        cv::drawContours( bgr, contours, maxIndex, drawColor, 2 );

        // -----------------------------------------------------
        // Camera image label
        //
        // Do NOT show BROKEN here.
        // Broken status will be shown in another GUI.
        // -----------------------------------------------------
        std::string text = label + " Area:" + std::to_string( static_cast<int>( maxArea ) );

        // =====================================================
        // Depth at balloon center
        // =====================================================

        if (!m_latestDepth.empty()) {

          int cx = box.x + box.width / 2;
          int cy = box.y + box.height / 2;

          if ( cx >= 0 && cx < m_latestDepth.cols && cy >= 0 && cy < m_latestDepth.rows )
          {
            uint16_t depthRaw = m_latestDepth.at<uint16_t>( cy, cx );
            text += " D:" + std::to_string( depthRaw );
          }
        }

        cv::putText( bgr, text, cv::Point( box.x, std::max( 20, box.y - 10 ) ), cv::FONT_HERSHEY_SIMPLEX, 0.55, drawColor, 2 );
      }
      // =======================================================
      // Balloon disappeared
      // =======================================================

      else if ( m_seen[index] && !m_isBroken[index] )
      {
        const int margin = 30;
        bool nearEdge =
          m_lastBox[index].x < margin ||
          m_lastBox[index].y < margin ||
          m_lastBox[index].br().x > bgr.cols - margin ||
          m_lastBox[index].br().y > bgr.rows - margin;
        // -----------------------------------------------------
        // Disappeared inside image
        // -> possible burst
        // -----------------------------------------------------

        if (!nearEdge) {
          m_dropCount[index]++;
          if ( m_dropCount[index] >= 5 )
          {
            m_isBroken[index] = true;
            std::cout << "******** " << label << " BALLOON BROKEN! " << "********" << std::endl;
            m_broken.data = CORBA::string_dup("BROKEN");
            setTimestamp(m_broken);
            std::cout << "[OUTPUT] send ->" << m_broken.data << std::endl;
            m_brokenOut.write();
            m_stop.data = true;
            setTimestamp(m_stop);
            m_stopOut.write();
          }
        }

        else {
          // Balloon disappeared from edge.
          // Assume it moved out of camera view.
          m_dropCount[index] = 0;
        }
      }
    };

    struct ColorCandidate
    {
        double area = 0.0;
        cv::Rect box;
        bool valid = false;
    };
    ColorCandidate candidates[8];
    auto getCandidate =[&](const cv::Mat& mask, int index)
    {
            std::vector<std::vector<cv::Point>> contours;
            cv::findContours( mask.clone(), contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE );
            double maxArea = 0.0;
            int maxIndex = -1;
            for (int i = 0; i < static_cast<int>(contours.size()); i++)
            {
                double area = cv::contourArea(contours[i]);
                if (area > maxArea) {
                    maxArea = area;
                    maxIndex = i;
                }
            }

            if (maxIndex >= 0 && maxArea > 500.0) {
                candidates[index].area = maxArea;
                candidates[index].box = cv::boundingRect( contours[maxIndex] );
                candidates[index].valid = true;
            }
     };

    getCandidate(redMask, 0);
    getCandidate(orangeMask, 1);
    getCandidate(yellowMask, 2);
    getCandidate(yellowGreenMask, 3);
    getCandidate(greenMask, 4);
    getCandidate(cyanMask, 5);
    getCandidate(purpleMask, 6);
    getCandidate(pinkMask, 7);

    bool enabled[8] = {
        true, true, true, true,
        true, true, true, true
    };

    for (int i = 0; i < 8; i++) {
        if (!candidates[i].valid) {
            continue;
        }

        for (int j = i + 1; j < 8; j++) {

            if (!candidates[j].valid) {
                continue;
            }

            cv::Rect intersection =candidates[i].box &candidates[j].box;

            // 枠が重なっている
            if (intersection.area() > 0) {

                if (candidates[i].area >=
                    candidates[j].area)
                {
                    // iの方が大きい
                    enabled[j] = false;
                }
                else {
                    // jの方が大きい
                    enabled[i] = false;
                }
            }
        }
    }
    // =========================================================
    // Process all colors
    // =========================================================
    if (enabled[0])
        processBalloon( redMask, 0, "RED", cv::Scalar(0, 0, 255) );
    if (enabled[1])
        processBalloon( orangeMask, 1, "ORANGE", cv::Scalar(0, 165, 255) );
    if (enabled[2])
        processBalloon( yellowMask, 2, "YELLOW", cv::Scalar(0, 255, 255) );
    if (enabled[3])
        processBalloon( yellowGreenMask, 3, "YELLOW-GREEN", cv::Scalar(100, 255, 100) );
    if (enabled[4])
        processBalloon( greenMask, 4, "GREEN", cv::Scalar(0, 255, 0) );
    if (enabled[5])
        processBalloon( cyanMask, 5, "CYAN", cv::Scalar(255, 255, 0) );
    if (enabled[6])
        processBalloon( purpleMask, 6, "PURPLE", cv::Scalar(255, 0, 255) );
    if (enabled[7])
        processBalloon( pinkMask, 7, "PINK", cv::Scalar(180, 105, 255) );
    // =========================================================
    // Labels
    // =========================================================
    const std::string labels[8] = {
      "RED",
      "ORANGE",
      "YELLOW",
      "YELLOW-GREEN",
      "GREEN",
      "CYAN",
      "PURPLE",
      "PINK"
    };

    // =========================================================
    // Separate status GUI
    // =========================================================
    cv::Mat statusGUI(750,1000,CV_8UC3,cv::Scalar(30,30,30) );

    // ---------------------------------------------------------
    // Title
    // ---------------------------------------------------------
    cv::putText( statusGUI, "BALLOON STATUS", cv::Point( 170, 50 ), cv::FONT_HERSHEY_SIMPLEX, 1.0, cv::Scalar( 255, 255, 255 ), 2 );

    // =========================================================
    // Show detected balloons
    // =========================================================
    int statusY = 100;

    for ( int i = 0; i < 8; i++ )
    {
      // Do not show colors
      // which have never been detected
      if (!m_seen[i]) {
        continue;
      }
      std::string statusText;
      if (m_isBroken[i]) {
        statusText = labels[i] + " : BROKEN";
      }
      else {
        statusText = labels[i] + " : NORMAL";
      }
      cv::Scalar statusColor;
      if (m_isBroken[i]) {
        statusColor = cv::Scalar( 0, 0, 255 );
      }
      else {
        statusColor = cv::Scalar( 255, 255, 255 );
      }
      cv::putText( statusGUI, statusText, cv::Point( 60, statusY ), cv::FONT_HERSHEY_SIMPLEX, 0.75, statusColor, 2 );
      statusY += 35;
    }
    // =========================================================
    // Find broken colors
    // =========================================================

    std::string brokenColors = "";

    for ( int i = 0; i < 8; i++ )
    {
      if (m_isBroken[i]) {
        if (!brokenColors.empty()) {
          brokenColors += " ";
        }
        brokenColors += labels[i];
      }
    }


    // =========================================================
    // Large BROKEN display
    // =========================================================

    if (!brokenColors.empty()) {
      cv::putText( statusGUI, "BROKEN BALLOON", cv::Point( 150, 400 ), cv::FONT_HERSHEY_SIMPLEX, 0.9, cv::Scalar( 0, 0, 255 ), 3 );

      cv::putText( statusGUI, brokenColors, cv::Point( 120, 455 ), cv::FONT_HERSHEY_SIMPLEX, 1.1, cv::Scalar( 0, 0, 255 ), 3 );
    }

    else {
      cv::putText( statusGUI, "NO BURST DETECTED", cv::Point( 145, 440 ), cv::FONT_HERSHEY_SIMPLEX, 0.8, cv::Scalar( 0, 255, 0 ), 2 );
    }
    // =========================================================
    // Web用画像をOutPortへ出力
    // =========================================================
    cv::Mat rgbOut;
    cv::cvtColor( bgr, rgbOut, cv::COLOR_BGR2RGB );
    m_webImage.width = static_cast<CORBA::UShort>(rgbOut.cols);
    m_webImage.height = static_cast<CORBA::UShort>(rgbOut.rows);
    m_webImage.bpp = 24;
    m_webImage.format = CORBA::string_dup("RGB8");
    m_webImage.fDiv = 1.0;
    const size_t imageSize = rgbOut.total() * rgbOut.elemSize();
    m_webImage.pixels.length( static_cast<CORBA::ULong>(imageSize) );
    std::memcpy( m_webImage.pixels.get_buffer(), rgbOut.data, imageSize );
    setTimestamp(m_webImage);
    m_webImageOut.write();
    // =========================================================
    // Display
    // =========================================================

    // Camera image
    cv::imshow( "RGB Balloon Detection", bgr );

    // Separate status screen
    cv::imshow( "Balloon Status", statusGUI );
  }

  if (m_resetIn.isNew())
  {
      m_resetIn.read();

      if (m_reset.data)
      {
          std::cout << "========== WEB RESET ==========" << std::endl;

          for (int i = 0; i < 8; i++)
          {
              m_areaEma[i] = 0.0;
              m_dropCount[i] = 0;
              m_seen[i] = false;
              m_isBroken[i] = false;
              m_lastBox[i] = cv::Rect();
          }

          std::cout
              << "Balloon status reset."
              << std::endl;
      }
  }
    return RTC::RTC_OK;
  }

//RTC::ReturnCode_t BalloonDetector::onAborting(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}


//RTC::ReturnCode_t BalloonDetector::onError(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}


//RTC::ReturnCode_t BalloonDetector::onReset(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}


//RTC::ReturnCode_t BalloonDetector::onStateUpdate(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}


//RTC::ReturnCode_t BalloonDetector::onRateChanged(RTC::UniqueId /*ec_id*/)
//{
//  return RTC::RTC_OK;
//}



extern "C"
{
 
  void BalloonDetectorInit(RTC::Manager* manager)
  {
    coil::Properties profile(balloondetector_spec);
    manager->registerFactory(profile,
                             RTC::Create<BalloonDetector>,
                             RTC::Delete<BalloonDetector>);
  }
  
}
