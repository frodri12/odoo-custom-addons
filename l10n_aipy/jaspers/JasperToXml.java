import net.sf.jasperreports.engine.JRException;
import net.sf.jasperreports.engine.util.JRLoader;
import net.sf.jasperreports.engine.xml.JRXmlWriter;
import net.sf.jasperreports.engine.JasperReport;
import java.io.*;

class JasperToXml {

  public static File sourcePath;
  public static String destinationPath;

  public static void main(String[] args) {
    sourcePath = new File(args[0]);
    destinationPath = args[1];

    try {
      JasperReport report = (JasperReport) JRLoader.loadObject(sourcePath);
      JRXmlWriter.writeReport(report, destinationPath, "UTF-8");
    } catch( JRException e) {
        e.printStackTrace();
    }
  }
}

