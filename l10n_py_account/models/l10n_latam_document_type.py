# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, api, fields, _
from odoo.exceptions import UserError


class L10nLatamDocumentType(models.Model):

    _inherit = 'l10n_latam.document.type'

    l10n_py_letter = fields.Selection(
        selection='_get_l10n_py_letters',
        string='Letters',
        help='Letters defined by the DNIT that can be used to identify the'
        ' documents presented to the government and that depends on the'
        ' operation type, the responsibility of both the issuer and the'
        ' receptor of the document')
    purchase_aliquots = fields.Selection(
        [('not_zero', 'Not Zero'), ('zero', 'Zero')], help='Raise an error if a vendor bill is miss encoded. "Not Zero"'
        ' means the VAT taxes are required for the invoices related to this document type, and those with "Zero" means'
        ' that only "VAT Not Applicable" tax is allowed.')

    def _get_l10n_py_letters(self):
        """ Return the list of values of the selection field. """
        return [
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('E', 'E'),
            ('M', 'M'),
            ('T', 'T'),
            ('R', 'R'),
            ('X', 'X'),
            ('I', 'I'),  # used for mapping of imports
        ]

    def _format_document_number(self, document_number):
        """ Make validation of Import Dispatch Number
          * making validations on the document_number. If it is wrong it should raise an exception
          * format the document_number against a pattern and return it
        """
        self.ensure_one()
        if self.country_id.code != "PY":
            return super()._format_document_number(document_number)

        if not document_number:
            return False

        if not self.code:
            return document_number

        # Import Dispatch Number Validator
        if self.code in ['66', '67']:
            if len(document_number) != 16:
                raise UserError(
                    _(
                        "%(value)s is not a valid value for %(field)s.\nThe number of import Dispatch must be 16 characters.",
                        value=document_number,
                        field=self.name,
                    ),
                )
            return document_number

        # Invoice Number Validator (For Eg: 123-123)
        failed = False
        args = document_number.split('-')
        if len(args) != 3:
            failed = True
        else:
            exp, pos, number = args
            if len(exp) > 3 or not exp.isdigit():
                failed = True
            elif len(pos) > 3 or not pos.isdigit():
                failed = True
            elif len(number) > 7 or not number.isdigit():
                failed = True
            document_number = '{:>03s}-{:>03s}-{:>07s}'.format(exp, pos, number)
        if failed:
            raise UserError(
                _(
                    "%(value)s is not a valid value for %(field)s.\nThe document number must be entered with a dash (-) and a maximum of 3 characters for the first part, 3 characters for the second part and 7 for the third. The following are examples of valid numbers:\n* 1-1-1\n* 001-001-0000001",
                    value=document_number,
                    field=self.name,
                ),
            )

        return document_number

    @api.depends('code')
    def _compute_display_name(self):
        for rec in self:
            name = rec.name
            if rec.code:
                name = f'{name}'
            rec.display_name = name

