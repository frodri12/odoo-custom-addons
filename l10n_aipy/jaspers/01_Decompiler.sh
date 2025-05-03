#!/bin/bash

ll="commons-beanutils-1.9.3.jar
commons-digester-2.1.jar
core-3.3.1.jar
gson-2.3.jar
itext-2.1.7.js9.jar
jasperreports-6.18.1.jar
javase-3.3.1.jar
org.apache.commons.collections_3.2.2.v201511171945.jar
org.apache.commons.commons-collections4_4.4.0.jar
org.apache.commons.logging_1.2.0.v20180409-1502.jar
org.apache.log4j_1.2.15.v201012070815.jar
org.apache.xalan_2.7.2.v20201124-1837.jar
"

ODOO_HOME="/opt/Odoo/odoo-18.0.developer/odoo-custom-addons/l10n_aipy/jaspers"
DD=/home/odoo/node_modules/facturacionelectronicapy-kude/dist/jasperLibs
CLASSPATH="/opt/Odoo/odoo-18.0.developer/odoo-custom-addons/l10n_aipy/jaspers"
export CLASSPATH
for i in $ll
do
  CLASSPATH="${CLASSPATH}:${DD}/${i}"
done

javac JasperToXml.java

if [ $? -eq 0 ]
then
  echo "Compiling JasperToXml.java succeeded"
  java JasperToXml ${ODOO_HOME}/01_JasperOriginal/AutoFactura.jasper ${ODOO_HOME}/02_JrXml/AutoFactura.jrxml
  java JasperToXml ${ODOO_HOME}/01_JasperOriginal/Factura.jasper ${ODOO_HOME}/02_JrXml/Factura.jrxml
  java JasperToXml ${ODOO_HOME}/01_JasperOriginal/Factura-Ticket.jasper ${ODOO_HOME}/02_JrXml/Factura-Ticket.jrxml
  java JasperToXml ${ODOO_HOME}/01_JasperOriginal/NotaCredito.jasper ${ODOO_HOME}/02_JrXml/NotaCredito.jrxml
  java JasperToXml ${ODOO_HOME}/01_JasperOriginal/NotaDeDebito.jasper ${ODOO_HOME}/02_JrXml/NotaDeDebito.jrxml
  java JasperToXml ${ODOO_HOME}/01_JasperOriginal/NotaDebito.jasper ${ODOO_HOME}/02_JrXml/NotaDebito.jrxml
  java JasperToXml ${ODOO_HOME}/01_JasperOriginal/NotaRemision.jasper ${ODOO_HOME}/02_JrXml/NotaRemision.jrxml
fi

