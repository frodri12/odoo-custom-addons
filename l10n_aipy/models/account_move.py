# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):

    _inherit = 'account.move'

    l10n_aipy_inverse_currency_rate = fields.Float(string='Inverse Currency Rate', readonly=True, store=True,
    compute="_compute_inverse_currency_rate", precompute=True, copy=False)

    l10n_aipy_random_code = fields.Char(string='Random Code', readonly=True, store=True, index = True,tracking=True, copy=False)
    
    l10n_aipy_response_status = fields.Selection([
        ('P', 'Pending'),
        ('E', 'Error'),
        ('A', 'Aproved'),
        ('O', 'Aproved with Observations'),
        ('R', 'Rejected'),
    ], string='DNIT Status', default='P', readonly=True,tracking=True, copy=False)
    
    @api.onchange('l10n_latam_document_type_id', 'l10n_latam_document_number')
    def _inverse_l10n_latam_document_number(self):
        super()._inverse_l10n_latam_document_number()

        to_review = self.filtered(lambda x: (
            x.l10n_latam_document_type_id
            and x.l10n_latam_document_number
            and (x.l10n_latam_manual_document_number or not x.highest_name)
            and x.l10n_latam_document_type_id.country_id.code == 'PY'
        ))
        for rec in to_review:
            number = str(rec.l10n_latam_document_type_id._format_document_number(rec.l10n_latam_document_number))

            current_exp = int(number.split("-")[0])
            current_pos = int(number.split("-")[1])
            if current_pos != rec.journal_id.l10n_aipy_dnit_expedition_point or current_exp != self.company_id.l10n_aipy_dnit_organization:
                invoices = self.search([('journal_id', '=', rec.journal_id.id), ('posted_before', '=', True)], limit=1)
                # If there is no posted before invoices the user can change the POS number (x.l10n_latam_document_number)
                if (not invoices):
                    rec.journal_id.l10n_aipy_dnit_expedition_point = current_pos
                    rec.journal_id._onchange_set_short_name()
                # If not, avoid that the user change the POS number
                else:
                    raise UserError(_('The document number can not be changed for this journal, you can only modify'
                                      ' the POS number if there is not posted (or posted before) invoices'))

    @api.depends('currency_id','company_currency_id','company_id','invoice_date')
    def _compute_inverse_currency_rate(self):
        """ Compute the inverse currency rate for the move """
        for move in self:
            if move.is_invoice( include_receipts=True):
                move.l10n_aipy_inverse_currency_rate = 1 / self.env['res.currency']._get_conversion_rate(
                    from_currency=move.company_currency_id,
                    to_currency=move.currency_id,
                    company=move.company_id,
                    date=move._get_invoice_currency_rate_date(),
                )
            else:
                move.l10n_aipy_inverse_currency_rate = 1


    def _get_formatted_sequence(self, number=0):
        return "%s %03d-%03d-%07d" % (self.l10n_latam_document_type_id.doc_code_prefix,
                                 self.company_id.l10n_aipy_dnit_organization,
                                 self.journal_id.l10n_aipy_dnit_expedition_point, number)
 
    def _get_starting_sequence(self):
        """ If use documents then will create a new starting sequence using the document type code prefix and the
        journal document number with a 8 padding number """
        if self.journal_id.l10n_latam_use_documents and self.company_id.account_fiscal_country_id.code == "PY":
            if self.l10n_latam_document_type_id:
                return self._get_formatted_sequence()
        return super()._get_starting_sequence()

