# En tu módulo personalizado, por ejemplo: l10n_sv_haciendaws_fe/models/ir_sequence_ext.py

from odoo import models
from odoo.tools import frozendict
from odoo.exceptions import UserError
from datetime import datetime
import pytz
import logging
from odoo import models, fields


_logger = logging.getLogger(__name__)

class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    def _get_prefix_suffix(self, date=None, date_range=None):
        def _interpolate(s, d):
            return (s % d) if s else ''

        def _interpolation_dict():
            tz_name = self._context.get('tz') or 'UTC'
            now = range_date = effective_date = datetime.now(pytz.timezone(tz_name))
            if date or self._context.get('ir_sequence_date'):
                effective_date = fields.Datetime.from_string(date or self._context.get('ir_sequence_date'))
            if date_range or self._context.get('ir_sequence_date_range'):
                range_date = fields.Datetime.from_string(date_range or self._context.get('ir_sequence_date_range'))

            sequences = {
                'year': '%Y','month': '%m','day': '%d','y': '%y','doy': '%j','woy': '%W',
                'weekday': '%w','h24': '%H','h12': '%I','min': '%M','sec': '%S',
            }
            res = {}
            for key, fmt in sequences.items():
                res[key] = effective_date.strftime(fmt)
                res['range_' + key] = range_date.strftime(fmt)
                res['current_' + key] = now.strftime(fmt)

            # Variables DTE personalizadas
            res['dte'] = self._context.get('dte', '')
            res['estable'] = self._context.get('estable', '')
            res['tipo_dte'] = self._context.get('tipo_dte', '')

            return frozendict(res)

        self.ensure_one()
        d = _interpolation_dict()
        try:
            interpolated_prefix = _interpolate(self.prefix, d)
            interpolated_suffix = _interpolate(self.suffix, d)
        except (ValueError, TypeError, KeyError) as e:
            raise UserError('Secuencia mal definida "%s": %s' % (self.name, str(e)))

        return interpolated_prefix, interpolated_suffix
