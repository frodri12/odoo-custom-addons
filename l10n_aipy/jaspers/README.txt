


       <field name="iAfecIVA" class="java.lang.Integer">
               <property name="net.sf.jasperreports.xpath.field.expression" value="gCamIVA/iAfecIVA"/>
               <fieldDescription><![CDATA[gCamIVA/iAfecIVA]]></fieldDescription>
       </field>
       <field name="dBasGravIVA" class="java.lang.Double">
               <property name="net.sf.jasperreports.xpath.field.expression" value="gCamIVA/dBasGravIVA"/>
               <fieldDescription><![CDATA[gCamIVA/dBasGravIVA]]></fieldDescription>
       </field>
       <field name="dBasExe" class="java.lang.Double">
               <property name="net.sf.jasperreports.xpath.field.expression" value="gCamIVA/dBasExe"/>
               <fieldDescription><![CDATA[gCamIVA/dBasExe]]></fieldDescription>
       </field>

-- 10%
   <textFieldExpression><![CDATA[( $F{iAfecIVA} == 4 ?  ( $F{dTasaIVA} == 10 ? $F{dBasGravIVA} : 0 ) : ( $F{dTasaIVA} == 10 ? $F{dTotOpeItem} : 0 ) )]]></textFieldExpression>
-- 0%
   <textFieldExpression><![CDATA[($F{iAfecIVA} == 4) ? $F{dBasExe} : ($F{iAfecIVA} == 3) ? $F{dTotOpeItem} : 0]]></textFieldExpression>
-- 5%
   <textFieldExpression><![CDATA[( $F{iAfecIVA} == 4 ?  ( $F{dTasaIVA} == 5 ? $F{dBasGravIVA} : 0 ) : ( $F{dTasaIVA} == 5 ? $F{dTotOpeItem} : 0 ) )]]></textFieldExpression>

