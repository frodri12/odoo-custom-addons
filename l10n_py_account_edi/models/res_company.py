# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ResCompany(models.Model):

    _inherit = "res.company"

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
