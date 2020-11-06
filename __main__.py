from math import isfinite
import threading
import time
import math
import copy
from operator import itemgetter, attrgetter

c = threading.Condition()

flag = 0  # shared between Thread_A and Thread_B


class Localizacion:
    """
    Una clase utilizada para representar una Localización

    ...

    Atributos
    ----------
    nombre : str
        nombre de la localización
    x : int
        coordenada x de la ubicación de la localización
    y : int
        coordenada y de la ubicación de la localización

    """

    def __init__(self, nombre, x, y):
        self.nombre = nombre
        self.x = x
        self.y = y

    def __repr__(self):
        return repr(self.nombre)


class Estacion(Localizacion):
    """
    Una clase utilizada para representar una Estación (extiende Localización)

    ...

    Atributos
    ----------
    numeroPasajeros : int
        número de pasajeros en la localización

    """

    def __init__(self, numeroPasajeros, *args, **kw):
        super().__init__(*args, **kw)
        self.numeroPasajeros = numeroPasajeros
        self.vecesVisitado = 0
        self.distancia = 0
        self.tiempo = 0



class Conductor:
    """
    Una clase utilizada para representar un Conductor

    ...

    Atributos
    ----------
    nombre : str
        nombre del conductor
    horaInicio : int
        hora de inicio de trabajo
    horasTrabajo : float
        cantidad de horas trabajando
    llegoAMaxHoras: bool
        representa si ya llegó a la máxima cantidad de horas
    activo : bool
        representa si actualmente el conductor está trabajando
    maxHorasTrabajo : int
        máxima cantidad de horas que puede trabajar el conductor (por defecto 10)
    tiempoEsperaMantenimiento : float
        cantidad de horas que espera un conductor mientras un bus está en mantenimiento

    """

    def __init__(self, nombre, horaInicio):
        self.nombre = nombre
        self.horaInicio = horaInicio
        self.horasTrabajo = 0
        self.activo = False
        self.maxHorasTrabajo = 10
        self.tiempoEsperaMantenimiento = 50 / 60
        self.terminoDia = False


    def __repr__(self):
        return repr((self.nombre, "Horas de trabajo", self.horasTrabajo))


# Variables globales
probabilidadDeBajarse = [0.2, 0.5, 0.3]
estacionesGlobales = [Estacion(nombre="Estación 1", x=1, y=4, numeroPasajeros=10),
                      Estacion(nombre="Estación 2", x=1,
                               y=7, numeroPasajeros=6),
                      Estacion(nombre="Estación 3", x=2,
                               y=9, numeroPasajeros=7),
                      Estacion(nombre="Estación 4", x=6,
                               y=-1, numeroPasajeros=5),
                      Estacion(nombre="Estación 5", x=4,
                               y=-5, numeroPasajeros=5),
                      Estacion(nombre="Estación 6", x=4,
                               y=1, numeroPasajeros=8),
                      Estacion(nombre="Estación 7", x=-6,
                               y=-4, numeroPasajeros=10),
                      Estacion(nombre="Estación 8", x=7,
                               y=9, numeroPasajeros=10),
                      Estacion(nombre="Estación 9", x=2,
                               y=10, numeroPasajeros=6),
                      Estacion(nombre="Estación 10", x=6, y=6, numeroPasajeros=8)]
conductoresGlobales = []
busesGlobales = []
for x in range(9):
    conductoresGlobales.append(Conductor(f"Conductor {x}", 6))


estacionesGlobalesDiccionario = {}
for estacion in estacionesGlobales:
    estacionesGlobalesDiccionario.setdefault(
        estacion.nombre, []).append(estacion)
Mantenimiento = Localizacion(nombre="Mantenimiento", x=-12, y=-10)
Estacionamiento = Localizacion(nombre="Estacionamiento", x=15, y=9)


