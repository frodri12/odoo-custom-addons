# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import stdnum.ar
import re
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):

    _inherit = 'res.partner'

    l10n_py_dnit_responsibility_type_id = fields.Many2one(
        'l10n_py.dnit.responsibility.type', string='DNIT Responsibility Type', index='btree_not_null', help='Defined by DNIT to'
        ' identify the type of responsibilities that a person or a legal entity could have and that impacts in the'
        ' type of operations and requirements they need.')
