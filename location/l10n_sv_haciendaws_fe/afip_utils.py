# from pysimplesoap.client import SimpleXMLElement
#import xml.etree.ElementTree as ET

def _get_response_info(xml_response):
    return SimpleXMLElement(xml_response)


def get_invoice_number_from_response(xml_response, afip_ws='wsfe'):
    if not xml_response:
        return  False
    try:
        xml = _get_response_info(xml_response)
        return int(xml('CbteDesde'))
       
    except:
        return  False


def check_invoice_number(account_move):
    pass