class Bus(threading.Thread):
    """
    Una clase utilizada para representar un bus

    ...

    Atributos
    ----------
    nombre : str
        nombre del bus
    conductor: Conductor
        conductor conduciendo el bus
    cantidadPasajeros: int
        cantidad de pasajeros actualmente en el bus
    haSidoDesinfectado: bool
        booleano para representar si el bus ya fue desinfectado
    estacionActual: Localización
        ubicación actual del bus
    listaEstaciones: list[Estaciones]
        estaciones existentes para el bus, utilizado para el cálculo de rutas
    ruta: list[Localizaciones]
        ruta actual del bus
    maxHorasEnRuta: int
        máxima cantidad de horas en ruta, por defecto 5.
    cantidadPasajerosABajarse: list[int]
        cantidad de pasajeros a bajarse en esta estación, en la siguiente o en la próxima a esa.
    velocidadEnKm: int
        velocidad del bus en kilómetros, por defecto 30.
    maxPasajeros: int
        máxima cantidad de pasajeros en el bus, por defecto 16.
    consumoGasolina: float
        consumo de gasolina (galón/km) del bus.
    costoGalon:
        costo del galón de gasolina.
    kilométrosRecorridos:
        cantidad de kilométros recorridos.
    distanciaEnKmAEstacionamiento: float
        cantidad de km desde Mantenimiento a Estacionamiento
    tiempoEnHorasAEstacionamiento: float
        tiempo en horas desde Mantenimiento a Estacionamiento
    llegoAMaxHoras: bool
        representa si llegó al máximo número de horas

    """

    def __init__(self, nombre, conductor, inicio_hora_ruta):
        threading.Thread.__init__(self)
        self.threadingLock = threading.Lock()
        self.nombre = nombre
        conductor.activo = True
        conductor.horaInicio = inicio_hora_ruta if conductor.horasTrabajo == 0 else conductor.horaInicio
        self.conductor = conductor
        self.cantidadPasajeros = 0
        self.estacionActual = Estacionamiento
        self.listaEstaciones = copy.deepcopy(estacionesGlobales)
        self.ruta = [Estacionamiento]
        self.activo = False
        self.cantidadRutasHechas = 0
        self.inicioHoraRuta = inicio_hora_ruta
        self.finHoraRuta = 0
        self.horasEnRuta = 0
        self.horasTotales = 0
        self.maxHorasEnRuta = 5
        self.pasajerosABajarse = []
        self.velocidadEnKm = 30
        self.maxPasajeros = 16
        self.consumoGasolina = 0.09
        self.costoGalon = 8700
        self.kilometrosRecorridos = 0
        self.distanciaEnKmAEstacionamiento = 0
        self.tiempoEnHorasAEstacionamiento = 0
        self.calcularDistanciaYTiempoAEstacionamiento()


    def calcularDistanciaYTiempoAEstacionamiento(self):
        """Calcula la distancia y tiempo desde Mantenimiento a Estacionamiento.

        """

        self.distanciaEnKmAEstacionamiento, self.tiempoEnHorasAEstacionamiento = self.calcular_distancia_tiempo(
            Mantenimiento, Estacionamiento)

    def calcularDistanciasAEstaciones(self):
        """Calcula la distancia desde la estación actual a todas las demás estaciones.

        """
        c.acquire()
        global estacionesGlobalesDiccionario
        for estacionPosible in self.listaEstaciones:
            estacionViable = self.definir_estacion_posible(estacionPosible)
            if estacionViable:
                distanciaEnKm, tiempoEnHoras = self.calcular_distancia_tiempo(
                    self.estacionActual,
                    estacionPosible
                )
                estacionPosible.tiempo = tiempoEnHoras
                estacionPosible.distancia = distanciaEnKm

            else:
                estacionPosible.tiempo = math.inf
                estacionPosible.distancia = math.inf
        self.listaEstaciones = sorted(self.listaEstaciones, key=attrgetter('distancia'))
        c.release()

    def definir_estacion_posible(self, estacion_posible):
        """Define si ir a una estación es viable o no.
        :param Estacion estacion_posible: Estación que se desea evaluar
        :return: Si es posible ir a la estación o no
        :rtype: bool

        """

        distanciaEnKm, tiempoEnHoras = self.calcular_distancia_tiempo(
            self.estacionActual,
            estacion_posible
        )
        distanciaEnKmAMantenimiento, tiempoEnHorasAMantenimiento = self.calcular_distancia_tiempo(
            estacion_posible,
            Mantenimiento
        )

        tiempoAdicional = tiempoEnHorasAMantenimiento + self.tiempoEnHorasAEstacionamiento
        c.acquire()
        estacionGlobal = estacionesGlobalesDiccionario[estacion_posible.nombre][0]
        pasajerosABajarse = self.pasajerosABajarse[0] if len(self.pasajerosABajarse) > 0 else 0
        cantidadHorasConductorSiVa = self.conductor.horasTrabajo + self.conductor.tiempoEsperaMantenimiento + \
                                     tiempoEnHoras + tiempoAdicional
        cantidadHorasBusSiVa = self.horasEnRuta + tiempoEnHoras + tiempoAdicional
        cantidadPasajerosSiVa = self.cantidadPasajeros + estacion_posible.numeroPasajeros - pasajerosABajarse

        if cantidadHorasBusSiVa > self.maxHorasEnRuta or cantidadPasajerosSiVa > self.maxPasajeros:
            estacion_posible.busPuedeIr = False
            estacion_posible.razonBusNoPuedeIr = "horas" if cantidadHorasBusSiVa > self.maxHorasEnRuta else "pasajeros"
        else:
            estacion_posible.busPuedeIr = True
            estacion_posible.razonBusNoPuedeIr = ""

        if cantidadHorasConductorSiVa > self.conductor.maxHorasTrabajo:
            estacion_posible.conductorPuedeIr = False
            estacion_posible.razonConductorNoPuedeIr = "horas"
        else:
            estacion_posible.conductorPuedeIr = True
            estacion_posible.razonConductorNoPuedeIr = ""

        if estacionGlobal.vecesVisitado >= 6:
            estacion_posible.conductorPuedeIr = False
            estacion_posible.busPuedeIr = False
            estacion_posible.razonConductorNoPuedeIr = "visitado"
            estacion_posible.razonBusNoPuedeIr = "visitado"

        if self.cantidadRutasHechas >= 3:
            estacion_posible.busPuedeIr = False
            estacion_posible.razonBusNoPuedeIr = "cantidad rutas"

        result = not((distanciaEnKm == 0 or
                   cantidadHorasConductorSiVa > self.conductor.maxHorasTrabajo or
                   cantidadHorasBusSiVa > self.maxHorasEnRuta or
                   cantidadPasajerosSiVa > self.maxPasajeros or
                   estacionGlobal.vecesVisitado >= 6 or
                   self.cantidadRutasHechas >= 3))
        c.release()
        return result

    def validar_opciones(self):
        return self.listaEstaciones[0].tiempo != math.inf

    def agregar_estacion(self):
        c.acquire()
        global estacionesGlobalesDiccionario
        estacionVisitada = self.listaEstaciones[0]
        estacionVisitada.vecesVisitado += 1
        estacionesGlobalesDiccionario[estacionVisitada.nombre][0].vecesVisitado += 1

        # Se bajan los pasajeros a bajarse
        if len(self.pasajerosABajarse) > 0:
            self.cantidadPasajeros = self.cantidadPasajeros - self.pasajerosABajarse.pop(0)
        # Se suben los pasajeros de la estación
        self.cantidadPasajeros = self.cantidadPasajeros + estacionVisitada.numeroPasajeros
        # Se calcula cuándo se bajarán los pasajeros
        self.calcular_pasajeros_a_bajarse(estacionVisitada)
        # Se suma el tiempo en ruta
        self.horasEnRuta = self.horasEnRuta + estacionVisitada.tiempo
        # Se cambia la estación actual
        self.estacionActual = self.listaEstaciones[0]
        # Se agrega la estación a la ruta
        self.ruta.append(self.listaEstaciones[0])
        # Se actualiza la cantidad de kilómetros recorridos
        self.kilometrosRecorridos = self.kilometrosRecorridos + estacionVisitada.distancia
        # Se actualiza la cantidad de horas trabajadas
        self.conductor.horasTrabajo = self.conductor.horasTrabajo + estacionVisitada.tiempo
        # Se recalcula las estaciones posibles desde la estación actual
        self.calcularDistanciasAEstaciones()
        c.release()

    def calcular_distancia_tiempo(self, inicio, fin):
        """Calcula la distancia euclidiana desde un punto inicial a un punto final

        :param Localizacion inicio: Punto inicial de la ruta
        :param Localizacion fin: Punto final de la ruta
        :return: lista con la distancia en kilómetros y el tiempo en horas para ir al punto fin desde inicio
        :rtype: list
        """
        distanciaEnKm = math.sqrt(math.pow(fin.x - inicio.x, 2) + math.pow(fin.y - inicio.y, 2))
        tiempoEnHoras = distanciaEnKm / self.velocidadEnKm
        return [distanciaEnKm, tiempoEnHoras]

    def calcular_pasajeros_a_bajarse(self, estacion):
        """Calcula la cantidad de pasajeros a bajarse al añadir una estación a la ruta

        :param Estacion estacion: Estación a la cuál se le calculará cuándo se bajarán sus pasajeros
        """
        global probabilidadDeBajarse
        # Si el arreglo está vacío, entonces se bajarán los de la nueva estación como dice el enunciado
        if len(self.pasajerosABajarse) == 0:
            self.pasajerosABajarse = [
                estacion.numeroPasajeros * probabilidadDeBajarse[0],
                estacion.numeroPasajeros * probabilidadDeBajarse[1],
                estacion.numeroPasajeros * probabilidadDeBajarse[2],
            ]
        # Si el arreglo tiene tamaño 2, entonces se actualiza los que se bajarán en las próximas 2 estaciones
        # y los demás son añadidos con base en lo del enunciado
        elif len(self.pasajerosABajarse) == 2:
            self.pasajerosABajarse[0] = self.pasajerosABajarse[0] + estacion.numeroPasajeros * probabilidadDeBajarse[0]
            self.pasajerosABajarse[1] = self.pasajerosABajarse[1] + estacion.numeroPasajeros * probabilidadDeBajarse[1]
            self.pasajerosABajarse.append(estacion.numeroPasajeros * probabilidadDeBajarse[2])

        # Se redondea la cantidad de pasajeros
        self.pasajerosABajarse = [round(numPasajeros)
                                  for numPasajeros in self.pasajerosABajarse]

    def finalizar_ruta(self):
        """Finaliza la ruta del bus llevándolo a mantenimiento y el estacionamiento.
        """
        distanciaAMantenimiento, tiempoAMantenimiento = self.calcular_distancia_tiempo(self.estacionActual,
                                                                                       Mantenimiento)
        c.acquire()
        print(f"_____________RESUMEN DE {self.nombre} - RUTA {self.cantidadRutasHechas + 1}______________")
        # Se bajan los pasajeros
        print("Ultima estación:", self.estacionActual)
        print("Cantidad pasajeros:", self.cantidadPasajeros)
        self.cantidadPasajeros = 0
        self.pasajerosABajarse = []

        # Se dirige a Mantenimiento
        self.horasEnRuta = self.horasEnRuta + tiempoAMantenimiento
        self.estacionActual = Mantenimiento
        self.ruta.append(Mantenimiento)
        self.kilometrosRecorridos = self.kilometrosRecorridos + distanciaAMantenimiento
        # El conductor espera el mantenimiento
        self.conductor.horasTrabajo = self.conductor.horasTrabajo + tiempoAMantenimiento + \
                                      self.conductor.tiempoEsperaMantenimiento

        # Se dirige a Estacionamiento
        self.horasEnRuta = self.horasEnRuta + self.tiempoEnHorasAEstacionamiento
        self.finHoraRuta = self.inicioHoraRuta + self.horasEnRuta + self.conductor.tiempoEsperaMantenimiento
        self.estacionActual = Estacionamiento
        self.ruta.append(Estacionamiento)
        self.kilometrosRecorridos = self.kilometrosRecorridos + self.distanciaEnKmAEstacionamiento
        self.conductor.horasTrabajo = self.conductor.horasTrabajo + self.tiempoEnHorasAEstacionamiento

        # Imprime resultados
        print("Ruta ", self.ruta)
        print("Hora inicio: ", self.inicioHoraRuta)
        print("Hora fin: ", self.finHoraRuta)
        print("Horas: ", self.horasEnRuta)
        print("Detalles conductor ", self.conductor)
        print("Kilómetros recorridos: ", self.kilometrosRecorridos)
        print("Costo transporte: ", self.kilometrosRecorridos *
              self.consumoGasolina * self.costoGalon)

        print(f"_____________FIN DE {self.nombre} - RUTA {self.cantidadRutasHechas + 1}______________")

        self.cantidadRutasHechas = self.cantidadRutasHechas + 1

        # Se encuentra listo para empezar de nuevo
        self.horasEnRuta = 0
        self.kilometrosRecorridos = 0
        self.inicioHoraRuta = self.finHoraRuta
        self.ruta = [Estacionamiento]
        self.calcularDistanciasAEstaciones()
        c.release()

    def asignar_conductor(self):
        c.acquire()
        global conductoresGlobales
        listaDisponibles = list(filter(
            lambda x: not x.terminoDia and not x.activo, conductoresGlobales))
        print("Lista disponibles: ", listaDisponibles)
        if len(listaDisponibles) == 0:
            c.release()
            return False
        else:
            listaDisponibles = sorted(
                listaDisponibles, key=attrgetter('horasTrabajo'), reverse=True)
            self.conductor = listaDisponibles[0]
            c.release()
            return True

    def debe_cambiar_conductor(self):
        conductorTerminoDia = len(list(filter(lambda x: x.conductorPuedeIr, self.listaEstaciones))) == 0
        self.conductor.terminoDia = conductorTerminoDia
        return conductorTerminoDia

    def puede_seguir_recorriendo(self):
        return len(list(filter(lambda x: x.busPuedeIr, self.listaEstaciones))) > 0

    def run(self):
        c.acquire()
        time.sleep(2)

        return self.recorrer()


    def recorrer(self):
        self.activo = True
        self.calcularDistanciasAEstaciones()

        while self.listaEstaciones[0].distancia < math.inf:
            self.agregar_estacion()

            # print("Ruta ", self.ruta)
            # print("Horas en ruta ", self.horasEnRuta)
            # print("Detalles conductor ", self.conductor)
            # print("Costo ", self.kilometrosRecorridos * self.consumoGasolina * self.costoGalon)
            self.calcularDistanciasAEstaciones()
        self.finalizar_ruta()
       # c.acquire()
        print("Estado de estaciones ", end='')
        for estacionRuta in estacionesGlobales:
            print(estacionRuta.vecesVisitado, ", ", end='', sep="")
        print()
        # c.release()
        if self.debe_cambiar_conductor():
            self.conductor.activo = False
            resp = self.asignar_conductor()
            if resp is False:
                c.release()
                return False
            else:
                return self.recorrer()
        if self.puede_seguir_recorriendo():
            return self.recorrer()
        else:
            c.release()
            return False


