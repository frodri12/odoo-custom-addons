# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError

import re

class ResCompany(models.Model):

    _inherit = "res.company"

    l10n_py_dnit_ws_idcsc1_prod = fields.Char( string='IDCSC1 Prod' )
    l10n_py_dnit_ws_idcsc2_prod = fields.Char( string='IDCSC2 Prod' )
    l10n_py_dnit_ws_idcsc1_test = fields.Char( string='IDCSC1 Test',default = "ABCD0000000000000000000000000000" )
    l10n_py_dnit_ws_idcsc2_test = fields.Char( string='IDCSC2 Test',default = "EFGH0000000000000000000000000000" )
 

    l10n_py_dnit_ws_environment = fields.Selection([('testing', 'Testing'), ('production', 'Production')], 
        string="DNIT Environment", default='testing',
        help="Environment used to connect to DNIT webservices. Production is to create real fiscal invoices in DNIT,"
        " Testing is for testing invoice creation in DNIT.")

    def _get_environment_type(self):
        """ This method is used to return the environment type of the company (testing or production) and will raise an
        exception when it has not been defined yet """
        self.ensure_one()
        if not self.l10n_py_dnit_ws_environment:
            raise UserError(_('DNIT environment not configured for company “%s”, please check accounting settings', self.name))
        return self.l10n_py_dnit_ws_environment

    def _get_l10n_py_dnit_ws_establecimiento( self):
        est = {}
        est.update({"codigo": "%03d" % self.l10n_py_establecimiento})
        est.update({"direccion": self.street}) #D107
        est.update({"numeroCasa": self.l10n_py_house if self.l10n_py_house else 0}) #D108
        if self.street2:
            est.update({"complementoDireccion1": self.street2}) #D109
        est.update({"departamento": int(self.state_id.code)}) #D111
        est.update({"distrito": int(self.l10n_py_district_id.code)}) #D113
        est.update({"ciudad": int(self.l10n_py_city_id.code)}) #D115
        if self.phone:
            phone = re.sub('[^0-9]', '', self.phone)
            if phone.__len__() < 6 or phone.__len__() > 15:
                raise UserError(_("Phone number must be between 6 and 15 digits"))
            else:
                est.update({"telefono": phone}) #D117
        else:
            raise UserError(_("Phone number is required"))
        if self.email:
            if self.email.find(",") > -1:
                est.update({"email": self.email.split(",")[0]}) #D118
            else:
                est.update({"email": self.email}) #D118
        else:
            raise UserError(_("Email is required"))
        estabecimientos = []
        estabecimientos.append(est)
        return estabecimientos

    def _get_l10n_py_dnit_ws_economic_activities( self):
        ecos = []
        ecos_count = 0
        for rec in self.l10n_aipy_economic_activity_ids:
            ecos.append(rec._get_l10n_py_dnit_ws_economic_avtivity())
            ecos_count += 1
        if ecos_count == 0:
            raise UserError(_("Economic activity is required for te company"))
        return ecos
