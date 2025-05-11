# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from dateutil.relativedelta import relativedelta

class AccountMove(models.Model):

    _inherit = 'account.move'

    ###
    ### Overwirtes
    ###
    def _is_manual_document_number(self):
        """ Document number should be manual input by user when the journal use documents and

        * if sales journal and not a DNIT pos (liquido producto case)
        * if purchase journal and not a DNIT pos (regular case of vendor bills)

        All the other cases the number should be automatic set, wiht only one exception, for pre-printed/online DNIT
        POS type, the first numeber will be always set manually by the user and then will be computed automatically
        from there """
        if self.country_code != 'PY':
            return super()._is_manual_document_number()

        if self.l10n_latam_use_documents and self.journal_id.type == 'purchase' and \
            not self.journal_id.l10n_py_is_pos and self.journal_id.l10n_py_dnit_pos_system in ['AUII_IM', 'AURLI_RLM']:
            return False
            
        # NOTE: There is a corner case where 2 sales documents can have the same number for the same DOC from a
        # different vendor, in that case, the user can create a new Sales Liquido Producto Journal
        return self.l10n_latam_use_documents and self.journal_id.type in ['purchase', 'sale'] and \
            not self.journal_id.l10n_py_is_pos

    @api.constrains('move_type', 'l10n_latam_document_type_id')
    def _check_invoice_type_document_type(self):
        """ LATAM module define that we are not able to use debit_note or invoice document types in an invoice refunds,
        However for Paraguayan Document Type's 99 (internal type = invoice) we are able to used in a refund invoices.

        In this method we exclude the paraguayan documents that can be used as invoice and refund from the generic
        constraint """
        docs_used_for_inv_and_ref = self.filtered(
            lambda x: x.country_code == 'PY' and
            x.l10n_latam_document_type_id.code in self._get_l10n_py_codes_used_for_inv_and_ref() and
            x.move_type in ['out_refund', 'in_refund'])

        super(AccountMove, self - docs_used_for_inv_and_ref)._check_invoice_type_document_type()

    @api.model
    def _get_l10n_py_codes_used_for_inv_and_ref(self):
        """ List of document types that can be used as an invoice and refund. This list can be increased once needed
        and demonstrated. As far as we've checked document types of wsfev1 don't allow negative amounts so, for example
        document 61 could not be used as refunds. """
        return ['99', '186', '188', '189', '60']

    def _get_l10n_latam_documents_domain(self):
        self.ensure_one()
        domain = super()._get_l10n_latam_documents_domain()
        if self.journal_id.company_id.account_fiscal_country_id.code == "PY":
            letters = self.journal_id._get_journal_letter(counterpart_partner=self.partner_id.commercial_partner_id)
            domain += ['|', ('l10n_py_letter', '=', False), ('l10n_py_letter', 'in', letters)]
            domain = expression.AND([
                domain or [],
                self.journal_id._get_journal_codes_domain(),
            ])
            if self.move_type in ['out_refund', 'in_refund']:
                domain = ['|', ('code', 'in', self._get_l10n_py_codes_used_for_inv_and_ref())] + domain
        return domain

    def _post(self, soft=True):
        py_invoices = self.filtered(lambda x: x.company_id.account_fiscal_country_id.code == "PY" and x.l10n_latam_use_documents)
        # We make validations here and not with a constraint because we want validation before sending electronic
        # data on EDI
        py_invoices._check_paraguayan_invoice_taxes()
        posted = super()._post(soft=soft)

        posted_py_invoices = posted & py_invoices
        posted_py_invoices._set_dnit_responsibility()
        posted_py_invoices._set_dnit_service_dates()
        return posted

    l10n_py_dnit_responsibility_type_id = fields.Many2one(
        'l10n_py.dnit.responsibility.type', string='DNIT Responsibility Type', help='Defined by DNIT to'
        ' identify the type of responsibilities that a person or a legal entity could have and that impacts in the'
        ' type of operations and requirements they need.')

    def _set_dnit_responsibility(self):
        """ We save the information about the receptor responsability at the time we validate the invoice, this is
        necessary because the user can change the responsability after that any time """
        for rec in self:
            rec.l10n_py_dnit_responsibility_type_id = rec.commercial_partner_id.l10n_py_dnit_responsibility_type_id.id

    # Mostly used on reports
    l10n_py_dnit_concept = fields.Selection(
        compute='_compute_l10n_py_dnit_concept', selection='_get_dnit_invoice_concepts', string="DNIT Concept",
        help="A concept is suggested regarding the type of the products on the invoice.")

    def _get_dnit_invoice_concepts(self):
        """ Return the list of values of the selection field. """
        return [('1', 'Products / Definitive export of goods'), ('2', 'Services'), ('3', 'Products and Services'),
                ('4', '4-Other (export)')]

    @api.depends('invoice_line_ids', 'invoice_line_ids.product_id', 'invoice_line_ids.product_id.type', 'journal_id')
    def _compute_l10n_py_dnit_concept(self):
        recs_afip = self.filtered(lambda x: x.company_id.account_fiscal_country_id.code == "PY" and x.l10n_latam_use_documents)
        for rec in recs_afip:
            rec.l10n_py_dnit_concept = rec._get_concept()
        remaining = self - recs_afip
        remaining.l10n_py_dnit_concept = ''

    def _get_concept(self):
        """ Method to get the concept of the invoice considering the type of the products on the invoice """
        self.ensure_one()
        invoice_lines = self.invoice_line_ids.filtered(lambda x: x.display_type not in ('line_note', 'line_section'))
        product_types = set([x.product_id.type for x in invoice_lines if x.product_id])
        consumable = {'consu'}
        service = set(['service'])
        # on expo invoice you can mix services and products
        expo_invoice = self.l10n_latam_document_type_id.code in ['19', '20', '21']

        # WSFEX 1668 - If Expo invoice and we have a "IVA Liberado – Ley Nº 19.640" (Zona Franca) partner
        # then DNIT concept to use should be type "Others (4)"
        #is_zona_franca = self.partner_id.l10n_py_dnit_responsibility_type_id == self.env.ref("l10n_py_account.res_IVA_LIB")
        is_zona_franca = False
        # Default value "product"
        afip_concept = '1'
        if expo_invoice and is_zona_franca:
            afip_concept = '4'
        elif product_types == service:
            afip_concept = '2'
        elif product_types - consumable and product_types - service and not expo_invoice:
            afip_concept = '3'
        return afip_concept


    def _set_dnit_service_dates(self):
        for rec in self.filtered(lambda m: m.invoice_date and m.l10n_py_dnit_concept in ['2', '3', '4']):
            if not rec.l10n_py_dnit_service_start:
                rec.l10n_py_dnit_service_start = rec.invoice_date + relativedelta(day=1)
            if not rec.l10n_py_dnit_service_end:
                rec.l10n_py_dnit_service_end = rec.invoice_date + relativedelta(day=1, days=-1, months=+1)

    def _check_paraguayan_invoice_taxes(self):

        # check vat on companies thats has it (Contribuyente)
        for inv in self.filtered(lambda x: x.company_id.l10n_py_company_requires_vat):
            purchase_aliquots = 'not_zero'
            # we require a single vat on each invoice line except from some purchase documents
            if inv.move_type in ['in_invoice', 'in_refund'] and inv.l10n_latam_document_type_id.purchase_aliquots == 'zero':
                purchase_aliquots = 'zero'
            for line in inv.mapped('invoice_line_ids').filtered(lambda x: x.display_type not in ('line_section', 'line_note')):
                vat_taxes = line.tax_ids.filtered(lambda x: x.tax_group_id.l10n_py_vat_dnit_code)
                if len(vat_taxes) != 1:
                    raise UserError(_("There should be a single tax from the “VAT“ tax group per line, but this is not the case for line “%s”. Please add a tax to this line or check the tax configuration's advanced options for the corresponding field “Tax Group”.", line.name))

                elif purchase_aliquots == 'zero' and vat_taxes.tax_group_id.l10n_py_vat_dnit_code != '0':
                    raise UserError(_('On invoice id “%s” you must use VAT Not Applicable on every line.', inv.id))
                elif purchase_aliquots == 'not_zero' and vat_taxes.tax_group_id.l10n_py_vat_dnit_code == '0':
                    raise UserError(_('On invoice id “%s” you must use a VAT tax that is not VAT Not Applicable', inv.id))

    l10n_py_dnit_service_start = fields.Date(string='DNIT Service Start Date')
    l10n_py_dnit_service_end = fields.Date(string='DNIT Service End Date')

    def _reverse_moves(self, default_values_list=None, cancel=False):
        if not default_values_list:
            default_values_list = [{} for move in self]
        for move, default_values in zip(self, default_values_list):
            default_values.update({
                'l10n_py_dnit_service_start': move.l10n_py_dnit_service_start,
                'l10n_py_dnit_service_end': move.l10n_py_dnit_service_end,
            })
        return super()._reverse_moves(default_values_list=default_values_list, cancel=cancel)

    def _get_starting_sequence(self):
        """ If use documents then will create a new starting sequence using the document type code prefix and the
        journal document number with a 7 padding number """
        if self.journal_id.l10n_latam_use_documents and self.company_id.account_fiscal_country_id.code == "PY":
            if self.l10n_latam_document_type_id:
                return self._get_formatted_sequence()
        return super()._get_starting_sequence()

    def _get_formatted_sequence(self, number=0):
        return "%s %03d-%03d-%07d" % (self.l10n_latam_document_type_id.doc_code_prefix,
                                 self.company_id.l10n_py_establecimiento,
                                 self.journal_id.l10n_py_dnit_pos_number, number)

    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super(AccountMove, self)._get_last_sequence_domain(relaxed)
        if self.company_id.account_fiscal_country_id.code == "PY" and self.l10n_latam_use_documents:
            where_string += " AND l10n_latam_document_type_id = %(l10n_latam_document_type_id)s"
            param['l10n_latam_document_type_id'] = self.l10n_latam_document_type_id.id or 0
        return where_string, param

    def _get_name_invoice_report(self):
        self.ensure_one()
        if self.l10n_latam_use_documents and self.company_id.account_fiscal_country_id.code == 'PY':
            return 'l10n_py_account.report_invoice_document'
        return super()._get_name_invoice_report()

    ###
    ### Constraints
    ###
    @api.constrains('move_type', 'journal_id')
    def _check_moves_use_documents(self):
        """ Do not let to create not invoices entries in journals that use documents """
        not_invoices = self.filtered(lambda x: x.company_id.account_fiscal_country_id.code == "PY" and x.journal_id.type in ['sale', 'purchase'] and x.l10n_latam_use_documents and not x.is_invoice())
        if not_invoices:
            raise ValidationError(_("The selected Journal can't be used in this transaction, please select one that doesn't use documents as these are just for Invoices."))

    ###
    ### OnChanges
    ###
    @api.onchange('partner_id')
    def _onchange_dnit_responsibility(self):
        if self.company_id.account_fiscal_country_id.code == 'PY' and self.l10n_latam_use_documents and self.partner_id \
           and not self.partner_id.l10n_py_dnit_responsibility_type_id:

            return {'warning': {
                'title': _('Missing Partner Configuration'),
                'message': _('Please configure the DNIT Responsibility for "%s" in order to continue',
                    self.partner_id.name)}}

    @api.onchange('partner_id')
    def _onchange_partner_journal(self):
        """ This method is used when the invoice is created from the sale or subscription """
        expo_journals = ['FEERCEL', 'FEEWS', 'FEERCELP']
        for rec in self.filtered(lambda x: x.company_id.account_fiscal_country_id.code == "PY" and x.journal_id.type == 'sale'
                                 and x.l10n_latam_use_documents and x.partner_id.l10n_py_dnit_responsibility_type_id):
            res_code = rec.partner_id.l10n_py_dnit_responsibility_type_id.code
            domain = [
                *self.env['account.journal']._check_company_domain(rec.company_id),
                ('l10n_latam_use_documents', '=', True),
                ('type', '=', 'sale'),
            ]
            journal = self.env['account.journal']
            msg = False
            if res_code in ['9', '10'] and rec.journal_id.l10n_py_dnit_pos_system not in expo_journals:
                # if partner is foregin and journal is not of expo, we try to change to expo journal
                journal = journal.search(domain + [('l10n_py_dnit_pos_system', 'in', expo_journals)], limit=1)
                msg = _('You are trying to create an invoice for foreign partner but you don\'t have an exportation journal')
            elif res_code not in ['9', '10'] and rec.journal_id.l10n_py_dnit_pos_system in expo_journals:
                # if partner is NOT foregin and journal is for expo, we try to change to local journal
                journal = journal.search(domain + [('l10n_py_dnit_pos_system', 'not in', expo_journals)], limit=1)
                msg = _('You are trying to create an invoice for domestic partner but you don\'t have a domestic market journal')
            if journal:
                rec.journal_id = journal.id
            elif msg:
                # Throw an error to user in order to proper configure the journal for the type of operation
                action = self.env.ref('account.action_account_journal_form')
                raise RedirectWarning(msg, action.id, _('Go to Journals'))

    @api.onchange('l10n_latam_document_type_id', 'l10n_latam_document_number', 'partner_id')
    def _inverse_l10n_latam_document_number(self):
        super()._inverse_l10n_latam_document_number()

        to_review = self.filtered(lambda x: (
            x.journal_id.l10n_py_is_pos
            and x.l10n_latam_document_type_id
            and x.l10n_latam_document_number
            and (x.l10n_latam_manual_document_number or not x.highest_name)
            and x.l10n_latam_document_type_id.country_id.code == 'PY'
        ))
        for rec in to_review:
            number = str(rec.l10n_latam_document_type_id._format_document_number(rec.l10n_latam_document_number))
            current_est = int(number.split("-")[0])
            current_pos = int(number.split("-")[1])
            if current_pos != rec.journal_id.l10n_py_dnit_pos_number or current_est != self.company_id.l10n_py_establecimiento:
                invoices = self.search([('journal_id', '=', rec.journal_id.id), ('posted_before', '=', True)], limit=1)
                # If there is no posted before invoices the user can change the POS number (x.l10n_latam_document_number)
                if (not invoices):
                    rec.journal_id.l10n_py_dnit_pos_number = current_pos
                    rec.journal_id._onchange_set_short_name()
                # If not, avoid that the user change the POS number
                else:
                    raise UserError(_('The document number can not be changed for this journal, you can only modify'
                                      ' the POS number if there is not posted (or posted before) invoices'))



    ########################
    @api.model
    def _l10n_py_get_document_number_parts(self, document_number, document_type_code):
        # import shipments
        if document_type_code in ['66', '67']:
            est = pos = invoice_number = '0'
        else:
            est, pos, invoice_number = document_number.split('-')
        return {'invoice_number': int(invoice_number), 'point_of_sale': int(pos), 'establecimiento': int(est)}

    ########################

    l10n_aipy_inverse_currency_rate = fields.Float(string='Inverse Currency Rate', readonly=True, store=True,
         compute="_compute_inverse_currency_rate", precompute=True, copy=False)

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

