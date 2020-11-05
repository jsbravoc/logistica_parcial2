from math import isfinite
import threading
import time
import math
import copy
from operator import itemgetter, attrgetter
c = threading.Condition()

flag = 0  # shared between Thread_A and Thread_B
val = 20

class Localizacion:
    def __init__(self, nombre, x, y):
        self.nombre = nombre
        self.x = x
        self.y = y

    def __repr__(self):
        return repr((self.nombre, self.x, self.y))


class Estacion(Localizacion):
    def __init__(self, numeroPasajeros, *args, **kw):
        super().__init__(*args, **kw)
        self.numeroPasajeros = numeroPasajeros
        self.vecesVisitado = 0
        self.distancia = 0
        self.tiempo = 0

    def __repr__(self):
        return repr((self.nombre))


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

estacionesGlobalesDiccionario = {}
for estacion in estacionesGlobales:
    estacionesGlobalesDiccionario.setdefault(
        estacion.nombre, []).append(estacion)


Mantenimiento = Localizacion(nombre="Mantenimiento",x=-12, y=-10)
Estacionamiento = Localizacion(nombre="Estacionamiento", x=15, y=9)



class Bus(threading.Thread):
    def __init__(self, nombre, conductor):
        threading.Thread.__init__(self)
        self.nombre = nombre
        self.conductor = conductor
        conductor.activo = True
        self.cantidadPasajeros = 0
        self.haSidoDesinfectado = False
        self.estacionActual = Estacionamiento
        self.listaEstaciones = copy.deepcopy(estacionesGlobales)
        self.ruta = []
        self.horasEnRuta = 0
        self.maxHorasEnRuta = 5
        self.pasajerosABajarse = []
        self.velocidadEnKm = 30
        self.maxPasajeros = 16
        self.consumoGasolina = 0.09
        self.costoGalon = 8700
        self.kilometrosRecorridos = 0
        self.calcularDistanciasAEstaciones()
        self.distanciaEnKmAEstacionamiento = None,
        self.tiempoEnHorasAEstacionamiento = None


    def calcularDistanciasAEstaciones(self):
        self.distanciaEnKmAEstacionamiento, self.tiempoEnHorasAEstacionamiento = self.calcularDistanciaYTiempo(
            Mantenimiento, Estacionamiento)
        global estacionesGlobalesDiccionario
        for estacion in self.listaEstaciones:
            distanciaEnKm, tiempoEnHoras = self.calcularDistanciaYTiempo(
                self.estacionActual,
                estacion
            )
            distanciaEnKmAMantenimiento, tiempoEnHorasAMantenimiento = self.calcularDistanciaYTiempo(
                estacion,
                Mantenimiento
            )

            tiempoAdicional = tiempoEnHorasAMantenimiento + self.tiempoEnHorasAEstacionamiento
            
            estacionGlobal = estacionesGlobalesDiccionario[estacion.nombre][0]
            if self.horasEnRuta != 0 and (distanciaEnKm == 0 or 
                                          self.conductor.horasTrabajo + self.conductor.tiempoEsperaMantenimiento + tiempoEnHoras + tiempoAdicional > self.conductor.maxHorasTrabajo or
                                          self.horasEnRuta + tiempoEnHoras + tiempoAdicional > self.maxHorasEnRuta or
            self.cantidadPasajeros + estacion.numeroPasajeros - self.pasajerosABajarse[0] > self.maxPasajeros 
            or estacionGlobal.vecesVisitado >= 6):
                estacion.tiempo = math.inf
                estacion.distancia = math.inf
            else:
                estacion.tiempo = tiempoEnHoras
                estacion.distancia = distanciaEnKm
        self.listaEstaciones = sorted(self.listaEstaciones, key=attrgetter('distancia'))
    
    def validarOpciones(self):
        return (self.listaEstaciones[0].tiempo != math.inf)
    
    def agregarEstacion(self):
        global estacionesGlobalesDiccionario
        self.listaEstaciones[0].vecesVisitado += 1
        estacionesGlobalesDiccionario[self.listaEstaciones[0].nombre][0].vecesVisitado += 1
        if len(self.pasajerosABajarse) > 0:
            self.cantidadPasajeros = self.cantidadPasajeros - \
                self.pasajerosABajarse.pop(0)
        self.cantidadPasajeros = self.cantidadPasajeros + \
            self.listaEstaciones[0].numeroPasajeros
        self.calcularPasajerosABajarse(self.listaEstaciones[0])
        self.horasEnRuta = self.horasEnRuta + self.listaEstaciones[0].tiempo
        self.estacionActual =  self.listaEstaciones[0]
        self.ruta.append(self.listaEstaciones[0])
        self.kilometrosRecorridos = self.kilometrosRecorridos + \
            self.listaEstaciones[0].distancia
        self.conductor.horasTrabajo = self.conductor.horasTrabajo + \
            self.listaEstaciones[0].tiempo
        self.calcularDistanciasAEstaciones()


    def calcularDistanciaYTiempo(self, inicio, fin):
        distanciaEnKm = math.sqrt(
            math.pow(fin.x - inicio.x, 2) + math.pow(fin.y - inicio.y, 2)
        )
        tiempoEnHoras = distanciaEnKm / self.velocidadEnKm
        return [distanciaEnKm, tiempoEnHoras]

    def calcularPasajerosABajarse(self, estacion):
        global probabilidadDeBajarse
        if len(self.pasajerosABajarse) == 0:
            self.pasajerosABajarse = [
                estacion.numeroPasajeros * probabilidadDeBajarse[0],
                estacion.numeroPasajeros * probabilidadDeBajarse[1],
                estacion.numeroPasajeros * probabilidadDeBajarse[2],
            ]
        elif len(self.pasajerosABajarse) == 1:
            self.pasajerosABajarse[0] = self.pasajerosABajarse[0] + \
                estacion.numeroPasajeros * probabilidadDeBajarse[0]
            self.pasajerosABajarse.append(
                estacion.numeroPasajeros * probabilidadDeBajarse[1])
            self.pasajerosABajarse.append(
                estacion.numeroPasajeros * probabilidadDeBajarse[2])
        elif len(self.pasajerosABajarse) == 2:
            self.pasajerosABajarse[0] = self.pasajerosABajarse[0] + \
                estacion.numeroPasajeros * probabilidadDeBajarse[0]
            self.pasajerosABajarse[1] = self.pasajerosABajarse[1] + \
                estacion.numeroPasajeros * probabilidadDeBajarse[1]
            self.pasajerosABajarse.append(
                estacion.numeroPasajeros * probabilidadDeBajarse[2])
        elif len(self.pasajerosABajarse) == 3:
            self.pasajerosABajarse[0] = self.pasajerosABajarse[0] + \
                estacion.numeroPasajeros * probabilidadDeBajarse[0]
            self.pasajerosABajarse[1] = self.pasajerosABajarse[1] + \
                estacion.numeroPasajeros * probabilidadDeBajarse[1]
            self.pasajerosABajarse[2] = self.pasajerosABajarse[2] + \
                estacion.numeroPasajeros * probabilidadDeBajarse[2]

        self.pasajerosABajarse = [round(numPasajeros)
                                  for numPasajeros in self.pasajerosABajarse]
    
    def finalizarRuta(self):
        distanciaAMantenimiento, tiempoAMantenimiento = self.calcularDistanciaYTiempo(self.estacionActual, Mantenimiento)
        print("Ultima estación:", self.estacionActual);
        print("Cantidad pasajeros:", self.cantidadPasajeros)
        self.cantidadPasajeros = 0
        self.pasajerosABajarse = []

        self.horasEnRuta = self.horasEnRuta + tiempoAMantenimiento
        self.estacionActual = Mantenimiento
        self.ruta.append(Mantenimiento)
        self.kilometrosRecorridos = self.kilometrosRecorridos + \
            distanciaAMantenimiento
        self.conductor.horasTrabajo = self.conductor.horasTrabajo + \
            tiempoAMantenimiento + self.conductor.tiempoEsperaMantenimiento

        self.haSidoDesinfectado = True
        
        self.horasEnRuta = self.horasEnRuta + self.tiempoEnHorasAEstacionamiento
        self.estacionActual = Estacionamiento
        self.ruta.append(Estacionamiento)
        self.kilometrosRecorridos = self.kilometrosRecorridos + \
            self.distanciaEnKmAEstacionamiento
        self.conductor.horasTrabajo = self.conductor.horasTrabajo + \
           self.tiempoEnHorasAEstacionamiento

        self.haSidoDesinfectado = False

        self.calcularDistanciasAEstaciones()




    def recorrer(self):
        while self.listaEstaciones[0].distancia < math.inf:
            self.agregarEstacion()
            print("Ruta ", self.ruta)
            print("Horas ", self.horasEnRuta)
            print("Horas trabajadas ", self.conductor.horasTrabajo)
            print("Costo ", self.kilometrosRecorridos * self.consumoGasolina * self.costoGalon)
        self.finalizarRuta()
        print("Ruta ", self.ruta, sep="->")
        print("Horas ", self.horasEnRuta)
        print("Horas trabajadas ", self.conductor.horasTrabajo)
        print("Costo ", self.kilometrosRecorridos *
              self.consumoGasolina * self.costoGalon)
        for estacion in estacionesGlobales:
            print(estacion.vecesVisitado)



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


class Conductor:
    def __init__(self, nombre, horaInicio):
        self.nombre = nombre
        self.horaInicio = horaInicio
        self.horasTrabajo = 0
        self.activo = False
        self.maxHorasTrabajo = 10
        self.tiempoEsperaMantenimiento = 50/60


Bus("Bus 1", Conductor("Juan", 6)).recorrer()
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
