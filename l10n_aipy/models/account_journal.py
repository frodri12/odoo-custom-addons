# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class AccountJournal(models.Model):

    _inherit = "account.journal"

    l10n_aipy_dnit_expedition_point = fields.Integer('Expeditions point', default = 1)

    @api.onchange('l10n_aipy_dnit_expedition_point', 'type')
    def _onchange_set_short_name(self):
        if self.type == 'sale' and self.l10n_aipy_dnit_expedition_point:
            self.code = "%03i" % self.l10n_aipy_dnit_expedition_point
            
