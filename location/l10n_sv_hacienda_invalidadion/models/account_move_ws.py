##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import base64
import pyqrcode
import pytz
import logging
import uuid

_logger = logging.getLogger(__name__)

# Zona horaria El Salvador
tz_el_salvador = pytz.timezone('America/El_Salvador')
COD_FE = "01"

class AccountMove(models.Model):
    _inherit = "account.move"

    ######################################### F-ANULACION

    def sit_anulacion_base_map_invoice_info(self):
        _logger.info("SIT [INICIO] sit_anulacion_base_map_invoice_info: self.id=%s, sel.factura_reemplazar=%s", self.id, self.sit_factura_a_reemplazar.company_id)

        invoice_info = {}
        vat = self.sit_factura_a_reemplazar.company_id.vat
        if isinstance(vat, str):
            nit = vat.replace("-", "")
        else:
            nit = None

        invoice_info["nit"] = nit
        invoice_info["activo"] = True
        invoice_info["passwordPri"] = self.company_id.sit_passwordPri

        _logger.info("SIT company_id.vat = %s, passwordPri = %s", nit, self.company_id.sit_passwordPri)

        invoice_info["dteJson"] = self.sit_anulacion_base_map_invoice_info_dtejson()
        _logger.info("SIT sit_anulacion_base_map_invoice_info generado: %s", invoice_info)
        return invoice_info

    def sit_anulacion_base_map_invoice_info_dtejson(self):
        _logger.info("SIT [INICIO] sit_anulacion_base_map_invoice_info_dtejson self=%s", self)
        invoice_info = {}
        invoice_info["identificacion"] = self.sit_invalidacion_base_map_invoice_info_identificacion()
        invoice_info["emisor"] = self.sit_invalidacion_base_map_invoice_info_emisor()
        invoice_info["documento"] = self.sit_invalidacion_base_map_invoice_info_documento()
        invoice_info["motivo"] = self.sit_invalidacion_base_map_invoice_info_motivo()

        _logger.info("SIT [RESULT] DTE JSON anulacion generado: %s", invoice_info)
        return invoice_info

    def sit_invalidacion_base_map_invoice_info_identificacion(self):
        _logger.info("SIT [INICIO] Identificación para anulación: self.id=%s", self.id)

        invoice_info = {}
        invoice_info["version"] = 2
        ambiente = "00" if self._compute_validation_type_2() == 'homologation' else "01"
        invoice_info["ambiente"] = ambiente

        if self.sit_codigoGeneracion_invalidacion:
            invoice_info["codigoGeneracion"] = self.sit_codigoGeneracion_invalidacion
        else:
            invoice_info["codigoGeneracion"] = self.sit_generar_uuid()  # company_id.sit_uuid.upper()

        import datetime, pytz, os
        os.environ["TZ"] = "America/El_Salvador"
        fecha_actual = datetime.datetime.now(pytz.timezone("America/El_Salvador"))
        _logger.info("Fecha en sesion 1: %s", fecha_actual)
        if self.sit_fec_hor_Anula:
            FechaHoraAnulacion = fecha_actual#self.sit_fec_hor_Anula
            _logger.info("SIT campo fecha anulacion: =%s", FechaHoraAnulacion)
        else:
            FechaHoraAnulacion = fecha_actual#datetime.now() - timedelta(hours=6)
            _logger.info("SIT fecha anulacion: =%s", FechaHoraAnulacion)

        invoice_info["fecAnula"] = FechaHoraAnulacion.strftime('%Y-%m-%d')
        invoice_info["horAnula"] = FechaHoraAnulacion.strftime('%H:%M:%S')

        _logger.info("SIT Identificación: ambiente=%s, codigoGeneracion=%s, fec=%s, hor=%s",
                     ambiente, invoice_info["codigoGeneracion"],
                     invoice_info["fecAnula"], invoice_info["horAnula"])
        return invoice_info


    def sit_invalidacion_base_map_invoice_info_emisor(self):
        _logger.info("SIT [INICIO] Emisor: self.id=%s", self.id)

        invoice_info = {}
        nit = self.company_id.vat.replace("-", "")
        invoice_info.update({
            "nit": nit,
            "nombre": self.company_id.name,
            "tipoEstablecimiento": self.company_id.tipoEstablecimiento.codigo,
            "nomEstablecimiento": self.company_id.tipoEstablecimiento.valores,
            "codEstableMH": self.journal_id.sit_codestable,
            "codEstable": self.journal_id.sit_codestable,
            "codPuntoVentaMH": self.journal_id.sit_codpuntoventa,
            "codPuntoVenta": self.journal_id.sit_codpuntoventa,
            "telefono": self.company_id.phone or None,
            "correo": self.company_id.email
        })

        _logger.info("SIT Emisor: %s", invoice_info)
        return invoice_info

    tz_el_salvador = pytz.timezone('America/El_Salvador')

    def sit_invalidacion_base_map_invoice_info_documento(self):
        _logger.info("SIT [INICIO] Documento: self.id=%s", self.id)

        invoice_info = {
            "tipoDte": self.journal_id.sit_tipo_documento.codigo,
            "codigoGeneracion": self.hacienda_codigoGeneracion_identificacion,
            "selloRecibido": self.hacienda_selloRecibido,
            "numeroControl": self.name,
            "montoIva": round(self.amount_total, 2),
        }

        fecha_facturacion = (datetime.strptime(self.fecha_facturacion_hacienda, '%Y-%m-%d')
                             if isinstance(self.fecha_facturacion_hacienda, str)
                             else self.fecha_facturacion_hacienda)

        if isinstance(fecha_facturacion, datetime):
            adjusted_fecha = fecha_facturacion - timedelta(hours=6)
        else:
            _logger.error("fecha_facturacion no es datetime, es: %s", type(fecha_facturacion))
            raise ValueError("fecha_facturacion no es un datetime válido")
        invoice_info["fecEmi"] = adjusted_fecha.strftime('%Y-%m-%d')
        _logger.info("SIT Codigo generacion R: self.id=%s", self.sit_codigoGeneracionR)
        if self.sit_tipoAnulacion == '2':
            self.sit_codigoGeneracionR = None

        invoice_info["codigoGeneracionR"] = self.sit_codigoGeneracionR or None

        if self.journal_id.sit_tipo_documento.codigo == COD_FE:
            nit = self.partner_id.dui.replace("-", "") if isinstance(self.partner_id.dui,str) and self.partner_id.dui.strip() else None
        else:
            nit = self.partner_id.fax.replace("-", "") if isinstance(self.partner_id.fax,str) and self.partner_id.fax.strip() else None

        # --- Manejo seguro de fecha de facturación Hacienda ---
        raw_date = self.fecha_facturacion_hacienda
        if not raw_date:
            # Si no hay fecha (draft), usamos ahora en El Salvador
            FechaEmi = datetime.now(tz_el_salvador)
        elif isinstance(raw_date, str):
            # Intentamos parsearla
            try:
                # ISO o con zona
                FechaEmi = datetime.fromisoformat(raw_date)
            except ValueError:
                FechaEmi = datetime.strptime(raw_date, '%Y-%m-%d %H:%M:%S')
            # Aseguramos tz
            if FechaEmi.tzinfo is None:
                FechaEmi = tz_el_salvador.localize(FechaEmi)
        else:
            # Ya es datetime
            FechaEmi = raw_date
            if FechaEmi.tzinfo is None:
                FechaEmi = tz_el_salvador.localize(FechaEmi)

        # --- Manejo seguro de fecha de facturación Hacienda ---
        raw_date = self.fecha_facturacion_hacienda
        if not raw_date:
            # Si no hay fecha (draft), usamos ahora en El Salvador
            FechaEmi = datetime.now(tz_el_salvador)
        elif isinstance(raw_date, str):
            # Intentamos parsearla
            try:
                # ISO o con zona
                FechaEmi = datetime.fromisoformat(raw_date)
            except ValueError:
                FechaEmi = datetime.strptime(raw_date, '%Y-%m-%d %H:%M:%S')
            # Aseguramos tz
            if FechaEmi.tzinfo is None:
                FechaEmi = tz_el_salvador.localize(FechaEmi)
        else:
            # Ya es datetime
            FechaEmi = raw_date
            if FechaEmi.tzinfo is None:
                FechaEmi = tz_el_salvador.localize(FechaEmi)

        # Ajuste a UTC-6 según spec
        adjusted = FechaEmi - timedelta(hours=6)
        invoice_info["fecEmi"] = adjusted.strftime('%Y-%m-%d')

        invoice_info["codigoGeneracionR"] = None  # ó self.sit_codigoGeneracionR

        # Datos del receptor
        dui = self.partner_id.dui or ''
        nit = dui.replace("-", "") if isinstance(dui, str) else None

        if dui:
            nit = dui.replace("-", "")
        else:
            nit_partner = self.partner_id.fax or ''
            nit = nit_partner.replace("-", "") if isinstance(nit_partner, str) else ''

        invoice_info["numDocumento"] = nit
        invoice_info["tipoDocumento"] = (
            self.partner_id.l10n_latam_identification_type_id.codigo
            if nit and self.partner_id.l10n_latam_identification_type_id
            else None
        )
        invoice_info["nombre"] = self.partner_id.name or None
        invoice_info["telefono"] = self.partner_id.phone or None
        invoice_info["correo"] = self.partner_id.email or None

        _logger.info("SIT Documento: %s", invoice_info)
        return invoice_info

    def sit_invalidacion_base_map_invoice_info_motivo(self):
        _logger.info("SIT [INICIO] Motivo anulación: self.id=%s", self.id)

        _logger.info("SIT Empresa-Receptor: self.id=%s", self.partner_id)
        if self.journal_id.sit_tipo_documento.codigo == COD_FE:
            dui = self.partner_id.dui
        else:
            dui = self.partner_id.fax
        if not dui:
            raise UserError(
                _("No se encontró el DUI del responsable en la empresa. Por favor verifique el campo DUI en el partner de la compañía."))

        #nit = self.company_id.partner_id.dui.replace("-", "")
        nit = dui.replace("-", "")
        invoice_info = {
            "tipoAnulacion": int(self.sit_tipoAnulacion),
            "motivoAnulacion": self.sit_motivoAnulacion if self.sit_tipoAnulacion == 3 else None,
            "nombreResponsable": self.partner_id.name,
            "tipDocResponsable": "36",
            "numDocResponsable": nit,
            "nombreSolicita": self.partner_id.name,
            "tipDocSolicita": "36",
            "numDocSolicita": nit
        }

        if not invoice_info["motivoAnulacion"]:
            invoice_info["motivoAnulacion"] = None

        _logger.info("SIT Motivo anulación: %s", invoice_info)
        return invoice_info

    def _compute_total_iva(self):
        IVA = 0.0
        for linea in self.invoice_line_ids:
            vat_taxes = linea.tax_ids.compute_all(
                linea.price_unit, self.currency_id,
                linea.quantity, product=linea.product_id, partner=self.partner_id,
            )
            if vat_taxes['taxes']:
                tax = vat_taxes['taxes'][0]
                _logger.info("SIT IVA linea: unit=%s, subtotal=%s, total=%s, discount=%s, amount=%s",
                             linea.price_unit, linea.price_subtotal, linea.price_total, linea.discount, tax['amount'])
                IVA += tax['amount']

        IVA = round(IVA, 6)
        _logger.info("SIT _compute_total_iva TOTAL=%s", IVA)
        return IVA

    def sit_obtener_payload_anulacion_dte_info(self, ambiente, doc_firmado):
        _logger.info("SIT [INICIO] Payload envío DTE anulado: self.id=%s", self.id)

        nit = self.company_id.vat.replace("-", "")
        invoice_info = {
            "ambiente": ambiente,
            "idEnvio": 1,
            "version": 2,
            "documento": doc_firmado
        }

        _logger.info("SIT Payload generado para envío: %s", invoice_info)
        return invoice_info

    def sit_generar_uuid(self):
        uuid_str = str(uuid.uuid4()).upper()
        _logger.info("SIT UUID generado: %s", uuid_str)
        return uuid_str

    ######################################### F-ANULACION
