# -*- coding: utf-8 -*-

from odoo import models, fields

class L10nLatamIdentificationType(models.Model):

    _inherit = "l10n_latam.identification.type"

    l10n_aipy_dnit_code = fields.Char("DNIT identification Code")
