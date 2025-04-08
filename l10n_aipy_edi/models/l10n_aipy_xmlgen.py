# -*- coding: utf-8 -*-

# Import necessary modules
import xml.etree.ElementTree as ET
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _

from odoo.addons.base.models.res_company import Company
from odoo.addons.base.models.res_partner import Partner
from odoo.addons.account.models.account_move import AccountMove
#from odoo.addons.l10n_aipy.models.res_company import Company

def _generate_gEmis( move_id:AccountMove, company_id:Company, partner_id:Partner): #D100
    """
    Generates the gEmis XML file for the given data.
    """
    # Create the root element
    gEmis = ET.Element("gEmis") # Root element
    # Add elements (example)
    ET.SubElement(gEmis, "dRucEm").text = company_id.vat.split("-")[0] #D101
    ET.SubElement(gEmis, "dDVEmi").text = company_id.vat.split("-")[1] #D102
    ET.SubElement(gEmis, "iTipCont").text = "2" if partner_id.is_company else "1" #D103 
    if company_id.l10n_aipy_regime_type_id.code:
        ET.SubElement(gEmis, "cTipReg").text = str(company_id.l10n_aipy_regime_type_id.code) #D104
    if company_id.l10n_aipy_testing_mode:
        ET.SubElement(gEmis, "dNomEmi").text = "DE generado en ambiente de prueba - sin valor comercial" #D105
        ET.SubElement(gEmis, "dNomFanEmi").text = company_id.name #D106
    else:
        ET.SubElement(gEmis, "dNomEmi").text = company_id.name #D105
    ET.SubElement(gEmis, "dDirEmi").text = company_id.street #D107
    if company_id.l10n_aipy_house:
        ET.SubElement(gEmis, "dNumCas").text = company_id.l10n_aipy_house #D108
    else:
        ET.SubElement(gEmis, "dNumCas").text = "0" #D108
    if company_id.street2:
        ET.SubElement(gEmis, "dCompDir1").text = company_id.street2

    # Generate XML string
    #xml_str = ET.tostring(gEmis, encoding="unicode", method="xml")
    #return xml_str
    return gEmis

    

    
    

    
    