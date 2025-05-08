# Original script: https://github.com/Axiacore/number-to-letters

# Changes from the original: just adapted to python 3.

# The MIT License (MIT)

# Copyright (c) 2014 AxiaCore

UNIDADES = (
    '',
    'UN ',
    'DOS ',
    'TRES ',
    'CUATRO ',
    'CINCO ',
    'SEIS ',
    'SIETE ',
    'OCHO ',
    'NUEVE ',
    'DIEZ ',
    'ONCE ',
    'DOCE ',
    'TRECE ',
    'CATORCE ',
    'QUINCE ',
    'DIECISEIS ',
    'DIECISIETE ',
    'DIECIOCHO ',
    'DIECINUEVE ',
    'VEINTE '
)

DECENAS = (
    'VEINTI',
    'TREINTA ',
    'CUARENTA ',
    'CINCUENTA ',
    'SESENTA ',
    'SETENTA ',
    'OCHENTA ',
    'NOVENTA ',
    'CIEN '
)

CENTENAS = (
    'CIENTO ',
    'DOSCIENTOS ',
    'TRESCIENTOS ',
    'CUATROCIENTOS ',
    'QUINIENTOS ',
    'SEISCIENTOS ',
    'SETECIENTOS ',
    'OCHOCIENTOS ',
    'NOVECIENTOS '
)

UNITS = (
    ('', ''),
    ('MIL ', 'MIL '),
    ('MILLON ', 'MILLONES '),
    ('MIL MILLONES ', 'MIL MILLONES '),
    ('BILLON ', 'BILLONES '),
    ('MIL BILLONES ', 'MIL BILLONES '),
    ('TRILLON ', 'TRILLONES '),
    ('MIL TRILLONES', 'MIL TRILLONES'),
    ('CUATRILLON', 'CUATRILLONES'),
    ('MIL CUATRILLONES', 'MIL CUATRILLONES'),
    ('QUINTILLON', 'QUINTILLONES'),
    ('MIL QUINTILLONES', 'MIL QUINTILLONES'),
    ('SEXTILLON', 'SEXTILLONES'),
    ('MIL SEXTILLONES', 'MIL SEXTILLONES'),
    ('SEPTILLON', 'SEPTILLONES'),
    ('MIL SEPTILLONES', 'MIL SEPTILLONES'),
    ('OCTILLON', 'OCTILLONES'),
    ('MIL OCTILLONES', 'MIL OCTILLONES'),
    ('NONILLON', 'NONILLONES'),
    ('MIL NONILLONES', 'MIL NONILLONES'),
    ('DECILLON', 'DECILLONES'),
    ('MIL DECILLONES', 'MIL DECILLONES'),
    ('UNDECILLON', 'UNDECILLONES'),
    ('MIL UNDECILLONES', 'MIL UNDECILLONES'),
    ('DUODECILLON', 'DUODECILLONES'),
    ('MIL DUODECILLONES', 'MIL DUODECILLONES'),
)

MONEDAS = (
    {'country': 'Colombia', 'currency': 'COP', 'singular': 'PESO COLOMBIANO', 'plural': 'PESOS COLOMBIANOS',
     'symbol': '$'},
    {'country': 'Estados Unidos', 'currency': 'USD', 'singular': 'DÓLAR', 'plural': 'DÓLARES', 'symbol': 'US$',
     'decimalsingular': 'Centavo', 'decimalplural':'Centavos'},
    {'country': 'Europa', 'currency': 'EUR', 'singular': 'EURO', 'plural': 'EUROS', 'symbol': '€',
     'decimalsingular': 'Céntimo', 'decimalplural': 'Céntimos'},
    {'country': 'México', 'currency': 'MXN', 'singular': 'PESO MEXICANO', 'plural': 'PESOS MEXICANOS', 'symbol': '$'},
    {'country': 'Perú', 'currency': 'PEN', 'singular': 'NUEVO SOL', 'plural': 'NUEVOS SOLES', 'symbol': 'S/.'},
    {'country': 'Reino Unido', 'currency': 'GBP', 'singular': 'LIBRA', 'plural': 'LIBRAS', 'symbol': '£'}
)


# Para definir la moneda me estoy basando en los código que establece el ISO 4217
# Decidí poner las variables en inglés, porque es más sencillo de ubicarlas sin importar el país
# Si, ya sé que Europa no es un país, pero no se me ocurrió un nombre mejor para la clave.


def hundreds_word(number):
    """Converts a positive number less than a thousand (1000) to words in Spanish
    Args:
        number (int): A positive number less than 1000
    Returns:
        A string in Spanish with first letters capitalized representing the number in letters
    Examples:
        >>> to_word(123)
        'Ciento Ventitres'
    """
    converted = ''
    if not (0 < number < 1000):
        return 'No es posible convertir el numero a letras'

    number_str = str(number).zfill(9)
    cientos = number_str[6:]

    if (cientos):
        if (cientos == '001'):
            converted += 'UN '
        elif (int(cientos) > 0):
            converted += '%s ' % __convert_group(cientos)

    return converted.title().strip()


def __convert_group(n):
    """Turn each group of numbers into letters"""
    output = ''

    if (n == '100'):
        output = "CIEN "
    elif (n[0] != '0'):
        output = CENTENAS[int(n[0]) - 1]

    k = int(n[1:])
    if (k <= 20):
        output += UNIDADES[k]
    else:
        if ((k > 30) & (n[2] != '0')):
            output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
        else:
            output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])

    return output


def to_word(number, mi_moneda='USD'):
    if mi_moneda is not None:
        try:
            moneda = filter(lambda x: x['currency'] == mi_moneda, MONEDAS).__next__()
            if int(number) == 1:
                entero = moneda['singular']
                fraccion = moneda['decimalsingular']
            else:
                entero = moneda['plural']
                fraccion = moneda['decimalplural']
        except:
            return "Tipo de moneda inválida"
    else:
        entero = ""
        fraccion = ""

    human_readable = []
    num_decimals = '{:,.2f}'.format(round(number, 2)).split('.')
    num_units = num_decimals[0].split(',')
    num_decimals = num_decimals[1].split(',')

    for i, n in enumerate(num_units):
        if int(n) != 0:
            words = hundreds_word(int(n))
            units = UNITS[len(num_units) - i - 1][0 if int(n) == 1 else 1]
            human_readable.append([words, units])

    human_readable = [item for sublist in human_readable for item in sublist]
    human_readable.append(entero)
    
    # Procesa la parte decimal en el formato deseado
    decimal_str = f"{int(num_decimals[0]):02d}/100"

    sentence = ' '.join(human_readable).replace('  ', ' ').title().strip()
    if sentence[0:len('un mil')] == 'Un Mil':
        sentence = 'Mil' + sentence[len('Un Mil'):]

    # Agrega la parte decimal en el formato deseado
    sentence = sentence + f' Con {decimal_str}'

    return sentence
