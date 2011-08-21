// Copyright 2011 Google Inc. All Rights Reserved.
package com.google.wireless.speed.speedometer.test;

import com.google.wireless.speed.speedometer.MeasurementDesc;
import com.google.wireless.speed.speedometer.MeasurementError;
import com.google.wireless.speed.speedometer.MeasurementResult;
import com.google.wireless.speed.speedometer.MeasurementScheduler;
import com.google.wireless.speed.speedometer.MeasurementTask;
import com.google.wireless.speed.speedometer.SpeedometerApp;

import android.app.Instrumentation;
import android.content.Context;
import android.test.ActivityInstrumentationTestCase2;
import android.util.Log;
import android.widget.TextView;

import java.util.Date;
import java.util.Map;

/**
 * Base class for test cases that involves UI. 
 * @author wenjiezeng@google.com (Steve Zeng)
 *
 */
public class TestMeasurementTaskBase extends 
    ActivityInstrumentationTestCase2<SpeedometerApp> {
  // The activity class through which we interact with the UI thread
  protected SpeedometerApp activity;
  // Required by the ActivityInstrumentationTestCase2 as shown in the Android tutorial
  protected Instrumentation inst;
  // The system console for the test case to print debugging message to the phone screen
  protected TextView systemConsole;
  protected MeasurementScheduler scheduler;
  
  @SuppressWarnings("unchecked")
  public TestMeasurementTaskBase() {
    super("com.google.wireless.speed.speedometer.SpeedometerApp", SpeedometerApp.class);
  }
  
  @SuppressWarnings("unchecked")
  public TestMeasurementTaskBase(boolean isCheckinEnabled) {
    super("com.google.wireless.speed.speedometer.SpeedometerApp", SpeedometerApp.class);
    //TODO(Wenjie): Need a way to correctly initialize the scheduler on whether to enable checkin
  }
  
  @Override
  public void setUp() throws Exception {
    super.setUp();
    this.activity = getActivity();
    this.inst = getInstrumentation();
    this.scheduler = this.activity.getScheduler();
    this.systemConsole = (TextView) 
        activity.findViewById(com.google.wireless.speed.speedometer.R.viewId.systemConsole);
  }
  
  /**
   * A task created only for testing purpose. It never finishes.
   * 
   * @author wenjiezeng@google.com (Steve Zeng)
   */
  public static class DummyTask extends MeasurementTask {
    /**
     * The description for the dummy task
     * 
     * @author wenjiezeng@google.com (Steve Zeng)
     */
    public static class DummyDesc extends MeasurementDesc {
      protected DummyDesc(String type, String key, Date startTime, Date endTime,
          double intervalSec, long count, long priority, Map<String, String> params) {
        super(type, key, startTime, endTime, intervalSec, count, priority, params);
      }

      @Override
      public String getType() {
        return "DummyEverlastingMeasurement";
      }
      
      @Override 
      public MeasurementTask clone() {
        return null;
      }

      @Override
      protected void initalizeParams(Map<String, String> params) {
        // no need to do anything here.
      }
      
    }
    protected DummyTask(MeasurementDesc measurementDesc, Context parent) {
      super(measurementDesc, parent);
    }

    /** 
     * Dummy call() that does nothing but sleeps forever 
     * */
    @Override
    public MeasurementResult call() throws MeasurementError {
      try {
        Thread.sleep(Long.MAX_VALUE);
      } catch (InterruptedException e) {
        Log.e(SpeedometerApp.TAG, "interrupted in dummy measurement");
      }
      return null;
    }

    /** 
     * @see com.google.wireless.speed.speedometer.MeasurementTask#getType() 
     * */
    @Override
    public String getType() {
      return "DummyEverlastingMeasurement";
    }

    /* (non-Javadoc)
     * @see com.google.wireless.speed.speedometer.MeasurementTask#clone()
     */
    @Override
    public MeasurementTask clone() {
      // TODO(wenjiezeng): Auto-generated method stub
      return null;
    }
  }
}
