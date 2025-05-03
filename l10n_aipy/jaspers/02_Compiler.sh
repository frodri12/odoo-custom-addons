#!/bin/bash

ll="commons-beanutils-1.9.3.jar
commons-digester-2.1.jar
core-3.3.1.jar
gson-2.3.jar
itext-2.1.7.js9.jar
javase-3.3.1.jar
org.apache.commons.collections_3.2.2.v201511171945.jar
org.apache.commons.commons-collections4_4.4.0.jar
org.apache.commons.logging_1.2.0.v20180409-1502.jar
org.apache.xalan_2.7.2.v20201124-1837.jar
jasperreports-6.18.1.jar
"
#org.apache.log4j_1.2.15.v201012070815.jar 

ODOO_HOME="/opt/Odoo/odoo-18.0.developer/odoo-custom-addons/l10n_aipy/jaspers"
DD=/home/odoo/node_modules/facturacionelectronicapy-kude/dist/jasperLibs
CLASSPATH="${DD}/../DE"
CLASSPATH="${ODOO_HOME}"
export CLASSPATH
for i in $ll
do
  CLASSPATH="${CLASSPATH}:${DD}/${i}"
done
#CLASSPATH=${CLASSPATH}:${DD}/../jasperreports-6.18.1.jar
#CLASSPATH=${CLASSPATH}:${DD}/../itext-2.1.7.js9.jar

javac XmlToJasper.java

if [ $? -eq 0 ]
then
  echo "Compiling XmlToJasper.java succeeded"
  cd ${ODOO_HOME}/02_JrXml/
  java XmlToJasper ${ODOO_HOME}/02_JrXml/AutoFactura.jrxml ${ODOO_HOME}/03_NewJaspers/AutoFactura.jasper
  java XmlToJasper ${ODOO_HOME}/02_JrXml/Factura.jrxml ${ODOO_HOME}/03_NewJaspers/Factura.jasper
  java XmlToJasper ${ODOO_HOME}/02_JrXml/Factura-Ticket.jrxml ${ODOO_HOME}/03_NewJaspers/Factura-Ticket.jasper
  java XmlToJasper ${ODOO_HOME}/02_JrXml/NotaCredito.jrxml ${ODOO_HOME}/03_NewJaspers/NotaCredito.jasper
  java XmlToJasper ${ODOO_HOME}/02_JrXml/NotaDeDebito.jrxml ${ODOO_HOME}/03_NewJaspers/NotaDeDebito.jasper
  java XmlToJasper ${ODOO_HOME}/02_JrXml/NotaDebito.jrxml ${ODOO_HOME}/03_NewJaspers/NotaDebito.jasper
  java XmlToJasper ${ODOO_HOME}/02_JrXml/NotaRemision.jrxml ${ODOO_HOME}/03_NewJaspers/NotaRemision.jasper
  cd ${ODOO_HOME}
fi

