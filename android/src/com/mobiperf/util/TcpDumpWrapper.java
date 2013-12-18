package com.mobiperf.util;

import java.io.DataOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.SocketException;

import org.apache.commons.net.ftp.FTP;
import org.apache.commons.net.ftp.FTPClient;

import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.AssetManager;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.Environment;
import android.preference.PreferenceManager;

import com.mobiperf.ConfigPrivate;
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

  /**
   * Check if the SD card is mounted.
   * @return
   */
  private static File checkMounted() {

    String state = Environment.getExternalStorageState();
    if (!Environment.MEDIA_MOUNTED.equals(state)) {
      Logger.w("State is" + state);
      Logger.w("NOT MOUNTED RETURNING NULL");
      return null; // can't write to sd.
    }
    File rootfile = Environment.getExternalStorageDirectory();
    if (!rootfile.canWrite()) {
      Logger.w("Can't write to external storage");
      Logger.w("NOT MOUNTED RETURNING NULL");
      return null;
    }
    return rootfile;

  }
/**
 * Check if a file is on the SD card.  REturn it if so.
 * @param file
 * @return
 */
  private static File checkSdCardFile(String file) {
    File rootfile = checkMounted();
    if (rootfile == null) {
      return null;
    }

    File logfile = new File(rootfile, file);
    return logfile;
  }

  /**
   * Check if a file is on the SD card.  If not, create it. Then, return the file.
   * 
   * @param directory
   * @return
   */
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

        

        Logger.w("Tcpdump starting");
        String sdcard = Environment.getExternalStorageDirectory().getPath();
        String filename =
            "rrc_inference" + System.currentTimeMillis() + ".pcap";
        try {
          process = Runtime.getRuntime().exec("su");
          DataOutputStream os = new DataOutputStream(process.getOutputStream());
          os.writeBytes("/data/local/imap-tcpdump ");
          		//" > " + sdcard
              //+ "/download/" + filename + "\n");

          //Logger.w("Writing file to " + sdcard + "/download/" + filename);
          os.flush();
          try {
            Thread.sleep(3000);
          } catch (InterruptedException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
          }

        } catch (IOException e) {
          // TODO Auto-generated catch block
          e.printStackTrace();
        }
  }

  public void stopTcpDump() {
        try {
          Thread.sleep(10000);
        } catch (InterruptedException e) {
          // TODO Auto-generated catch block
          e.printStackTrace();
        }
        Logger.w("Tcpdump stopping");
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
    File tcpdump = new File("/data/local/", "imap-tcpdump");
    if (tcpdump.exists()) {
      Logger.w("tcpdump exists");
      return true;
    }
    
    // Otherwise, copy the file from assets and install it.
    AssetManager assetManager = context.getAssets();
    try {
      checkOrCreateFile("/traces/"); // for storing the traces
      File result = checkOrCreateFile("/download/");
      if (result == null) {
        Logger.w("Failed to install due to not creating download folder");
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
      Logger.w("Successfully saved imap-tcpdump");
    } catch (IOException e) {
      e.printStackTrace();
      return false;
    }
    try {
      Process process = Runtime.getRuntime().exec("su");
      DataOutputStream os = new DataOutputStream(process.getOutputStream());
      os.writeBytes("cp /sdcard/download/imap-tcpdump /data/local/\n");
      os.writeBytes("chmod 777 /data/local/imap-tcpdump\n");
      os.flush();

      Logger.w("Successfully copied imap-tcpdump, probably");
    } catch (IOException e) {

      e.printStackTrace();
      return false;
    }
    return true;
  }
  
  private File[] getFileList() {

    File sdcard = new File(Environment.getExternalStorageDirectory().getPath());
    File[] files = sdcard.listFiles();
    return files;
    
  }
  
  
  public void upload() {
    // check if uploaded recently, if not cancel.
    SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(context);
    Logger.w("Going to upload files");
    long last_uploaded = preferences.getLong("last_uploaded", 0);
    long time = System.currentTimeMillis();
    if (time < last_uploaded + 43200000) {
      Logger.w("Uploaded too recently, cancel upload");
      return;
    }
    
    // Check if there is anything to upload, if not cancel.
    File[] file_list = getFileList();
    if (file_list.length == 0) {
      Logger.w("No files to upload, cancel upload");
      return;
    }
    
    // Check if we are on WiFi, if not cancel.

    ConnectivityManager cm = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
    NetworkInfo netInfo = cm.getNetworkInfo(ConnectivityManager.TYPE_WIFI);

    if (!netInfo.isConnected()) {
      Logger.w("No wifi, upload later");
      return;
    } 
    

    
    
   // Iterate through files, upload and delete
   try {
     FTPClient ftp = new FTPClient();  
    ftp.connect(ConfigPrivate.ftp_server, 21);
    ftp.login(ConfigPrivate.ftp_username, ConfigPrivate.ftp_password);
    ftp.setFileType(FTP.BINARY_FILE_TYPE);
    ftp.enterLocalPassiveMode();
    
    for (File uploadme: file_list) {
      netInfo = cm.getNetworkInfo(ConnectivityManager.TYPE_WIFI);
      if (!netInfo.isConnected()) {
        Logger.w("Wifi stopped, upload some other time");
        ftp.disconnect();
        return;
      } 
      
      FileInputStream in =
          new FileInputStream(uploadme);
      boolean success = ftp.storeFile(uploadme.getName(), in);
      in.close();
      if (success) {
        uploadme.delete();
      }      
    }
    ftp.disconnect();
  
    // Indicate the last time an upload happened
    setUploaded();
    
    } catch (SocketException e) {
      e.printStackTrace();
    } catch (IOException e) {
      e.printStackTrace();
    }
  }
  
  /**
   * On a successful upload, record the last uploaded time
   */
  public void setUploaded() {
    long time = System.currentTimeMillis();
    SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(context);
    SharedPreferences.Editor editor = preferences.edit();
    editor.putLong("last_uploaded", time);
    editor.commit();    
  }
}
