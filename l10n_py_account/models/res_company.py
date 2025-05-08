# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError

class ResCompany(models.Model):

    _inherit = "res.company"

    l10n_py_dnit_responsibility_type_id = fields.Many2one(
        domain="[('code', 'in', [1, 4, 6])]", related='partner_id.l10n_py_dnit_responsibility_type_id', readonly=False)
