import net.sf.jasperreports.engine.JRException;
import net.sf.jasperreports.engine.util.JRLoader;
import net.sf.jasperreports.engine.xml.JRXmlWriter;
import net.sf.jasperreports.engine.JasperReport;
import net.sf.jasperreports.engine.JasperCompileManager;
import java.io.*;

class XmlToJasper {

    public static File sourcePath;
    public static String destinationPath;

    public static void main(String[] args) {

        try {
            // the path to the jrxml file to compile
            // the path and name we want to save the compiled file to
            JasperCompileManager.compileReportToFile( args[0], args[1]); 
        } catch( JRException e) {
            e.printStackTrace();
        }
    }
}

