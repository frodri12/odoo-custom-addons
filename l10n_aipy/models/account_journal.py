# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class AccountJournal(models.Model):

    _inherit = "account.journal"

    l10n_aipy_dnit_expedition_point = fields.Integer('Expeditions point', default = 1)

    l10n_aipy_is_pos = fields.Boolean(
        compute="_compute_l10n_aipy_is_pos", store=True, readonly=False,
        string="Is DNIT POS?",
        help="Paraguay: Specify if this Journal will be used to send electronic invoices to DNIT.",
    )

    @api.onchange('l10n_aipy_dnit_expedition_point', 'type')
    def _onchange_set_short_name(self):
        if self.type == 'sale' and self.l10n_aipy_dnit_expedition_point:
            self.code = "%03i" % self.l10n_aipy_dnit_expedition_point
            
    @api.depends('country_code', 'type', 'l10n_latam_use_documents')
    def _compute_l10n_aipy_is_pos(self):
        for journal in self:
            journal.l10n_aipy_is_pos = journal.country_code == 'PY' and journal.type == 'sale' and journal.l10n_latam_use_documents

