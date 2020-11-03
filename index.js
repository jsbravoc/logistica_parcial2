const { runInThisContext } = require("vm");

require("dotenv").config();
const plotly = require("plotly")(
  process.env.USUARIO,
  process.env.LLAVE_201712259
);
const _ = require("lodash");

/** Clase que representa un bus */
class Bus {
  #velocidadEnKm = 30;
  #costoGalon = 8700;
  #consumoGasolina = 0.09;
  #maxPasajeros = 16;
  #kilometrosRecorridos = 0;
  #listaEstaciones = [];
  constructor(conductor, estacionInicial) {
    this.conductor = conductor;
    conductor.activo = true;
    this.cantidadPasajeros = estacionInicial.numeroPasajeros;
    this.haSidoDesinfectado = false;
    this.estacionActual = estacionInicial;
    this.ruta = [estacionInicial];
    this.horasEnRuta = 0;
    this.pasajerosABajarse = [];
    this.calcularPasajerosABajarse(estacionInicial);
    this.calcularDistanciasAEstaciones();
  }

  calcularDistanciaYTiempo(inicio, fin) {
    const distanciaEnKm = Math.sqrt(
      Math.pow(fin.x - inicio.x, 2) + Math.pow(fin.y - inicio.y, 2)
    );
    const tiempoEnHoras = distanciaEnKm / this.#velocidadEnKm;
    return { distanciaEnKm, tiempoEnHoras };
  }

  calcularPasajerosABajarse(estacion) {
    if (this.pasajerosABajarse == null || this.pasajerosABajarse.length === 0) {
      this.pasajerosABajarse = [
        estacion.numeroPasajeros * probabilidadDeBajarse[0],
        estacion.numeroPasajeros * probabilidadDeBajarse[1],
        estacion.numeroPasajeros * probabilidadDeBajarse[2],
      ];
    } else if (this.pasajerosABajarse.length === 1) {
      this.pasajerosABajarse[0] +=
        estacion.numeroPasajeros * probabilidadDeBajarse[0];
      this.pasajerosABajarse.push(
        estacion.numeroPasajeros * probabilidadDeBajarse[1]
      );
      this.pasajerosABajarse.push(
        estacion.numeroPasajeros * probabilidadDeBajarse[2]
      );
    } else if (this.pasajerosABajarse.length === 2) {
      this.pasajerosABajarse[0] +=
        estacion.numeroPasajeros * probabilidadDeBajarse[0];
      this.pasajerosABajarse[1] +=
        estacion.numeroPasajeros * probabilidadDeBajarse[1];
      this.pasajerosABajarse.push(
        estacion.numeroPasajeros * probabilidadDeBajarse[2]
      );
    } else if (this.pasajerosABajarse.length === 3) {
      this.pasajerosABajarse[0] +=
        estacion.numeroPasajeros * probabilidadDeBajarse[0];
      this.pasajerosABajarse[1] +=
        estacion.numeroPasajeros * probabilidadDeBajarse[1];
      this.pasajerosABajarse[2] +=
        estacion.numeroPasajeros * probabilidadDeBajarse[2];
    }
    this.pasajerosABajarse = this.pasajerosABajarse.map((x) => Math.round(x));
  }

