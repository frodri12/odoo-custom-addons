# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning

# Para que no de error el IDE
from odoo.addons.base.models.res_partner import Partner

class AccountJournal(models.Model):

    _inherit = "account.journal"

    def _get_l10n_py_dnit_ws_timbrado( self, CompanyId):
        timbrado = {}
        auth_code = self.l10n_py_dnit_timbrado
        auth_date = self.l10n_py_dnit_timbrado_start_date
        auth_duo = self.l10n_py_dnit_timbrado_end_date
        if CompanyId.l10n_py_dnit_ws_environment == 'testing':
            auth_code = self.l10n_py_dnit_timbrado_test
            auth_date = self.l10n_py_dnit_timbrado_start_date_test
            auth_duo = self.l10n_py_dnit_timbrado_end_date_test

        if not auth_code or not auth_date:
            raise UserError(_("Timbrado number and date are required at the journal definition"))
        if auth_code.__len__() != 8 and auth_code.__len__() != 11:
            raise UserError(_("Timbrado number must be 8 digits (12345678) or 11 digits (AA-12345678)"))
        if auth_code.__len__() == 8:
            timbrado.update({'timbradoNumero':auth_code}) #C004
        else:
            if auth_code.split("-").__len__() != 2:
                raise UserError(_("Timbrado number must be 8 digits (12345678) or 11 digits (AA-12345678)"))
            timbrado.update({'timbradoNumero':auth_code.split("-")[1]}) #C004
            timbrado.update({'numeroSerie':auth_code.split("-")[0]}) #C010
        if auth_date:
            timbrado.update({'timbradoFecha':auth_date.strftime("%Y-%m-%d")}) #C008
        else:
            raise UserError(_("Timbrado date is required at the journal definition"))
        return timbrado
        