for a in range(7):
    busesGlobales.append(Bus(f"Bus {a}", conductoresGlobales[a], 6))

horaInicio = 6

for hilo_ejecucion in busesGlobales:
    hilo_ejecucion.inicioHoraRuta = horaInicio
    hilo_ejecucion.start()

for hilo_ejecucion in busesGlobales:
    hilo_ejecucion.join()
    c.acquire()
    horaInicio = hilo_ejecucion.finHoraRuta
    c.release()








# def run(self):
#     global flag
#     global val  # made global here
#     while True:
#         c.acquire()
#         if flag == 0:
#             print "A: val=" + str(val)
#             time.sleep(0.1)
#             flag = 1
#             val = 30
#             c.notify_all()
#         else:
#             c.wait()
#         c.release()


# class Thread_B(threading.Thread):
#     def __init__(self, name):
#         threading.Thread.__init__(self)
#         self.name = name

#     def run(self):
#         global flag
#         global val  # made global here
#         while True:
#             c.acquire()
#             if flag == 1:
#                 print "B: val=" + str(val)
#                 time.sleep(0.5)
#                 flag = 0
#                 val = 20
#                 c.notify_all()
#             else:
#                 c.wait()
#             c.release()


# a = Thread_A("myThread_name_A")
# b = Thread_B("myThread_name_B")

# b.start()
# a.start()

# a.join()
# b.join()