  calcularDistanciasAEstaciones() {
    if (this.#listaEstaciones.length > 0) {
        this.#listaEstaciones.forEach((estacion, index, lista) => {
            const { distanciaEnKm, tiempoEnHoras } = this.calcularDistanciaYTiempo(
                this.estacionActual,
                estacion
            );
            const localizacion = localizaciones[estacion.nombre];
            const estacionActualizada = _.cloneDeep(estacion);
            if ( distanciaEnKm === 0 ||
                this.horasEnRuta + tiempoEnHoras > 5 ||
                this.conductor.horasTrabajo + tiempoEnHoras > 10 ||
                this.cantidadPasajeros +
                estacion.numeroPasajeros -
                this.pasajerosABajarse[0] >
                this.#maxPasajeros ||
                localizacion.vecesVisitado >= 6
            ) {
                estacionActualizada.tiempo = Infinity;
                estacionActualizada.distancia = Infinity;
            } else {
                estacionActualizada.tiempo = tiempoEnHoras;
                estacionActualizada.distancia = distanciaEnKm;
            }
            lista[index] = estacionActualizada;
      });
      this.#listaEstaciones = this.#listaEstaciones.sort(
        (a, b) => a.distancia - b.distancia
      );
    } else {
      for (const localizacion in localizaciones) {
        if (
          localizaciones.hasOwnProperty(localizacion) &&
          localizacion.includes("Estación")
        ) {
          const estacion = localizaciones[localizacion];
          const {
            distanciaEnKm,
            tiempoEnHoras,
          } = this.calcularDistanciaYTiempo(this.estacionActual, estacion);
          if (distanciaEnKm === 0) continue;
          const estacionAAgregar = _.cloneDeep(estacion);
          estacionAAgregar.distancia = distanciaEnKm;
          estacionAAgregar.tiempo = tiempoEnHoras;
          estacionAAgregar.nombre = localizacion;
          this.#listaEstaciones.push(estacionAAgregar);
        }
      }
      this.#listaEstaciones = this.#listaEstaciones.sort(
        (a, b) => a.distancia - b.distancia
      );
    }
  }

  validarOpciones() {
    return (
      this.#listaEstaciones[0] && this.#listaEstaciones[0].tiempo !== Infinity
    );
  }
  agregarEstacion() {
    this.#listaEstaciones[0].vecesVisitado += 1;
    const estacionMasCercana = this.#listaEstaciones[0];
    localizaciones[estacionMasCercana.nombre].vecesVisitado += 1;
    this.cantidadPasajeros -= this.pasajerosABajarse.shift();
    this.cantidadPasajeros += estacionMasCercana.numeroPasajeros;
    this.calcularPasajerosABajarse(estacionMasCercana);
    this.horasEnRuta += estacionMasCercana.tiempo;
    this.estacionActual = estacionMasCercana;
    this.ruta.push(estacionMasCercana);
    this.#kilometrosRecorridos += estacionMasCercana.distancia;
    this.conductor.horasTrabajo += estacionMasCercana.tiempo;
    this.calcularDistanciasAEstaciones();
  }

  asignarConductor() {
    const conductor = this.conductores.find(
      (x) => x.activo === false && x.horasTrabajo < 10
    );
    if (conductor != null) {
      conductor.activo = true;
      this.conductor = conductor;
      return true;
    }
    return false;
  }

  recorrer() {
    while (this.validarOpciones()) {
      this.agregarEstacion();
      console.log("Ruta:", this.ruta);
      console.log("Horas:", this.horasEnRuta);
      console.log("Horas trabajadas:", this.conductor.horasTrabajo);
      console.log(
        "Costo:",
        this.#kilometrosRecorridos * this.#consumoGasolina * this.#costoGalon
      );
    }
  }
}

/** Clase que representa un conductor */
class Conductor {
  constructor(nombre, horaInicio) {
    this.nombre = nombre;
    this.horasTrabajo = 0;
    this.horaInicio = horaInicio;
    this.activo = false;
  }
}

const fechaInicio = new Date(2020, 11, 2, 6, 0);
const fechaFin = new Date(2020, 11, 2, 23, 0);

const probabilidadDeBajarse = [0.2, 0.5, 0.3];
const localizaciones = {
  "Estación 1": { x: 1, y: 4, numeroPasajeros: 10, vecesVisitado: 0 },
  "Estación 2": { x: 1, y: 7, numeroPasajeros: 6, vecesVisitado: 0 },
  "Estación 3": { x: 2, y: 9, numeroPasajeros: 7, vecesVisitado: 0 },
  "Estación 4": { x: 6, y: -1, numeroPasajeros: 5, vecesVisitado: 0 },
  "Estación 5": { x: 4, y: -5, numeroPasajeros: 5, vecesVisitado: 0 },
  "Estación 6": { x: 4, y: 1, numeroPasajeros: 8, vecesVisitado: 0 },
  "Estación 7": { x: -6, y: -4, numeroPasajeros: 10, vecesVisitado: 0 },
  "Estación 8": { x: 7, y: 9, numeroPasajeros: 10, vecesVisitado: 0 },
  "Estación 9": { x: 2, y: 10, numeroPasajeros: 6, vecesVisitado: 0 },
  "Estación 10": { x: 6, y: 6, numeroPasajeros: 8, vecesVisitado: 0 },
  Mantenimiento: { x: -12, y: -10 },
  Estacionamiento: { x: 15, y: 9 },
};

const estacionamiento = {
  x: [localizaciones.Estacionamiento.x],
  y: [localizaciones.Estacionamiento.y],
  mode: "markers",
  type: "scatter",
  name: "Estacionamiento",
  marker: { size: 12 },
};
const mantenimiento = {
  x: [localizaciones.Mantenimiento.x],
  y: [localizaciones.Mantenimiento.y],
  mode: "markers",
  type: "scatter",
  name: "Mantenimiento",
  marker: { size: 12 },
};

const data = [estacionamiento, mantenimiento];

for (const localizacion in localizaciones) {
  if (
    localizaciones.hasOwnProperty(localizacion) &&
    localizacion.startsWith("Estación")
  ) {
    const estacion = localizaciones[localizacion];
    const dataEstacion = {
      x: [estacion.x],
      y: [estacion.y],
      mode: "markers",
      type: "scatter",
      name: localizacion,
      text: [`Cantidad de pasajeros: ${estacion.numeroPasajeros}`],
      marker: { size: Math.ceil(estacion.numeroPasajeros * 1.5) },
    };
    data.push(dataEstacion);
  }
}

new Bus(new Conductor("Juan", 6), localizaciones["Estación 1"]).recorrer();
// const graphOptions = {
//   filename: "line-scatter",
//   fileopt: "overwrite",
//   layout: {
//     hovermode: "closest",
//   },
// };
// plotly.plot(data, graphOptions, function (err, msg) {
//   console.log(msg);
// });
