package com.mobiperf.util;

import java.io.DataOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.AssetManager;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.Environment;
import android.preference.PreferenceManager;

import com.mobiperf.Logger;

/**
 * Needed for measuring LTE fine grained inference
 * 
 * @author sanae
 * 
 */
public class TcpDumpWrapper {

  Context context;
  Process process;

  public TcpDumpWrapper(Context context) {
    this.context = context;
  }

  private static File checkMounted() {

    String state = Environment.getExternalStorageState();
    if (!Environment.MEDIA_MOUNTED.equals(state)) {
      Logger.w("NOT MOUNTED RETURNING NULL");
      return null; // can't write to sd.
    }
    File rootfile = Environment.getExternalStorageDirectory();
    if (!rootfile.canWrite()) {
      Logger.w("NOT MOUNTED RETURNING NULL");
      return null;
    }
    return rootfile;

  }

  private static File checkSdCardFile(String file) {
    File rootfile = checkMounted();
    if (rootfile == null) {
      return null;
    }

    File logfile = new File(rootfile, file);
    return logfile;
  }

  private static File checkOrCreateFile(String directory) {
    File rootfile = checkMounted();
    if (rootfile == null) {
      return null;
    }

    File logfile = new File(rootfile, directory);
    if (!logfile.exists()) {
      Logger.w("file doesn't exist, creating directory");
      logfile.mkdirs();
    }
    Logger.w("directory " + directory + " exists");
    return rootfile;
  }

  public void startTcpDump() {

    if (checkSdCardFile("/download/") == null) {
      return;
    }
    new Thread(new Runnable() {

      @Override
      public void run() {
        String sdcard = Environment.getExternalStorageDirectory().getPath();
        String filename =
            "rrc_inference" + System.currentTimeMillis() + ".pcap";
        try {
          process = Runtime.getRuntime().exec("su");
          DataOutputStream os = new DataOutputStream(process.getOutputStream());
          os.writeBytes("/data/imap-tcpdump -vv -s 0 > " + sdcard
              + "/download/" + filename + "\n");
          os.flush();

        } catch (IOException e) {
          // TODO Auto-generated catch block
          e.printStackTrace();
        }
      }
    }).start();
  }

  public void stopTcpDump() {
    if (process != null) {
      process.destroy();
    }
  }

  /**
   * Checks if tcpdump exists; if it does not, install it.
   * Copies the binary from assets and loads it
   *
   * @return false on a failure
   */
  public boolean checkOrInstallTcpdump() {;
    // Check if the file is installed. If so, we're done.
    File tcpdump = new File("/data/", "imap-tcpdump");
    if (!tcpdump.exists()) {
      return true;
    }
    
    // Otherwise, copy the file from assets and install it.
    AssetManager assetManager = context.getAssets();
    try {
      checkOrCreateFile("/traces/"); // for storing the traces
      File result = checkOrCreateFile("/download/");
      if (result == null) {
        return false; // Failure
      }

      InputStream iwconfig = assetManager.open("imap-tcpdump");
      String sdcard = Environment.getExternalStorageDirectory().getPath();
      OutputStream out =
          new FileOutputStream(sdcard + "/download/imap-tcpdump");
      byte[] buffer = new byte[1024];
      int bytesread;
      while ((bytesread = iwconfig.read(buffer)) != -1) {
        out.write(buffer, 0, bytesread);
      }
      iwconfig.close();
      out.flush();
      out.close();
      iwconfig.close();
    } catch (IOException e) {
      e.printStackTrace();
      return false;
    }
    try {
      Process process = Runtime.getRuntime().exec("su");
      DataOutputStream os = new DataOutputStream(process.getOutputStream());
      os.writeBytes("cp /sdcard/download/iwconfig /data/\n");
      os.flush();

    } catch (IOException e) {

      e.printStackTrace();
      return false;
    }
    return true;
  }
  
  public boolean doIUpload() {
    
    
    // Step 1: is there anything to upload
    // Step 2: are we on wifi and is the time good
    long time = System.currentTimeMillis();
    SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(context);
    long last_uploaded = preferences.getLong("last_uploaded", 0);

    if (time > last_uploaded + 43200000) {

      ConnectivityManager cm = (ConnectivityManager) context.getSystemService(context.CONNECTIVITY_SERVICE);
      NetworkInfo netInfo = cm.getNetworkInfo(ConnectivityManager.TYPE_WIFI);

      if (netInfo.isConnected()) {
              last_uploaded = time;
              SharedPreferences.Editor editor = preferences.edit();
              editor.putLong("last_uploaded", time);
              editor.commit();
              return true;
      } 
    }
    return false;
    
    }
}
