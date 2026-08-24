import pyodbc
import xml.etree.ElementTree as ET

# Configuración de conexión a SQL Server
conn_str = (
   r'DRIVER={ODBC Driver 17 for SQL Server};'
   r'SERVER=localhost;'
   r'DATABASE=Test;'
   r'Trusted_Connection=yes;'
)

def importar_albaranes_xml(xml_path, conexion):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        cursor = conexion.cursor()
        for albaran in root.find('Albaranes').findall('Albaran'):
            numero = albaran.findtext('Numero')
            empresa = albaran.findtext('Empresa')
            fecha = albaran.findtext('Fecha')
            tiporec = albaran.findtext('TipoRec')
            alias = albaran.findtext('Alias')
            proveedor = albaran.findtext('Proveedor')
            tiposer = albaran.findtext('TipoSer')
            hora = albaran.findtext('Hora')
            hora_aeropuerto = albaran.findtext('HoraAeropuerto')
            letrero = albaran.findtext('Letrero')
            ttoo = albaran.findtext('TTOO')
            agencia = albaran.findtext('Agencia')
            excursion = albaran.findtext('Excursion')
            guia = albaran.findtext('Guia')
            aeropuerto = albaran.findtext('Aeropuerto')
            vuelo = albaran.findtext('Vuelo')
            observacion = albaran.findtext('Observacion')
            referencia = albaran.findtext('Referencia')
            observacion_chofer = albaran.findtext('ObservacionChofer')
            cursor.execute(
                """
                INSERT INTO albaranes (numero, empresa, fecha, tiporec, alias, proveedor, tiposer, hora, hora_aeropuerto, letrero, ttoo, agencia, excursion, guia, aeropuerto, vuelo, observacion, referencia, observacion_chofer)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                numero, empresa, fecha, tiporec, alias, proveedor, tiposer, hora, hora_aeropuerto, letrero, ttoo, agencia, excursion, guia, aeropuerto, vuelo, observacion, referencia, observacion_chofer
            )
            albaran_id = cursor.execute('SELECT SCOPE_IDENTITY()').fetchone()[0]
            zonas = albaran.find('Zonas')
            if zonas is not None:
                for zona in zonas.findall('Zona'):
                    orden = zona.findtext('Orden')
                    zona_inicio = zona.findtext('ZonaInicio')
                    zona_fin = zona.findtext('ZonaFin')
                    hora_zona = zona.findtext('Hora')
                    personas = zona.findtext('Personas')
                    adultos = zona.findtext('Adultos')
                    ninos = zona.findtext('Niños')
                    bicis = zona.findtext('Bicis')
                    bebes = zona.findtext('Bebes')
                    ninosb = zona.findtext('NiñosB')
                    invitados = zona.findtext('Invitados')
                    cursor.execute(
                        """
                        INSERT INTO zonas (albaran_id, orden, zona_inicio, zona_fin, hora, personas, adultos, ninos, bicis, bebes, ninosb, invitados)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        numero, orden, zona_inicio, zona_fin, hora_zona, personas, adultos, ninos, bicis, bebes, ninosb, invitados
                    )
                    zona_id = cursor.execute('SELECT SCOPE_IDENTITY()').fetchone()[0]
                    hoteles = zona.find('Hoteles')
                    if hoteles is not None:
                        for hotel in hoteles.findall('Hotel'):
                            orden_hotel = hotel.findtext('Orden')
                            establecimiento = hotel.findtext('Establecimiento')
                            #habitacion = hotel.findtext('Habitacion')
                            hora_hotel = hotel.findtext('Hora')
                            personas_hotel = hotel.findtext('Personas')
                            adultos_hotel = hotel.findtext('Adultos')
                            ninos_hotel = hotel.findtext('Niños')
                            bebes_hotel = hotel.findtext('Bebes')
                            bicis_hotel = hotel.findtext('Bicis')
                            agencia_hotel = hotel.findtext('Agencia')
                            lugar_recogida = hotel.findtext('LugarRecogida')
                            observacion_hotel = hotel.findtext('Observacion')
                            cursor.execute(
                                """
                                INSERT INTO hoteles (zona_id, albaran, orden, establecimiento, hora, personas, adultos, ninos, bebes, bicis, agencia, lugar_recogida, observacion)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                zona_id, numero, orden_hotel, establecimiento, hora_hotel, personas_hotel, adultos_hotel, ninos_hotel, bebes_hotel, bicis_hotel, agencia_hotel, lugar_recogida, observacion_hotel
                            )
        conexion.commit()
        print('Importación completa de todos los nodos del XML.')
        cursor.close()
    except Exception as e:
        print('Error al importar XML:', e)

if __name__ == "__main__":
    xml_path = 'albaranes1.xml'  # Cambia por la ruta de tu archivo XML
    try:
        conn = pyodbc.connect(conn_str)
        importar_albaranes_xml(xml_path, conn)
        conn.close()
    except Exception as e:
        print('Error de conexión o inserción:', e)
