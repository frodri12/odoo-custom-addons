from odoo import api, fields, models, _, SUPERUSER_ID

env = api.Environment(cr, SUPERUSER_ID, {})

# Install desired language (e.g., German)
lang_es = env['base.language.install'].create({'lang_ids': 'lang_es_PY', 'overwrite': False})

